GRANT CREATE ON SCHEMA cv TO cv_guard;
CREATE TABLE cv.publication_snapshot (
 tenant_id uuid NOT NULL, id uuid NOT NULL, position_id uuid NOT NULL, jd_id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0), agency_display text NOT NULL, company_display text,
 role_title text NOT NULL, location text, work_arrangement text, employment_type text,
 approved_jd text NOT NULL, application_instructions text NOT NULL,
 approved_by uuid NOT NULL, approved_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,position_id,version), UNIQUE(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,position_id,jd_id) REFERENCES cv.jd_version(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,approved_by) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.publication (
 tenant_id uuid NOT NULL, id uuid NOT NULL UNIQUE, position_id uuid NOT NULL, snapshot_id uuid NOT NULL,
 state text NOT NULL CHECK(state IN ('draft','published','withdrawn')),
 expires_at timestamptz NOT NULL, revision integer NOT NULL CHECK(revision>0),
 purpose_id uuid NOT NULL, source_policy_id uuid NOT NULL, consent_policy_id uuid NOT NULL,
 retention_policy_id uuid NOT NULL, erasure_policy_id uuid NOT NULL, resource_policy_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,id,snapshot_id),
 FOREIGN KEY(tenant_id,position_id,snapshot_id) REFERENCES cv.publication_snapshot(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,purpose_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,source_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,consent_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,retention_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,erasure_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,resource_policy_id) REFERENCES cv.policy_version(tenant_id,id)
);
CREATE INDEX publication_visible ON cv.publication(state,expires_at,id) WHERE state='published';
CREATE TABLE cv.public_upload_grant (
 tenant_id uuid NOT NULL, id uuid NOT NULL, publication_id uuid NOT NULL, snapshot_id uuid NOT NULL,
 proof_digest cv.digest NOT NULL UNIQUE, object_key uuid NOT NULL, content_digest cv.digest NOT NULL,
 byte_count bigint NOT NULL CHECK(byte_count>0), validated_at timestamptz NOT NULL,
 expires_at timestamptz NOT NULL, synthetic boolean NOT NULL, scope_id uuid,
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,object_key),
 FOREIGN KEY(tenant_id,publication_id) REFERENCES cv.publication(tenant_id,id),
 FOREIGN KEY(tenant_id,snapshot_id) REFERENCES cv.publication_snapshot(tenant_id,id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 CHECK(expires_at>validated_at)
);
CREATE TABLE cv.intake (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, publication_id uuid NOT NULL,
 snapshot_id uuid NOT NULL, upload_grant_id uuid NOT NULL, document_id uuid NOT NULL,
 receipt uuid NOT NULL UNIQUE, operation_key uuid NOT NULL, payload_digest cv.digest NOT NULL,
 submitted_at timestamptz NOT NULL DEFAULT clock_timestamp(), source_at timestamptz NOT NULL,
 revision integer NOT NULL CHECK(revision>0), state text NOT NULL CHECK(state IN ('pending','linked','rejected')),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,upload_grant_id),
 UNIQUE(tenant_id,publication_id,operation_key),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,publication_id) REFERENCES cv.publication(tenant_id,id),
 FOREIGN KEY(tenant_id,snapshot_id) REFERENCES cv.publication_snapshot(tenant_id,id),
 FOREIGN KEY(tenant_id,upload_grant_id) REFERENCES cv.public_upload_grant(tenant_id,id),
 FOREIGN KEY(tenant_id,scope_id,document_id) REFERENCES cv.document_version(tenant_id,scope_id,id)
);
CREATE INDEX intake_pending ON cv.intake(tenant_id,state,submitted_at,id);
CREATE TABLE cv.intake_review (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, intake_id uuid NOT NULL,
 decision text NOT NULL CHECK(decision IN ('link','create','reject')), candidate_id uuid, application_id uuid,
 actor_id uuid NOT NULL, reason text NOT NULL CHECK(btrim(reason)<>''),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,intake_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,intake_id) REFERENCES cv.intake(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,candidate_id) REFERENCES cv.privacy_scope(tenant_id,id,candidate_id),
 FOREIGN KEY(tenant_id,scope_id,application_id) REFERENCES cv.application(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id),
 CHECK((decision='reject' AND candidate_id IS NULL AND application_id IS NULL)
 OR (decision IN ('link','create') AND candidate_id IS NOT NULL AND application_id IS NOT NULL))
);

