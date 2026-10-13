# Phase 03 verification

Repair update at head `0016_read_finalization` (2026-10-13): all seven reported defects now have an implementation repair, subject to the current full checkpoint and the same independent reviewer's follow-up. Forward 0015 introduces sealed profile-source relations and calculation format v2. Canonical identity binds actual immutable document content, parser/normalization definitions, extraction state, semantic span text/locations and reviewed fact-evidence mappings. New evaluation claims require a source profile; the v1 claim entry point rejects new work. Historical rows are preserved with unknown legacy source attribution rather than guessed backfills.

Forward 0016 records successful private RLS reads as transaction scope/purpose obligations. The final validator therefore rechecks private reads as well as mutations. The selected purpose for a tenant-wide read is deterministic among currently authorized grants. All results remain provisional until the trusted adapter context exits successfully. The authorization boundary remains the finalization point immediately before commit, not a guarantee about clock progression during WAL/network completion.

Targeted actual PostgreSQL checks passed: 26 calculation/advisory/prior-repair cases, nine source identity cases, and two new read-finalization expiry cases. The full current checkpoint is running; no current whole-phase PASS or independent closure is claimed. No Phase 04 work is authorized.

Date: 2026-10-13. IN PROGRESS; no current Phase 03 PASS. Predecessor integrity is recorded in evidence-03/predecessor-and-start.json. Required evidence follows the complete PHASE_03_POSTGRESQL_SCHEMA_AND_MIGRATIONS.md prompt and Phase 01 stable IDs DAT-001, DAT-002, DAT-005 and AI-007, with supporting public/security/domain conditions.

Current repair checkpoint (2026-10-13): head `0014_policy_parameters`, fourteen frozen forward revisions. The restricted adapter now owns commit/autocommit and returns materialized query results without a raw connection/cursor. Forward 0013 records private transaction-local scope/purpose/public/erasure obligations; 0014 fixes a parameter/column ambiguity found by real tests. Early constraint or explicit authorization checks do not consume obligations. Finalization locks every recorded authority before sampling the database clock, then the adapter commits without further caller work.

The current canonical database command passed **80 PostgreSQL tests**, regenerated scoped query plans and exported the 0014 catalog. Empty up/down/up, populated forward preservation, populated downgrade refusal and the legacy precision rejection check passed. Formatting, lint and strict typing (**35 files**) passed after affected edits. The last full nine-command checkpoint is still the dated 0012 run (65 DB / 59 Python); it is not a current-source whole-phase checkpoint.

R2's mutation-finalization repair is implemented and passes the new adversarial cases; full read-path coverage and the same reviewer's follow-up remain to be audited before closure. R4's extraction/semantic-evidence calculation identity remains open. Phase 03 stays STOP; Phase 04 is not authorized.

The historical assessment below is retained; it does not override the open findings or current-source limits above.

The main agent completed the initial implementation/checkpoint. Exactly one independent read-only reviewer, Copernicus (`01a13300-1440-7733-87f9-04521f464566`), returned findings after resuming from a usage-limit interruption. The same reviewer owns follow-up. Self-review cannot replace that review.

Business endpoints/authentication orchestration, physical document recovery, real model execution, public website functionality and release/HTTPS qualification remain UNVERIFIED under their later owners.

## Main evidence so far

| Requirement / boundary | Source and real evidence | Current result |
| --- | --- | --- |
| DAT-001, scoped references/history | Ten frozen revisions and tests/database; actual PostgreSQL 18.6 | Main owned persistence checks pass; independent review pending. |
| DAT-002, atomic commands/claims | Restricted runtime connections, rollback/idempotency/stage and concurrent extraction/evaluation/intake cases | Negative payload/revision and expiry-at-commit rollback cases pass; review pending. |
| DAT-005, policy/consent/privacy | Immutable policy owners and scope references; revocation visibility and authorized database erase tests | Missing/wrong-kind/synthetic-only and revoked/expired policy cases pass; no real onboarding approval. |
| AI-007 persistence | Normalized manifest/task/run/evidence/finding/question/edit/review references; real history/isolation/erasure tests | Covered cases pass; actual model and device/attachment runtime remain UNVERIFIED owners 10/15. |
| Canonical identity/math binding | Actual derived snapshot/hash, numeric normalization, rubric/engine/JD pins, concurrent evaluation claims, exact 12.5→13 / 75 / Unknown cases | Persistence cases pass; actual scorer and product restart/reupload qualification remain 10. |
| Public projection/intake | No direct candidate/count access; publication/snapshot binding, concurrency, pending identity, explicit review and expiry-before-commit rollback | Covered cases pass; website/HTTP/files remain 06/08. |
| Migration lifecycle | Canonical migration:check with explicit database config; evidence-03/migration-lifecycle.json | Head 0010 empty up/down/up, forward preservation and populated downgrade denial pass. Every pre-existing table is compared; row counts identify the populated identity/policy/domain fixture coverage. |
| Query planning | database_query_evidence.py; evidence-03/query-plans.json | Restricted-role ANALYZE/BUFFERS for three scoped queries on configured synthetic volumes; no production speed claim. |
| Schema documentation | database_catalog.py, actual schema catalog, generated dictionary and DATABASE_DESIGN.md | Export complete; final document audit/reviewer pending. |

Database pytest: **53 passed**. Existing Python pytest: **59 passed**. Mypy: **32 source files passed**. Targeted advisory checks were repeated after adding canonical erasure coverage. Initial math tests correctly rejected mandatory fail/Unknown for criteria without mandatory definitions; fixtures now create a new rubric with explicit synthetic mandatory rules. Constraints were preserved.

An empty downgrade exposed missing schema creation permission when restoring guard-owned functions. The migration environment now grants it only inside the empty downgrade transaction and revokes it afterward; populated downgrade still fails first. Applied revision bytes were preserved. The subsequent current lifecycle passed.

The latest Phase 03 checkpoint at head 0010 completed all **nine commands** successfully: formatting, lint, strict typing, existing tests/real API-worker lifecycle, generated clients, database tests/catalog/query plans, migration lifecycle, Compose configuration and desktop/web builds. Commands and timestamps are in evidence-03/commands.json; each command has its own log. It writes evidence-03 and preserves the historical evidence-02 directory. No model download, package installation or visible UI implementation was added by this checkpoint.

The main owned acceptance ledger is in PHASE_03_ACCEPTANCE_LEDGER.md. Current extraction/policy/authority cases and broader populated preservation pass. The single independent review is the remaining gate step; confirmed findings require repair and affected re-verification before PASS.

Gate decision: STOP
