# Phase 03 independent review

Reviewer: Copernicus, agent `01a13300-1440-7733-87f9-04521f464566`. Exactly one reviewer was dispatched after main implementation and the complete nine-command checkpoint at head `0010_final_command_authority`. It is read-only, cannot delegate and cannot mutate files or database. Follow-up must reuse this ID.

The packet includes the full Phase 03 prompt, acceptance ledger, schema/migrations/adapter/settings, database tests, actual catalog, query plans, migration preservation and command logs. Source/evidence hashes at dispatch are recorded in `evidence-03/review-start-0010.json`.

The initial review stopped with a tool-reported usage-limit error before a final report. The main agent verified that terminal state, recovered its read-only observations and resumed the same reviewer ID. No second reviewer was created. The resumed review is in progress; no independent approval or absence of findings is claimed.

## Confirmed observations and initial repairs

| Observation | Main validation and repair | Verification |
| --- | --- | --- |
| Division by 4 can round a long exact decimal before final half-up | Read-only PostgreSQL output showed weight 49.9999999999999999999999999999 divided by 4 becomes 12.500… while multiplication by exact 0.25 remains 12.499999999999999999999999999975. Forward 0011 changes the stored generated expression and refuses migration if existing values would change. | New real DB test preserves the exact contribution and final total 12. |
| Nullable expected revision bypasses `<>` conditions | Source validation in move_stage/review_intake confirms SQL NULL condition behavior. Forward 0011 uses IS DISTINCT FROM. | Missing-stage and missing-review revision tests reject the operation. |
| Nullable displayed public pins bypass `<>` checks | Source validation in accept_intake confirms displayed publication/snapshot/consent can make the rejection expression NULL. Forward 0011 uses IS DISTINCT FROM for all pins. | Three public-role tests reject each missing pin. |