CREATE TABLE cv.advisory_manifest (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 application_id uuid NOT NULL, position_id uuid NOT NULL, profile_id uuid NOT NULL, jd_id uuid NOT NULL,
 input_digest cv.digest NOT NULL, model_digest cv.digest NOT NULL, tokenizer_digest cv.digest NOT NULL,
 rule_digest cv.digest NOT NULL, template_digest cv.digest NOT NULL, config_digest cv.digest NOT NULL,
 manifest_digest cv.digest NOT NULL, definition jsonb NOT NULL CHECK(jsonb_typeof(definition)='object'),
 approved_by uuid NOT NULL, expires_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,manifest_digest),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,application_id,position_id) REFERENCES cv.application(tenant_id,scope_id,id,position_id),
 FOREIGN KEY(tenant_id,scope_id,profile_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,position_id,jd_id) REFERENCES cv.jd_version(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,approved_by) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.advisory_manifest_evidence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, manifest_id uuid NOT NULL, evidence_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,manifest_id,evidence_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,manifest_id) REFERENCES cv.advisory_manifest(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,evidence_id) REFERENCES cv.evidence_span(tenant_id,scope_id,id)
);
CREATE TABLE cv.advisory_task (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, manifest_id uuid NOT NULL,
 actor_id uuid NOT NULL, state text NOT NULL CHECK(state IN ('queued','running','completed','failed','cancelled','revoked')),
 deadline timestamptz NOT NULL, revision integer NOT NULL CHECK(revision>0),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,id,manifest_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,manifest_id) REFERENCES cv.advisory_manifest(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.advisory_run (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, task_id uuid NOT NULL, manifest_id uuid NOT NULL,
 attempt integer NOT NULL CHECK(attempt>0), claimed_device text NOT NULL, claimed_runtime text NOT NULL,
 execution_claim jsonb NOT NULL CHECK(jsonb_typeof(execution_claim)='object'),
 authorization_verified_by uuid NOT NULL, authorization_verified_at timestamptz NOT NULL,
 execution_verification text NOT NULL CHECK(execution_verification='unattested-client-claim'),
 output_digest cv.digest NOT NULL, rank_definition jsonb NOT NULL CHECK(jsonb_typeof(rank_definition)='object'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,task_id,attempt),
 UNIQUE(tenant_id,scope_id,id,manifest_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,task_id,manifest_id) REFERENCES cv.advisory_task(tenant_id,scope_id,id,manifest_id),
 FOREIGN KEY(tenant_id,authorization_verified_by) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.advisory_evidence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, run_id uuid NOT NULL, manifest_id uuid NOT NULL,
 evidence_id uuid NOT NULL, criterion_key text NOT NULL, rank integer NOT NULL CHECK(rank>0),
 similarity double precision NOT NULL CHECK(similarity>=-1 AND similarity<=1),
 PRIMARY KEY(tenant_id,scope_id,run_id,criterion_key,rank), UNIQUE(tenant_id,scope_id,run_id,evidence_id,criterion_key),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,run_id,manifest_id) REFERENCES cv.advisory_run(tenant_id,scope_id,id,manifest_id),
 FOREIGN KEY(tenant_id,scope_id,manifest_id,evidence_id) REFERENCES cv.advisory_manifest_evidence(tenant_id,scope_id,manifest_id,evidence_id)
);
CREATE TABLE cv.advisory_finding (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, run_id uuid NOT NULL,
 rule_key text NOT NULL, category text NOT NULL CHECK(category='information-to-verify'),
 vietnamese_text text NOT NULL, PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,run_id) REFERENCES cv.advisory_run(tenant_id,scope_id,id)
);
CREATE TABLE cv.advisory_finding_evidence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, finding_id uuid NOT NULL, run_id uuid NOT NULL,
 criterion_key text NOT NULL, evidence_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,finding_id,evidence_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,finding_id,run_id) REFERENCES cv.advisory_finding(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,scope_id,run_id,evidence_id,criterion_key) REFERENCES cv.advisory_evidence(tenant_id,scope_id,run_id,evidence_id,criterion_key)
);
CREATE TABLE cv.question_set (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, run_id uuid NOT NULL,
 template_digest cv.digest NOT NULL, PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,run_id) REFERENCES cv.advisory_run(tenant_id,scope_id,id)
);
CREATE TABLE cv.question_revision (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, question_set_id uuid NOT NULL,
 run_id uuid NOT NULL, question_key text NOT NULL, version integer NOT NULL CHECK(version>0),
 previous_id uuid, finding_id uuid, vietnamese_text text NOT NULL,
 editor_id uuid, edit_reason text,
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,question_set_id,question_key,version),
 UNIQUE(tenant_id,scope_id,id,question_set_id,question_key),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,question_set_id,run_id) REFERENCES cv.question_set(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,scope_id,previous_id,question_set_id,question_key) REFERENCES cv.question_revision(tenant_id,scope_id,id,question_set_id,question_key),
 FOREIGN KEY(tenant_id,scope_id,finding_id,run_id) REFERENCES cv.advisory_finding(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,editor_id) REFERENCES cv.membership(tenant_id,user_id),
 CHECK((version=1 AND previous_id IS NULL) OR
 (version>1 AND previous_id IS NOT NULL AND editor_id IS NOT NULL AND coalesce(btrim(edit_reason),'')<>''))
);
CREATE TABLE cv.advisory_review (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, run_id uuid NOT NULL,
 finding_id uuid, actor_id uuid NOT NULL, decision text NOT NULL CHECK(decision IN ('acknowledged','dismissed','needs-verification')),
 reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,run_id) REFERENCES cv.advisory_run(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,finding_id,run_id) REFERENCES cv.advisory_finding(tenant_id,scope_id,id,run_id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id)
);

