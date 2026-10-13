DROP TRIGGER evaluation_evidence_source ON cv.evaluation_evidence;
DROP TRIGGER profile_evidence_child ON cv.profile_evidence;
DROP TABLE cv.profile_source;
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.calculation_binding_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE expected jsonb;
BEGIN
 expected:=cv.calculation_snapshot_v1(NEW.tenant_id,NEW.rubric_id);
 IF expected IS NULL OR NEW.calculation_definition IS DISTINCT FROM expected
 OR NEW.calculation_digest<>cv.canonical_digest_v1(expected) THEN
  RAISE EXCEPTION 'CALCULATION_BINDING_MISMATCH' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision p WHERE (p.tenant_id,p.scope_id)=(NEW.tenant_id,NEW.scope_id)
 AND cv.canonical_digest_v1(p.factual_content)=NEW.factual_digest) THEN
  RAISE EXCEPTION 'FACT_CONTENT_REQUIRED' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION cv.claim_evaluation(scope uuid,target_position uuid,rubric uuid,jd uuid,engine uuid,facts cv.digest,calculation cv.digest,definition jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; result uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.lock_scope(a.tenant_id,scope);
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision WHERE (tenant_id,scope_id)=(a.tenant_id,scope) AND cv.canonical_digest_v1(factual_content)=facts) THEN
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

CREATE OR REPLACE FUNCTION cv.occurrence_binding_check() RETURNS trigger
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
DROP FUNCTION cv.profile_source_child_check();
DROP FUNCTION cv.evaluation_evidence_source_check();
DROP FUNCTION cv.claim_evaluation(uuid,uuid,uuid,uuid,uuid,cv.digest,cv.digest,jsonb,uuid);
DROP FUNCTION cv.calculation_snapshot_v2(uuid,uuid,uuid,uuid);
DROP FUNCTION cv.profile_source_snapshot_v1(uuid,uuid,uuid);
RESET ROLE;
ALTER TABLE cv.evaluation DROP COLUMN source_profile_id;
ALTER TABLE cv.profile_revision DROP COLUMN construction_xid;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
