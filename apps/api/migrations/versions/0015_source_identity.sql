ALTER TABLE cv.profile_revision ADD COLUMN construction_xid xid8 NOT NULL DEFAULT pg_current_xact_id();
CREATE TABLE cv.profile_source (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, profile_id uuid NOT NULL, extraction_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,profile_id,extraction_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,profile_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,extraction_id) REFERENCES cv.extraction(tenant_id,scope_id,id)
);
CREATE INDEX profile_source_extraction ON cv.profile_source(tenant_id,scope_id,extraction_id);
ALTER TABLE cv.profile_source ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv.profile_source FORCE ROW LEVEL SECURITY;
CREATE POLICY guard ON cv.profile_source TO cv_guard USING(true) WITH CHECK(true);
CREATE POLICY staff ON cv.profile_source TO cv_runtime USING(cv.scope_allowed(tenant_id,scope_id));
GRANT SELECT,INSERT,UPDATE,DELETE ON cv.profile_source TO cv_guard;
GRANT SELECT ON cv.profile_source TO cv_runtime;
-- NULL means pre-v2 historical attribution was not recorded. Never backfill it
-- by guessing a profile from an equal factual hash.
ALTER TABLE cv.evaluation ADD COLUMN source_profile_id uuid;
ALTER TABLE cv.evaluation ADD CONSTRAINT evaluation_source_profile_fk
 FOREIGN KEY(tenant_id,scope_id,source_profile_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id);
CREATE INDEX evaluation_source_profile ON cv.evaluation(tenant_id,scope_id,source_profile_id);
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;

CREATE FUNCTION cv.profile_source_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision p
 WHERE (p.tenant_id,p.scope_id,p.id)=(NEW.tenant_id,NEW.scope_id,NEW.profile_id)
 AND p.construction_xid=pg_current_xact_id()) THEN
  RAISE EXCEPTION 'PROFILE_SOURCE_SET_SEALED' USING ERRCODE='23514'; END IF;
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

-- Both projection functions are SECURITY INVOKER and read only RLS-visible rows.
-- Full immutable definitions/text are retained; declared semantic hashes alone
-- never substitute for the actual evidence being pinned.
CREATE FUNCTION cv.profile_source_snapshot_v1(t uuid,s uuid,p uuid) RETURNS jsonb
LANGUAGE sql STABLE SET search_path=pg_catalog,cv AS $$
 SELECT cv.canonical_json_v1(jsonb_build_object('format','cv-profile-source-v1',
 'sources',jsonb_agg(source.definition ORDER BY cv.canonical_json_v1(source.definition)::text)))
 FROM (SELECT jsonb_build_object('document_content',x.content_digest,
 'extraction_definition',x.definition,'extraction_state',x.state,
 'semantic_evidence',coalesce((SELECT jsonb_agg(jsonb_build_object(
 'page',e.page,'start',e.start_offset,'end',e.end_offset,'locator',e.semantic_locator,'text',e.text_content)
 ORDER BY e.page,e.start_offset,e.end_offset,e.semantic_locator,e.text_content)
 FROM cv.evidence_span e WHERE (e.tenant_id,e.scope_id,e.extraction_id)=(x.tenant_id,x.scope_id,x.id)),'[]'::jsonb),
 'reviewed_evidence',coalesce((SELECT jsonb_agg(jsonb_build_object('fact',r.fact_key,
 'page',e.page,'start',e.start_offset,'end',e.end_offset,'locator',e.semantic_locator,'text',e.text_content)
 ORDER BY r.fact_key,e.page,e.start_offset,e.end_offset,e.semantic_locator,e.text_content)
 FROM cv.profile_evidence r JOIN cv.evidence_span e ON (e.tenant_id,e.scope_id,e.id)=(r.tenant_id,r.scope_id,r.evidence_id)
 WHERE (r.tenant_id,r.scope_id,r.profile_id,e.extraction_id)=(t,s,p,x.id)),'[]'::jsonb)) AS definition
 FROM cv.profile_source ps JOIN cv.extraction x ON
 (x.tenant_id,x.scope_id,x.id)=(ps.tenant_id,ps.scope_id,ps.extraction_id)
 WHERE (ps.tenant_id,ps.scope_id,ps.profile_id)=(t,s,p)) source
 HAVING count(*)>0
$$;

CREATE FUNCTION cv.calculation_snapshot_v2(t uuid,s uuid,r uuid,p uuid) RETURNS jsonb
LANGUAGE sql STABLE SET search_path=pg_catalog,cv AS $$
 SELECT cv.canonical_json_v1(jsonb_build_object('identity_format','cv-calculation-v2',
 'calculation',cv.calculation_snapshot_v1(t,r),'source',cv.profile_source_snapshot_v1(t,s,p)))
 WHERE cv.calculation_snapshot_v1(t,r) IS NOT NULL AND cv.profile_source_snapshot_v1(t,s,p) IS NOT NULL
$$;

