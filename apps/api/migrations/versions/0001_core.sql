CREATE SCHEMA cv;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA cv FROM PUBLIC;
GRANT USAGE ON SCHEMA cv TO cv_guard, cv_runtime, cv_public, cv_probe;
GRANT CREATE ON SCHEMA cv TO cv_guard;
ALTER DEFAULT PRIVILEGES IN SCHEMA cv REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

CREATE DOMAIN cv.digest AS text CHECK (VALUE ~ '^[0-9a-f]{64}$');
CREATE DOMAIN cv.stage AS text CHECK (VALUE IN ('received','evaluating','interview','hired','not_continuing'));
CREATE DOMAIN cv.mandatory AS text CHECK (VALUE IN ('pass','fail','unknown'));

CREATE TABLE cv.agency (
 id uuid PRIMARY KEY, realm_key text NOT NULL CHECK (btrim(realm_key)<>''),
 name text NOT NULL CHECK (btrim(name)<>''), created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE cv.staff_user (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 login_name text NOT NULL, credential_hash text NOT NULL,
 active boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,login_name)
);
CREATE TABLE cv.membership (
 tenant_id uuid NOT NULL, user_id uuid NOT NULL,
 role text NOT NULL CHECK(role IN ('admin','recruiter')), active boolean NOT NULL,
 revision integer NOT NULL CHECK(revision>0), PRIMARY KEY(tenant_id,user_id),
 FOREIGN KEY(tenant_id,user_id) REFERENCES cv.staff_user(tenant_id,id)
);
CREATE TABLE cv.staff_session (
 tenant_id uuid NOT NULL, id uuid NOT NULL, user_id uuid NOT NULL,
 token_digest cv.digest NOT NULL UNIQUE, expires_at timestamptz NOT NULL,
 revoked_at timestamptz, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,user_id) REFERENCES cv.membership(tenant_id,user_id),
 CHECK(expires_at>created_at)
);
CREATE INDEX staff_session_user ON cv.staff_session(tenant_id,user_id);
CREATE TABLE cv.transaction_context (
 backend_pid integer PRIMARY KEY, transaction_id xid8 NOT NULL,
 tenant_id uuid NOT NULL, session_id uuid NOT NULL, user_id uuid NOT NULL,
 FOREIGN KEY(tenant_id,session_id) REFERENCES cv.staff_session(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,user_id) REFERENCES cv.membership(tenant_id,user_id)
);

