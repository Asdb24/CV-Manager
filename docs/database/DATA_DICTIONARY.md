# PostgreSQL data dictionary

Generated from the actual migrated PostgreSQL catalog by `scripts/database_catalog.py`.
No recruitment records or credentials are exported. Read DATABASE_DESIGN.md for nullable semantics, authority, workflow and deletion limits.

Catalog SHA-256: `17dfedd58061ddd11657748e37bf571479b153f09a04186c0bcf1788eb4537c0`.

## advisory_evidence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| manifest_id | `uuid` | False | — |
| evidence_id | `uuid` | False | — |
| criterion_key | `text` | False | — |
| rank | `integer` | False | — |
| similarity | `double precision` | False | — |

Constraints:

- `advisory_evidence_criterion_key_not_null`: `NOT NULL criterion_key`
- `advisory_evidence_evidence_id_not_null`: `NOT NULL evidence_id`
- `advisory_evidence_manifest_id_not_null`: `NOT NULL manifest_id`
- `advisory_evidence_pkey`: `PRIMARY KEY (tenant_id, scope_id, run_id, criterion_key, rank)`
- `advisory_evidence_rank_check`: `CHECK ((rank > 0))`
- `advisory_evidence_rank_not_null`: `NOT NULL rank`
- `advisory_evidence_run_id_not_null`: `NOT NULL run_id`
- `advisory_evidence_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_evidence_similarity_check`: `CHECK (((similarity >= ('-1'::integer)::double precision) AND (similarity <= (1)::double precision)))`
- `advisory_evidence_similarity_not_null`: `NOT NULL similarity`
- `advisory_evidence_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_evidence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_evidence_tenant_id_scope_id_manifest_id_evidence__fkey`: `FOREIGN KEY (tenant_id, scope_id, manifest_id, evidence_id) REFERENCES cv.advisory_manifest_evidence(tenant_id, scope_id, manifest_id, evidence_id)`
- `advisory_evidence_tenant_id_scope_id_run_id_evidence_id_cri_key`: `UNIQUE (tenant_id, scope_id, run_id, evidence_id, criterion_key)`
- `advisory_evidence_tenant_id_scope_id_run_id_manifest_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, run_id, manifest_id) REFERENCES cv.advisory_run(tenant_id, scope_id, id, manifest_id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_finding

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| rule_key | `text` | False | — |
| category | `text` | False | — |
| vietnamese_text | `text` | False | — |

Constraints:

- `advisory_finding_category_check`: `CHECK ((category = 'information-to-verify'::text))`
- `advisory_finding_category_not_null`: `NOT NULL category`
- `advisory_finding_id_not_null`: `NOT NULL id`
- `advisory_finding_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `advisory_finding_rule_key_not_null`: `NOT NULL rule_key`
- `advisory_finding_run_id_not_null`: `NOT NULL run_id`
- `advisory_finding_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_finding_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_finding_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_finding_tenant_id_scope_id_id_run_id_key`: `UNIQUE (tenant_id, scope_id, id, run_id)`
- `advisory_finding_tenant_id_scope_id_run_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, run_id) REFERENCES cv.advisory_run(tenant_id, scope_id, id)`
- `advisory_finding_vietnamese_text_not_null`: `NOT NULL vietnamese_text`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_finding_evidence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| finding_id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| criterion_key | `text` | False | — |
| evidence_id | `uuid` | False | — |

Constraints:

- `advisory_finding_evidence_criterion_key_not_null`: `NOT NULL criterion_key`
- `advisory_finding_evidence_evidence_id_not_null`: `NOT NULL evidence_id`
- `advisory_finding_evidence_finding_id_not_null`: `NOT NULL finding_id`
- `advisory_finding_evidence_pkey`: `PRIMARY KEY (tenant_id, scope_id, finding_id, evidence_id)`
- `advisory_finding_evidence_run_id_not_null`: `NOT NULL run_id`
- `advisory_finding_evidence_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_finding_evidence_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_finding_evidence_tenant_id_scope_id_finding_id_ru_fkey`: `FOREIGN KEY (tenant_id, scope_id, finding_id, run_id) REFERENCES cv.advisory_finding(tenant_id, scope_id, id, run_id)`
- `advisory_finding_evidence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_finding_evidence_tenant_id_scope_id_run_id_eviden_fkey`: `FOREIGN KEY (tenant_id, scope_id, run_id, evidence_id, criterion_key) REFERENCES cv.advisory_evidence(tenant_id, scope_id, run_id, evidence_id, criterion_key)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_manifest

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| application_id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| profile_id | `uuid` | False | — |
| jd_id | `uuid` | False | — |
| input_digest | `cv.digest` | False | — |
| model_digest | `cv.digest` | False | — |
| tokenizer_digest | `cv.digest` | False | — |
| rule_digest | `cv.digest` | False | — |
| template_digest | `cv.digest` | False | — |
| config_digest | `cv.digest` | False | — |
| manifest_digest | `cv.digest` | False | — |
| definition | `jsonb` | False | — |
| approved_by | `uuid` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| construction_xid | `xid8` | False | pg_current_xact_id() |

Constraints:

- `advisory_manifest_application_id_not_null`: `NOT NULL application_id`
- `advisory_manifest_approved_by_not_null`: `NOT NULL approved_by`
- `advisory_manifest_config_digest_not_null`: `NOT NULL config_digest`
- `advisory_manifest_construction_xid_not_null`: `NOT NULL construction_xid`
- `advisory_manifest_definition_check`: `CHECK ((jsonb_typeof(definition) = 'object'::text))`
- `advisory_manifest_definition_not_null`: `NOT NULL definition`
- `advisory_manifest_expires_at_not_null`: `NOT NULL expires_at`
- `advisory_manifest_id_not_null`: `NOT NULL id`
- `advisory_manifest_input_digest_not_null`: `NOT NULL input_digest`
- `advisory_manifest_jd_id_not_null`: `NOT NULL jd_id`
- `advisory_manifest_manifest_digest_not_null`: `NOT NULL manifest_digest`
- `advisory_manifest_model_digest_not_null`: `NOT NULL model_digest`
- `advisory_manifest_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `advisory_manifest_position_id_not_null`: `NOT NULL position_id`
- `advisory_manifest_profile_id_not_null`: `NOT NULL profile_id`
- `advisory_manifest_rule_digest_not_null`: `NOT NULL rule_digest`
- `advisory_manifest_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_manifest_template_digest_not_null`: `NOT NULL template_digest`
- `advisory_manifest_tenant_id_approved_by_fkey`: `FOREIGN KEY (tenant_id, approved_by) REFERENCES cv.membership(tenant_id, user_id)`
- `advisory_manifest_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_manifest_tenant_id_position_id_jd_id_fkey`: `FOREIGN KEY (tenant_id, position_id, jd_id) REFERENCES cv.jd_version(tenant_id, position_id, id)`
- `advisory_manifest_tenant_id_scope_id_application_id_positi_fkey`: `FOREIGN KEY (tenant_id, scope_id, application_id, position_id) REFERENCES cv.application(tenant_id, scope_id, id, position_id)`
- `advisory_manifest_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_manifest_tenant_id_scope_id_manifest_digest_key`: `UNIQUE (tenant_id, scope_id, manifest_digest)`
- `advisory_manifest_tenant_id_scope_id_profile_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, profile_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`
- `advisory_manifest_tokenizer_digest_not_null`: `NOT NULL tokenizer_digest`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_manifest_evidence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| manifest_id | `uuid` | False | — |
| evidence_id | `uuid` | False | — |

Constraints:

- `advisory_manifest_evidence_evidence_id_not_null`: `NOT NULL evidence_id`
- `advisory_manifest_evidence_manifest_id_not_null`: `NOT NULL manifest_id`
- `advisory_manifest_evidence_pkey`: `PRIMARY KEY (tenant_id, scope_id, manifest_id, evidence_id)`
- `advisory_manifest_evidence_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_manifest_evidence_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_manifest_evidence_tenant_id_scope_id_evidence_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, evidence_id) REFERENCES cv.evidence_span(tenant_id, scope_id, id)`
- `advisory_manifest_evidence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_manifest_evidence_tenant_id_scope_id_manifest_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, manifest_id) REFERENCES cv.advisory_manifest(tenant_id, scope_id, id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_review

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| finding_id | `uuid` | True | — |
| actor_id | `uuid` | False | — |
| decision | `text` | False | — |
| reason | `text` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `advisory_review_actor_id_not_null`: `NOT NULL actor_id`
- `advisory_review_created_at_not_null`: `NOT NULL created_at`
- `advisory_review_decision_check`: `CHECK ((decision = ANY (ARRAY['acknowledged'::text, 'dismissed'::text, 'needs-verification'::text])))`
- `advisory_review_decision_not_null`: `NOT NULL decision`
- `advisory_review_id_not_null`: `NOT NULL id`
- `advisory_review_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `advisory_review_reason_not_null`: `NOT NULL reason`
- `advisory_review_run_id_not_null`: `NOT NULL run_id`
- `advisory_review_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_review_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `advisory_review_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_review_tenant_id_scope_id_finding_id_run_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, finding_id, run_id) REFERENCES cv.advisory_finding(tenant_id, scope_id, id, run_id)`
- `advisory_review_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_review_tenant_id_scope_id_run_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, run_id) REFERENCES cv.advisory_run(tenant_id, scope_id, id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_run

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| task_id | `uuid` | False | — |
| manifest_id | `uuid` | False | — |
| attempt | `integer` | False | — |
| claimed_device | `text` | False | — |
| claimed_runtime | `text` | False | — |
| execution_claim | `jsonb` | False | — |
| authorization_verified_by | `uuid` | False | — |
| authorization_verified_at | `timestamp with time zone` | False | — |
| execution_verification | `text` | False | — |
| output_digest | `cv.digest` | False | — |
| rank_definition | `jsonb` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |
| construction_xid | `xid8` | False | pg_current_xact_id() |

Constraints:

- `advisory_run_attempt_check`: `CHECK ((attempt > 0))`
- `advisory_run_attempt_not_null`: `NOT NULL attempt`
- `advisory_run_authorization_verified_at_not_null`: `NOT NULL authorization_verified_at`
- `advisory_run_authorization_verified_by_not_null`: `NOT NULL authorization_verified_by`
- `advisory_run_claimed_device_not_null`: `NOT NULL claimed_device`
- `advisory_run_claimed_runtime_not_null`: `NOT NULL claimed_runtime`
- `advisory_run_construction_xid_not_null`: `NOT NULL construction_xid`
- `advisory_run_created_at_not_null`: `NOT NULL created_at`
- `advisory_run_execution_claim_check`: `CHECK ((jsonb_typeof(execution_claim) = 'object'::text))`
- `advisory_run_execution_claim_not_null`: `NOT NULL execution_claim`
- `advisory_run_execution_verification_check`: `CHECK ((execution_verification = 'unattested-client-claim'::text))`
- `advisory_run_execution_verification_not_null`: `NOT NULL execution_verification`
- `advisory_run_id_not_null`: `NOT NULL id`
- `advisory_run_manifest_id_not_null`: `NOT NULL manifest_id`
- `advisory_run_output_digest_not_null`: `NOT NULL output_digest`
- `advisory_run_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `advisory_run_rank_definition_check`: `CHECK ((jsonb_typeof(rank_definition) = 'object'::text))`
- `advisory_run_rank_definition_not_null`: `NOT NULL rank_definition`
- `advisory_run_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_run_task_id_not_null`: `NOT NULL task_id`
- `advisory_run_tenant_id_authorization_verified_by_fkey`: `FOREIGN KEY (tenant_id, authorization_verified_by) REFERENCES cv.membership(tenant_id, user_id)`
- `advisory_run_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_run_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_run_tenant_id_scope_id_id_manifest_id_key`: `UNIQUE (tenant_id, scope_id, id, manifest_id)`
- `advisory_run_tenant_id_scope_id_task_id_attempt_key`: `UNIQUE (tenant_id, scope_id, task_id, attempt)`
- `advisory_run_tenant_id_scope_id_task_id_manifest_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, task_id, manifest_id) REFERENCES cv.advisory_task(tenant_id, scope_id, id, manifest_id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## advisory_task

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| manifest_id | `uuid` | False | — |
| actor_id | `uuid` | False | — |
| state | `text` | False | — |
| deadline | `timestamp with time zone` | False | — |
| revision | `integer` | False | — |

Constraints:

- `advisory_task_actor_id_not_null`: `NOT NULL actor_id`
- `advisory_task_deadline_not_null`: `NOT NULL deadline`
- `advisory_task_id_not_null`: `NOT NULL id`
- `advisory_task_manifest_id_not_null`: `NOT NULL manifest_id`
- `advisory_task_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `advisory_task_revision_check`: `CHECK ((revision > 0))`
- `advisory_task_revision_not_null`: `NOT NULL revision`
- `advisory_task_scope_id_not_null`: `NOT NULL scope_id`
- `advisory_task_state_check`: `CHECK ((state = ANY (ARRAY['queued'::text, 'running'::text, 'completed'::text, 'failed'::text, 'cancelled'::text, 'revoked'::text])))`
- `advisory_task_state_not_null`: `NOT NULL state`
- `advisory_task_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `advisory_task_tenant_id_not_null`: `NOT NULL tenant_id`
- `advisory_task_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `advisory_task_tenant_id_scope_id_id_manifest_id_key`: `UNIQUE (tenant_id, scope_id, id, manifest_id)`
- `advisory_task_tenant_id_scope_id_manifest_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, manifest_id) REFERENCES cv.advisory_manifest(tenant_id, scope_id, id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## agency

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| id | `uuid` | False | — |
| realm_key | `text` | False | — |
| name | `text` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `agency_created_at_not_null`: `NOT NULL created_at`
- `agency_id_not_null`: `NOT NULL id`
- `agency_name_check`: `CHECK ((btrim(name) <> ''::text))`
- `agency_name_not_null`: `NOT NULL name`
- `agency_pkey`: `PRIMARY KEY (id)`
- `agency_realm_key_check`: `CHECK ((btrim(realm_key) <> ''::text))`
- `agency_realm_key_not_null`: `NOT NULL realm_key`

## application

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| candidate_id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| stage | `cv.stage` | False | — |
| revision | `integer` | False | — |
| removed_at | `timestamp with time zone` | True | — |

Constraints:

- `application_candidate_id_not_null`: `NOT NULL candidate_id`
- `application_id_not_null`: `NOT NULL id`
- `application_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `application_position_id_not_null`: `NOT NULL position_id`
- `application_revision_check`: `CHECK ((revision > 0))`
- `application_revision_not_null`: `NOT NULL revision`
- `application_scope_id_not_null`: `NOT NULL scope_id`
- `application_stage_not_null`: `NOT NULL stage`
- `application_tenant_id_candidate_id_position_id_scope_id_key`: `UNIQUE (tenant_id, candidate_id, position_id, scope_id)`
- `application_tenant_id_not_null`: `NOT NULL tenant_id`
- `application_tenant_id_position_id_fkey`: `FOREIGN KEY (tenant_id, position_id) REFERENCES cv."position"(tenant_id, id)`
- `application_tenant_id_scope_id_candidate_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, candidate_id) REFERENCES cv.privacy_scope(tenant_id, id, candidate_id) ON DELETE CASCADE`
- `application_tenant_id_scope_id_id_position_id_key`: `UNIQUE (tenant_id, scope_id, id, position_id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## audit_event

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| actor_id | `uuid` | False | — |
| scope_id | `uuid` | True | — |
| action | `text` | False | — |
| record_id | `uuid` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `audit_event_action_not_null`: `NOT NULL action`
- `audit_event_actor_id_not_null`: `NOT NULL actor_id`
- `audit_event_created_at_not_null`: `NOT NULL created_at`
- `audit_event_id_not_null`: `NOT NULL id`
- `audit_event_pkey`: `PRIMARY KEY (tenant_id, id)`
- `audit_event_record_id_not_null`: `NOT NULL record_id`
- `audit_event_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `audit_event_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `audit_event_tenant_id_not_null`: `NOT NULL tenant_id`
- `audit_event_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## auth_attempt

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| login_digest | `cv.digest` | False | — |
| window_started | `timestamp with time zone` | False | — |
| attempts | `integer` | False | — |

Constraints:

- `auth_attempt_attempts_check`: `CHECK ((attempts > 0))`
- `auth_attempt_attempts_not_null`: `NOT NULL attempts`
- `auth_attempt_login_digest_not_null`: `NOT NULL login_digest`
- `auth_attempt_pkey`: `PRIMARY KEY (login_digest)`
- `auth_attempt_window_started_not_null`: `NOT NULL window_started`

## auth_audit

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| id | `uuid` | False | gen_random_uuid() |
| instance_id | `uuid` | False | — |
| actor_id | `uuid` | True | — |
| action | `text` | False | — |
| record_id | `uuid` | True | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `auth_audit_action_not_null`: `NOT NULL action`
- `auth_audit_created_at_not_null`: `NOT NULL created_at`
- `auth_audit_id_not_null`: `NOT NULL id`
- `auth_audit_instance_id_fkey`: `FOREIGN KEY (instance_id) REFERENCES cv.auth_installation(instance_id)`
- `auth_audit_instance_id_not_null`: `NOT NULL instance_id`
- `auth_audit_pkey`: `PRIMARY KEY (id)`

## auth_command

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| instance_id | `uuid` | False | — |
| actor_id | `uuid` | False | — |
| operation | `text` | False | — |
| operation_key | `uuid` | False | — |
| payload_digest | `cv.digest` | False | — |
| result | `jsonb` | False | — |

Constraints:

- `auth_command_actor_id_not_null`: `NOT NULL actor_id`
- `auth_command_instance_id_fkey`: `FOREIGN KEY (instance_id) REFERENCES cv.auth_installation(instance_id)`
- `auth_command_instance_id_not_null`: `NOT NULL instance_id`
- `auth_command_operation_key_not_null`: `NOT NULL operation_key`
- `auth_command_operation_not_null`: `NOT NULL operation`
- `auth_command_payload_digest_not_null`: `NOT NULL payload_digest`
- `auth_command_pkey`: `PRIMARY KEY (instance_id, actor_id, operation, operation_key)`
- `auth_command_result_not_null`: `NOT NULL result`

## auth_grant_revision

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| user_id | `uuid` | False | — |
| purpose_id | `uuid` | False | — |
| revision | `integer` | False | — |

Constraints:

- `auth_grant_revision_pkey`: `PRIMARY KEY (tenant_id, user_id, purpose_id)`
- `auth_grant_revision_purpose_id_not_null`: `NOT NULL purpose_id`
- `auth_grant_revision_revision_check`: `CHECK ((revision > 0))`
- `auth_grant_revision_revision_not_null`: `NOT NULL revision`
- `auth_grant_revision_tenant_id_not_null`: `NOT NULL tenant_id`
- `auth_grant_revision_tenant_id_user_id_purpose_id_fkey`: `FOREIGN KEY (tenant_id, user_id, purpose_id) REFERENCES cv.purpose_grant(tenant_id, user_id, purpose_id)`
- `auth_grant_revision_user_id_not_null`: `NOT NULL user_id`

## auth_installation

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| singleton | `boolean` | False | — |
| instance_id | `uuid` | False | — |
| state | `text` | False | — |
| realm | `text` | True | — |
| realm_key | `text` | True | — |
| tenant_id | `uuid` | True | — |
| policy | `jsonb` | True | — |
| startup_digest | `cv.digest` | True | — |
| startup_expires_at | `timestamp with time zone` | True | — |
| command_secret | `text` | True | — |
| window_started | `timestamp with time zone` | False | clock_timestamp() |
| attempts | `integer` | False | 0 |

Constraints:

- `auth_installation_attempts_check`: `CHECK ((attempts >= 0))`
- `auth_installation_attempts_not_null`: `NOT NULL attempts`
- `auth_installation_check`: `CHECK (((realm IS NULL) = (realm_key IS NULL)))`
- `auth_installation_check1`: `CHECK (((state <> 'initialized'::text) OR (tenant_id IS NOT NULL)))`
- `auth_installation_instance_id_key`: `UNIQUE (instance_id)`
- `auth_installation_instance_id_not_null`: `NOT NULL instance_id`
- `auth_installation_pkey`: `PRIMARY KEY (singleton)`
- `auth_installation_realm_check`: `CHECK ((realm = ANY (ARRAY['local'::text, 'server'::text])))`
- `auth_installation_singleton_check`: `CHECK (singleton)`
- `auth_installation_singleton_not_null`: `NOT NULL singleton`
- `auth_installation_state_check`: `CHECK ((state = ANY (ARRAY['new'::text, 'initialized'::text, 'closed'::text])))`
- `auth_installation_state_not_null`: `NOT NULL state`
- `auth_installation_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `auth_installation_window_started_not_null`: `NOT NULL window_started`

## auth_session

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| session_id | `uuid` | False | — |
| instance_id | `uuid` | False | — |

Constraints:

- `auth_session_instance_id_fkey`: `FOREIGN KEY (instance_id) REFERENCES cv.auth_installation(instance_id)`
- `auth_session_instance_id_not_null`: `NOT NULL instance_id`
- `auth_session_pkey`: `PRIMARY KEY (tenant_id, session_id)`
- `auth_session_session_id_not_null`: `NOT NULL session_id`
- `auth_session_tenant_id_not_null`: `NOT NULL tenant_id`
- `auth_session_tenant_id_session_id_fkey`: `FOREIGN KEY (tenant_id, session_id) REFERENCES cv.staff_session(tenant_id, id)`

## candidate

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| revision | `integer` | False | — |
| removed_at | `timestamp with time zone` | True | — |

Constraints:

- `candidate_id_not_null`: `NOT NULL id`
- `candidate_pkey`: `PRIMARY KEY (tenant_id, id)`
- `candidate_revision_check`: `CHECK ((revision > 0))`
- `candidate_revision_not_null`: `NOT NULL revision`
- `candidate_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `candidate_tenant_id_not_null`: `NOT NULL tenant_id`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## command_result

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| actor_id | `uuid` | False | — |
| purpose_id | `uuid` | False | — |
| operation | `text` | False | — |
| operation_key | `uuid` | False | — |
| payload_digest | `cv.digest` | False | — |
| scope_id | `uuid` | True | — |
| result_id | `uuid` | False | — |

Constraints:

- `command_result_actor_id_not_null`: `NOT NULL actor_id`
- `command_result_operation_key_not_null`: `NOT NULL operation_key`
- `command_result_operation_not_null`: `NOT NULL operation`
- `command_result_payload_digest_not_null`: `NOT NULL payload_digest`
- `command_result_pkey`: `PRIMARY KEY (tenant_id, actor_id, purpose_id, operation, operation_key)`
- `command_result_purpose_id_not_null`: `NOT NULL purpose_id`
- `command_result_result_id_not_null`: `NOT NULL result_id`
- `command_result_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `command_result_tenant_id_not_null`: `NOT NULL tenant_id`
- `command_result_tenant_id_purpose_id_fkey`: `FOREIGN KEY (tenant_id, purpose_id) REFERENCES cv.policy_version(tenant_id, id)`
- `command_result_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `final_command_purpose`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## company

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| name | `text` | False | — |
| revision | `integer` | False | — |
| removed_at | `timestamp with time zone` | True | — |

Constraints:

- `company_id_not_null`: `NOT NULL id`
- `company_name_check`: `CHECK ((btrim(name) <> ''::text))`
- `company_name_not_null`: `NOT NULL name`
- `company_pkey`: `PRIMARY KEY (tenant_id, id)`
- `company_revision_check`: `CHECK ((revision > 0))`
- `company_revision_not_null`: `NOT NULL revision`
- `company_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `company_tenant_id_not_null`: `NOT NULL tenant_id`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## contact_revision

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| version | `integer` | False | — |
| display_name | `text` | False | — |
| email | `text` | True | — |
| phone | `text` | True | — |
| author_id | `uuid` | True | — |

Constraints:

- `contact_revision_check`: `CHECK (((COALESCE(btrim(email), ''::text) <> ''::text) OR (COALESCE(btrim(phone), ''::text) <> ''::text)))`
- `contact_revision_display_name_check`: `CHECK ((btrim(display_name) <> ''::text))`
- `contact_revision_display_name_not_null`: `NOT NULL display_name`
- `contact_revision_id_not_null`: `NOT NULL id`
- `contact_revision_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `contact_revision_scope_id_not_null`: `NOT NULL scope_id`
- `contact_revision_tenant_id_author_id_fkey`: `FOREIGN KEY (tenant_id, author_id) REFERENCES cv.membership(tenant_id, user_id)`
- `contact_revision_tenant_id_not_null`: `NOT NULL tenant_id`
- `contact_revision_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `contact_revision_tenant_id_scope_id_version_key`: `UNIQUE (tenant_id, scope_id, version)`
- `contact_revision_version_check`: `CHECK ((version > 0))`
- `contact_revision_version_not_null`: `NOT NULL version`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## document_version

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| intent_id | `uuid` | False | — |
| version | `integer` | False | — |
| content_digest | `cv.digest` | False | — |
| media_type | `text` | False | — |
| byte_count | `bigint` | False | — |
| source_at | `timestamp with time zone` | False | — |
| received_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `document_version_byte_count_check`: `CHECK ((byte_count > 0))`
- `document_version_byte_count_not_null`: `NOT NULL byte_count`
- `document_version_content_digest_not_null`: `NOT NULL content_digest`
- `document_version_id_not_null`: `NOT NULL id`
- `document_version_intent_id_not_null`: `NOT NULL intent_id`
- `document_version_media_type_check`: `CHECK ((media_type = 'application/pdf'::text))`
- `document_version_media_type_not_null`: `NOT NULL media_type`
- `document_version_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `document_version_received_at_not_null`: `NOT NULL received_at`
- `document_version_scope_id_not_null`: `NOT NULL scope_id`
- `document_version_source_at_not_null`: `NOT NULL source_at`
- `document_version_tenant_id_not_null`: `NOT NULL tenant_id`
- `document_version_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `document_version_tenant_id_scope_id_intent_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, intent_id) REFERENCES cv.file_intent(tenant_id, scope_id, id)`
- `document_version_tenant_id_scope_id_intent_id_key`: `UNIQUE (tenant_id, scope_id, intent_id)`
- `document_version_version_check`: `CHECK ((version > 0))`
- `document_version_version_not_null`: `NOT NULL version`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## engine_definition

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| version | `text` | False | — |
| definition | `jsonb` | False | — |
| definition_digest | `cv.digest` | False | — |
| rounding | `text` | False | — |
| unknown_rule | `text` | False | — |

Constraints:

- `engine_definition_definition_check`: `CHECK ((jsonb_typeof(definition) = 'object'::text))`
- `engine_definition_definition_digest_not_null`: `NOT NULL definition_digest`
- `engine_definition_definition_not_null`: `NOT NULL definition`
- `engine_definition_id_not_null`: `NOT NULL id`
- `engine_definition_pkey`: `PRIMARY KEY (tenant_id, id)`
- `engine_definition_rounding_check`: `CHECK ((rounding = 'final-integer-half-up'::text))`
- `engine_definition_rounding_not_null`: `NOT NULL rounding`
- `engine_definition_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `engine_definition_tenant_id_not_null`: `NOT NULL tenant_id`
- `engine_definition_tenant_id_version_key`: `UNIQUE (tenant_id, version)`
- `engine_definition_unknown_rule_check`: `CHECK ((unknown_rule = 'positive-weight-unknown-blocks-total'::text))`
- `engine_definition_unknown_rule_not_null`: `NOT NULL unknown_rule`
- `engine_definition_version_not_null`: `NOT NULL version`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## erasure_context

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| backend_pid | `integer` | False | — |
| transaction_id | `xid8` | False | — |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |

Constraints:

- `erasure_context_backend_pid_not_null`: `NOT NULL backend_pid`
- `erasure_context_pkey`: `PRIMARY KEY (backend_pid)`
- `erasure_context_scope_id_not_null`: `NOT NULL scope_id`
- `erasure_context_tenant_id_not_null`: `NOT NULL tenant_id`
- `erasure_context_transaction_id_not_null`: `NOT NULL transaction_id`

## erasure_file

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| request_id | `uuid` | False | — |
| object_key | `uuid` | False | — |
| deleted_at | `timestamp with time zone` | True | — |

Constraints:

- `erasure_file_object_key_not_null`: `NOT NULL object_key`
- `erasure_file_pkey`: `PRIMARY KEY (tenant_id, request_id, object_key)`
- `erasure_file_request_id_not_null`: `NOT NULL request_id`
- `erasure_file_tenant_id_not_null`: `NOT NULL tenant_id`
- `erasure_file_tenant_id_request_id_fkey`: `FOREIGN KEY (tenant_id, request_id) REFERENCES cv.erasure_request(tenant_id, id)`

## erasure_request

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| scope_id | `uuid` | True | — |
| actor_id | `uuid` | False | — |
| status | `text` | False | — |
| requested_at | `timestamp with time zone` | False | clock_timestamp() |
| erasure_policy_id | `uuid` | True | — |

Constraints:

- `erasure_policy_reference`: `FOREIGN KEY (tenant_id, erasure_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `erasure_request_actor_id_not_null`: `NOT NULL actor_id`
- `erasure_request_id_not_null`: `NOT NULL id`
- `erasure_request_pkey`: `PRIMARY KEY (tenant_id, id)`
- `erasure_request_requested_at_not_null`: `NOT NULL requested_at`
- `erasure_request_status_check`: `CHECK ((status = ANY (ARRAY['requested'::text, 'database_purged'::text, 'files_pending'::text, 'verified'::text])))`
- `erasure_request_status_not_null`: `NOT NULL status`
- `erasure_request_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `erasure_request_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `erasure_request_tenant_id_not_null`: `NOT NULL tenant_id`
- `erasure_request_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE SET NULL (scope_id)`
- `final_erasure`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evaluation

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| rubric_id | `uuid` | False | — |
| jd_id | `uuid` | False | — |
| engine_id | `uuid` | False | — |
| factual_digest | `cv.digest` | False | — |
| calculation_digest | `cv.digest` | False | — |
| calculation_definition | `jsonb` | False | — |
| state | `text` | False | — |
| exact_total | `numeric` | True | — |
| total | `smallint` | True | — |
| mandatory_status | `cv.mandatory` | True | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |
| source_profile_id | `uuid` | True | — |

Constraints:

- `evaluation_calculation_definition_check`: `CHECK ((jsonb_typeof(calculation_definition) = 'object'::text))`
- `evaluation_calculation_definition_not_null`: `NOT NULL calculation_definition`
- `evaluation_calculation_digest_not_null`: `NOT NULL calculation_digest`
- `evaluation_check`: `CHECK (((exact_total IS NULL) = (total IS NULL)))`
- `evaluation_check1`: `CHECK (((total IS NULL) OR ((total)::numeric = floor((exact_total + 0.5)))))`
- `evaluation_check2`: `CHECK ((((state = 'complete'::text) AND (total IS NOT NULL) AND (mandatory_status IS NOT NULL)) OR ((state = 'incomplete'::text) AND (total IS NULL) AND (mandatory_status IS NOT NULL)) OR ((state = ANY (ARRAY['claimed'::text, 'failed'::text])) AND (total IS NULL) AND (mandatory_status IS NULL))))`
- `evaluation_created_at_not_null`: `NOT NULL created_at`
- `evaluation_engine_id_not_null`: `NOT NULL engine_id`
- `evaluation_exact_total_check`: `CHECK (((exact_total IS NULL) OR ((exact_total >= (0)::numeric) AND (exact_total <= (100)::numeric))))`
- `evaluation_factual_digest_not_null`: `NOT NULL factual_digest`
- `evaluation_id_not_null`: `NOT NULL id`
- `evaluation_jd_id_not_null`: `NOT NULL jd_id`
- `evaluation_math`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `evaluation_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `evaluation_position_id_not_null`: `NOT NULL position_id`
- `evaluation_rubric_id_not_null`: `NOT NULL rubric_id`
- `evaluation_scope_id_not_null`: `NOT NULL scope_id`
- `evaluation_source_profile_fk`: `FOREIGN KEY (tenant_id, scope_id, source_profile_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`
- `evaluation_state_check`: `CHECK ((state = ANY (ARRAY['claimed'::text, 'complete'::text, 'incomplete'::text, 'failed'::text])))`
- `evaluation_state_not_null`: `NOT NULL state`
- `evaluation_tenant_id_not_null`: `NOT NULL tenant_id`
- `evaluation_tenant_id_position_id_rubric_id_jd_id_engine_id_fkey`: `FOREIGN KEY (tenant_id, position_id, rubric_id, jd_id, engine_id) REFERENCES cv.rubric_version(tenant_id, position_id, id, jd_id, engine_id)`
- `evaluation_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `evaluation_tenant_id_scope_id_id_rubric_id_key`: `UNIQUE (tenant_id, scope_id, id, rubric_id)`
- `evaluation_tenant_id_scope_id_position_id_factual_digest_ca_key`: `UNIQUE (tenant_id, scope_id, position_id, factual_digest, calculation_digest)`
- `evaluation_total_check`: `CHECK (((total >= 0) AND (total <= 100)))`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `final_calculation_binding`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evaluation_component

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| evaluation_id | `uuid` | False | — |
| rubric_id | `uuid` | False | — |
| criterion_key | `text` | False | — |
| rating | `smallint` | True | — |
| weight | `numeric` | False | — |
| contribution | `numeric` | True | ((weight * (rating)::numeric) * 0.25) |
| mandatory_status | `cv.mandatory` | False | — |

Constraints:

- `component_math`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `evaluation_component_criterion_key_not_null`: `NOT NULL criterion_key`
- `evaluation_component_evaluation_id_not_null`: `NOT NULL evaluation_id`
- `evaluation_component_mandatory_status_not_null`: `NOT NULL mandatory_status`
- `evaluation_component_pkey`: `PRIMARY KEY (tenant_id, scope_id, evaluation_id, criterion_key)`
- `evaluation_component_rating_check`: `CHECK (((rating >= 0) AND (rating <= 4)))`
- `evaluation_component_rubric_id_not_null`: `NOT NULL rubric_id`
- `evaluation_component_scope_id_not_null`: `NOT NULL scope_id`
- `evaluation_component_tenant_id_not_null`: `NOT NULL tenant_id`
- `evaluation_component_tenant_id_rubric_id_criterion_key_fkey`: `FOREIGN KEY (tenant_id, rubric_id, criterion_key) REFERENCES cv.rubric_criterion(tenant_id, rubric_id, criterion_key)`
- `evaluation_component_tenant_id_scope_id_evaluation_id_rubr_fkey`: `FOREIGN KEY (tenant_id, scope_id, evaluation_id, rubric_id) REFERENCES cv.evaluation(tenant_id, scope_id, id, rubric_id)`
- `evaluation_component_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `evaluation_component_weight_check`: `CHECK (((weight >= (0)::numeric) AND (weight <= (100)::numeric)))`
- `evaluation_component_weight_not_null`: `NOT NULL weight`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evaluation_evidence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| evaluation_id | `uuid` | False | — |
| criterion_key | `text` | False | — |
| evidence_id | `uuid` | False | — |

Constraints:

- `evaluation_evidence_criterion_key_not_null`: `NOT NULL criterion_key`
- `evaluation_evidence_evaluation_id_not_null`: `NOT NULL evaluation_id`
- `evaluation_evidence_evidence_id_not_null`: `NOT NULL evidence_id`
- `evaluation_evidence_pkey`: `PRIMARY KEY (tenant_id, scope_id, evaluation_id, criterion_key, evidence_id)`
- `evaluation_evidence_scope_id_not_null`: `NOT NULL scope_id`
- `evaluation_evidence_tenant_id_not_null`: `NOT NULL tenant_id`
- `evaluation_evidence_tenant_id_scope_id_evaluation_id_crite_fkey`: `FOREIGN KEY (tenant_id, scope_id, evaluation_id, criterion_key) REFERENCES cv.evaluation_component(tenant_id, scope_id, evaluation_id, criterion_key)`
- `evaluation_evidence_tenant_id_scope_id_evidence_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, evidence_id) REFERENCES cv.evidence_span(tenant_id, scope_id, id)`
- `evaluation_evidence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evaluation_explanation

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| evaluation_id | `uuid` | False | — |
| locale | `text` | False | — |
| renderer_digest | `cv.digest` | False | — |
| content | `jsonb` | False | — |

Constraints:

- `evaluation_explanation_content_not_null`: `NOT NULL content`
- `evaluation_explanation_evaluation_id_not_null`: `NOT NULL evaluation_id`
- `evaluation_explanation_locale_not_null`: `NOT NULL locale`
- `evaluation_explanation_pkey`: `PRIMARY KEY (tenant_id, scope_id, evaluation_id, locale, renderer_digest)`
- `evaluation_explanation_renderer_digest_not_null`: `NOT NULL renderer_digest`
- `evaluation_explanation_scope_id_not_null`: `NOT NULL scope_id`
- `evaluation_explanation_tenant_id_not_null`: `NOT NULL tenant_id`
- `evaluation_explanation_tenant_id_scope_id_evaluation_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, evaluation_id) REFERENCES cv.evaluation(tenant_id, scope_id, id)`
- `evaluation_explanation_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evaluation_occurrence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| evaluation_id | `uuid` | False | — |
| application_id | `uuid` | False | — |
| profile_id | `uuid` | False | — |
| document_id | `uuid` | False | — |
| actor_id | `uuid` | False | — |

Constraints:

- `evaluation_occurrence_actor_id_not_null`: `NOT NULL actor_id`
- `evaluation_occurrence_application_id_not_null`: `NOT NULL application_id`
- `evaluation_occurrence_document_id_not_null`: `NOT NULL document_id`
- `evaluation_occurrence_evaluation_id_not_null`: `NOT NULL evaluation_id`
- `evaluation_occurrence_id_not_null`: `NOT NULL id`
- `evaluation_occurrence_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `evaluation_occurrence_profile_id_not_null`: `NOT NULL profile_id`
- `evaluation_occurrence_scope_id_not_null`: `NOT NULL scope_id`
- `evaluation_occurrence_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `evaluation_occurrence_tenant_id_not_null`: `NOT NULL tenant_id`
- `evaluation_occurrence_tenant_id_scope_id_application_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, application_id) REFERENCES cv.application(tenant_id, scope_id, id)`
- `evaluation_occurrence_tenant_id_scope_id_document_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, document_id) REFERENCES cv.document_version(tenant_id, scope_id, id)`
- `evaluation_occurrence_tenant_id_scope_id_evaluation_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, evaluation_id) REFERENCES cv.evaluation(tenant_id, scope_id, id)`
- `evaluation_occurrence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `evaluation_occurrence_tenant_id_scope_id_profile_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, profile_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## evidence_span

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| extraction_id | `uuid` | False | — |
| page | `integer` | False | — |
| start_offset | `integer` | False | — |
| end_offset | `integer` | False | — |
| semantic_locator | `text` | False | — |
| text_content | `text` | False | — |
| content_digest | `cv.digest` | False | — |

Constraints:

- `evidence_span_check`: `CHECK ((end_offset > start_offset))`
- `evidence_span_content_digest_not_null`: `NOT NULL content_digest`
- `evidence_span_end_offset_not_null`: `NOT NULL end_offset`
- `evidence_span_extraction_id_not_null`: `NOT NULL extraction_id`
- `evidence_span_id_not_null`: `NOT NULL id`
- `evidence_span_page_check`: `CHECK ((page >= 1))`
- `evidence_span_page_not_null`: `NOT NULL page`
- `evidence_span_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `evidence_span_scope_id_not_null`: `NOT NULL scope_id`
- `evidence_span_semantic_locator_not_null`: `NOT NULL semantic_locator`
- `evidence_span_start_offset_check`: `CHECK ((start_offset >= 0))`
- `evidence_span_start_offset_not_null`: `NOT NULL start_offset`
- `evidence_span_tenant_id_not_null`: `NOT NULL tenant_id`
- `evidence_span_tenant_id_scope_id_extraction_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, extraction_id) REFERENCES cv.extraction(tenant_id, scope_id, id)`
- `evidence_span_tenant_id_scope_id_extraction_id_semantic_loc_key`: `UNIQUE (tenant_id, scope_id, extraction_id, semantic_locator)`
- `evidence_span_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `evidence_span_text_content_not_null`: `NOT NULL text_content`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## extraction

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| content_digest | `cv.digest` | False | — |
| parser_digest | `cv.digest` | False | — |
| normalization_digest | `cv.digest` | False | — |
| definition | `jsonb` | False | — |
| state | `text` | False | — |
| semantic_digest | `cv.digest` | True | — |

Constraints:

- `extraction_content_digest_not_null`: `NOT NULL content_digest`
- `extraction_definition_check`: `CHECK ((jsonb_typeof(definition) = 'object'::text))`
- `extraction_definition_not_null`: `NOT NULL definition`
- `extraction_id_not_null`: `NOT NULL id`
- `extraction_normalization_digest_not_null`: `NOT NULL normalization_digest`
- `extraction_parser_digest_not_null`: `NOT NULL parser_digest`
- `extraction_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `extraction_scope_id_not_null`: `NOT NULL scope_id`
- `extraction_state_check`: `CHECK ((state = ANY (ARRAY['claimed'::text, 'complete'::text, 'failed'::text, 'incomplete'::text])))`
- `extraction_state_not_null`: `NOT NULL state`
- `extraction_tenant_id_not_null`: `NOT NULL tenant_id`
- `extraction_tenant_id_scope_id_content_digest_parser_digest__key`: `UNIQUE (tenant_id, scope_id, content_digest, parser_digest, normalization_digest)`
- `extraction_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## extraction_document

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| extraction_id | `uuid` | False | — |
| document_id | `uuid` | False | — |

Constraints:

- `extraction_document_document_id_not_null`: `NOT NULL document_id`
- `extraction_document_extraction_id_not_null`: `NOT NULL extraction_id`
- `extraction_document_pkey`: `PRIMARY KEY (tenant_id, scope_id, extraction_id, document_id)`
- `extraction_document_scope_id_not_null`: `NOT NULL scope_id`
- `extraction_document_tenant_id_not_null`: `NOT NULL tenant_id`
- `extraction_document_tenant_id_scope_id_document_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, document_id) REFERENCES cv.document_version(tenant_id, scope_id, id)`
- `extraction_document_tenant_id_scope_id_extraction_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, extraction_id) REFERENCES cv.extraction(tenant_id, scope_id, id)`
- `extraction_document_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## file_intent

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| object_key | `uuid` | False | — |
| purpose | `text` | False | — |
| state | `text` | False | — |
| byte_count | `bigint` | False | — |
| content_digest | `cv.digest` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| revision | `integer` | False | — |