CREATE OR REPLACE FUNCTION cv.calculation_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE expected jsonb;
BEGIN
 IF NEW.source_profile_id IS NULL THEN
  RAISE EXCEPTION 'PROFILE_SOURCE_REQUIRED' USING ERRCODE='23514'; END IF;
 expected:=cv.calculation_snapshot_v2(NEW.tenant_id,NEW.scope_id,NEW.rubric_id,NEW.source_profile_id);
 IF expected IS NULL OR NEW.calculation_definition IS DISTINCT FROM expected
 OR NEW.calculation_digest<>cv.canonical_digest_v1(expected) THEN
  RAISE EXCEPTION 'CALCULATION_BINDING_MISMATCH' USING ERRCODE='23514'; END IF;
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision p WHERE
 (p.tenant_id,p.scope_id,p.id)=(NEW.tenant_id,NEW.scope_id,NEW.source_profile_id)
 AND cv.canonical_digest_v1(p.factual_content)=NEW.factual_digest) THEN
  RAISE EXCEPTION 'FACT_CONTENT_REQUIRED' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION cv.claim_evaluation(scope uuid,target_position uuid,rubric uuid,jd uuid,engine uuid,facts cv.digest,calculation cv.digest,definition jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 RAISE EXCEPTION 'PROFILE_SOURCE_REQUIRED' USING ERRCODE='23514';
END $$;

CREATE FUNCTION cv.claim_evaluation(scope uuid,target_position uuid,rubric uuid,jd uuid,engine uuid,facts cv.digest,calculation cv.digest,definition jsonb,profile uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; result uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.lock_scope(a.tenant_id,scope);
 INSERT INTO cv.evaluation(tenant_id,scope_id,id,position_id,rubric_id,jd_id,engine_id,
 factual_digest,calculation_digest,calculation_definition,state,source_profile_id)
 VALUES(a.tenant_id,scope,gen_random_uuid(),target_position,rubric,jd,engine,facts,calculation,definition,'claimed',profile)
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

CREATE OR REPLACE FUNCTION cv.occurrence_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.evaluation e
 JOIN cv.application a ON (a.tenant_id,a.scope_id,a.position_id)=(e.tenant_id,e.scope_id,e.position_id)
 JOIN cv.profile_revision p ON (p.tenant_id,p.scope_id)=(e.tenant_id,e.scope_id)
 WHERE (e.tenant_id,e.scope_id,e.id,a.id,p.id)=
 (NEW.tenant_id,NEW.scope_id,NEW.evaluation_id,NEW.application_id,NEW.profile_id)
 AND cv.canonical_digest_v1(p.factual_content)=e.factual_digest
 AND e.calculation_definition=cv.calculation_snapshot_v2(e.tenant_id,e.scope_id,e.rubric_id,p.id)
 AND EXISTS(SELECT 1 FROM cv.profile_source ps JOIN cv.extraction_document d
 ON (d.tenant_id,d.scope_id,d.extraction_id)=(ps.tenant_id,ps.scope_id,ps.extraction_id)
 WHERE (ps.tenant_id,ps.scope_id,ps.profile_id,d.document_id)=
 (NEW.tenant_id,NEW.scope_id,NEW.profile_id,NEW.document_id))) THEN
  RAISE EXCEPTION 'EVALUATION_OCCURRENCE_MISMATCH' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION cv.evaluation_evidence_source_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.evaluation e JOIN cv.profile_evidence p
 ON (p.tenant_id,p.scope_id,p.profile_id)=(e.tenant_id,e.scope_id,e.source_profile_id)
 WHERE (e.tenant_id,e.scope_id,e.id,p.evidence_id)=
 (NEW.tenant_id,NEW.scope_id,NEW.evaluation_id,NEW.evidence_id)) THEN
  RAISE EXCEPTION 'EVALUATION_EVIDENCE_NOT_APPROVED' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cv.profile_source_child_check(),cv.profile_source_snapshot_v1(uuid,uuid,uuid),
 cv.calculation_snapshot_v2(uuid,uuid,uuid,uuid),cv.evaluation_evidence_source_check(),
 cv.claim_evaluation(uuid,uuid,uuid,uuid,uuid,cv.digest,cv.digest,jsonb,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.profile_source_snapshot_v1(uuid,uuid,uuid),
 cv.calculation_snapshot_v2(uuid,uuid,uuid,uuid),
 cv.claim_evaluation(uuid,uuid,uuid,uuid,uuid,cv.digest,cv.digest,jsonb,uuid) TO cv_runtime;
RESET ROLE;
CREATE TRIGGER profile_source_child BEFORE INSERT ON cv.profile_source
 FOR EACH ROW EXECUTE FUNCTION cv.profile_source_child_check();
CREATE TRIGGER profile_evidence_child BEFORE INSERT ON cv.profile_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.profile_source_child_check();
CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON cv.profile_source
 FOR EACH ROW EXECUTE FUNCTION cv.immutable_row();
CREATE CONSTRAINT TRIGGER final_authority AFTER INSERT OR UPDATE ON cv.profile_source
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_authority_check();
CREATE TRIGGER evaluation_evidence_source BEFORE INSERT ON cv.evaluation_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.evaluation_evidence_source_check();
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
