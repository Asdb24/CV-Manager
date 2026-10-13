SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.claim_evaluation(scope uuid,target_position uuid,rubric uuid,jd uuid,engine uuid,facts cv.digest,calculation cv.digest,definition jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; result uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 PERFORM cv.lock_scope(a.tenant_id,scope);
 IF NOT EXISTS(SELECT 1 FROM cv.profile_revision WHERE (tenant_id,scope_id,factual_digest)=(a.tenant_id,scope,facts)) THEN
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
RESET ROLE;
DROP TRIGGER result_child ON cv.evidence_span;
DROP TRIGGER result_child ON cv.evaluation_evidence;
DROP TRIGGER result_child ON cv.evaluation_component;
DROP TRIGGER definition_child ON cv.rubric_criterion;
DROP TRIGGER final_calculation_binding ON cv.evaluation;
DROP TRIGGER calculation_binding ON cv.evaluation;
DROP INDEX cv.profile_content_identity;
DROP FUNCTION cv.result_child_check();
DROP FUNCTION cv.definition_child_check();
DROP FUNCTION cv.calculation_binding_check();
DROP FUNCTION cv.calculation_snapshot_v1(uuid,uuid);
DROP FUNCTION cv.canonical_digest_v1(jsonb);
DROP FUNCTION cv.canonical_json_v1(jsonb);
ALTER TABLE cv.rubric_version DROP COLUMN construction_xid;