CREATE FUNCTION cv.publication_open(t uuid,p uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.publication j JOIN cv.position p ON (p.tenant_id,p.id)=(j.tenant_id,j.position_id)
 JOIN cv.company c ON (c.tenant_id,c.id)=(p.tenant_id,p.company_id)
 WHERE (j.tenant_id,j.id)=(t,publication_open.p) AND j.state='published' AND j.expires_at>statement_timestamp()
 AND p.removed_at IS NULL AND c.removed_at IS NULL
 AND cv.policy_live(t,j.purpose_id,'purpose') AND cv.policy_live(t,j.source_policy_id,'source')
 AND cv.policy_live(t,j.consent_policy_id,'consent') AND cv.policy_live(t,j.retention_policy_id,'retention')
 AND cv.policy_live(t,j.erasure_policy_id,'erasure') AND cv.policy_live(t,j.resource_policy_id,'resource'))
$$;
CREATE FUNCTION cv.public_job(publication_id uuid)
RETURNS TABLE(publication uuid,snapshot uuid,agency_name text,company_name text,title text,location text,
 work_arrangement text,employment_type text,jd text,instructions text,expires_at timestamptz,consent_version uuid)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT p.id,s.id,s.agency_display,s.company_display,s.role_title,s.location,s.work_arrangement,s.employment_type,
 s.approved_jd,s.application_instructions,p.expires_at,p.consent_policy_id
 FROM cv.publication p JOIN cv.publication_snapshot s ON (s.tenant_id,s.id)=(p.tenant_id,p.snapshot_id)
 WHERE p.id=publication_id AND cv.publication_open(p.tenant_id,p.id)
$$;

