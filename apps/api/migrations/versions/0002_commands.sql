GRANT CREATE ON SCHEMA cv TO cv_guard;

CREATE TABLE cv.erasure_context (
 backend_pid integer PRIMARY KEY, transaction_id xid8 NOT NULL, tenant_id uuid NOT NULL, scope_id uuid NOT NULL
);
ALTER TABLE cv.erasure_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv.erasure_context FORCE ROW LEVEL SECURITY;
CREATE POLICY guard ON cv.erasure_context TO cv_guard USING(true) WITH CHECK(true);
GRANT SELECT,INSERT,UPDATE,DELETE ON cv.erasure_context TO cv_guard;

CREATE OR REPLACE FUNCTION cv.immutable_row() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='DELETE' AND current_user='cv_guard' AND EXISTS(SELECT 1 FROM cv.erasure_context c
 WHERE c.backend_pid=pg_backend_pid() AND c.transaction_id=pg_current_xact_id()
 AND c.tenant_id=(to_jsonb(OLD)->>'tenant_id')::uuid AND c.scope_id=(to_jsonb(OLD)->>'scope_id')::uuid)
 THEN RETURN OLD; END IF;
 RAISE EXCEPTION 'IMMUTABLE_HISTORY' USING ERRCODE='23514';
END $$;

CREATE FUNCTION cv.require_authority(t uuid, admin_only boolean) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; BEGIN
 SELECT * INTO a FROM cv.current_authority() WHERE tenant_id=t;
 IF NOT FOUND OR (admin_only AND a.role<>'admin') THEN
  RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 RETURN a.user_id;
END $$;
CREATE FUNCTION cv.lock_scope(t uuid,s uuid) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a uuid; p cv.privacy_scope; BEGIN
 a:=cv.require_authority(t,false);
 SELECT * INTO p FROM cv.privacy_scope WHERE (tenant_id,id)=(t,s) FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'SCOPE_DENIED' USING ERRCODE='42501'; END IF;
 PERFORM 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=(t,a,p.purpose_id) FOR SHARE;
 PERFORM 1 FROM cv.policy_version WHERE tenant_id=t AND id IN
 (p.purpose_id,p.source_policy_id,p.consent_policy_id,p.retention_policy_id,p.erasure_policy_id,p.resource_policy_id)
 ORDER BY id FOR SHARE;
 IF NOT cv.scope_allowed(t,s) THEN RAISE EXCEPTION 'SCOPE_DENIED' USING ERRCODE='42501'; END IF;
 RETURN p.purpose_id;
END $$;
CREATE FUNCTION cv.revocation_lock() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(NEW.tenant_id,NEW.policy_id) FOR UPDATE;
 RETURN NEW;
END $$;
CREATE TRIGGER revoke_policy_lock BEFORE INSERT ON cv.policy_revocation
 FOR EACH ROW EXECUTE FUNCTION cv.revocation_lock();

-- One active command key serializes only its own actor/purpose/operation partition.
CREATE FUNCTION cv.command_begin(t uuid,p uuid,op text,k uuid,payload cv.digest) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a uuid; found_result cv.command_result; BEGIN
 a:=cv.require_authority(t,false);
 PERFORM pg_advisory_xact_lock(hashtextextended(t::text||a::text||p::text||op||k::text,0));
 SELECT * INTO found_result FROM cv.command_result WHERE
 (tenant_id,actor_id,purpose_id,operation,operation_key)=(t,a,p,op,k);
 IF FOUND THEN
  IF found_result.payload_digest<>payload THEN RAISE EXCEPTION 'IDEMPOTENCY_CONFLICT' USING ERRCODE='23514'; END IF;
  IF found_result.scope_id IS NOT NULL THEN PERFORM cv.lock_scope(t,found_result.scope_id); END IF;
  RETURN found_result.result_id;
 END IF;
 RETURN NULL;