All six targeted repair tests passed; strict typing passed for 33 source files. Full current checkpoint and reviewer follow-up are pending. Applied revisions 0001–0010 remain unchanged. The [PostgreSQL 18 ALTER TABLE contract](https://www.postgresql.org/docs/18/sql-altertable.html) documents generated-expression replacement; the explicit preservation precheck prevents silently rewriting a differing historical result.

The long-decimal test keeps its JSON numeric snapshot inside PostgreSQL to avoid Python's default JSON float decoding. Future scorer serialization must preserve exact decimal values; rounding a caller snapshot is rejected by calculation binding rather than silently accepted.

## Reviewer report and remaining repairs

The resumed reviewer returned seven findings and exact STOP. Its independent scope included schema/source and read-only PostgreSQL probes; it did not mutate data or run fixture-writing tests. It confirmed the initial query plans support their synthetic cases, not production recovery or comprehensive populated-history preservation.

| ID / severity | Finding | Current disposition |
| --- | --- | --- |
| R1 / P1 High | Division by 4 can round before final half-up. | Forward 0011 and exact-boundary test pass. A disposable legacy DB at 0010 proves upgrade rejection preserves old revision, components and total; legacy-precision.json records PASS. Reviewer follow-up pending. |
| R2 / P1 High | SET CONSTRAINTS ALL IMMEDIATE can consume deferred checks before expiry and allow a later commit. Adapter checks only staff identity. | Forward 0013/0014 and the restricted adapter implement mutation finalization. Fifteen additional real DB cases pass, including blocked-lock expiry. Full read-path audit and same-reviewer follow-up remain pending. |
| R3 / P1 High | Missing public version/consent pins can bypass SQL `<>` rejection. | Forward 0011 and three negative tests pass; reviewer follow-up pending. |
| R4 / P1 High | Canonical evaluation reuse omits document/extraction and semantic-evidence definitions required by PRODUCT_SPEC. | Confirmed. Full persisted source-definition/evidence pins and binding still required; scorer runtime remains future-owned. |
| R5 / P2 Medium | NULL expected revisions bypass stage/intake revision checks. | Forward 0011 and two negative tests pass; reviewer follow-up pending. |
| R6 / P2 Medium | Occurrence can combine evaluation job/facts with a different same-scope application/profile. | Forward 0012 enforces matching position and canonical factual content. Valid/mismatched occurrence tests added; source/evidence binding will also follow R4. |
| R7 / P2 Medium | Approved manifest and run child sets can grow after commit. | Forward 0012 seals manifest evidence and initial run output children to their construction transaction; later question edits must append the next version. Tests reject late children and version gaps; reviewer follow-up pending. |

### R2 accepted design and current implementation

Core PostgreSQL constraint triggers do not supply an un-deferrable commit-only authorization hook. The reviewer accepts a combined trusted adapter/database protocol, provided private backend/transaction obligations survive early validation and idempotent replays; the adapter owns commit/autocommit and exposes no unrestricted transaction control; final validation checks every current scope/purpose/publication/grant/erasure obligation after locking and with a fresh database clock. Erasure retains its separate administrator/policy authority after scope deletion. Tests must include early SET CONSTRAINTS, early explicit validation, multiple obligations, expiry and full rollback.

The qualified boundary must be documented as authorization at the finalization point immediately before commit, not a claim that wall-clock expiry cannot pass during WAL/network completion. Direct service-login SQL bypassing the trusted adapter does not receive that finalization guarantee. Existing RLS/constraints/guarded commands remain independent. This is an accepted repair design from the same reviewer, not closure of R2 or permission to omit the implementation.

### Current repair evidence at 0012

All nine checkpoint commands passed, with **65 database tests** and **59 Python tests**. The catalog and query plans now identify head 0012. The separate legacy precision upgrade test then passed and was added to the canonical migration command; its source passed lint/format and the expanded strict mypy set of **34 files**. The full checkpoint must run again after R2/R4 and any follow-up changes. No phase PASS is claimed from these repair checks.

### R2 repair evidence at 0014

The adapter yields a `Transaction` facade accepting one prepared SELECT and an explicit early-constraint check. No public commit, rollback, autocommit or raw connection/cursor is exposed. Results remain provisional until context exit succeeds. On successful exit, the facade closes, pending constraints run, `cv.validate_transaction()` validates, and the connection context commits with no intervening caller operation. This is a trusted application API boundary, not isolation against arbitrary Python code deliberately inspecting private attributes or using service credentials directly.

Obligations use a guard-owned, forced-RLS temporary table with backend/xid pins and ON COMMIT DROP. Registration occurs inside scope locks, command begin (including replay), public acceptance (including replay) and erasure-policy pinning before deletion. A caller-created table with the reserved name cannot impersonate guard ownership. Early validation never removes obligations. No erased scope/equality identifiers are retained in a durable obligation queue.

The validator takes all relevant locks before a single fresh clock sample. It checks staff identity/role, every recorded scope and six policies, exact purpose grants, publication/snapshot/current company-position status, grant/consent expiry/quota, and the independent erasure policy after deletion. Fifteen added cases exercise absent transaction controls, prepared multi-statement refusal, early checks followed by expiry, replay plus unrelated writes, multiple scopes, public new/replay finalization, erasure rollback, successful erasure after consent revocation, private obligation denial and a real observed lock wait crossing expiry. The complete database suite passes 80 cases. See `evidence-03/continuation-0014-finalization.json`.

A SQL parameter ambiguity in 0013 was discovered by the main real-DB tests and repaired only in forward 0014. Applied bytes remain frozen. One formatting-only exception preserves already-applied 0013 Python bytes; lint/typing/security checks still include it. Future migration authoring must run formatting before application.

R2 is not declared independently closed. Its remaining read-path coverage audit and reviewer follow-up, plus R4 implementation and the final whole-phase checkpoint, are still required.

Repair update at head `0016_read_finalization` (2026-10-13): all seven reported defects now have an implementation repair, subject to the current full checkpoint and the same independent reviewer's follow-up. Forward 0015 introduces sealed profile-source relations and calculation format v2. Canonical identity binds actual immutable document content, parser/normalization definitions, extraction state, semantic span text/locations and reviewed fact-evidence mappings. New evaluation claims require a source profile; the v1 claim entry point rejects new work. Historical rows are preserved with unknown legacy source attribution rather than guessed backfills.

Forward 0016 records successful private RLS reads as transaction scope/purpose obligations. The final validator therefore rechecks private reads as well as mutations. The selected purpose for a tenant-wide read is deterministic among currently authorized grants. All results remain provisional until the trusted adapter context exits successfully. The authorization boundary remains the finalization point immediately before commit, not a guarantee about clock progression during WAL/network completion.

Targeted actual PostgreSQL checks passed: 26 calculation/advisory/prior-repair cases, nine source identity cases, and two new read-finalization expiry cases. The full current checkpoint is running; no current whole-phase PASS or independent closure is claimed. No Phase 04 work is authorized.

R2/R4 are ready for follow-up only after the current full checkpoint succeeds. Reuse reviewer Copernicus; no new reviewer is authorized.

Gate decision: STOP
