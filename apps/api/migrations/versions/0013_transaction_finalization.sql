-- Private, connection-local obligations disappear on commit/rollback, including
-- erased scope identifiers. Early validation never clears this table.
DO $$ BEGIN
 EXECUTE format('GRANT TEMPORARY ON DATABASE %I TO cv_guard',current_database());
END $$;
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;

CREATE FUNCTION cv.ensure_obligations() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF to_regclass('pg_temp.cv_authority_obligations') IS NULL THEN
  CREATE TEMPORARY TABLE cv_authority_obligations (
   backend_pid integer NOT NULL DEFAULT pg_backend_pid(),
   transaction_id xid8 NOT NULL DEFAULT pg_current_xact_id(),
   kind text NOT NULL CHECK(kind IN ('scope','purpose','public','erasure')),
   tenant_id uuid NOT NULL, actor_id uuid, subject_id uuid NOT NULL,
   UNIQUE NULLS NOT DISTINCT(kind,tenant_id,actor_id,subject_id)
  ) ON COMMIT DROP;
  ALTER TABLE pg_temp.cv_authority_obligations ENABLE ROW LEVEL SECURITY;
  ALTER TABLE pg_temp.cv_authority_obligations FORCE ROW LEVEL SECURITY;
  CREATE POLICY guard ON pg_temp.cv_authority_obligations TO cv_guard USING(true) WITH CHECK(true);
  REVOKE ALL ON pg_temp.cv_authority_obligations FROM PUBLIC;
 ELSIF NOT EXISTS(SELECT 1 FROM pg_class WHERE oid=to_regclass('pg_temp.cv_authority_obligations')
   AND relowner='cv_guard'::regrole AND relkind='r' AND relpersistence='t'
   AND relrowsecurity AND relforcerowsecurity) THEN
  RAISE EXCEPTION 'TRANSACTION_STATE_INVALID' USING ERRCODE='42501';
 END IF;
END $$;

CREATE FUNCTION cv.register_obligation(kind text,t uuid,a uuid,subject uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 PERFORM cv.ensure_obligations();
 INSERT INTO pg_temp.cv_authority_obligations(kind,tenant_id,actor_id,subject_id)
 VALUES(kind,t,a,subject) ON CONFLICT DO NOTHING;
END $$;

CREATE FUNCTION cv.lock_authority_policies(t uuid,definition jsonb) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 PERFORM 1 FROM cv.policy_version WHERE tenant_id=t AND id IN
 ((definition->>'purpose_id')::uuid,(definition->>'source_policy_id')::uuid,
 (definition->>'consent_policy_id')::uuid,(definition->>'retention_policy_id')::uuid,
 (definition->>'erasure_policy_id')::uuid,(definition->>'resource_policy_id')::uuid)
 ORDER BY id FOR SHARE;
END $$;

CREATE FUNCTION cv.policy_live_at(t uuid,p uuid,k text,instant timestamptz) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.policy_version v WHERE (v.tenant_id,v.id,v.kind)=(t,p,k)
 AND v.activated_at<=instant AND v.expires_at>instant
 AND NOT EXISTS(SELECT 1 FROM cv.policy_revocation r WHERE (r.tenant_id,r.policy_id)=(t,p)))
$$;

CREATE FUNCTION cv.authority_policies_live(t uuid,definition jsonb,instant timestamptz) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT bool_and(cv.policy_live_at(t,(definition->>column_name)::uuid,kind,instant))
 FROM (VALUES ('purpose','purpose_id'),('source','source_policy_id'),
 ('consent','consent_policy_id'),('retention','retention_policy_id'),
 ('erasure','erasure_policy_id'),('resource','resource_policy_id')) AS pins(kind,column_name)
$$;

CREATE FUNCTION cv.validate_transaction() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE o record; context cv.transaction_context; s cv.privacy_scope; p cv.publication;
 i cv.intake; g cv.public_upload_grant; instant timestamptz; staff_role text; cap integer;