Constraints:

- `file_intent_byte_count_check`: `CHECK ((byte_count > 0))`
- `file_intent_byte_count_not_null`: `NOT NULL byte_count`
- `file_intent_content_digest_not_null`: `NOT NULL content_digest`
- `file_intent_expires_at_not_null`: `NOT NULL expires_at`
- `file_intent_id_not_null`: `NOT NULL id`
- `file_intent_object_key_not_null`: `NOT NULL object_key`
- `file_intent_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `file_intent_purpose_check`: `CHECK ((purpose = ANY (ARRAY['resume'::text, 'intake'::text, 'export'::text, 'snapshot'::text])))`
- `file_intent_purpose_not_null`: `NOT NULL purpose`
- `file_intent_revision_check`: `CHECK ((revision > 0))`
- `file_intent_revision_not_null`: `NOT NULL revision`
- `file_intent_scope_id_not_null`: `NOT NULL scope_id`
- `file_intent_state_check`: `CHECK ((state = ANY (ARRAY['reserved'::text, 'written'::text, 'committed'::text, 'finalized'::text, 'cleanup_pending'::text, 'deleted'::text])))`
- `file_intent_state_not_null`: `NOT NULL state`
- `file_intent_tenant_id_not_null`: `NOT NULL tenant_id`
- `file_intent_tenant_id_object_key_key`: `UNIQUE (tenant_id, object_key)`
- `file_intent_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`

## intake

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| publication_id | `uuid` | False | — |
| snapshot_id | `uuid` | False | — |
| upload_grant_id | `uuid` | False | — |
| document_id | `uuid` | False | — |
| receipt | `uuid` | False | — |
| operation_key | `uuid` | False | — |
| payload_digest | `cv.digest` | False | — |
| submitted_at | `timestamp with time zone` | False | clock_timestamp() |
| source_at | `timestamp with time zone` | False | — |
| revision | `integer` | False | — |
| state | `text` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `final_public_acceptance`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `intake_document_id_not_null`: `NOT NULL document_id`
- `intake_id_not_null`: `NOT NULL id`
- `intake_operation_key_not_null`: `NOT NULL operation_key`
- `intake_payload_digest_not_null`: `NOT NULL payload_digest`
- `intake_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `intake_publication_id_not_null`: `NOT NULL publication_id`
- `intake_receipt_key`: `UNIQUE (receipt)`
- `intake_receipt_not_null`: `NOT NULL receipt`
- `intake_revision_check`: `CHECK ((revision > 0))`
- `intake_revision_not_null`: `NOT NULL revision`
- `intake_scope_id_not_null`: `NOT NULL scope_id`
- `intake_snapshot_id_not_null`: `NOT NULL snapshot_id`
- `intake_source_at_not_null`: `NOT NULL source_at`
- `intake_state_check`: `CHECK ((state = ANY (ARRAY['pending'::text, 'linked'::text, 'rejected'::text])))`
- `intake_state_not_null`: `NOT NULL state`
- `intake_submitted_at_not_null`: `NOT NULL submitted_at`
- `intake_tenant_id_not_null`: `NOT NULL tenant_id`
- `intake_tenant_id_publication_id_fkey`: `FOREIGN KEY (tenant_id, publication_id) REFERENCES cv.publication(tenant_id, id)`
- `intake_tenant_id_publication_id_operation_key_key`: `UNIQUE (tenant_id, publication_id, operation_key)`
- `intake_tenant_id_scope_id_document_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, document_id) REFERENCES cv.document_version(tenant_id, scope_id, id)`
- `intake_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `intake_tenant_id_snapshot_id_fkey`: `FOREIGN KEY (tenant_id, snapshot_id) REFERENCES cv.publication_snapshot(tenant_id, id)`
- `intake_tenant_id_upload_grant_id_fkey`: `FOREIGN KEY (tenant_id, upload_grant_id) REFERENCES cv.public_upload_grant(tenant_id, id)`
- `intake_tenant_id_upload_grant_id_key`: `UNIQUE (tenant_id, upload_grant_id)`
- `intake_upload_grant_id_not_null`: `NOT NULL upload_grant_id`

## intake_review

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| intake_id | `uuid` | False | — |
| decision | `text` | False | — |
| candidate_id | `uuid` | True | — |
| application_id | `uuid` | True | — |
| actor_id | `uuid` | False | — |
| reason | `text` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `intake_review_actor_id_not_null`: `NOT NULL actor_id`
- `intake_review_check`: `CHECK ((((decision = 'reject'::text) AND (candidate_id IS NULL) AND (application_id IS NULL)) OR ((decision = ANY (ARRAY['link'::text, 'create'::text])) AND (candidate_id IS NOT NULL) AND (application_id IS NOT NULL))))`
- `intake_review_created_at_not_null`: `NOT NULL created_at`
- `intake_review_decision_check`: `CHECK ((decision = ANY (ARRAY['link'::text, 'create'::text, 'reject'::text])))`
- `intake_review_decision_not_null`: `NOT NULL decision`
- `intake_review_id_not_null`: `NOT NULL id`
- `intake_review_intake_id_not_null`: `NOT NULL intake_id`
- `intake_review_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `intake_review_reason_check`: `CHECK ((btrim(reason) <> ''::text))`
- `intake_review_reason_not_null`: `NOT NULL reason`
- `intake_review_scope_id_not_null`: `NOT NULL scope_id`
- `intake_review_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `intake_review_tenant_id_not_null`: `NOT NULL tenant_id`
- `intake_review_tenant_id_scope_id_application_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, application_id) REFERENCES cv.application(tenant_id, scope_id, id)`
- `intake_review_tenant_id_scope_id_candidate_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, candidate_id) REFERENCES cv.privacy_scope(tenant_id, id, candidate_id)`
- `intake_review_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `intake_review_tenant_id_scope_id_intake_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, intake_id) REFERENCES cv.intake(tenant_id, scope_id, id)`
- `intake_review_tenant_id_scope_id_intake_id_key`: `UNIQUE (tenant_id, scope_id, intake_id)`

