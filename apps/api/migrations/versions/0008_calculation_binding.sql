-- Content format v1 fixes JSONB object ordering, array order and exact numeric
-- normalization. No filename, upload identity, actor, locale or clock is added.
GRANT CREATE ON SCHEMA cv TO cv_guard;
ALTER TABLE cv.rubric_version ADD COLUMN construction_xid xid8 NOT NULL DEFAULT pg_current_xact_id();
SET ROLE cv_guard;
CREATE FUNCTION cv.canonical_json_v1(value jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE STRICT SET search_path=pg_catalog,cv AS $$
DECLARE result jsonb;
BEGIN
 CASE jsonb_typeof(value)
 WHEN 'object' THEN
  SELECT coalesce(jsonb_object_agg(key,cv.canonical_json_v1(v) ORDER BY key),'{}'::jsonb)
  INTO result FROM jsonb_each(value) AS entry(key,v);
 WHEN 'array' THEN
  SELECT coalesce(jsonb_agg(cv.canonical_json_v1(v) ORDER BY ordinal),'[]'::jsonb)
  INTO result FROM jsonb_array_elements(value) WITH ORDINALITY AS entry(v,ordinal);
 WHEN 'number' THEN result:=to_jsonb(trim_scale((value#>>'{}')::numeric));
 ELSE result:=value;
 END CASE;
 RETURN result;
END $$;
CREATE FUNCTION cv.canonical_digest_v1(value jsonb) RETURNS cv.digest
LANGUAGE sql IMMUTABLE STRICT SET search_path=pg_catalog,cv AS $$
 SELECT encode(sha256(convert_to('cv-jsonb-v1:'||cv.canonical_json_v1(value)::text,'UTF8')),'hex')::cv.digest
$$;
-- SECURITY INVOKER: a runtime caller can construct only a snapshot it may read.
CREATE FUNCTION cv.calculation_snapshot_v1(t uuid,r uuid) RETURNS jsonb
LANGUAGE sql STABLE SET search_path=pg_catalog,cv AS $$
 SELECT cv.canonical_json_v1(jsonb_build_object(
 'identity_format','cv-calculation-v1',
 'jd',jsonb_build_object('version',j.version,'content',j.content),
 'rubric',jsonb_build_object('version',r.version,'definition',r.definition,
 'reference_date',r.reference_date,'criteria',(
 SELECT jsonb_agg(jsonb_build_object('key',c.criterion_key,'ordinal',c.ordinal,'weight',c.weight,
 'adapter',c.adapter,'mandatory',c.mandatory_definition) ORDER BY c.ordinal,c.criterion_key)
 FROM cv.rubric_criterion c WHERE (c.tenant_id,c.rubric_id)=(r.tenant_id,r.id))),
 'engine',jsonb_build_object('version',e.version,'definition',e.definition,
 'rounding',e.rounding,'unknown_rule',e.unknown_rule)))
 FROM cv.rubric_version r JOIN cv.jd_version j ON (j.tenant_id,j.position_id,j.id)=(r.tenant_id,r.position_id,r.jd_id)
 JOIN cv.engine_definition e ON (e.tenant_id,e.id)=(r.tenant_id,r.engine_id)
 WHERE (r.tenant_id,r.id)=(t,calculation_snapshot_v1.r)
$$;
CREATE FUNCTION cv.calculation_binding_check() RETURNS trigger
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
CREATE FUNCTION cv.definition_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM cv.rubric_version r WHERE (r.tenant_id,r.id)=(NEW.tenant_id,NEW.rubric_id)
 AND r.construction_xid=pg_current_xact_id()) THEN
  RAISE EXCEPTION 'PUBLISHED_RUBRIC_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cv.result_child_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE parent_state text;
BEGIN
 IF TG_TABLE_NAME='evidence_span' THEN
  SELECT state INTO parent_state FROM cv.extraction
  WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.extraction_id) FOR UPDATE;
 ELSE
  SELECT state INTO parent_state FROM cv.evaluation
  WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.evaluation_id) FOR UPDATE;
 END IF;
 IF parent_state IS DISTINCT FROM 'claimed' THEN
  RAISE EXCEPTION 'SEALED_RESULT_CHILD' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cv.canonical_json_v1(jsonb),cv.canonical_digest_v1(jsonb),
 cv.calculation_snapshot_v1(uuid,uuid),cv.calculation_binding_check(),
 cv.definition_child_check(),cv.result_child_check() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.canonical_json_v1(jsonb),cv.canonical_digest_v1(jsonb),
 cv.calculation_snapshot_v1(uuid,uuid) TO cv_runtime;
RESET ROLE;
CREATE INDEX profile_content_identity ON cv.profile_revision(tenant_id,scope_id,cv.canonical_digest_v1(factual_content));
CREATE TRIGGER calculation_binding BEFORE INSERT ON cv.evaluation
 FOR EACH ROW EXECUTE FUNCTION cv.calculation_binding_check();
CREATE CONSTRAINT TRIGGER final_calculation_binding AFTER INSERT OR UPDATE ON cv.evaluation
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.calculation_binding_check();
CREATE TRIGGER definition_child BEFORE INSERT ON cv.rubric_criterion
 FOR EACH ROW EXECUTE FUNCTION cv.definition_child_check();
CREATE TRIGGER result_child BEFORE INSERT ON cv.evaluation_component
 FOR EACH ROW EXECUTE FUNCTION cv.result_child_check();
CREATE TRIGGER result_child BEFORE INSERT ON cv.evaluation_evidence
 FOR EACH ROW EXECUTE FUNCTION cv.result_child_check();
CREATE TRIGGER result_child BEFORE INSERT ON cv.evidence_span
 FOR EACH ROW EXECUTE FUNCTION cv.result_child_check();

SET ROLE cv_guard;
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
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
