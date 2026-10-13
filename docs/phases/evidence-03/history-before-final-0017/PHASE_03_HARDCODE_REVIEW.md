# Phase 03 hardcode review

Date: 2026-10-13. Main review completed; independent review pending. Reviewed active connection/session/migration/readiness/seed paths and manually classify SQL definitions, configuration, immutable migration content and isolated fixtures. A regex count does not prove correctness.

Operational connection bounds, paths, credentials and test volumes must have validated settings/native-tool owners. Database role/schema identifiers, scoring/state constraints and migration identities are versioned security/domain definitions, not operational fallback.

## Reviewed active paths

| Path / values | Classification and owner | Disposition / evidence |
| --- | --- | --- |
| DatabaseConnectionSettings; adapter host/port/database/user/password/SSL/timeouts/connection limit | Operational settings, validated central owner | Closed required schema; SecretStr; remote connections require verify-full and CA; no configured-secret fallback. Actual adapter/readiness tests and Python settings checks. |
| DatabaseTestSettings; owned cluster/config/credential path, port, timeouts, seed validity, synthetic volumes/page size | Explicit synthetic test configuration | infra/config/database-test.json supplies values. Paths are confined to project-owned .local/phase03. Script parameters require explicit config. No real-data onboarding permission. |
| Cluster tool executables and project root | Native context | Resolve installed binaries through PATH and validate owned marker; record actual executable hashes/version. No workstation absolute path embedded in application source. |
| cv_migrator/cv_guard/cv_runtime/cv_public/cv_probe; cv schema; transaction-context tables | Fixed security definitions | Distinct roles are part of the reviewed migration/adapter contract, never caller-selected authority. Superuser fixture role stays in isolated test scripts. |
| SQL states, role names, 0–4 ratings, weight total 100, final half-up, Unknown rule | Sourced product/security invariants | Keep in immutable migrations. Exact numeric tests include 12.5→13, 75, Unknown and separate mandatory result. Not configurable permission/score switches. |
| Applied migration filenames/revision IDs and SHA-256 ledger | Immutable version contract | Byte checks cover exact SQL/Python inventory and graph. New fixes use forward revisions. Three narrowly scoped applied Python formatting exceptions preserve frozen bytes; no type/security/assertion rule is weakened. |
| Synthetic identities, example.invalid contacts, sample 75 score and two-second expiry crossing | Isolated test/golden fixtures | Not runtime records or operational defaults. Synthetic labels, deterministic base IDs, redacted credential representation and actual PostgreSQL tests. |
| Readiness revision constant and unavailable-capability codes | Version/protocol contract | Actual database revision must match supported head. Overall readiness remains unavailable for future-owned capabilities; no fake successful domain readiness. |
| Fixed cv-jsonb-v1 / cv-calculation-v1 format labels | Immutable content-identity format | Exact numeric normalization and full persisted definition snapshot; clock/upload/locale inputs rejected by binding tests. A future format change requires explicit versioning. |
| Query/index tooling; SQL identifiers and table inventory | Developer evidence mechanism | Page size and data volume are validated settings; table/column/index identifiers are fixed schema references. EXPLAIN uses actual runtime role with RLS enabled. |
| Phase 03 output paths and checkpoint command set | Fixed phase artifact ownership | Separate evidence-03 output preserves predecessor evidence-02. Explicit --database-config is required for actual DB checks. No repeated model download or unrelated package installation. |

The candidate scan is saved as evidence-03/hardcode-candidates.txt. It covers changed connection/migration/catalog/query scripts and the runtime adapter; it is a navigation aid, not a zero-hardcode proof. Manual review additionally follows settings, API/worker readiness and SQL command paths. Main manual review is complete for current head 0010; any reviewer repairs require updated classification and verification.

Forward revisions 0009/0010 add versioned extraction format keys and fixed privacy/commit invariants, not operational overrides. The one/two-second waits in negative tests deliberately cross expiry and are isolated test stimuli; they do not set production retention or timeouts. The populated lifecycle imports the same synthetic seed and compares existing business values while excluding newly added construction transaction metadata. A scan of current generated cluster credentials against Phase 03 evidence found no matching secrets; it does not claim to be a general secret/security certification.

### 0013/0014 repair review

The temporary obligation table name, four obligation kinds, PostgreSQL role/schema identifiers, SQLSTATE mapping, single-SELECT interface and closure codes are fixed security/protocol definitions. The backend PID, xid, policy pins and validation clock come from PostgreSQL/native authorized context; no caller tenant assertion or operational fallback is introduced. TEMPORARY privilege is granted only to the nonlogin guard for its private ON COMMIT DROP obligation table. The adapter continues to use central connection/time/concurrency settings.

Two/three-second expirations, 0.01-second observation polling and synthetic contacts in test_finalization.py are isolated adversarial fixture stimuli. Blocking tests use configured connection/lock/statement bounds and the actual database deadline. They do not define production retention. Fixtures now inspect all visible tenant IDs and the tested record's audit entries rather than assuming the synthetic database has exactly one company or no unrelated audit history.

The applied 0013 downgrade wrapper needs only a formatting line wrap. Its exact bytes remain frozen, so it joins the narrow formatter-only exclusions. No lint, typing, security or assertion rule is suppressed for this repair. The new 0014 was format-checked before application. The current-source format/lint/type commands passed; the full phase gate still requires R4 and reviewer follow-up.

### 0015/0016 repair review

`cv-profile-source-v1` and `cv-calculation-v2`, source relation names, construction xid checks, approved extraction states and legacy rejection codes are fixed content/security definitions. Full immutable source fields resolve from authorized records. No filename, upload ID, current clock, model manifest or operational setting enters canonical calculation identity. Fixtures carry synthetic bytes labels only; SQL metadata is not proof of actual PDF parsing. The two-second private-read expiry scenarios are adversarial tests, not production retention settings. RLS registration uses native backend/xid context and a guard-owned temporary table; no new connection paths, secrets or fallback values were added.

Both new Python migration wrappers were format/lint checked before application. Existing frozen bytes and their narrow historical exceptions remain unchanged. Source-identity fixture setup creates new factual revisions; it does not rewrite existing applied/history records.

0017 adds fixed relational first-use guards and a stable rejection code. They derive use from actual evaluation/occurrence/manifest references, not from a configurable switch or client flag. Its wrapper was format/lint checked before application. The two new fixture tests force early constraints to exercise the defect; no security or assertion rule was weakened.

Gate decision: STOP
