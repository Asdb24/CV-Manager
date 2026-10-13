DROP TRIGGER extraction_binding ON cv.extraction;
DROP TRIGGER extraction_document_binding ON cv.extraction_document;
DROP FUNCTION cv.extraction_binding_check();
DROP FUNCTION cv.extraction_document_check();
CREATE OR REPLACE FUNCTION cv.scope_policy_check() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,cv AS $$
DECLARE p uuid; k text; v cv.policy_version; BEGIN
 FOR p,k IN SELECT * FROM (VALUES(NEW.purpose_id,'purpose'),(NEW.source_policy_id,'source'),
 (NEW.consent_policy_id,'consent'),(NEW.retention_policy_id,'retention'),
 (NEW.erasure_policy_id,'erasure'),(NEW.resource_policy_id,'resource')) AS required(id,kind) LOOP
  SELECT * INTO v FROM cv.policy_version WHERE tenant_id=NEW.tenant_id AND id=p FOR SHARE;
  IF NOT FOUND OR v.kind<>k OR NOT cv.policy_live(NEW.tenant_id,p,k)
  OR (v.synthetic_only AND NOT NEW.synthetic) OR NEW.consent_expires_at>v.expires_at THEN
   RAISE EXCEPTION 'POLICY_SCOPE_INVALID' USING ERRCODE='23514'; END IF;
 END LOOP;
 IF TG_OP='UPDATE' AND (to_jsonb(OLD)-ARRAY['revoked_at','candidate_id']) IS DISTINCT FROM
 (to_jsonb(NEW)-ARRAY['revoked_at','candidate_id']) THEN
  RAISE EXCEPTION 'PRIVACY_SCOPE_IMMUTABLE' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND OLD.candidate_id IS NOT NULL AND NEW.candidate_id IS DISTINCT FROM OLD.candidate_id THEN
  RAISE EXCEPTION 'PERSON_LINK_IMMUTABLE' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
  RAISE EXCEPTION 'REVOCATION_IMMUTABLE' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