BEGIN
 IF session_user NOT IN ('cv_runtime','cv_public') THEN
  RAISE EXCEPTION 'TRANSACTION_ROLE_INVALID' USING ERRCODE='42501'; END IF;
 PERFORM cv.ensure_obligations();
 IF session_user='cv_runtime' THEN
  SELECT * INTO context FROM cv.transaction_context WHERE backend_pid=pg_backend_pid()
  AND transaction_id=pg_current_xact_id();
  IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
  PERFORM 1 FROM cv.staff_session ss JOIN cv.membership m
  ON (m.tenant_id,m.user_id)=(ss.tenant_id,ss.user_id)
  JOIN cv.staff_user u ON (u.tenant_id,u.id)=(m.tenant_id,m.user_id)
  WHERE (ss.tenant_id,ss.id,ss.user_id)=(context.tenant_id,context.session_id,context.user_id)
  FOR SHARE OF ss,m,u;
 END IF;
 -- Acquire every potentially blocking lock before taking the validation clock.
 FOR o IN SELECT * FROM pg_temp.cv_authority_obligations ORDER BY kind,tenant_id,subject_id LOOP
  IF o.backend_pid<>pg_backend_pid() OR o.transaction_id<>pg_current_xact_id() THEN
   RAISE EXCEPTION 'TRANSACTION_STATE_INVALID' USING ERRCODE='42501'; END IF;
  IF o.kind='scope' THEN
   SELECT * INTO s FROM cv.privacy_scope WHERE (tenant_id,id)=(o.tenant_id,o.subject_id) FOR SHARE;
   PERFORM 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=
    (o.tenant_id,o.actor_id,s.purpose_id) FOR SHARE;
   PERFORM cv.lock_authority_policies(o.tenant_id,to_jsonb(s));
  ELSIF o.kind='purpose' THEN
   PERFORM 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=
    (o.tenant_id,o.actor_id,o.subject_id) FOR SHARE;
   PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(o.tenant_id,o.subject_id) FOR SHARE;
  ELSIF o.kind='erasure' THEN
   PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(o.tenant_id,o.subject_id) FOR SHARE;
  ELSE
   SELECT * INTO i FROM cv.intake WHERE (tenant_id,receipt)=(o.tenant_id,o.subject_id) FOR SHARE;
   SELECT * INTO p FROM cv.publication WHERE (tenant_id,id)=(i.tenant_id,i.publication_id) FOR SHARE;
   PERFORM 1 FROM cv.position j JOIN cv.company c ON (c.tenant_id,c.id)=(j.tenant_id,j.company_id)
    WHERE (j.tenant_id,j.id)=(p.tenant_id,p.position_id) FOR SHARE OF j,c;
   PERFORM 1 FROM cv.privacy_scope WHERE (tenant_id,id)=(i.tenant_id,i.scope_id) FOR SHARE;
   PERFORM 1 FROM cv.public_upload_grant WHERE (tenant_id,id)=(i.tenant_id,i.upload_grant_id) FOR SHARE;
   PERFORM cv.lock_authority_policies(o.tenant_id,to_jsonb(p));
  END IF;
 END LOOP;
 instant:=clock_timestamp();
 IF session_user='cv_runtime' THEN
  SELECT m.role INTO staff_role FROM cv.staff_session ss JOIN cv.membership m
  ON (m.tenant_id,m.user_id)=(ss.tenant_id,ss.user_id)
  JOIN cv.staff_user u ON (u.tenant_id,u.id)=(m.tenant_id,m.user_id)
  WHERE (ss.tenant_id,ss.id,ss.user_id)=(context.tenant_id,context.session_id,context.user_id)
  AND ss.revoked_at IS NULL AND ss.expires_at>instant AND m.active AND u.active;
  IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 END IF;
 FOR o IN SELECT * FROM pg_temp.cv_authority_obligations ORDER BY kind,tenant_id,subject_id LOOP
  IF o.kind<>'public' AND (session_user<>'cv_runtime' OR
    (o.tenant_id,o.actor_id) IS DISTINCT FROM (context.tenant_id,context.user_id)) THEN
   RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501'; END IF;
  IF o.kind='scope' THEN
   SELECT * INTO s FROM cv.privacy_scope WHERE (tenant_id,id)=(o.tenant_id,o.subject_id);
   IF NOT FOUND OR s.revoked_at IS NOT NULL OR s.consent_expires_at<=instant
   OR NOT cv.authority_policies_live(o.tenant_id,to_jsonb(s),instant)
   OR NOT EXISTS(SELECT 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=
    (o.tenant_id,o.actor_id,s.purpose_id) AND active) THEN
    RAISE EXCEPTION 'SCOPE_DENIED' USING ERRCODE='42501'; END IF;
  ELSIF o.kind='purpose' THEN
   IF NOT cv.policy_live_at(o.tenant_id,o.subject_id,'purpose',instant)
   OR NOT EXISTS(SELECT 1 FROM cv.purpose_grant WHERE (tenant_id,user_id,purpose_id)=
    (o.tenant_id,o.actor_id,o.subject_id) AND active) THEN
    RAISE EXCEPTION 'COMMAND_PURPOSE_REVOKED' USING ERRCODE='42501'; END IF;
  ELSIF o.kind='erasure' THEN
   IF staff_role<>'admin' OR NOT cv.policy_live_at(o.tenant_id,o.subject_id,'erasure',instant) THEN
    RAISE EXCEPTION 'ERASURE_AUTH_REVOKED' USING ERRCODE='42501'; END IF;
  ELSE
   IF session_user<>'cv_public' THEN RAISE EXCEPTION 'TRANSACTION_ROLE_INVALID' USING ERRCODE='42501'; END IF;
   SELECT * INTO i FROM cv.intake WHERE (tenant_id,receipt)=(o.tenant_id,o.subject_id);
   SELECT * INTO p FROM cv.publication WHERE (tenant_id,id)=(i.tenant_id,i.publication_id);
   SELECT * INTO s FROM cv.privacy_scope WHERE (tenant_id,id)=(i.tenant_id,i.scope_id);
   SELECT * INTO g FROM cv.public_upload_grant WHERE (tenant_id,id)=(i.tenant_id,i.upload_grant_id);
   SELECT (definition->>'public_submission_quota')::integer INTO cap
    FROM cv.policy_version WHERE (tenant_id,id)=(p.tenant_id,p.resource_policy_id);
   IF p.id IS NULL OR s.id IS NULL OR g.id IS NULL OR p.state<>'published'
   OR p.snapshot_id IS DISTINCT FROM i.snapshot_id OR p.expires_at<=instant OR g.expires_at<=instant
   OR s.revoked_at IS NOT NULL OR s.consent_expires_at<=instant
   OR NOT cv.authority_policies_live(o.tenant_id,to_jsonb(p),instant)
   OR cap IS NULL OR cap<=0 OR (SELECT count(*) FROM cv.intake
    WHERE (tenant_id,publication_id)=(p.tenant_id,p.id))>cap
   OR NOT EXISTS(SELECT 1 FROM cv.position j JOIN cv.company c
    ON (c.tenant_id,c.id)=(j.tenant_id,j.company_id)
    WHERE (j.tenant_id,j.id)=(p.tenant_id,p.position_id) AND j.removed_at IS NULL AND c.removed_at IS NULL) THEN
    RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501'; END IF;
  END IF;
 END LOOP;