CREATE FUNCTION cv.accept_intake(proof text,displayed_publication uuid,displayed_snapshot uuid,
 displayed_consent uuid,applicant_name text,email text,phone text,explicit_consent boolean,operation_key uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE g cv.public_upload_grant; p cv.publication; resource jsonb; s uuid; intent uuid; doc uuid; result uuid;
 h cv.digest; existing cv.intake; cap integer; retention_seconds integer; expiry timestamptz; BEGIN
 SELECT * INTO g FROM cv.public_upload_grant WHERE proof_digest=encode(sha256(convert_to(proof,'UTF8')),'hex');
 IF NOT FOUND THEN RAISE EXCEPTION 'INTAKE_UNAVAILABLE' USING ERRCODE='42501'; END IF;
 SELECT * INTO p FROM cv.publication WHERE (tenant_id,id)=(g.tenant_id,g.publication_id) FOR UPDATE;
 IF NOT FOUND OR NOT cv.publication_open(p.tenant_id,p.id) OR p.id<>displayed_publication
 OR p.snapshot_id<>displayed_snapshot OR g.snapshot_id<>displayed_snapshot OR p.consent_policy_id<>displayed_consent
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

CREATE FUNCTION cv.review_intake(scope uuid,intake_id uuid,expected_revision integer,decision text,
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
 IF NOT FOUND OR i.revision<>expected_revision OR i.state<>'pending' OR coalesce(btrim(reason),'')=''
 OR decision NOT IN ('link','create','reject') THEN RAISE EXCEPTION 'REVIEW_CONFLICT' USING ERRCODE='23514'; END IF;
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

DO $$ DECLARE r record; expression text; cols text; BEGIN
 FOR r IN SELECT unnest(ARRAY['publication_snapshot','publication','public_upload_grant','intake','intake_review',
 'advisory_manifest','advisory_manifest_evidence','advisory_task','advisory_run','advisory_evidence',
 'advisory_finding','advisory_finding_evidence','question_set','question_revision','advisory_review']) AS tablename LOOP
  EXECUTE format('ALTER TABLE cv.%I ENABLE ROW LEVEL SECURITY',r.tablename);
  EXECUTE format('ALTER TABLE cv.%I FORCE ROW LEVEL SECURITY',r.tablename);
  EXECUTE format('CREATE POLICY guard ON cv.%I TO cv_guard USING(true) WITH CHECK(true)',r.tablename);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON cv.%I TO cv_guard',r.tablename);
  IF r.tablename<>'public_upload_grant' THEN
   IF r.tablename IN ('publication_snapshot','publication') THEN expression:='cv.tenant_allowed(tenant_id)';
   ELSE expression:='cv.scope_allowed(tenant_id,scope_id)'; END IF;
   EXECUTE format('CREATE POLICY staff ON cv.%I TO cv_runtime USING(%s) WITH CHECK(%s)',r.tablename,expression,expression);
   EXECUTE format('GRANT SELECT ON cv.%I TO cv_runtime',r.tablename);
  END IF;
  IF r.tablename NOT IN ('publication','public_upload_grant','intake','advisory_task') THEN
   EXECUTE format('CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON cv.%I FOR EACH ROW EXECUTE FUNCTION cv.immutable_row()',r.tablename);
  END IF;
  EXECUTE format('CREATE CONSTRAINT TRIGGER final_auth AFTER INSERT OR UPDATE ON cv.%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_authority_check()',r.tablename);
 END LOOP;
 FOR r IN SELECT c.conname,c.conrelid::regclass AS relation,c.conkey FROM pg_constraint c
 JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='cv' AND c.contype='f'
 AND NOT EXISTS(SELECT 1 FROM pg_index i WHERE i.indrelid=c.conrelid AND i.indisvalid
 AND (i.indkey::smallint[])[0:cardinality(c.conkey)-1]=c.conkey) LOOP
  SELECT string_agg(quote_ident(a.attname),',' ORDER BY x.ordinality) INTO cols
  FROM unnest(r.conkey) WITH ORDINALITY x(attnum,ordinality)
  JOIN pg_attribute a ON a.attrelid=r.relation AND a.attnum=x.attnum;
  EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %s(%s)','fk_'||substr(md5(r.conname||r.relation::text),1,20),r.relation,cols);
 END LOOP;
 FOR r IN SELECT p.oid::regprocedure AS identity FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='cv' AND p.prosecdef LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO cv_guard',r.identity);
 END LOOP;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cv FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA cv TO cv_guard;
GRANT EXECUTE ON FUNCTION cv.public_job(uuid),cv.accept_intake(text,uuid,uuid,uuid,text,text,text,boolean,uuid) TO cv_public;
GRANT EXECUTE ON FUNCTION cv.review_intake(uuid,uuid,integer,text,uuid,text,uuid) TO cv_runtime;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