CREATE TABLE cv.policy_version (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('source','purpose','consent','retention','erasure','resource')),
 version text NOT NULL, owner_user_id uuid NOT NULL, owner_role text NOT NULL,
 synthetic_only boolean NOT NULL, activated_at timestamptz NOT NULL,
 expires_at timestamptz NOT NULL, definition jsonb NOT NULL CHECK(jsonb_typeof(definition)='object'),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,kind,version), UNIQUE(tenant_id,id,kind),
 FOREIGN KEY(tenant_id,owner_user_id) REFERENCES cv.membership(tenant_id,user_id),
 CHECK(expires_at>activated_at), CHECK(owner_role IN ('workspace-admin','agency-admin','operator'))
);
CREATE TABLE cv.policy_revocation (
 tenant_id uuid NOT NULL, policy_id uuid NOT NULL, revoked_at timestamptz NOT NULL,
 actor_id uuid NOT NULL, reason text NOT NULL CHECK(btrim(reason)<>''),
 PRIMARY KEY(tenant_id,policy_id),
 FOREIGN KEY(tenant_id,policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.purpose_grant (
 tenant_id uuid NOT NULL, user_id uuid NOT NULL, purpose_id uuid NOT NULL,
 active boolean NOT NULL, PRIMARY KEY(tenant_id,user_id,purpose_id),
 FOREIGN KEY(tenant_id,user_id) REFERENCES cv.membership(tenant_id,user_id),
 FOREIGN KEY(tenant_id,purpose_id) REFERENCES cv.policy_version(tenant_id,id)
);
CREATE TABLE cv.company (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 name text NOT NULL CHECK(btrim(name)<>''), revision integer NOT NULL CHECK(revision>0),
 removed_at timestamptz, PRIMARY KEY(tenant_id,id)
);
CREATE INDEX company_active_name ON cv.company(tenant_id,name,id) WHERE removed_at IS NULL;
CREATE TABLE cv.position (
 tenant_id uuid NOT NULL, id uuid NOT NULL, company_id uuid NOT NULL,
 title text NOT NULL CHECK(btrim(title)<>''), revision integer NOT NULL CHECK(revision>0),
 removed_at timestamptz, PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,company_id,id),
 FOREIGN KEY(tenant_id,company_id) REFERENCES cv.company(tenant_id,id)
);
CREATE INDEX position_company ON cv.position(tenant_id,company_id,id);
CREATE TABLE cv.jd_version (
 tenant_id uuid NOT NULL, id uuid NOT NULL, position_id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0), content text NOT NULL,
 content_digest cv.digest NOT NULL, author_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,position_id,version), UNIQUE(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,position_id) REFERENCES cv.position(tenant_id,id),
 FOREIGN KEY(tenant_id,author_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.engine_definition (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 version text NOT NULL, definition jsonb NOT NULL CHECK(jsonb_typeof(definition)='object'),
 definition_digest cv.digest NOT NULL,
 rounding text NOT NULL CHECK(rounding='final-integer-half-up'),
 unknown_rule text NOT NULL CHECK(unknown_rule='positive-weight-unknown-blocks-total'),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,version)
);
CREATE TABLE cv.rubric_version (
 tenant_id uuid NOT NULL, id uuid NOT NULL, position_id uuid NOT NULL,
 jd_id uuid NOT NULL, engine_id uuid NOT NULL, version integer NOT NULL CHECK(version>0),
 reference_date date, definition jsonb NOT NULL CHECK(jsonb_typeof(definition)='object'),
 definition_digest cv.digest NOT NULL, author_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,position_id,version),
 UNIQUE(tenant_id,position_id,id,jd_id,engine_id),
 FOREIGN KEY(tenant_id,position_id,jd_id) REFERENCES cv.jd_version(tenant_id,position_id,id),
 FOREIGN KEY(tenant_id,engine_id) REFERENCES cv.engine_definition(tenant_id,id),
 FOREIGN KEY(tenant_id,author_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.rubric_criterion (
 tenant_id uuid NOT NULL, rubric_id uuid NOT NULL, criterion_key text NOT NULL,
 ordinal integer NOT NULL CHECK(ordinal>=0), weight numeric NOT NULL CHECK(weight>=0 AND weight<=100),
 adapter jsonb NOT NULL CHECK(jsonb_typeof(adapter)='object'), mandatory_definition jsonb,
 PRIMARY KEY(tenant_id,rubric_id,criterion_key), UNIQUE(tenant_id,rubric_id,ordinal),
 FOREIGN KEY(tenant_id,rubric_id) REFERENCES cv.rubric_version(tenant_id,id)
);

CREATE TABLE cv.candidate (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 revision integer NOT NULL CHECK(revision>0), removed_at timestamptz,
 PRIMARY KEY(tenant_id,id)
);
CREATE TABLE cv.privacy_scope (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL, candidate_id uuid,
 purpose_id uuid NOT NULL, privacy_epoch uuid NOT NULL,
 source_policy_id uuid NOT NULL, consent_policy_id uuid NOT NULL,
 retention_policy_id uuid NOT NULL, erasure_policy_id uuid NOT NULL, resource_policy_id uuid NOT NULL,
 consent_at timestamptz NOT NULL, consent_expires_at timestamptz NOT NULL,
 revoked_at timestamptz, synthetic boolean NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,id,candidate_id),
 UNIQUE(tenant_id,candidate_id,purpose_id,privacy_epoch),
 FOREIGN KEY(tenant_id,candidate_id) REFERENCES cv.candidate(tenant_id,id),
 FOREIGN KEY(tenant_id,purpose_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,source_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,consent_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,retention_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,erasure_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,resource_policy_id) REFERENCES cv.policy_version(tenant_id,id),
 CHECK(consent_expires_at>consent_at)
);
CREATE TABLE cv.contact_revision (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0), display_name text NOT NULL CHECK(btrim(display_name)<>''),
 email text, phone text, author_id uuid,
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,version),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,author_id) REFERENCES cv.membership(tenant_id,user_id),
 CHECK(coalesce(btrim(email),'')<>'' OR coalesce(btrim(phone),'')<>'')
);
CREATE TABLE cv.file_intent (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 object_key uuid NOT NULL, purpose text NOT NULL CHECK(purpose IN ('resume','intake','export','snapshot')),
 state text NOT NULL CHECK(state IN ('reserved','written','committed','finalized','cleanup_pending','deleted')),
 byte_count bigint NOT NULL CHECK(byte_count>0), content_digest cv.digest NOT NULL,
 expires_at timestamptz NOT NULL, revision integer NOT NULL CHECK(revision>0),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,object_key),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE
);
CREATE TABLE cv.document_version (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, intent_id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0), content_digest cv.digest NOT NULL,
 media_type text NOT NULL CHECK(media_type='application/pdf'), byte_count bigint NOT NULL CHECK(byte_count>0),
 source_at timestamptz NOT NULL, received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,intent_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,intent_id) REFERENCES cv.file_intent(tenant_id,scope_id,id)
);
CREATE TABLE cv.processing_task (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, document_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('extract','evaluate')),
 state text NOT NULL CHECK(state IN ('queued','running','succeeded','failed','cancelled')),
 definition_digest cv.digest NOT NULL, deadline timestamptz NOT NULL, error_code text,
 PRIMARY KEY(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,document_id) REFERENCES cv.document_version(tenant_id,scope_id,id)
);
CREATE TABLE cv.extraction (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 content_digest cv.digest NOT NULL, parser_digest cv.digest NOT NULL, normalization_digest cv.digest NOT NULL,
 definition jsonb NOT NULL CHECK(jsonb_typeof(definition)='object'),
 state text NOT NULL CHECK(state IN ('claimed','complete','failed','incomplete')),
 semantic_digest cv.digest, PRIMARY KEY(tenant_id,scope_id,id),
 UNIQUE(tenant_id,scope_id,content_digest,parser_digest,normalization_digest),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE
);
CREATE TABLE cv.extraction_document (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, extraction_id uuid NOT NULL, document_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,extraction_id,document_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,extraction_id) REFERENCES cv.extraction(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,document_id) REFERENCES cv.document_version(tenant_id,scope_id,id)
);
CREATE TABLE cv.evidence_span (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, extraction_id uuid NOT NULL,
 page integer NOT NULL CHECK(page>=1), start_offset integer NOT NULL CHECK(start_offset>=0),
 end_offset integer NOT NULL, semantic_locator text NOT NULL, text_content text NOT NULL,
 content_digest cv.digest NOT NULL, PRIMARY KEY(tenant_id,scope_id,id),
 UNIQUE(tenant_id,scope_id,extraction_id,semantic_locator),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,extraction_id) REFERENCES cv.extraction(tenant_id,scope_id,id),
 CHECK(end_offset>start_offset)
);
CREATE TABLE cv.profile_revision (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, version integer NOT NULL CHECK(version>0),
 previous_id uuid, factual_content jsonb NOT NULL CHECK(jsonb_typeof(factual_content)='object'),
 factual_digest cv.digest NOT NULL, author_id uuid NOT NULL, reason text NOT NULL CHECK(btrim(reason)<>''),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,version),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,previous_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,author_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.profile_evidence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, profile_id uuid NOT NULL, evidence_id uuid NOT NULL,
 fact_key text NOT NULL, PRIMARY KEY(tenant_id,scope_id,profile_id,fact_key,evidence_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,profile_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,evidence_id) REFERENCES cv.evidence_span(tenant_id,scope_id,id)
);
CREATE TABLE cv.application (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, candidate_id uuid NOT NULL,
 position_id uuid NOT NULL, stage cv.stage NOT NULL, revision integer NOT NULL CHECK(revision>0),
 removed_at timestamptz, PRIMARY KEY(tenant_id,scope_id,id),
 UNIQUE(tenant_id,scope_id,id,position_id), UNIQUE(tenant_id,candidate_id,position_id,scope_id),
 FOREIGN KEY(tenant_id,scope_id,candidate_id) REFERENCES cv.privacy_scope(tenant_id,id,candidate_id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,position_id) REFERENCES cv.position(tenant_id,id)
);
CREATE INDEX application_pipeline ON cv.application(tenant_id,position_id,stage,id) WHERE removed_at IS NULL;
CREATE TABLE cv.stage_event (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL, application_id uuid NOT NULL,
 from_stage cv.stage, to_stage cv.stage NOT NULL, revision integer NOT NULL CHECK(revision>0),
 actor_id uuid NOT NULL, reason text, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,application_id,revision),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,application_id) REFERENCES cv.application(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.evaluation (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 position_id uuid NOT NULL, rubric_id uuid NOT NULL, jd_id uuid NOT NULL, engine_id uuid NOT NULL,
 factual_digest cv.digest NOT NULL, calculation_digest cv.digest NOT NULL,
 calculation_definition jsonb NOT NULL CHECK(jsonb_typeof(calculation_definition)='object'),
 state text NOT NULL CHECK(state IN ('claimed','complete','incomplete','failed')),
 exact_total numeric, total smallint CHECK(total BETWEEN 0 AND 100), mandatory_status cv.mandatory,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,scope_id,id), UNIQUE(tenant_id,scope_id,id,rubric_id),
 UNIQUE(tenant_id,scope_id,position_id,factual_digest,calculation_digest),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,position_id,rubric_id,jd_id,engine_id)
 REFERENCES cv.rubric_version(tenant_id,position_id,id,jd_id,engine_id),
 CHECK(exact_total IS NULL OR exact_total BETWEEN 0 AND 100),
 CHECK((exact_total IS NULL)=(total IS NULL)),
 CHECK(total IS NULL OR total=floor(exact_total+0.5)),
 CHECK((state='complete' AND total IS NOT NULL AND mandatory_status IS NOT NULL)
 OR (state='incomplete' AND total IS NULL AND mandatory_status IS NOT NULL)
 OR (state IN ('claimed','failed') AND total IS NULL AND mandatory_status IS NULL))
);
CREATE TABLE cv.evaluation_component (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, evaluation_id uuid NOT NULL,
 rubric_id uuid NOT NULL, criterion_key text NOT NULL,
 rating smallint CHECK(rating BETWEEN 0 AND 4), weight numeric NOT NULL CHECK(weight>=0 AND weight<=100),
 contribution numeric GENERATED ALWAYS AS (weight*rating/4) STORED,
 mandatory_status cv.mandatory NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,evaluation_id,criterion_key),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,evaluation_id,rubric_id) REFERENCES cv.evaluation(tenant_id,scope_id,id,rubric_id),
 FOREIGN KEY(tenant_id,rubric_id,criterion_key) REFERENCES cv.rubric_criterion(tenant_id,rubric_id,criterion_key)
);
CREATE TABLE cv.evaluation_evidence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, evaluation_id uuid NOT NULL,
 criterion_key text NOT NULL, evidence_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,evaluation_id,criterion_key,evidence_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,evaluation_id,criterion_key) REFERENCES cv.evaluation_component(tenant_id,scope_id,evaluation_id,criterion_key),
 FOREIGN KEY(tenant_id,scope_id,evidence_id) REFERENCES cv.evidence_span(tenant_id,scope_id,id)
);
CREATE TABLE cv.evaluation_occurrence (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, id uuid NOT NULL,
 evaluation_id uuid NOT NULL, application_id uuid NOT NULL, profile_id uuid NOT NULL,
 document_id uuid NOT NULL, actor_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,evaluation_id) REFERENCES cv.evaluation(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,application_id) REFERENCES cv.application(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,profile_id) REFERENCES cv.profile_revision(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,scope_id,document_id) REFERENCES cv.document_version(tenant_id,scope_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id)
);
CREATE TABLE cv.evaluation_explanation (
 tenant_id uuid NOT NULL, scope_id uuid NOT NULL, evaluation_id uuid NOT NULL,
 locale text NOT NULL, renderer_digest cv.digest NOT NULL, content jsonb NOT NULL,
 PRIMARY KEY(tenant_id,scope_id,evaluation_id,locale,renderer_digest),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE,
 FOREIGN KEY(tenant_id,scope_id,evaluation_id) REFERENCES cv.evaluation(tenant_id,scope_id,id)
);
CREATE TABLE cv.command_result (
 tenant_id uuid NOT NULL, actor_id uuid NOT NULL, purpose_id uuid NOT NULL,
 operation text NOT NULL, operation_key uuid NOT NULL, payload_digest cv.digest NOT NULL,
 scope_id uuid, result_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,actor_id,purpose_id,operation,operation_key),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id),
 FOREIGN KEY(tenant_id,purpose_id) REFERENCES cv.policy_version(tenant_id,id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE
);
CREATE TABLE cv.audit_event (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL,
 actor_id uuid NOT NULL, scope_id uuid, action text NOT NULL, record_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE CASCADE
);
CREATE TABLE cv.erasure_request (
 tenant_id uuid NOT NULL REFERENCES cv.agency(id), id uuid NOT NULL, scope_id uuid,
 actor_id uuid NOT NULL, status text NOT NULL CHECK(status IN ('requested','database_purged','files_pending','verified')),
 requested_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,actor_id) REFERENCES cv.membership(tenant_id,user_id),
 FOREIGN KEY(tenant_id,scope_id) REFERENCES cv.privacy_scope(tenant_id,id) ON DELETE SET NULL (scope_id)
);
CREATE TABLE cv.erasure_file (
 tenant_id uuid NOT NULL, request_id uuid NOT NULL, object_key uuid NOT NULL,
 deleted_at timestamptz, PRIMARY KEY(tenant_id,request_id,object_key),
 FOREIGN KEY(tenant_id,request_id) REFERENCES cv.erasure_request(tenant_id,id)
);