## jd_version

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| version | `integer` | False | — |
| content | `text` | False | — |
| content_digest | `cv.digest` | False | — |
| author_id | `uuid` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `jd_version_author_id_not_null`: `NOT NULL author_id`
- `jd_version_content_digest_not_null`: `NOT NULL content_digest`
- `jd_version_content_not_null`: `NOT NULL content`
- `jd_version_created_at_not_null`: `NOT NULL created_at`
- `jd_version_id_not_null`: `NOT NULL id`
- `jd_version_pkey`: `PRIMARY KEY (tenant_id, id)`
- `jd_version_position_id_not_null`: `NOT NULL position_id`
- `jd_version_tenant_id_author_id_fkey`: `FOREIGN KEY (tenant_id, author_id) REFERENCES cv.membership(tenant_id, user_id)`
- `jd_version_tenant_id_not_null`: `NOT NULL tenant_id`
- `jd_version_tenant_id_position_id_fkey`: `FOREIGN KEY (tenant_id, position_id) REFERENCES cv."position"(tenant_id, id)`
- `jd_version_tenant_id_position_id_id_key`: `UNIQUE (tenant_id, position_id, id)`
- `jd_version_tenant_id_position_id_version_key`: `UNIQUE (tenant_id, position_id, version)`
- `jd_version_version_check`: `CHECK ((version > 0))`
- `jd_version_version_not_null`: `NOT NULL version`