END $$;
CREATE FUNCTION cv.command_finish(t uuid,p uuid,op text,k uuid,payload cv.digest,s uuid,result uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a uuid; BEGIN
 a:=cv.require_authority(t,false);
 INSERT INTO cv.command_result VALUES(t,a,p,op,k,payload,s,result);
 INSERT INTO cv.audit_event(tenant_id,id,actor_id,scope_id,action,record_id)
 VALUES(t,gen_random_uuid(),a,s,op,result);
END $$;

CREATE FUNCTION cv.rename_company(company uuid,expected_revision integer,new_name text,purpose uuid,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; h cv.digest; existing uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=(a.tenant_id,a.user_id,purpose) AND active FOR SHARE;
 IF NOT FOUND OR NOT cv.policy_live(a.tenant_id,purpose,'purpose') THEN RAISE EXCEPTION 'PURPOSE_DENIED' USING ERRCODE='42501'; END IF;
 IF btrim(new_name)='' THEN RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
 h:=encode(sha256(convert_to(jsonb_build_array(company,expected_revision,new_name)::text,'UTF8')),'hex');
 existing:=cv.command_begin(a.tenant_id,purpose,'company.rename',operation_key,h);
 IF existing IS NOT NULL THEN RETURN existing; END IF;
 UPDATE cv.company SET name=new_name,revision=revision+1
 WHERE (tenant_id,id,revision)=(a.tenant_id,company,expected_revision) AND removed_at IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
 PERFORM cv.command_finish(a.tenant_id,purpose,'company.rename',operation_key,h,NULL,company);
 RETURN company;
END $$;
CREATE FUNCTION cv.move_stage(scope uuid,application uuid,expected_revision integer,target cv.stage,reason text,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; row cv.application; p uuid; h cv.digest; result uuid; allowed boolean; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 p:=cv.lock_scope(a.tenant_id,scope);
 h:=encode(sha256(convert_to(jsonb_build_array(scope,application,expected_revision,target,reason)::text,'UTF8')),'hex');
 result:=cv.command_begin(a.tenant_id,p,'application.stage',operation_key,h);
 IF result IS NOT NULL THEN RETURN result; END IF;
 SELECT * INTO row FROM cv.application WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,application) FOR UPDATE;
 IF NOT FOUND OR row.revision<>expected_revision OR row.removed_at IS NOT NULL THEN
  RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
 allowed:= (row.stage='received' AND target='evaluating')
 OR (row.stage='evaluating' AND target='interview') OR (row.stage='interview' AND target='hired')
 OR (row.stage IN ('received','evaluating','interview') AND target='not_continuing')
 OR (coalesce(btrim(reason),'')<>'' AND ((row.stage='evaluating' AND target='received')
 OR (row.stage='interview' AND target='evaluating')
 OR (row.stage IN ('hired','not_continuing') AND target='received' AND a.role='admin')));
 IF NOT allowed THEN RAISE EXCEPTION 'STAGE_TRANSITION_DENIED' USING ERRCODE='23514'; END IF;
 UPDATE cv.application SET stage=target,revision=revision+1 WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,application);
 result:=gen_random_uuid();
 INSERT INTO cv.stage_event(tenant_id,scope_id,id,application_id,from_stage,to_stage,revision,actor_id,reason)
 VALUES(a.tenant_id,scope,result,application,row.stage,target,row.revision+1,a.user_id,reason);
 PERFORM cv.command_finish(a.tenant_id,p,'application.stage',operation_key,h,scope,result);
 RETURN result;
END $$;

CREATE FUNCTION cv.claim_extraction(scope uuid,content cv.digest,parser cv.digest,normalization cv.digest,definition jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; result uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.lock_scope(a.tenant_id,scope);
 INSERT INTO cv.extraction(tenant_id,scope_id,id,content_digest,parser_digest,normalization_digest,definition,state)
 VALUES(a.tenant_id,scope,gen_random_uuid(),content,parser,normalization,definition,'claimed')
 ON CONFLICT(tenant_id,scope_id,content_digest,parser_digest,normalization_digest) DO NOTHING RETURNING id INTO result;
 IF result IS NULL THEN
  SELECT id INTO result FROM cv.extraction WHERE (tenant_id,scope_id,content_digest,parser_digest,normalization_digest)
  =(a.tenant_id,scope,content,parser,normalization) AND cv.extraction.definition=claim_extraction.definition;
  IF result IS NULL THEN RAISE EXCEPTION 'DEFINITION_CONFLICT' USING ERRCODE='23514'; END IF;
 ELSE
  INSERT INTO cv.audit_event(tenant_id,id,actor_id,scope_id,action,record_id)
  VALUES(a.tenant_id,gen_random_uuid(),a.user_id,scope,'extraction.claim',result);
 END IF;
 RETURN result;
END $$;
CREATE FUNCTION cv.claim_evaluation(scope uuid,target_position uuid,rubric uuid,jd uuid,engine uuid,facts cv.digest,calculation cv.digest,definition jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; result uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.lock_scope(a.tenant_id,scope);
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision WHERE (tenant_id,scope_id,factual_digest)=(a.tenant_id,scope,facts)) THEN
  RAISE EXCEPTION 'FACTS_REQUIRED' USING ERRCODE='23514'; END IF;
 INSERT INTO cv.evaluation(tenant_id,scope_id,id,position_id,rubric_id,jd_id,engine_id,factual_digest,calculation_digest,calculation_definition,state)
 VALUES(a.tenant_id,scope,gen_random_uuid(),target_position,rubric,jd,engine,facts,calculation,definition,'claimed')
 ON CONFLICT(tenant_id,scope_id,position_id,factual_digest,calculation_digest) DO NOTHING RETURNING id INTO result;
 IF result IS NULL THEN
  SELECT id INTO result FROM cv.evaluation WHERE
  (tenant_id,scope_id,position_id,factual_digest,calculation_digest,rubric_id,jd_id,engine_id)
  =(a.tenant_id,scope,target_position,facts,calculation,rubric,jd,engine) AND calculation_definition=definition;
  IF result IS NULL THEN RAISE EXCEPTION 'DEFINITION_CONFLICT' USING ERRCODE='23514'; END IF;
 ELSE
  INSERT INTO cv.audit_event(tenant_id,id,actor_id,scope_id,action,record_id)
  VALUES(a.tenant_id,gen_random_uuid(),a.user_id,scope,'evaluation.claim',result);
 END IF;
 RETURN result;
END $$;

CREATE FUNCTION cv.erase_scope(scope uuid,request_id uuid) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; p uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.require_authority(a.tenant_id,true);
 SELECT purpose_id INTO p FROM cv.privacy_scope WHERE (tenant_id,id)=(a.tenant_id,scope) FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'SCOPE_DENIED' USING ERRCODE='42501'; END IF;
 -- Erasure must still work after consent expiry/revocation; admin and erasure policy are separate authority.
 IF NOT EXISTS(SELECT 1 FROM cv.privacy_scope s WHERE (s.tenant_id,s.id)=(a.tenant_id,scope)
 AND cv.policy_live(s.tenant_id,s.erasure_policy_id,'erasure')) THEN
  RAISE EXCEPTION 'ERASURE_POLICY_REQUIRED' USING ERRCODE='42501'; END IF;
 INSERT INTO cv.erasure_request(tenant_id,id,scope_id,actor_id,status) VALUES(a.tenant_id,request_id,scope,a.user_id,'requested');
 INSERT INTO cv.erasure_file SELECT a.tenant_id,request_id,object_key,NULL FROM cv.file_intent WHERE (tenant_id,scope_id)=(a.tenant_id,scope);
 INSERT INTO cv.erasure_context VALUES(pg_backend_pid(),pg_current_xact_id(),a.tenant_id,scope)
 ON CONFLICT(backend_pid) DO UPDATE SET transaction_id=excluded.transaction_id,tenant_id=excluded.tenant_id,scope_id=excluded.scope_id;
 DELETE FROM cv.privacy_scope WHERE (tenant_id,id)=(a.tenant_id,scope);
 UPDATE cv.erasure_request SET status=CASE WHEN EXISTS(SELECT 1 FROM cv.erasure_file WHERE (tenant_id,cv.erasure_file.request_id)=(a.tenant_id,erase_scope.request_id))
 THEN 'files_pending' ELSE 'database_purged' END WHERE (tenant_id,id)=(a.tenant_id,request_id);
 DELETE FROM cv.erasure_context WHERE backend_pid=pg_backend_pid();
 RETURN request_id;
END $$;

CREATE FUNCTION cv.database_ready() RETURNS text
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT version_num::text FROM public.alembic_version
$$;
GRANT SELECT ON public.alembic_version TO cv_guard;

DO $$ DECLARE r record; cols text; BEGIN
 FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='cv' AND tablename NOT IN
 ('transaction_context','erasure_context','agency','staff_session','staff_user','membership','purpose_grant','erasure_request','erasure_file') LOOP
  EXECUTE format('CREATE CONSTRAINT TRIGGER final_auth AFTER INSERT OR UPDATE ON cv.%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_authority_check()',r.tablename);
 END LOOP;
 FOR r IN SELECT c.oid,c.conname,c.conrelid::regclass AS relation,c.conkey FROM pg_constraint c
 JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='cv' AND c.contype='f'
 AND NOT EXISTS(SELECT 1 FROM pg_index i WHERE i.indrelid=c.conrelid AND i.indisvalid
 AND (i.indkey::smallint[])[0:cardinality(c.conkey)-1]=c.conkey) LOOP
  SELECT string_agg(quote_ident(a.attname),',' ORDER BY x.ordinality) INTO cols
  FROM unnest(r.conkey) WITH ORDINALITY x(attnum,ordinality)
  JOIN pg_attribute a ON a.attrelid=r.relation AND a.attnum=x.attnum;
  EXECUTE format('CREATE INDEX %I ON %s(%s)','fk_'||substr(md5(r.conname||r.relation::text),1,20),r.relation,cols);
 END LOOP;
 FOR r IN SELECT p.oid::regprocedure AS identity FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='cv' AND p.prosecdef LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO cv_guard',r.identity);
 END LOOP;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cv FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA cv TO cv_guard;
GRANT EXECUTE ON FUNCTION cv.rename_company(uuid,integer,text,uuid,uuid),cv.move_stage(uuid,uuid,integer,cv.stage,text,uuid),
 cv.claim_extraction(uuid,cv.digest,cv.digest,cv.digest,jsonb),cv.claim_evaluation(uuid,uuid,uuid,uuid,uuid,cv.digest,cv.digest,jsonb),
 cv.erase_scope(uuid,uuid) TO cv_runtime;
GRANT EXECUTE ON FUNCTION cv.database_ready() TO cv_runtime,cv_public,cv_probe;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