END $$;

REVOKE ALL ON FUNCTION cv.ensure_obligations(),cv.register_obligation(text,uuid,uuid,uuid),
 cv.lock_authority_policies(uuid,jsonb),cv.policy_live_at(uuid,uuid,text,timestamptz),
 cv.authority_policies_live(uuid,jsonb,timestamptz),cv.validate_transaction() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.validate_transaction() TO cv_runtime,cv_public;

CREATE OR REPLACE FUNCTION cv.lock_scope(t uuid,s uuid) RETURNS uuid
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
 PERFORM cv.register_obligation('scope',t,a,s);
 RETURN p.purpose_id;
END $$;

CREATE OR REPLACE FUNCTION cv.command_begin(t uuid,p uuid,op text,k uuid,payload cv.digest) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a uuid; found_result cv.command_result; BEGIN
 a:=cv.require_authority(t,false);
 PERFORM cv.register_obligation('purpose',t,a,p);
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

CREATE OR REPLACE FUNCTION cv.erasure_policy_pin() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  SELECT erasure_policy_id INTO NEW.erasure_policy_id FROM cv.privacy_scope
  WHERE (tenant_id,id)=(NEW.tenant_id,NEW.scope_id) FOR UPDATE;
  IF NEW.erasure_policy_id IS NULL THEN
   RAISE EXCEPTION 'ERASURE_POLICY_REQUIRED' USING ERRCODE='42501'; END IF;
  PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(NEW.tenant_id,NEW.erasure_policy_id) FOR SHARE;
  IF session_user='cv_runtime' THEN
   PERFORM cv.register_obligation('erasure',NEW.tenant_id,NEW.actor_id,NEW.erasure_policy_id);
  END IF;
 ELSIF NEW.erasure_policy_id IS DISTINCT FROM OLD.erasure_policy_id THEN
  RAISE EXCEPTION 'ERASURE_POLICY_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION cv.accept_intake(proof text,displayed_publication uuid,displayed_snapshot uuid,
 displayed_consent uuid,applicant_name text,email text,phone text,explicit_consent boolean,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE g cv.public_upload_grant; p cv.publication; resource jsonb; s uuid; intent uuid; doc uuid; result uuid;
 h cv.digest; existing cv.intake; cap integer; retention_seconds integer; expiry timestamptz; BEGIN
 SELECT * INTO g FROM cv.public_upload_grant WHERE proof_digest=encode(sha256(convert_to(proof,'UTF8')),'hex');
 IF NOT FOUND THEN RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501'; END IF;
 SELECT * INTO p FROM cv.publication WHERE (tenant_id,id)=(g.tenant_id,g.publication_id) FOR UPDATE;
 IF NOT FOUND OR NOT cv.publication_open(p.tenant_id,p.id) OR p.id IS DISTINCT FROM displayed_publication
 OR p.snapshot_id IS DISTINCT FROM displayed_snapshot OR g.snapshot_id IS DISTINCT FROM displayed_snapshot OR p.consent_policy_id IS DISTINCT FROM displayed_consent
 OR NOT explicit_consent OR explicit_consent IS NULL OR g.expires_at<=clock_timestamp()
 THEN RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501'; END IF;
 PERFORM 1 FROM cv.policy_version WHERE tenant_id=p.tenant_id AND id IN
 (p.purpose_id,p.source_policy_id,p.consent_policy_id,p.retention_policy_id,p.erasure_policy_id,p.resource_policy_id)
 ORDER BY id FOR SHARE;
 SELECT definition INTO resource FROM cv.policy_version WHERE (tenant_id,id)=(p.tenant_id,p.resource_policy_id);
 cap:=(resource->>'public_submission_quota')::integer;
 SELECT (definition->>'retention_seconds')::integer INTO retention_seconds FROM cv.policy_version
 WHERE (tenant_id,id)=(p.tenant_id,p.retention_policy_id);
 IF cap IS NULL OR cap<=0 OR retention_seconds IS NULL OR retention_seconds<=0 OR
 (resource->>'max_pdf_bytes') IS NULL OR g.byte_count>(resource->>'max_pdf_bytes')::bigint OR
 coalesce(btrim(applicant_name),'')='' OR coalesce(btrim(email),'')='' AND coalesce(btrim(phone),'')='' OR
 length(applicant_name)>coalesce((resource->>'contact_max_characters')::integer,0) OR
 length(coalesce(email,''))>coalesce((resource->>'contact_max_characters')::integer,0) OR
 length(coalesce(phone,''))>coalesce((resource->>'contact_max_characters')::integer,0)
 THEN RAISE EXCEPTION 'INTAKE_INVALID' USING ERRCODE='23514'; END IF;
 h:=encode(sha256(convert_to(jsonb_build_array(displayed_publication,displayed_snapshot,displayed_consent,
 applicant_name,email,phone,g.content_digest,explicit_consent)::text,'UTF8')),'hex');
 SELECT * INTO existing FROM cv.intake WHERE tenant_id=p.tenant_id AND publication_id=p.id AND intake.operation_key=accept_intake.operation_key;
 IF FOUND THEN
  IF existing.payload_digest<>h OR existing.upload_grant_id<>g.id OR NOT EXISTS(SELECT 1 FROM cv.privacy_scope
  WHERE (tenant_id,id)=(existing.tenant_id,existing.scope_id) AND revoked_at IS NULL AND consent_expires_at>clock_timestamp())
  THEN RAISE EXCEPTION 'INTAKE_CONFLICT' USING ERRCODE='23514'; END IF;
  PERFORM cv.register_obligation('public',p.tenant_id,NULL,existing.receipt);
  RETURN existing.receipt;
 END IF;
 IF g.scope_id IS NOT NULL OR (SELECT count(*) FROM cv.intake WHERE tenant_id=p.tenant_id AND publication_id=p.id)>=cap
 THEN RAISE EXCEPTION 'INTAKE_LIMIT' USING ERRCODE='23514'; END IF;
 SELECT least(clock_timestamp()+make_interval(secs=>retention_seconds),min(expires_at)) INTO expiry
 FROM cv.policy_version WHERE tenant_id=p.tenant_id AND id IN
 (p.purpose_id,p.source_policy_id,p.consent_policy_id,p.retention_policy_id,p.erasure_policy_id,p.resource_policy_id);
 s:=gen_random_uuid();intent:=gen_random_uuid();doc:=gen_random_uuid();result:=gen_random_uuid();
 INSERT INTO cv.privacy_scope VALUES(p.tenant_id,s,NULL,p.purpose_id,gen_random_uuid(),p.source_policy_id,
 p.consent_policy_id,p.retention_policy_id,p.erasure_policy_id,p.resource_policy_id,
 clock_timestamp(),expiry,NULL,g.synthetic,clock_timestamp());
 UPDATE cv.public_upload_grant SET scope_id=s WHERE (tenant_id,id)=(g.tenant_id,g.id);
 INSERT INTO cv.contact_revision VALUES(p.tenant_id,s,gen_random_uuid(),1,applicant_name,email,phone,NULL);
 -- A validated grant supplies a durable database intent, not a physical-file success claim.
 INSERT INTO cv.file_intent VALUES(p.tenant_id,s,intent,g.object_key,'intake','committed',g.byte_count,g.content_digest,expiry,1);
 INSERT INTO cv.document_version VALUES(p.tenant_id,s,doc,intent,1,g.content_digest,'application/pdf',g.byte_count,g.validated_at,clock_timestamp());
 INSERT INTO cv.intake VALUES(p.tenant_id,s,gen_random_uuid(),p.id,p.snapshot_id,g.id,doc,result,operation_key,h,
 clock_timestamp(),g.validated_at,1,'pending');
 IF NOT cv.publication_open(p.tenant_id,p.id) THEN RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501'; END IF;
 PERFORM cv.register_obligation('public',p.tenant_id,NULL,result);
 RETURN result;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
