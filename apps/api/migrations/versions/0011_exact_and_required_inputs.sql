-- A forward repair must not silently rewrite a historical rounded result.
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM cv.evaluation_component
 WHERE contribution IS DISTINCT FROM weight*rating*0.25::numeric) THEN
  RAISE EXCEPTION 'LEGACY_ROUNDED_COMPONENT_REQUIRES_EXPLICIT_REPAIR';
 END IF;
END $$;
ALTER TABLE cv.evaluation_component ALTER COLUMN contribution
 SET EXPRESSION AS (weight*rating*0.25::numeric);
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.move_stage(scope uuid,application uuid,expected_revision integer,target cv.stage,reason text,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; row cv.application; p uuid; h cv.digest; result uuid; allowed boolean; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 p:=cv.lock_scope(a.tenant_id,scope);
 h:=encode(sha256(convert_to(jsonb_build_array(scope,application,expected_revision,target,reason)::text,'UTF8')),'hex');
 result:=cv.command_begin(a.tenant_id,p,'application.stage',operation_key,h);
 IF result IS NOT NULL THEN RETURN result; END IF;
 SELECT * INTO row FROM cv.application WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,move_stage.application) FOR UPDATE;
 IF NOT FOUND OR row.revision IS DISTINCT FROM expected_revision OR row.removed_at IS NOT NULL THEN
  RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
 allowed:= (row.stage='received' AND target='evaluating')
 OR (row.stage='evaluating' AND target='interview') OR (row.stage='interview' AND target='hired')
 OR (row.stage IN ('received','evaluating','interview') AND target='not_continuing')
 OR (coalesce(btrim(reason),'')<>'' AND ((row.stage='evaluating' AND target='received')
 OR (row.stage='interview' AND target='evaluating')
 OR (row.stage IN ('hired','not_continuing') AND target='received' AND a.role='admin')));
 IF allowed IS NOT TRUE THEN RAISE EXCEPTION 'STAGE_TRANSITION_DENIED' USING ERRCODE='23514'; END IF;
 UPDATE cv.application SET stage=target,revision=revision+1 WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,move_stage.application);
 result:=gen_random_uuid();
 INSERT INTO cv.stage_event(tenant_id,scope_id,id,application_id,from_stage,to_stage,revision,actor_id,reason)
 VALUES(a.tenant_id,scope,result,application,row.stage,target,row.revision+1,a.user_id,reason);
 PERFORM cv.command_finish(a.tenant_id,p,'application.stage',operation_key,h,scope,result);
 RETURN result;
END $$;

CREATE OR REPLACE FUNCTION cv.review_intake(scope uuid,intake_id uuid,expected_revision integer,decision text,
 chosen_candidate uuid,reason text,operation_key uuid) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record; i cv.intake; p uuid; h cv.digest; result uuid; person uuid; app uuid; position uuid; BEGIN
 SELECT * INTO a FROM cv.current_authority();
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 p:=cv.lock_scope(a.tenant_id,scope);
 h:=encode(sha256(convert_to(jsonb_build_array(scope,intake_id,expected_revision,decision,chosen_candidate,reason)::text,'UTF8')),'hex');
 result:=cv.command_begin(a.tenant_id,p,'intake.review',operation_key,h);
 IF result IS NOT NULL THEN RETURN result; END IF;
 SELECT * INTO i FROM cv.intake WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,review_intake.intake_id) FOR UPDATE;
 IF NOT FOUND OR i.revision IS DISTINCT FROM expected_revision OR i.state<>'pending' OR coalesce(btrim(reason),'')=''
 OR decision IS NULL OR decision NOT IN ('link','create','reject') THEN RAISE EXCEPTION 'REVIEW_CONFLICT' USING ERRCODE='23514'; END IF;
 IF decision IN ('link','create') THEN
  IF NOT EXISTS(SELECT 1 FROM cv.document_version d JOIN cv.file_intent f
  ON (f.tenant_id,f.scope_id,f.id)=(d.tenant_id,d.scope_id,d.intent_id)
  WHERE (d.tenant_id,d.scope_id,d.id)=(a.tenant_id,scope,i.document_id) AND f.state='finalized') THEN
   RAISE EXCEPTION 'FILE_NOT_FINALIZED' USING ERRCODE='23514'; END IF;
  IF decision='create' THEN
   IF chosen_candidate IS NOT NULL THEN RAISE EXCEPTION 'REVIEW_INVALID' USING ERRCODE='23514'; END IF;
   person:=gen_random_uuid(); INSERT INTO cv.candidate VALUES(a.tenant_id,person,1,NULL);
  ELSE
   person:=chosen_candidate;
   IF NOT EXISTS(SELECT 1 FROM cv.candidate c WHERE (c.tenant_id,c.id)=(a.tenant_id,person) AND c.removed_at IS NULL
   AND EXISTS(SELECT 1 FROM cv.privacy_scope s WHERE (s.tenant_id,s.candidate_id)=(c.tenant_id,c.id) AND cv.scope_allowed(s.tenant_id,s.id)))
   THEN RAISE EXCEPTION 'PERSON_DENIED' USING ERRCODE='42501'; END IF;
  END IF;
  UPDATE cv.privacy_scope SET candidate_id=person WHERE (tenant_id,id)=(a.tenant_id,scope);
  SELECT position_id INTO position FROM cv.publication_snapshot WHERE (tenant_id,id)=(a.tenant_id,i.snapshot_id);
  app:=gen_random_uuid(); INSERT INTO cv.application VALUES(a.tenant_id,scope,app,person,position,'received',1,NULL);
 ELSE
  IF chosen_candidate IS NOT NULL THEN RAISE EXCEPTION 'REVIEW_INVALID' USING ERRCODE='23514'; END IF;
 END IF;
 result:=gen_random_uuid();
 INSERT INTO cv.intake_review VALUES(a.tenant_id,scope,result,i.id,decision,person,app,a.user_id,reason,clock_timestamp());
 UPDATE cv.intake SET state=CASE WHEN decision='reject' THEN 'rejected' ELSE 'linked' END,revision=revision+1
 WHERE (tenant_id,scope_id,id)=(a.tenant_id,scope,i.id);
 PERFORM cv.command_finish(a.tenant_id,p,'intake.review',operation_key,h,scope,result);
 RETURN result;
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
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
