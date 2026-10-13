GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE FUNCTION cv.extraction_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NEW.definition->>'format' IS DISTINCT FROM 'cv-extraction-v1'
 OR jsonb_typeof(NEW.definition->'parser') IS DISTINCT FROM 'object'
 OR jsonb_typeof(NEW.definition->'normalization') IS DISTINCT FROM 'object'
 OR NEW.definition-ARRAY['format','parser','normalization']<>'{}'::jsonb
 OR NEW.parser_digest<>cv.canonical_digest_v1(NEW.definition->'parser')
 OR NEW.normalization_digest<>cv.canonical_digest_v1(NEW.definition->'normalization') THEN
  RAISE EXCEPTION 'EXTRACTION_BINDING_MISMATCH' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cv.extraction_document_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.extraction e JOIN cv.document_version d
 ON (e.tenant_id,e.scope_id,e.content_digest)=(d.tenant_id,d.scope_id,d.content_digest)
 WHERE (e.tenant_id,e.scope_id,e.id,d.id)=(NEW.tenant_id,NEW.scope_id,NEW.extraction_id,NEW.document_id)) THEN
  RAISE EXCEPTION 'EXTRACTION_DOCUMENT_MISMATCH' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cv.extraction_binding_check(),cv.extraction_document_check() FROM PUBLIC;
RESET ROLE;
CREATE TRIGGER extraction_binding BEFORE INSERT ON cv.extraction
 FOR EACH ROW EXECUTE FUNCTION cv.extraction_binding_check();
CREATE TRIGGER extraction_document_binding BEFORE INSERT ON cv.extraction_document
 FOR EACH ROW EXECUTE FUNCTION cv.extraction_document_check();
REVOKE CREATE ON SCHEMA cv FROM cv_guard;

CREATE OR REPLACE FUNCTION cv.scope_policy_check() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,cv AS $$
DECLARE p uuid; k text; v cv.policy_version; BEGIN
 -- Revocation removes authority even after its original policies expire.
 IF TG_OP='UPDATE' AND OLD.revoked_at IS NULL AND NEW.revoked_at IS NOT NULL
 AND (to_jsonb(OLD)-'revoked_at')=(to_jsonb(NEW)-'revoked_at') THEN RETURN NEW; END IF;
 IF TG_OP='UPDATE' AND NEW.candidate_id IS DISTINCT FROM OLD.candidate_id
 AND (OLD.revoked_at IS NOT NULL OR OLD.consent_expires_at<=clock_timestamp()) THEN
  RAISE EXCEPTION 'INACTIVE_SCOPE_LINK_DENIED' USING ERRCODE='23514'; END IF;
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