-- These lookups run as a non-login, non-owner, non-BYPASSRLS role under explicit policies.
CREATE FUNCTION cv.bind_session(proof text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,cv AS $$
DECLARE s cv.staff_session; BEGIN
 SELECT ss.* INTO s FROM cv.staff_session ss
 JOIN cv.membership m ON (m.tenant_id,m.user_id)=(ss.tenant_id,ss.user_id)
 JOIN cv.staff_user u ON (u.tenant_id,u.id)=(m.tenant_id,m.user_id)
 WHERE ss.token_digest=encode(sha256(convert_to(proof,'UTF8')),'hex')
 AND ss.revoked_at IS NULL AND ss.expires_at>clock_timestamp() AND m.active AND u.active
 FOR SHARE OF ss,m,u;
 IF NOT FOUND THEN RAISE EXCEPTION 'AUTH_REQUIRED' USING ERRCODE='42501'; END IF;
 IF EXISTS(SELECT 1 FROM cv.transaction_context WHERE backend_pid=pg_backend_pid()
 AND transaction_id=pg_current_xact_id()) THEN
  RAISE EXCEPTION 'CONTEXT_ALREADY_BOUND' USING ERRCODE='42501';
 END IF;
 INSERT INTO cv.transaction_context VALUES(pg_backend_pid(),pg_current_xact_id(),s.tenant_id,s.id,s.user_id)
 ON CONFLICT(backend_pid) DO UPDATE SET transaction_id=excluded.transaction_id,
 tenant_id=excluded.tenant_id, session_id=excluded.session_id,user_id=excluded.user_id;
END $$;
CREATE FUNCTION cv.current_authority() RETURNS TABLE(tenant_id uuid,user_id uuid,role text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT c.tenant_id,c.user_id,m.role FROM cv.transaction_context c
 JOIN cv.staff_session s ON (s.tenant_id,s.id)=(c.tenant_id,c.session_id)
 JOIN cv.membership m ON (m.tenant_id,m.user_id)=(c.tenant_id,c.user_id)
 JOIN cv.staff_user u ON (u.tenant_id,u.id)=(c.tenant_id,c.user_id)
 WHERE c.backend_pid=pg_backend_pid() AND c.transaction_id=pg_current_xact_id()
 AND s.revoked_at IS NULL AND s.expires_at>statement_timestamp() AND m.active AND u.active
$$;
CREATE FUNCTION cv.tenant_allowed(t uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.current_authority() a WHERE a.tenant_id=t)
$$;
CREATE FUNCTION cv.policy_live(t uuid,p uuid,k text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.policy_version v WHERE v.tenant_id=t AND v.id=p AND v.kind=k
 AND v.activated_at<=statement_timestamp() AND v.expires_at>statement_timestamp()
 AND NOT EXISTS(SELECT 1 FROM cv.policy_revocation r WHERE (r.tenant_id,r.policy_id)=(t,p)))
$$;
CREATE FUNCTION cv.scope_allowed(t uuid,s uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.privacy_scope p JOIN cv.current_authority() a ON a.tenant_id=p.tenant_id
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id,g.purpose_id)=(p.tenant_id,a.user_id,p.purpose_id)
 WHERE (p.tenant_id,p.id)=(t,s) AND g.active AND p.revoked_at IS NULL
 AND p.consent_expires_at>statement_timestamp()
 AND cv.policy_live(t,p.purpose_id,'purpose') AND cv.policy_live(t,p.source_policy_id,'source')
 AND cv.policy_live(t,p.consent_policy_id,'consent') AND cv.policy_live(t,p.retention_policy_id,'retention')
 AND cv.policy_live(t,p.erasure_policy_id,'erasure') AND cv.policy_live(t,p.resource_policy_id,'resource'))
$$;
CREATE FUNCTION cv.final_authority_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; s uuid; BEGIN
 IF session_user<>'cv_runtime' THEN RETURN NULL; END IF;
 t := (to_jsonb(NEW)->>'tenant_id')::uuid;
 s := (to_jsonb(NEW)->>'scope_id')::uuid;
 IF NOT cv.tenant_allowed(t) OR (s IS NOT NULL AND NOT cv.scope_allowed(t,s)) THEN
  RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501';
 END IF;
 RETURN NULL;
END $$;

CREATE FUNCTION cv.immutable_row() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 -- Only the fixed erasure function (running as cv_guard) may cascade a revoked scope purge.
 IF TG_OP='DELETE' AND current_user='cv_guard' AND
 EXISTS(SELECT 1 FROM cv.erasure_request r WHERE r.tenant_id=(to_jsonb(OLD)->>'tenant_id')::uuid
 AND r.scope_id=(to_jsonb(OLD)->>'scope_id')::uuid AND r.status='requested') THEN RETURN OLD; END IF;
 RAISE EXCEPTION 'IMMUTABLE_HISTORY' USING ERRCODE='23514';
END $$;
CREATE FUNCTION cv.rubric_total_check() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; r uuid; BEGIN
 t:=NEW.tenant_id; r:=CASE WHEN TG_TABLE_NAME='rubric_version' THEN NEW.id ELSE NEW.rubric_id END;
 IF (SELECT coalesce(sum(weight),0) FROM cv.rubric_criterion WHERE tenant_id=t AND rubric_id=r)<>100
 THEN RAISE EXCEPTION 'RUBRIC_WEIGHT_SUM' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER rubric_sum AFTER INSERT ON cv.rubric_version
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.rubric_total_check();
CREATE CONSTRAINT TRIGGER criterion_sum AFTER INSERT ON cv.rubric_criterion
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.rubric_total_check();

CREATE FUNCTION cv.seal_result() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 IF OLD.state NOT IN ('claimed') OR NEW.state='claimed' THEN
  RAISE EXCEPTION 'IMMUTABLE_RESULT' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='evaluation' AND
 (to_jsonb(OLD)-ARRAY['state','exact_total','total','mandatory_status']) IS DISTINCT FROM
 (to_jsonb(NEW)-ARRAY['state','exact_total','total','mandatory_status']) THEN
  RAISE EXCEPTION 'CALCULATION_IDENTITY_IMMUTABLE' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='extraction' AND (to_jsonb(OLD)-ARRAY['state','semantic_digest']) IS DISTINCT FROM
 (to_jsonb(NEW)-ARRAY['state','semantic_digest']) THEN
  RAISE EXCEPTION 'EXTRACTION_IDENTITY_IMMUTABLE' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER evaluation_seal BEFORE UPDATE ON cv.evaluation FOR EACH ROW EXECUTE FUNCTION cv.seal_result();
CREATE TRIGGER extraction_seal BEFORE UPDATE ON cv.extraction FOR EACH ROW EXECUTE FUNCTION cv.seal_result();

DO $$ DECLARE r record; expression text; BEGIN
 FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='cv' LOOP
  EXECUTE format('ALTER TABLE cv.%I ENABLE ROW LEVEL SECURITY',r.tablename);
  EXECUTE format('ALTER TABLE cv.%I FORCE ROW LEVEL SECURITY',r.tablename);
  EXECUTE format('CREATE POLICY guard ON cv.%I TO cv_guard USING(true) WITH CHECK(true)',r.tablename);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON cv.%I TO cv_guard',r.tablename);
  IF r.tablename NOT IN ('transaction_context','staff_user','membership','staff_session','purpose_grant') THEN
   IF r.tablename='agency' THEN expression:='cv.tenant_allowed(id)';
   ELSIF r.tablename='privacy_scope' THEN expression:='cv.scope_allowed(tenant_id,id)';
   ELSIF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='cv' AND table_name=r.tablename AND column_name='scope_id')
   THEN expression:='cv.tenant_allowed(tenant_id) AND (scope_id IS NULL OR cv.scope_allowed(tenant_id,scope_id))';
   ELSE expression:='cv.tenant_allowed(tenant_id)'; END IF;
   EXECUTE format('CREATE POLICY staff ON cv.%I TO cv_runtime USING(%s) WITH CHECK(%s)',r.tablename,expression,expression);
   EXECUTE format('GRANT SELECT ON cv.%I TO cv_runtime',r.tablename);
  END IF;
 END LOOP;
 FOR r IN SELECT unnest(ARRAY['policy_version','policy_revocation','jd_version','engine_definition','rubric_version','rubric_criterion','contact_revision','document_version','extraction_document','evidence_span','profile_revision','profile_evidence','stage_event','evaluation_component','evaluation_evidence','evaluation_occurrence','evaluation_explanation','audit_event','command_result']) AS tablename LOOP
  EXECUTE format('CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON cv.%I FOR EACH ROW EXECUTE FUNCTION cv.immutable_row()',r.tablename);
 END LOOP;
 FOR r IN SELECT p.oid::regprocedure AS identity FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='cv' AND p.prosecdef LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO cv_guard',r.identity);
 END LOOP;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cv FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.bind_session(text),cv.current_authority(),cv.tenant_allowed(uuid),cv.scope_allowed(uuid,uuid) TO cv_runtime;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA cv TO cv_guard;