## membership

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| user_id | `uuid` | False | — |
| role | `text` | False | — |
| active | `boolean` | False | — |
| revision | `integer` | False | — |

Constraints:

- `membership_active_not_null`: `NOT NULL active`
- `membership_pkey`: `PRIMARY KEY (tenant_id, user_id)`
- `membership_revision_check`: `CHECK ((revision > 0))`
- `membership_revision_not_null`: `NOT NULL revision`
- `membership_role_check`: `CHECK ((role = ANY (ARRAY['admin'::text, 'recruiter'::text])))`
- `membership_role_not_null`: `NOT NULL role`
- `membership_tenant_id_not_null`: `NOT NULL tenant_id`
- `membership_tenant_id_user_id_fkey`: `FOREIGN KEY (tenant_id, user_id) REFERENCES cv.staff_user(tenant_id, id)`
- `membership_user_id_not_null`: `NOT NULL user_id`

## policy_revocation

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| policy_id | `uuid` | False | — |
| revoked_at | `timestamp with time zone` | False | — |
| actor_id | `uuid` | False | — |
| reason | `text` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `policy_revocation_actor_id_not_null`: `NOT NULL actor_id`
- `policy_revocation_pkey`: `PRIMARY KEY (tenant_id, policy_id)`
- `policy_revocation_policy_id_not_null`: `NOT NULL policy_id`
- `policy_revocation_reason_check`: `CHECK ((btrim(reason) <> ''::text))`
- `policy_revocation_reason_not_null`: `NOT NULL reason`
- `policy_revocation_revoked_at_not_null`: `NOT NULL revoked_at`
- `policy_revocation_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `policy_revocation_tenant_id_not_null`: `NOT NULL tenant_id`
- `policy_revocation_tenant_id_policy_id_fkey`: `FOREIGN KEY (tenant_id, policy_id) REFERENCES cv.policy_version(tenant_id, id)`

## policy_version

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| kind | `text` | False | — |
| version | `text` | False | — |
| owner_user_id | `uuid` | False | — |
| owner_role | `text` | False | — |
| synthetic_only | `boolean` | False | — |
| activated_at | `timestamp with time zone` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| definition | `jsonb` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `policy_version_activated_at_not_null`: `NOT NULL activated_at`
- `policy_version_check`: `CHECK ((expires_at > activated_at))`
- `policy_version_definition_check`: `CHECK ((jsonb_typeof(definition) = 'object'::text))`
- `policy_version_definition_not_null`: `NOT NULL definition`
- `policy_version_expires_at_not_null`: `NOT NULL expires_at`
- `policy_version_id_not_null`: `NOT NULL id`
- `policy_version_kind_check`: `CHECK ((kind = ANY (ARRAY['source'::text, 'purpose'::text, 'consent'::text, 'retention'::text, 'erasure'::text, 'resource'::text])))`
- `policy_version_kind_not_null`: `NOT NULL kind`
- `policy_version_owner_role_check`: `CHECK ((owner_role = ANY (ARRAY['workspace-admin'::text, 'agency-admin'::text, 'operator'::text])))`
- `policy_version_owner_role_not_null`: `NOT NULL owner_role`
- `policy_version_owner_user_id_not_null`: `NOT NULL owner_user_id`
- `policy_version_pkey`: `PRIMARY KEY (tenant_id, id)`
- `policy_version_synthetic_only_not_null`: `NOT NULL synthetic_only`
- `policy_version_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `policy_version_tenant_id_id_kind_key`: `UNIQUE (tenant_id, id, kind)`
- `policy_version_tenant_id_kind_version_key`: `UNIQUE (tenant_id, kind, version)`
- `policy_version_tenant_id_not_null`: `NOT NULL tenant_id`
- `policy_version_tenant_id_owner_user_id_fkey`: `FOREIGN KEY (tenant_id, owner_user_id) REFERENCES cv.membership(tenant_id, user_id)`
- `policy_version_version_not_null`: `NOT NULL version`

