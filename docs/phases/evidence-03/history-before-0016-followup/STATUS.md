# Current project status

Repair update at head `0016_read_finalization` (2026-10-13): all seven reported defects now have an implementation repair, subject to the current full checkpoint and the same independent reviewer's follow-up. Forward 0015 introduces sealed profile-source relations and calculation format v2. Canonical identity binds actual immutable document content, parser/normalization definitions, extraction state, semantic span text/locations and reviewed fact-evidence mappings. New evaluation claims require a source profile; the v1 claim entry point rejects new work. Historical rows are preserved with unknown legacy source attribution rather than guessed backfills.

Forward 0016 records successful private RLS reads as transaction scope/purpose obligations. The final validator therefore rechecks private reads as well as mutations. The selected purpose for a tenant-wide read is deterministic among currently authorized grants. All results remain provisional until the trusted adapter context exits successfully. The authorization boundary remains the finalization point immediately before commit, not a guarantee about clock progression during WAL/network completion.

Targeted actual PostgreSQL checks passed: 26 calculation/advisory/prior-repair cases, nine source identity cases, and two new read-finalization expiry cases. The full current checkpoint is running; no current whole-phase PASS or independent closure is claimed. No Phase 04 work is authorized.

Date: 2026-10-13 (Asia/Saigon). Current phase: 03, PostgreSQL schema and migrations, IN PROGRESS. Predecessor: exact Phase 02 `Gate decision: PASS`; all 253 recorded predecessor source/evidence hashes were checked before Phase 03 edits. The prior current-status and decisions bytes are preserved in Phase 03 evidence. Phase 01/02 dated evidence remains unchanged.

Current repair checkpoint (2026-10-13): head `0014_policy_parameters`, fourteen frozen forward revisions. The restricted adapter now owns commit/autocommit and returns materialized query results without a raw connection/cursor. Forward 0013 records private transaction-local scope/purpose/public/erasure obligations; 0014 fixes a parameter/column ambiguity found by real tests. Early constraint or explicit authorization checks do not consume obligations. Finalization locks every recorded authority before sampling the database clock, then the adapter commits without further caller work.

The current canonical database command passed **80 PostgreSQL tests**, regenerated scoped query plans and exported the 0014 catalog. Empty up/down/up, populated forward preservation, populated downgrade refusal and the legacy precision rejection check passed. Formatting, lint and strict typing (**35 files**) passed after affected edits. The last full nine-command checkpoint is still the dated 0012 run (65 DB / 59 Python); it is not a current-source whole-phase checkpoint.

R2's mutation-finalization repair is implemented and passes the new adversarial cases; full read-path coverage and the same reviewer's follow-up remain to be audited before closure. R4's extraction/semantic-evidence calculation identity remains open. Phase 03 stays STOP; Phase 04 is not authorized.

| Area | Current status | Runtime / remaining owner |
| --- | --- | --- |
| Product, quality, release, deferred, AI authorities | SPECIFICATION VERIFIED | Contract 01 |
| Monorepo/toolchain/configuration/OpenAPI/model artifact contracts | VERIFIED foundation; Phase 02 PASS | 02 |
| Minimal desktop/public shells and actual inspections | VERIFIED shell; full product UX UNVERIFIED | 02 foundation; 05 workflows/accessibility |
| PostgreSQL schema/publication/intake/advisory persistence | IMPLEMENTED, partial verification; gate STOP | 03 |
| Local/server staff identity and public authority | UNVERIFIED | 04 |
| Company/position/rubric/publication/public browsing | UNVERIFIED | 06 |
| Candidate/application/stage and intake review contracts | UNVERIFIED | 07 |
| Protected durable files/public application/connected inbox | UNVERIFIED | 08 |
| Extraction/evidence/fact review/approved AI input | UNVERIFIED | 09 |
| Exact scoring/Vietnamese explanations/product local AI | UNVERIFIED | 10 |
| Official evaluation/pipeline/advisory UI | UNVERIFIED | 11 |
| Reports/statistics/synthetic import/batch | UNVERIFIED | 12 |
| Development standalone/public/connected E2E | UNVERIFIED | 13 |
| Private runtime/model/process supervision | UNVERIFIED | 14 |
| Native dual-mode bridge/bootstrap/device sessions/inference | UNVERIFIED | 15 |
| Backup/upgrade/artifacts and server/web deployment | UNVERIFIED | 16 |
| Clean offline Windows artifacts and approved HTTPS | UNVERIFIED | 17 |
| Security/100-CV product resources/AI quality/handoff | UNVERIFIED | 18 |

Docker engine is unavailable. Actual database tests use the separately owned native PostgreSQL 18.6 synthetic cluster. The unbundled debug executable uses this workstation's developer environment and Evergreen WebView2. Model CPU compatibility on this host is separate from product advice and 100-CV memory/quality. No real onboarding/legal-retention approval, private release runtime, zero-recipient-setup artifact or approved HTTPS qualification is claimed.

Read [Phase 03 status](phases/PHASE_03_STATUS.md), [verification](phases/PHASE_03_VERIFICATION.md), [database design](database/DATABASE_DESIGN.md) and [ordered phase index](phases/PHASE_INDEX.md). Phase 04 is not authorized for execution until Phase 03 has exact PASS and its complete prompt is supplied.

Gate decision: STOP
