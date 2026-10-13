# Phase 03 status

Repair update at head `0016_read_finalization` (2026-10-13): all seven reported defects now have an implementation repair, subject to the current full checkpoint and the same independent reviewer's follow-up. Forward 0015 introduces sealed profile-source relations and calculation format v2. Canonical identity binds actual immutable document content, parser/normalization definitions, extraction state, semantic span text/locations and reviewed fact-evidence mappings. New evaluation claims require a source profile; the v1 claim entry point rejects new work. Historical rows are preserved with unknown legacy source attribution rather than guessed backfills.

Forward 0016 records successful private RLS reads as transaction scope/purpose obligations. The final validator therefore rechecks private reads as well as mutations. The selected purpose for a tenant-wide read is deterministic among currently authorized grants. All results remain provisional until the trusted adapter context exits successfully. The authorization boundary remains the finalization point immediately before commit, not a guarantee about clock progression during WAL/network completion.

Targeted actual PostgreSQL checks passed: 26 calculation/advisory/prior-repair cases, nine source identity cases, and two new read-finalization expiry cases. The full current checkpoint is running; no current whole-phase PASS or independent closure is claimed. No Phase 04 work is authorized.

Date: 2026-10-13. Predecessor: exact Phase 02 `Gate decision: PASS`, with all 253 recorded source/evidence hashes verified before changes. The complete supplied Phase 03 prompt governs this run.

The main checkpoint at 0010 passed, then the single independent reviewer Copernicus (`01a13300-1440-7733-87f9-04521f464566`) returned seven findings and STOP. Repairs are in progress at 0014. The same reviewer handles follow-up; no second reviewer exists. No Phase 04 work is authorized.

Required evidence: relational domain/policy/public/advisory schema; restricted login and forced RLS; tenant/company/person/purpose/epoch references; immutable published definitions/results; exact calculation bindings and atomic claims; transaction/revision/idempotency/audit rollback; real readiness and persistence adapter; isolated synthetic seeds; empty up/down/up and populated forward migration preservation; public allowlist/current-publication/intake/review concurrency; advisory history/erasure linkage; EXPLAIN ANALYZE BUFFERS; ERD/dictionary/constraints/privacy/index documentation; current checks, hardcode review and independent review.

PostgreSQL 18.6 tools are already installed. The dedicated project test cluster supplies real database evidence; existing PostgreSQL services are outside this phase's scope. Docker's daemon is unavailable. No new database package was needed.

Current repair checkpoint (2026-10-13): head `0014_policy_parameters`, fourteen frozen forward revisions. The restricted adapter now owns commit/autocommit and returns materialized query results without a raw connection/cursor. Forward 0013 records private transaction-local scope/purpose/public/erasure obligations; 0014 fixes a parameter/column ambiguity found by real tests. Early constraint or explicit authorization checks do not consume obligations. Finalization locks every recorded authority before sampling the database clock, then the adapter commits without further caller work.

The current canonical database command passed **80 PostgreSQL tests**, regenerated scoped query plans and exported the 0014 catalog. Empty up/down/up, populated forward preservation, populated downgrade refusal and the legacy precision rejection check passed. Formatting, lint and strict typing (**35 files**) passed after affected edits. The last full nine-command checkpoint is still the dated 0012 run (65 DB / 59 Python); it is not a current-source whole-phase checkpoint.

R2's mutation-finalization repair is implemented and passes the new adversarial cases; full read-path coverage and the same reviewer's follow-up remain to be audited before closure. R4's extraction/semantic-evidence calculation identity remains open. Phase 03 stays STOP; Phase 04 is not authorized.

Skills read: project-spec-no-slop, no-ai-slop and eval, create-specification. The requested Supabase PostgreSQL skill was absent from the initial catalog, then became available in the updated catalog. Its complete SKILL.md and relevant security, index, locking and query-measurement references have now been read and applied alongside official PostgreSQL 18 documentation. No visible UI is being implemented.

Gate decision: STOP