## position

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| company_id | `uuid` | False | — |
| title | `text` | False | — |
| revision | `integer` | False | — |
| removed_at | `timestamp with time zone` | True | — |

Constraints:


## privacy_scope

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| candidate_id | `uuid` | True | — |
| purpose_id | `uuid` | False | — |
| privacy_epoch | `uuid` | False | — |
| source_policy_id | `uuid` | False | — |
| consent_policy_id | `uuid` | False | — |
| retention_policy_id | `uuid` | False | — |
| erasure_policy_id | `uuid` | False | — |
| resource_policy_id | `uuid` | False | — |
| consent_at | `timestamp with time zone` | False | — |
| consent_expires_at | `timestamp with time zone` | False | — |
| revoked_at | `timestamp with time zone` | True | — |
| synthetic | `boolean` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `privacy_scope_check`: `CHECK ((consent_expires_at > consent_at))`
- `privacy_scope_consent_at_not_null`: `NOT NULL consent_at`
- `privacy_scope_consent_expires_at_not_null`: `NOT NULL consent_expires_at`
- `privacy_scope_consent_policy_id_not_null`: `NOT NULL consent_policy_id`
- `privacy_scope_created_at_not_null`: `NOT NULL created_at`
- `privacy_scope_erasure_policy_id_not_null`: `NOT NULL erasure_policy_id`
- `privacy_scope_id_not_null`: `NOT NULL id`
- `privacy_scope_pkey`: `PRIMARY KEY (tenant_id, id)`
- `privacy_scope_privacy_epoch_not_null`: `NOT NULL privacy_epoch`
- `privacy_scope_purpose_id_not_null`: `NOT NULL purpose_id`
- `privacy_scope_resource_policy_id_not_null`: `NOT NULL resource_policy_id`
- `privacy_scope_retention_policy_id_not_null`: `NOT NULL retention_policy_id`
- `privacy_scope_source_policy_id_not_null`: `NOT NULL source_policy_id`
- `privacy_scope_synthetic_not_null`: `NOT NULL synthetic`
- `privacy_scope_tenant_id_candidate_id_fkey`: `FOREIGN KEY (tenant_id, candidate_id) REFERENCES cv.candidate(tenant_id, id)`
- `privacy_scope_tenant_id_candidate_id_purpose_id_privacy_epo_key`: `UNIQUE (tenant_id, candidate_id, purpose_id, privacy_epoch)`
- `privacy_scope_tenant_id_consent_policy_id_fkey`: `FOREIGN KEY (tenant_id, consent_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `privacy_scope_tenant_id_erasure_policy_id_fkey`: `FOREIGN KEY (tenant_id, erasure_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `privacy_scope_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `privacy_scope_tenant_id_id_candidate_id_key`: `UNIQUE (tenant_id, id, candidate_id)`
- `privacy_scope_tenant_id_not_null`: `NOT NULL tenant_id`
- `privacy_scope_tenant_id_purpose_id_fkey`: `FOREIGN KEY (tenant_id, purpose_id) REFERENCES cv.policy_version(tenant_id, id)`
- `privacy_scope_tenant_id_resource_policy_id_fkey`: `FOREIGN KEY (tenant_id, resource_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `privacy_scope_tenant_id_retention_policy_id_fkey`: `FOREIGN KEY (tenant_id, retention_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `privacy_scope_tenant_id_source_policy_id_fkey`: `FOREIGN KEY (tenant_id, source_policy_id) REFERENCES cv.policy_version(tenant_id, id)`

## processing_task

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| document_id | `uuid` | False | — |
| kind | `text` | False | — |
| state | `text` | False | — |
| definition_digest | `cv.digest` | False | — |
| deadline | `timestamp with time zone` | False | — |
| error_code | `text` | True | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `processing_task_deadline_not_null`: `NOT NULL deadline`
- `processing_task_definition_digest_not_null`: `NOT NULL definition_digest`
- `processing_task_document_id_not_null`: `NOT NULL document_id`
- `processing_task_id_not_null`: `NOT NULL id`
- `processing_task_kind_check`: `CHECK ((kind = ANY (ARRAY['extract'::text, 'evaluate'::text])))`
- `processing_task_kind_not_null`: `NOT NULL kind`
- `processing_task_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `processing_task_scope_id_not_null`: `NOT NULL scope_id`
- `processing_task_state_check`: `CHECK ((state = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))`
- `processing_task_state_not_null`: `NOT NULL state`
- `processing_task_tenant_id_not_null`: `NOT NULL tenant_id`
- `processing_task_tenant_id_scope_id_document_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, document_id) REFERENCES cv.document_version(tenant_id, scope_id, id)`
- `processing_task_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`

## profile_evidence

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| profile_id | `uuid` | False | — |
| evidence_id | `uuid` | False | — |
| fact_key | `text` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `profile_evidence_evidence_id_not_null`: `NOT NULL evidence_id`
- `profile_evidence_fact_key_not_null`: `NOT NULL fact_key`
- `profile_evidence_pkey`: `PRIMARY KEY (tenant_id, scope_id, profile_id, fact_key, evidence_id)`
- `profile_evidence_profile_id_not_null`: `NOT NULL profile_id`
- `profile_evidence_scope_id_not_null`: `NOT NULL scope_id`
- `profile_evidence_tenant_id_not_null`: `NOT NULL tenant_id`
- `profile_evidence_tenant_id_scope_id_evidence_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, evidence_id) REFERENCES cv.evidence_span(tenant_id, scope_id, id)`
- `profile_evidence_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `profile_evidence_tenant_id_scope_id_profile_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, profile_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`

## profile_revision

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| version | `integer` | False | — |
| previous_id | `uuid` | True | — |
| factual_content | `jsonb` | False | — |
| factual_digest | `cv.digest` | False | — |
| author_id | `uuid` | False | — |
| reason | `text` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |
| construction_xid | `xid8` | False | pg_current_xact_id() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `profile_revision_author_id_not_null`: `NOT NULL author_id`
- `profile_revision_construction_xid_not_null`: `NOT NULL construction_xid`
- `profile_revision_created_at_not_null`: `NOT NULL created_at`
- `profile_revision_factual_content_check`: `CHECK ((jsonb_typeof(factual_content) = 'object'::text))`
- `profile_revision_factual_content_not_null`: `NOT NULL factual_content`
- `profile_revision_factual_digest_not_null`: `NOT NULL factual_digest`
- `profile_revision_id_not_null`: `NOT NULL id`
- `profile_revision_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `profile_revision_reason_check`: `CHECK ((btrim(reason) <> ''::text))`
- `profile_revision_reason_not_null`: `NOT NULL reason`
- `profile_revision_scope_id_not_null`: `NOT NULL scope_id`
- `profile_revision_tenant_id_author_id_fkey`: `FOREIGN KEY (tenant_id, author_id) REFERENCES cv.membership(tenant_id, user_id)`
- `profile_revision_tenant_id_not_null`: `NOT NULL tenant_id`
- `profile_revision_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `profile_revision_tenant_id_scope_id_previous_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, previous_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`
- `profile_revision_tenant_id_scope_id_version_key`: `UNIQUE (tenant_id, scope_id, version)`
- `profile_revision_version_check`: `CHECK ((version > 0))`
- `profile_revision_version_not_null`: `NOT NULL version`

## profile_source

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| profile_id | `uuid` | False | — |
| extraction_id | `uuid` | False | — |

Constraints:

- `final_authority`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `profile_source_extraction_id_not_null`: `NOT NULL extraction_id`
- `profile_source_pkey`: `PRIMARY KEY (tenant_id, scope_id, profile_id, extraction_id)`
- `profile_source_profile_id_not_null`: `NOT NULL profile_id`
- `profile_source_scope_id_not_null`: `NOT NULL scope_id`
- `profile_source_tenant_id_not_null`: `NOT NULL tenant_id`
- `profile_source_tenant_id_scope_id_extraction_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, extraction_id) REFERENCES cv.extraction(tenant_id, scope_id, id)`
- `profile_source_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `profile_source_tenant_id_scope_id_profile_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, profile_id) REFERENCES cv.profile_revision(tenant_id, scope_id, id)`

## public_upload_grant

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| publication_id | `uuid` | False | — |
| snapshot_id | `uuid` | False | — |
| proof_digest | `cv.digest` | False | — |
| object_key | `uuid` | False | — |
| content_digest | `cv.digest` | False | — |
| byte_count | `bigint` | False | — |
| validated_at | `timestamp with time zone` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| synthetic | `boolean` | False | — |
| scope_id | `uuid` | True | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `public_upload_grant_byte_count_check`: `CHECK ((byte_count > 0))`
- `public_upload_grant_byte_count_not_null`: `NOT NULL byte_count`
- `public_upload_grant_check`: `CHECK ((expires_at > validated_at))`
- `public_upload_grant_content_digest_not_null`: `NOT NULL content_digest`
- `public_upload_grant_expires_at_not_null`: `NOT NULL expires_at`
- `public_upload_grant_id_not_null`: `NOT NULL id`
- `public_upload_grant_object_key_not_null`: `NOT NULL object_key`
- `public_upload_grant_pkey`: `PRIMARY KEY (tenant_id, id)`
- `public_upload_grant_proof_digest_key`: `UNIQUE (proof_digest)`
- `public_upload_grant_proof_digest_not_null`: `NOT NULL proof_digest`
- `public_upload_grant_publication_id_not_null`: `NOT NULL publication_id`
- `public_upload_grant_snapshot_id_not_null`: `NOT NULL snapshot_id`
- `public_upload_grant_synthetic_not_null`: `NOT NULL synthetic`
- `public_upload_grant_tenant_id_not_null`: `NOT NULL tenant_id`
- `public_upload_grant_tenant_id_object_key_key`: `UNIQUE (tenant_id, object_key)`
- `public_upload_grant_tenant_id_publication_id_fkey`: `FOREIGN KEY (tenant_id, publication_id) REFERENCES cv.publication(tenant_id, id)`
- `public_upload_grant_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `public_upload_grant_tenant_id_snapshot_id_fkey`: `FOREIGN KEY (tenant_id, snapshot_id) REFERENCES cv.publication_snapshot(tenant_id, id)`
- `public_upload_grant_validated_at_not_null`: `NOT NULL validated_at`

## publication

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| snapshot_id | `uuid` | False | — |
| state | `text` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| revision | `integer` | False | — |
| purpose_id | `uuid` | False | — |
| source_policy_id | `uuid` | False | — |
| consent_policy_id | `uuid` | False | — |
| retention_policy_id | `uuid` | False | — |
| erasure_policy_id | `uuid` | False | — |
| resource_policy_id | `uuid` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `publication_consent_policy_id_not_null`: `NOT NULL consent_policy_id`
- `publication_erasure_policy_id_not_null`: `NOT NULL erasure_policy_id`
- `publication_expires_at_not_null`: `NOT NULL expires_at`
- `publication_id_key`: `UNIQUE (id)`
- `publication_id_not_null`: `NOT NULL id`
- `publication_pkey`: `PRIMARY KEY (tenant_id, id)`
- `publication_position_id_not_null`: `NOT NULL position_id`
- `publication_purpose_id_not_null`: `NOT NULL purpose_id`
- `publication_resource_policy_id_not_null`: `NOT NULL resource_policy_id`
- `publication_retention_policy_id_not_null`: `NOT NULL retention_policy_id`
- `publication_revision_check`: `CHECK ((revision > 0))`
- `publication_revision_not_null`: `NOT NULL revision`
- `publication_snapshot_id_not_null1`: `NOT NULL snapshot_id`
- `publication_source_policy_id_not_null`: `NOT NULL source_policy_id`
- `publication_state_check`: `CHECK ((state = ANY (ARRAY['draft'::text, 'published'::text, 'withdrawn'::text])))`
- `publication_state_not_null`: `NOT NULL state`
- `publication_tenant_id_consent_policy_id_fkey`: `FOREIGN KEY (tenant_id, consent_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `publication_tenant_id_erasure_policy_id_fkey`: `FOREIGN KEY (tenant_id, erasure_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `publication_tenant_id_id_snapshot_id_key`: `UNIQUE (tenant_id, id, snapshot_id)`
- `publication_tenant_id_not_null`: `NOT NULL tenant_id`
- `publication_tenant_id_position_id_snapshot_id_fkey`: `FOREIGN KEY (tenant_id, position_id, snapshot_id) REFERENCES cv.publication_snapshot(tenant_id, position_id, id)`
- `publication_tenant_id_purpose_id_fkey`: `FOREIGN KEY (tenant_id, purpose_id) REFERENCES cv.policy_version(tenant_id, id)`
- `publication_tenant_id_resource_policy_id_fkey`: `FOREIGN KEY (tenant_id, resource_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `publication_tenant_id_retention_policy_id_fkey`: `FOREIGN KEY (tenant_id, retention_policy_id) REFERENCES cv.policy_version(tenant_id, id)`
- `publication_tenant_id_source_policy_id_fkey`: `FOREIGN KEY (tenant_id, source_policy_id) REFERENCES cv.policy_version(tenant_id, id)`

## publication_snapshot

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| jd_id | `uuid` | False | — |
| version | `integer` | False | — |
| agency_display | `text` | False | — |
| company_display | `text` | True | — |
| role_title | `text` | False | — |
| location | `text` | True | — |
| work_arrangement | `text` | True | — |
| employment_type | `text` | True | — |
| approved_jd | `text` | False | — |
| application_instructions | `text` | False | — |
| approved_by | `uuid` | False | — |
| approved_at | `timestamp with time zone` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `publication_snapshot_agency_display_not_null`: `NOT NULL agency_display`
- `publication_snapshot_application_instructions_not_null`: `NOT NULL application_instructions`
- `publication_snapshot_approved_at_not_null`: `NOT NULL approved_at`
- `publication_snapshot_approved_by_not_null`: `NOT NULL approved_by`
- `publication_snapshot_approved_jd_not_null`: `NOT NULL approved_jd`
- `publication_snapshot_id_not_null`: `NOT NULL id`
- `publication_snapshot_jd_id_not_null`: `NOT NULL jd_id`
- `publication_snapshot_pkey`: `PRIMARY KEY (tenant_id, id)`
- `publication_snapshot_position_id_not_null`: `NOT NULL position_id`
- `publication_snapshot_role_title_not_null`: `NOT NULL role_title`
- `publication_snapshot_tenant_id_approved_by_fkey`: `FOREIGN KEY (tenant_id, approved_by) REFERENCES cv.membership(tenant_id, user_id)`
- `publication_snapshot_tenant_id_not_null`: `NOT NULL tenant_id`
- `publication_snapshot_tenant_id_position_id_id_key`: `UNIQUE (tenant_id, position_id, id)`
- `publication_snapshot_tenant_id_position_id_jd_id_fkey`: `FOREIGN KEY (tenant_id, position_id, jd_id) REFERENCES cv.jd_version(tenant_id, position_id, id)`
- `publication_snapshot_tenant_id_position_id_version_key`: `UNIQUE (tenant_id, position_id, version)`
- `publication_snapshot_version_check`: `CHECK ((version > 0))`
- `publication_snapshot_version_not_null`: `NOT NULL version`

## purpose_grant

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| user_id | `uuid` | False | — |
| purpose_id | `uuid` | False | — |
| active | `boolean` | False | — |

Constraints:

- `purpose_grant_active_not_null`: `NOT NULL active`
- `purpose_grant_pkey`: `PRIMARY KEY (tenant_id, user_id, purpose_id)`
- `purpose_grant_purpose_id_not_null`: `NOT NULL purpose_id`
- `purpose_grant_tenant_id_not_null`: `NOT NULL tenant_id`
- `purpose_grant_tenant_id_purpose_id_fkey`: `FOREIGN KEY (tenant_id, purpose_id) REFERENCES cv.policy_version(tenant_id, id)`
- `purpose_grant_tenant_id_user_id_fkey`: `FOREIGN KEY (tenant_id, user_id) REFERENCES cv.membership(tenant_id, user_id)`
- `purpose_grant_user_id_not_null`: `NOT NULL user_id`

## question_revision

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| question_set_id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| question_key | `text` | False | — |
| version | `integer` | False | — |
| previous_id | `uuid` | True | — |
| finding_id | `uuid` | True | — |
| vietnamese_text | `text` | False | — |
| editor_id | `uuid` | True | — |
| edit_reason | `text` | True | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `question_revision_check`: `CHECK ((((version = 1) AND (previous_id IS NULL)) OR ((version > 1) AND (previous_id IS NOT NULL) AND (editor_id IS NOT NULL) AND (COALESCE(btrim(edit_reason), ''::text) <> ''::text))))`
- `question_revision_id_not_null`: `NOT NULL id`
- `question_revision_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `question_revision_question_key_not_null`: `NOT NULL question_key`
- `question_revision_question_set_id_not_null`: `NOT NULL question_set_id`
- `question_revision_run_id_not_null`: `NOT NULL run_id`
- `question_revision_scope_id_not_null`: `NOT NULL scope_id`
- `question_revision_tenant_id_editor_id_fkey`: `FOREIGN KEY (tenant_id, editor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `question_revision_tenant_id_not_null`: `NOT NULL tenant_id`
- `question_revision_tenant_id_scope_id_finding_id_run_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, finding_id, run_id) REFERENCES cv.advisory_finding(tenant_id, scope_id, id, run_id)`
- `question_revision_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `question_revision_tenant_id_scope_id_id_question_set_id_que_key`: `UNIQUE (tenant_id, scope_id, id, question_set_id, question_key)`
- `question_revision_tenant_id_scope_id_previous_id_question__fkey`: `FOREIGN KEY (tenant_id, scope_id, previous_id, question_set_id, question_key) REFERENCES cv.question_revision(tenant_id, scope_id, id, question_set_id, question_key)`
- `question_revision_tenant_id_scope_id_question_set_id_questi_key`: `UNIQUE (tenant_id, scope_id, question_set_id, question_key, version)`
- `question_revision_tenant_id_scope_id_question_set_id_run_i_fkey`: `FOREIGN KEY (tenant_id, scope_id, question_set_id, run_id) REFERENCES cv.question_set(tenant_id, scope_id, id, run_id)`
- `question_revision_version_check`: `CHECK ((version > 0))`
- `question_revision_version_not_null`: `NOT NULL version`
- `question_revision_vietnamese_text_not_null`: `NOT NULL vietnamese_text`

## question_set

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| run_id | `uuid` | False | — |
| template_digest | `cv.digest` | False | — |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `question_set_id_not_null`: `NOT NULL id`
- `question_set_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `question_set_run_id_not_null`: `NOT NULL run_id`
- `question_set_scope_id_not_null`: `NOT NULL scope_id`
- `question_set_template_digest_not_null`: `NOT NULL template_digest`
- `question_set_tenant_id_not_null`: `NOT NULL tenant_id`
- `question_set_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `question_set_tenant_id_scope_id_id_run_id_key`: `UNIQUE (tenant_id, scope_id, id, run_id)`
- `question_set_tenant_id_scope_id_run_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, run_id) REFERENCES cv.advisory_run(tenant_id, scope_id, id)`

## rubric_criterion

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| rubric_id | `uuid` | False | — |
| criterion_key | `text` | False | — |
| ordinal | `integer` | False | — |
| weight | `numeric` | False | — |
| adapter | `jsonb` | False | — |
| mandatory_definition | `jsonb` | True | — |

Constraints:

- `criterion_sum`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `rubric_criterion_adapter_check`: `CHECK ((jsonb_typeof(adapter) = 'object'::text))`
- `rubric_criterion_adapter_not_null`: `NOT NULL adapter`
- `rubric_criterion_criterion_key_not_null`: `NOT NULL criterion_key`
- `rubric_criterion_ordinal_check`: `CHECK ((ordinal >= 0))`
- `rubric_criterion_ordinal_not_null`: `NOT NULL ordinal`
- `rubric_criterion_pkey`: `PRIMARY KEY (tenant_id, rubric_id, criterion_key)`
- `rubric_criterion_rubric_id_not_null`: `NOT NULL rubric_id`
- `rubric_criterion_tenant_id_not_null`: `NOT NULL tenant_id`
- `rubric_criterion_tenant_id_rubric_id_fkey`: `FOREIGN KEY (tenant_id, rubric_id) REFERENCES cv.rubric_version(tenant_id, id)`
- `rubric_criterion_tenant_id_rubric_id_ordinal_key`: `UNIQUE (tenant_id, rubric_id, ordinal)`
- `rubric_criterion_weight_check`: `CHECK (((weight >= (0)::numeric) AND (weight <= (100)::numeric)))`
- `rubric_criterion_weight_not_null`: `NOT NULL weight`

## rubric_version

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| position_id | `uuid` | False | — |
| jd_id | `uuid` | False | — |
| engine_id | `uuid` | False | — |
| version | `integer` | False | — |
| reference_date | `date` | True | — |
| definition | `jsonb` | False | — |
| definition_digest | `cv.digest` | False | — |
| author_id | `uuid` | False | — |
| construction_xid | `xid8` | False | pg_current_xact_id() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `rubric_sum`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `rubric_version_author_id_not_null`: `NOT NULL author_id`
- `rubric_version_construction_xid_not_null`: `NOT NULL construction_xid`
- `rubric_version_definition_check`: `CHECK ((jsonb_typeof(definition) = 'object'::text))`
- `rubric_version_definition_digest_not_null`: `NOT NULL definition_digest`
- `rubric_version_definition_not_null`: `NOT NULL definition`
- `rubric_version_engine_id_not_null`: `NOT NULL engine_id`
- `rubric_version_id_not_null`: `NOT NULL id`
- `rubric_version_jd_id_not_null`: `NOT NULL jd_id`
- `rubric_version_pkey`: `PRIMARY KEY (tenant_id, id)`
- `rubric_version_position_id_not_null`: `NOT NULL position_id`
- `rubric_version_tenant_id_author_id_fkey`: `FOREIGN KEY (tenant_id, author_id) REFERENCES cv.membership(tenant_id, user_id)`
- `rubric_version_tenant_id_engine_id_fkey`: `FOREIGN KEY (tenant_id, engine_id) REFERENCES cv.engine_definition(tenant_id, id)`
- `rubric_version_tenant_id_not_null`: `NOT NULL tenant_id`
- `rubric_version_tenant_id_position_id_id_jd_id_engine_id_key`: `UNIQUE (tenant_id, position_id, id, jd_id, engine_id)`
- `rubric_version_tenant_id_position_id_jd_id_fkey`: `FOREIGN KEY (tenant_id, position_id, jd_id) REFERENCES cv.jd_version(tenant_id, position_id, id)`
- `rubric_version_tenant_id_position_id_version_key`: `UNIQUE (tenant_id, position_id, version)`
- `rubric_version_version_check`: `CHECK ((version > 0))`
- `rubric_version_version_not_null`: `NOT NULL version`

## staff_session

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| user_id | `uuid` | False | — |
| token_digest | `cv.digest` | False | — |
| expires_at | `timestamp with time zone` | False | — |
| revoked_at | `timestamp with time zone` | True | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `staff_session_check`: `CHECK ((expires_at > created_at))`
- `staff_session_created_at_not_null`: `NOT NULL created_at`
- `staff_session_expires_at_not_null`: `NOT NULL expires_at`
- `staff_session_id_not_null`: `NOT NULL id`
- `staff_session_pkey`: `PRIMARY KEY (tenant_id, id)`
- `staff_session_tenant_id_not_null`: `NOT NULL tenant_id`
- `staff_session_tenant_id_user_id_fkey`: `FOREIGN KEY (tenant_id, user_id) REFERENCES cv.membership(tenant_id, user_id)`
- `staff_session_token_digest_key`: `UNIQUE (token_digest)`
- `staff_session_token_digest_not_null`: `NOT NULL token_digest`
- `staff_session_user_id_not_null`: `NOT NULL user_id`

## staff_user

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| id | `uuid` | False | — |
| login_name | `text` | False | — |
| credential_hash | `text` | False | — |
| active | `boolean` | False | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `staff_user_active_not_null`: `NOT NULL active`
- `staff_user_created_at_not_null`: `NOT NULL created_at`
- `staff_user_credential_hash_not_null`: `NOT NULL credential_hash`
- `staff_user_id_not_null`: `NOT NULL id`
- `staff_user_login_name_not_null`: `NOT NULL login_name`
- `staff_user_pkey`: `PRIMARY KEY (tenant_id, id)`
- `staff_user_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES cv.agency(id)`
- `staff_user_tenant_id_login_name_key`: `UNIQUE (tenant_id, login_name)`
- `staff_user_tenant_id_not_null`: `NOT NULL tenant_id`

## stage_event

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| tenant_id | `uuid` | False | — |
| scope_id | `uuid` | False | — |
| id | `uuid` | False | — |
| application_id | `uuid` | False | — |
| from_stage | `cv.stage` | True | — |
| to_stage | `cv.stage` | False | — |
| revision | `integer` | False | — |
| actor_id | `uuid` | False | — |
| reason | `text` | True | — |
| created_at | `timestamp with time zone` | False | clock_timestamp() |

Constraints:

- `final_auth`: `TRIGGER DEFERRABLE INITIALLY DEFERRED`
- `stage_event_actor_id_not_null`: `NOT NULL actor_id`
- `stage_event_application_id_not_null`: `NOT NULL application_id`
- `stage_event_created_at_not_null`: `NOT NULL created_at`
- `stage_event_id_not_null`: `NOT NULL id`
- `stage_event_pkey`: `PRIMARY KEY (tenant_id, scope_id, id)`
- `stage_event_revision_check`: `CHECK ((revision > 0))`
- `stage_event_revision_not_null`: `NOT NULL revision`
- `stage_event_scope_id_not_null`: `NOT NULL scope_id`
- `stage_event_tenant_id_actor_id_fkey`: `FOREIGN KEY (tenant_id, actor_id) REFERENCES cv.membership(tenant_id, user_id)`
- `stage_event_tenant_id_not_null`: `NOT NULL tenant_id`
- `stage_event_tenant_id_scope_id_application_id_fkey`: `FOREIGN KEY (tenant_id, scope_id, application_id) REFERENCES cv.application(tenant_id, scope_id, id)`
- `stage_event_tenant_id_scope_id_application_id_revision_key`: `UNIQUE (tenant_id, scope_id, application_id, revision)`
- `stage_event_tenant_id_scope_id_fkey`: `FOREIGN KEY (tenant_id, scope_id) REFERENCES cv.privacy_scope(tenant_id, id) ON DELETE CASCADE`
- `stage_event_to_stage_not_null`: `NOT NULL to_stage`

## transaction_context

Owner: `cv_migrator`. RLS enabled: True; forced: True.

| Column | PostgreSQL type | Nullable | Default / generated expression |
| --- | --- | --- | --- |
| backend_pid | `integer` | False | — |
| transaction_id | `xid8` | False | — |
| tenant_id | `uuid` | False | — |
| session_id | `uuid` | False | — |
| user_id | `uuid` | False | — |

Constraints:

- `transaction_context_backend_pid_not_null`: `NOT NULL backend_pid`
- `transaction_context_pkey`: `PRIMARY KEY (backend_pid)`
- `transaction_context_session_id_not_null`: `NOT NULL session_id`
- `transaction_context_tenant_id_not_null`: `NOT NULL tenant_id`
- `transaction_context_tenant_id_session_id_fkey`: `FOREIGN KEY (tenant_id, session_id) REFERENCES cv.staff_session(tenant_id, id) ON DELETE CASCADE`
- `transaction_context_tenant_id_user_id_fkey`: `FOREIGN KEY (tenant_id, user_id) REFERENCES cv.membership(tenant_id, user_id)`
- `transaction_context_transaction_id_not_null`: `NOT NULL transaction_id`
- `transaction_context_user_id_not_null`: `NOT NULL user_id`
