GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.rename_company(company uuid,expected_revision integer,new_name text,purpose uuid,operation_key uuid)
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
 WHERE (tenant_id,id,revision)=(a.tenant_id,rename_company.company,expected_revision) AND removed_at IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
 PERFORM cv.command_finish(a.tenant_id,purpose,'company.rename',operation_key,h,NULL,company);
 RETURN company;
END $$;

CREATE OR REPLACE FUNCTION cv.move_stage(scope uuid,application uuid,expected_revision integer,target cv.stage,reason text,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; row cv.application; p uuid; h cv.digest; result uuid; allowed boolean; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 p:=cv.lock_scope(a.tenant_id,scope);
 h:=encode(sha256(convert_to(jsonb_build_array(scope,application,expected_revision,target,reason)::text,'UTF8')),'hex');
 result:=cv.command_begin(a.tenant_id,p,'application.stage',operation_key,h);
 IF result IS NOT NULL THEN RETURN result; END IF;
 SELECT * INTO row FROM cv.application WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,move_stage.application) FOR UPDATE;
 IF NOT FOUND OR row.revision<>expected_revision OR row.removed_at IS NOT NULL THEN
  RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
 allowed:= (row.stage='received' AND target='evaluating')
 OR (row.stage='evaluating' AND target='interview') OR (row.stage='interview' AND target='hired')
 OR (row.stage IN ('received','evaluating','interview') AND target='not_continuing')
 OR (coalesce(btrim(reason),'')<>'' AND ((row.stage='evaluating' AND target='received')
 OR (row.stage='interview' AND target='evaluating')
 OR (row.stage IN ('hired','not_continuing') AND target='received' AND a.role='admin')));
 IF NOT allowed THEN RAISE EXCEPTION 'STAGE_TRANSITION_DENIED' USING ERRCODE='23514'; END IF;
 UPDATE cv.application SET stage=target,revision=revision+1 WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,move_stage.application);
 result:=gen_random_uuid();
 INSERT INTO cv.stage_event(tenant_id,scope_id,id,application_id,from_stage,to_stage,revision,actor_id,reason)
 VALUES(a.tenant_id,scope,result,application,row.stage,target,row.revision+1,a.user_id,reason);
 PERFORM cv.command_finish(a.tenant_id,p,'application.stage',operation_key,h,scope,result);
 RETURN result;
END $$;


CREATE OR REPLACE FUNCTION cv.erase_scope(scope uuid,request_id uuid) RETURNS uuid
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
 THEN 'files_pending' ELSE 'database_purged' END WHERE (tenant_id,id)=(a.tenant_id,erase_scope.request_id);
 DELETE FROM cv.erasure_context WHERE backend_pid=pg_backend_pid();
 RETURN request_id;
END $$;


RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
