GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.profile_source_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision p
 WHERE (p.tenant_id,p.scope_id,p.id)=(NEW.tenant_id,NEW.scope_id,NEW.profile_id)
 AND p.construction_xid=pg_current_xact_id()) THEN
  RAISE EXCEPTION 'PROFILE_SOURCE_SET_SEALED' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT 1 FROM cv.evaluation e WHERE
  (e.tenant_id,e.scope_id,e.source_profile_id)=(NEW.tenant_id,NEW.scope_id,NEW.profile_id))
 OR EXISTS(SELECT 1 FROM cv.evaluation_occurrence o WHERE
  (o.tenant_id,o.scope_id,o.profile_id)=(NEW.tenant_id,NEW.scope_id,NEW.profile_id))
 OR EXISTS(SELECT 1 FROM cv.advisory_manifest m WHERE
  (m.tenant_id,m.scope_id,m.profile_id)=(NEW.tenant_id,NEW.scope_id,NEW.profile_id)) THEN
  RAISE EXCEPTION 'PROFILE_SOURCE_ALREADY_USED' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='profile_source' THEN
  IF NOT EXISTS(SELECT 1 FROM cv.extraction x JOIN cv.extraction_document d
  ON (d.tenant_id,d.scope_id,d.extraction_id)=(x.tenant_id,x.scope_id,x.id)
  WHERE (x.tenant_id,x.scope_id,x.id)=(NEW.tenant_id,NEW.scope_id,NEW.extraction_id)
  AND x.state IN ('complete','incomplete')) THEN
   RAISE EXCEPTION 'PROFILE_DOCUMENT_SOURCE_REQUIRED' USING ERRCODE='23514'; END IF;
 ELSE
  IF NOT EXISTS(SELECT 1 FROM cv.evidence_span e JOIN cv.profile_source p
  ON (p.tenant_id,p.scope_id,p.extraction_id)=(e.tenant_id,e.scope_id,e.extraction_id)
  WHERE (p.tenant_id,p.scope_id,p.profile_id,e.id)=
  (NEW.tenant_id,NEW.scope_id,NEW.profile_id,NEW.evidence_id)) THEN
   RAISE EXCEPTION 'PROFILE_EVIDENCE_SOURCE_MISMATCH' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION cv.definition_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.rubric_version r WHERE (r.tenant_id,r.id)=(NEW.tenant_id,NEW.rubric_id)
 AND r.construction_xid=pg_current_xact_id())
 OR EXISTS(SELECT 1 FROM cv.evaluation e WHERE (e.tenant_id,e.rubric_id)=(NEW.tenant_id,NEW.rubric_id)) THEN
  RAISE EXCEPTION 'PUBLISHED_RUBRIC_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
