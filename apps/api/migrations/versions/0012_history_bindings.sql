ALTER TABLE cv.advisory_manifest ADD COLUMN construction_xid xid8 NOT NULL DEFAULT pg_current_xact_id();
ALTER TABLE cv.advisory_run ADD COLUMN construction_xid xid8 NOT NULL DEFAULT pg_current_xact_id();
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE FUNCTION cv.advisory_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE construction xid8;
BEGIN
 IF TG_TABLE_NAME='advisory_manifest_evidence' THEN
  SELECT construction_xid INTO construction FROM cv.advisory_manifest
  WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.manifest_id);
 ELSE
  SELECT construction_xid INTO construction FROM cv.advisory_run
  WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.run_id);
 END IF;
 IF construction IS DISTINCT FROM pg_current_xact_id() THEN
  RAISE EXCEPTION 'ADVISORY_CHILD_SET_SEALED' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cv.question_chain_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NEW.version=1 THEN
  IF NOT EXISTS(SELECT 1 FROM cv.advisory_run r
  WHERE (r.tenant_id,r.scope_id,r.id)=(NEW.tenant_id,NEW.scope_id,NEW.run_id)
  AND r.construction_xid=pg_current_xact_id()) THEN
   RAISE EXCEPTION 'ADVISORY_CHILD_SET_SEALED' USING ERRCODE='23514'; END IF;
 ELSIF NOT EXISTS(SELECT 1 FROM cv.question_revision q
 WHERE (q.tenant_id,q.scope_id,q.id,q.question_set_id,q.question_key,q.version)=
 (NEW.tenant_id,NEW.scope_id,NEW.previous_id,NEW.question_set_id,NEW.question_key,NEW.version-1)) THEN
  RAISE EXCEPTION 'QUESTION_REVISION_GAP' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cv.occurrence_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.evaluation e
 JOIN cv.application a ON (a.tenant_id,a.scope_id,a.position_id)=(e.tenant_id,e.scope_id,e.position_id)
 JOIN cv.profile_revision p ON (p.tenant_id,p.scope_id)=(e.tenant_id,e.scope_id)
 WHERE (e.tenant_id,e.scope_id,e.id,a.id,p.id)=
 (NEW.tenant_id,NEW.scope_id,NEW.evaluation_id,NEW.application_id,NEW.profile_id)
 AND cv.canonical_digest_v1(p.factual_content)=e.factual_digest) THEN
  RAISE EXCEPTION 'EVALUATION_OCCURRENCE_MISMATCH' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cv.advisory_child_check(),cv.question_chain_check(),cv.occurrence_binding_check() FROM PUBLIC;
RESET ROLE;
CREATE TRIGGER sealed_children BEFORE INSERT ON cv.advisory_manifest_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.advisory_child_check();
CREATE TRIGGER sealed_children BEFORE INSERT ON cv.advisory_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.advisory_child_check();
CREATE TRIGGER sealed_children BEFORE INSERT ON cv.advisory_finding
 FOR EACH ROW EXECUTE FUNCTION cv.advisory_child_check();
CREATE TRIGGER sealed_children BEFORE INSERT ON cv.advisory_finding_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.advisory_child_check();
CREATE TRIGGER sealed_children BEFORE INSERT ON cv.question_set
 FOR EACH ROW EXECUTE FUNCTION cv.advisory_child_check();
CREATE TRIGGER question_chain BEFORE INSERT ON cv.question_revision
 FOR EACH ROW EXECUTE FUNCTION cv.question_chain_check();
CREATE TRIGGER occurrence_binding BEFORE INSERT ON cv.evaluation_occurrence
 FOR EACH ROW EXECUTE FUNCTION cv.occurrence_binding_check();
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