GRANT SELECT ON cv.policy_version TO cv_probe;
CREATE POLICY probe_policy ON cv.policy_version TO cv_probe USING(false);
REVOKE CREATE ON SCHEMA cv FROM cv_guard;

CREATE FUNCTION cv.scope_policy_check() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,cv AS $$
DECLARE p uuid; k text; v cv.policy_version; BEGIN
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
CREATE TRIGGER scope_policies BEFORE INSERT OR UPDATE ON cv.privacy_scope
 FOR EACH ROW EXECUTE FUNCTION cv.scope_policy_check();

CREATE FUNCTION cv.evaluation_math_check() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,cv AS $$
DECLARE e cv.evaluation; n integer; expected integer; missing integer; amount numeric; mandatory_value text; BEGIN
 IF TG_TABLE_NAME='evaluation' THEN
  SELECT * INTO e FROM cv.evaluation WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.id);
 ELSE
  SELECT * INTO e FROM cv.evaluation WHERE (tenant_id,scope_id,id)=(NEW.tenant_id,NEW.scope_id,NEW.evaluation_id);
 END IF;
 IF e.state NOT IN ('complete','incomplete') THEN RETURN NULL; END IF;
 SELECT count(*) INTO expected FROM cv.rubric_criterion WHERE tenant_id=e.tenant_id AND rubric_id=e.rubric_id;
 SELECT count(*),count(*) FILTER(WHERE c.weight>0 AND c.rating IS NULL),sum(c.contribution),
 CASE WHEN bool_or(c.mandatory_status='fail') THEN 'fail'
 WHEN bool_or(c.mandatory_status='unknown') THEN 'unknown' ELSE 'pass' END
 INTO n,missing,amount,mandatory_value FROM cv.evaluation_component c
 WHERE (c.tenant_id,c.scope_id,c.evaluation_id)=(e.tenant_id,e.scope_id,e.id);
 IF n<>expected OR EXISTS(SELECT 1 FROM cv.evaluation_component c
 JOIN cv.rubric_criterion r ON (r.tenant_id,r.rubric_id,r.criterion_key)=(c.tenant_id,c.rubric_id,c.criterion_key)
 WHERE (c.tenant_id,c.scope_id,c.evaluation_id)=(e.tenant_id,e.scope_id,e.id)
 AND (c.weight<>r.weight OR (r.mandatory_definition IS NULL AND c.mandatory_status<>'pass')))
 OR e.mandatory_status<>mandatory_value
 OR (missing>0 AND e.state<>'incomplete') OR (missing=0 AND (e.state<>'complete' OR e.exact_total IS DISTINCT FROM amount))
 THEN RAISE EXCEPTION 'EVALUATION_OPERANDS_INVALID' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER evaluation_math AFTER INSERT OR UPDATE ON cv.evaluation
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.evaluation_math_check();
CREATE CONSTRAINT TRIGGER component_math AFTER INSERT ON cv.evaluation_component
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.evaluation_math_check();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cv FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA cv TO cv_guard;
