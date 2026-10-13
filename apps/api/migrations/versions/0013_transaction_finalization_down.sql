GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
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
 RETURN p.purpose_id;
END $$;

CREATE OR REPLACE FUNCTION cv.command_begin(t uuid,p uuid,op text,k uuid,payload cv.digest) RETURNS uuid
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

CREATE OR REPLACE FUNCTION cv.erasure_policy_pin() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  SELECT erasure_policy_id INTO NEW.erasure_policy_id FROM cv.privacy_scope
  WHERE (tenant_id,id)=(NEW.tenant_id,NEW.scope_id) FOR UPDATE;
  IF NEW.erasure_policy_id IS NULL THEN
   RAISE EXCEPTION 'ERASURE_POLICY_REQUIRED' USING ERRCODE='42501'; END IF;
  PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(NEW.tenant_id,NEW.erasure_policy_id) FOR SHARE;
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
 RETURN result;
END $$;
DROP FUNCTION cv.validate_transaction();
DROP FUNCTION cv.register_obligation(text,uuid,uuid,uuid);
DROP FUNCTION cv.ensure_obligations();
DROP FUNCTION cv.authority_policies_live(uuid,jsonb,timestamptz);
DROP FUNCTION cv.policy_live_at(uuid,uuid,text,timestamptz);
DROP FUNCTION cv.lock_authority_policies(uuid,jsonb);
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
DO $$ BEGIN
 EXECUTE format('REVOKE TEMPORARY ON DATABASE %I FROM cv_guard',current_database());
END $$;
