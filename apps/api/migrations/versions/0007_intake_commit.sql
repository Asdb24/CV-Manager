-- Public authority is resolved by publication. Independent foreign keys alone
-- cannot prove that its snapshot, upload grant and document belong together.
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE FUNCTION cv.publication_identity_check() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 IF (NEW.tenant_id,NEW.id,NEW.position_id) IS DISTINCT FROM
    (OLD.tenant_id,OLD.id,OLD.position_id) THEN
  RAISE EXCEPTION 'PUBLICATION_IDENTITY_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION cv.upload_grant_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='UPDATE' THEN
  IF (to_jsonb(NEW)-'scope_id') IS DISTINCT FROM (to_jsonb(OLD)-'scope_id')
  OR OLD.scope_id IS NOT NULL AND NEW.scope_id IS DISTINCT FROM OLD.scope_id THEN
   RAISE EXCEPTION 'UPLOAD_GRANT_IMMUTABLE' USING ERRCODE='23514';
  END IF;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM cv.publication p JOIN cv.publication_snapshot s
 ON (s.tenant_id,s.position_id)=(p.tenant_id,p.position_id)
 WHERE (p.tenant_id,p.id,s.id)=(NEW.tenant_id,NEW.publication_id,NEW.snapshot_id)) THEN
  RAISE EXCEPTION 'PUBLICATION_SNAPSHOT_MISMATCH' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION cv.intake_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='UPDATE' AND (to_jsonb(NEW)-ARRAY['state','revision']) IS DISTINCT FROM
                      (to_jsonb(OLD)-ARRAY['state','revision']) THEN
  RAISE EXCEPTION 'INTAKE_SOURCE_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM cv.public_upload_grant g
 JOIN cv.document_version d ON (d.tenant_id,d.scope_id)=(g.tenant_id,g.scope_id)
 JOIN cv.file_intent f ON (f.tenant_id,f.scope_id,f.id)=(d.tenant_id,d.scope_id,d.intent_id)
 WHERE (g.tenant_id,g.id,g.scope_id,g.publication_id,g.snapshot_id,d.id)=
       (NEW.tenant_id,NEW.upload_grant_id,NEW.scope_id,NEW.publication_id,NEW.snapshot_id,NEW.document_id)
 AND d.content_digest=g.content_digest AND d.byte_count=g.byte_count AND f.object_key=g.object_key) THEN
  RAISE EXCEPTION 'INTAKE_BINDING_MISMATCH' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION cv.final_public_acceptance_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE p cv.publication; s cv.privacy_scope; g cv.public_upload_grant; at_commit timestamptz;
BEGIN
 -- All callers, including trusted ingestion, must satisfy the same final check.
 SELECT * INTO p FROM cv.publication WHERE (tenant_id,id)=(NEW.tenant_id,NEW.publication_id) FOR UPDATE;
 SELECT * INTO s FROM cv.privacy_scope WHERE (tenant_id,id)=(NEW.tenant_id,NEW.scope_id) FOR SHARE;
 SELECT * INTO g FROM cv.public_upload_grant WHERE (tenant_id,id)=(NEW.tenant_id,NEW.upload_grant_id) FOR SHARE;
 at_commit:=clock_timestamp();
 IF p.id IS NULL OR s.id IS NULL OR g.id IS NULL OR NOT cv.publication_open(p.tenant_id,p.id)
 OR p.snapshot_id<>NEW.snapshot_id OR p.expires_at<=at_commit OR g.expires_at<=at_commit
 OR s.revoked_at IS NOT NULL OR s.consent_expires_at<=at_commit
 OR EXISTS(SELECT 1 FROM cv.policy_version v WHERE v.tenant_id=p.tenant_id
 AND v.id IN (p.purpose_id,p.source_policy_id,p.consent_policy_id,p.retention_policy_id,
 p.erasure_policy_id,p.resource_policy_id) AND v.expires_at<=at_commit) THEN
  RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cv.publication_identity_check(),cv.upload_grant_binding_check(),
 cv.intake_binding_check(),cv.final_public_acceptance_check() FROM PUBLIC;
RESET ROLE;
CREATE TRIGGER publication_identity BEFORE UPDATE ON cv.publication
 FOR EACH ROW EXECUTE FUNCTION cv.publication_identity_check();
CREATE TRIGGER grant_binding BEFORE INSERT OR UPDATE ON cv.public_upload_grant
 FOR EACH ROW EXECUTE FUNCTION cv.upload_grant_binding_check();
CREATE TRIGGER intake_binding BEFORE INSERT OR UPDATE ON cv.intake
 FOR EACH ROW EXECUTE FUNCTION cv.intake_binding_check();
CREATE CONSTRAINT TRIGGER final_public_acceptance AFTER INSERT ON cv.intake
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_public_acceptance_check();
CREATE TRIGGER immutable_delete BEFORE DELETE ON cv.extraction
 FOR EACH ROW EXECUTE FUNCTION cv.immutable_row();
CREATE TRIGGER immutable_delete BEFORE DELETE ON cv.evaluation
 FOR EACH ROW EXECUTE FUNCTION cv.immutable_row();
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
