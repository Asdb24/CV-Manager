# Phase 03 verification

Date: 2026-10-13. Current head: `0017_used_definition_seals`, seventeen frozen forward migrations. Predecessor: exact Phase 02 `Gate decision: PASS`; all 253 recorded source/evidence hashes were verified before Phase 03 edits. The full supplied Phase 03 prompt governs this run.

The current nine-command checkpoint passed: formatting, lint, strict typing (36 files), tests (59 Python plus actual API/worker lifecycle), generated clients, database (94 real PostgreSQL tests plus query plans/catalog), migration lifecycle, infrastructure config and desktop/web builds. Commands/timestamps/logs are in evidence-03. The same independent reviewer has also approved this head; its scoped report is recorded in evidence-03/independent-review-0017.json.

The single reviewer Copernicus (`01a13300-1440-7733-87f9-04521f464566`) reported seven defects at 0010. Forward 0011–0017 now address all seven: exact decimal arithmetic, required revision/public pins, occurrence/history bindings, adapter-owned finalization with private non-consumable obligations for reads/mutations/replays, and full source/evidence calculation identity. All affected and full current checks pass. The same reviewer closed R1–R7 and the additional construction-time P1 at 0017 with PASS. No second reviewer was created. Final main evidence/requirement audit is complete; no mandatory Phase 03 condition remains unresolved.

| Requirement / boundary | Source and real evidence | Current result |
| --- | --- | --- |
| DAT-001, scoped references/history | Seventeen frozen revisions and tests/database; actual PostgreSQL 18.6 | Current persistence checks pass; independent repair follow-up PASS. |
| DAT-002, atomic commands/claims | Restricted runtime connections, rollback/idempotency/stage and concurrent extraction/evaluation/intake cases | Read/write/replay obligations, early-check expiry and lock-wait cases pass; independent follow-up PASS. |
| DAT-005, policy/consent/privacy | Immutable policy owners and scope references; revocation visibility and authorized database erase tests | Missing/wrong-kind/synthetic-only and revoked/expired policy cases pass; no real onboarding approval. |
| AI-007 persistence | Normalized manifest/task/run/evidence/finding/question/edit/review references; real history/isolation/erasure tests | Covered cases pass; actual model and device/attachment runtime remain UNVERIFIED owners 10/15. |
| Canonical identity/math binding | Actual derived snapshot/hash, numeric normalization, rubric/engine/JD pins, concurrent evaluation claims, exact 12.5→13 / 75 / Unknown cases | Persistence cases pass; actual scorer and product restart/reupload qualification remain 10. |
| Public projection/intake | No direct candidate/count access; publication/snapshot binding, concurrency, pending identity, explicit review and expiry-before-commit rollback | Covered cases pass; website/HTTP/files remain 06/08. |
| Migration lifecycle | Canonical migration:check with explicit database config; evidence-03/migration-lifecycle.json | Head 0017 empty up/down/up, forward preservation and populated downgrade denial pass. Every pre-existing table is compared; row counts identify the populated identity/policy/domain fixture coverage. |
| Query planning | database_query_evidence.py; evidence-03/query-plans.json | Restricted-role ANALYZE/BUFFERS for three scoped queries on configured synthetic volumes; no production speed claim. |
| Schema documentation | database_catalog.py, actual schema catalog, generated dictionary and DATABASE_DESIGN.md | Export, final document audit and independent review complete. |


## Repair-specific evidence

- `test_review_repairs.py`: exact long decimal before final half-up; NULL stage/review guards; three NULL public pins.
- `test_advisory.py`: sealed manifest/run children, contiguous question edits, valid and wrong job/facts/document occurrences, personal source/advisory/canonical erasure.
- `test_finalization.py`: 17 real cases covering a restricted adapter facade, single prepared SELECT, early checks, expiration, replay, multiple scopes, public intake/replay, erasure, private queue denial, observed blocking-lock expiry and both private read types.
- `test_source_identity.py`: eleven cases covering changed bytes/parser/normalization/reviewed evidence, equivalent reupload provenance, sealed profile child sets, retired legacy claim denial and foreign source projection isolation.
- Existing real concurrency, RLS, composite-key, policy, public and math checks remain in the 94-test suite.

Migration preservation compares every pre-existing table's business values at 0004 with head; the recorded row counts identify the populated identity/policy/company/candidate/profile/application coverage. Empty result/document tables are not evidence of populated result-history preservation. The separate legacy precision check constructs an invalid rounded evaluation at 0010 and proves upgrade refusal preserves the old head/components/total. Empty downgrade is a synthetic lifecycle test, not production recovery.

Private reads have internal temporary authorization bookkeeping. The trusted adapter owns transaction completion; SQL responses inside its context remain provisional. Authorization is checked at the finalization point immediately before commit, not continuously through WAL/network completion. Direct service-login SQL and deliberately hostile Python inspection of private attributes are outside that adapter guarantee. RLS/constraints remain independently enforced.

The earlier implementation assessments and repair progression are preserved in evidence-03/history-before-0016-followup and PHASE_03_REVIEW. Current evidence supersedes narrower historical claims. Follow-up review and final main audit are complete at 0017.

The dedicated synthetic database uses installed native PostgreSQL 18.6. Docker engine is unavailable; no existing workstation database/service was changed. Authentication orchestration (04), visible workflows (05–12), physical document finalization (08), parsing (09), actual scorer/product AI (10), E2E/native/releases/HTTPS/100-CV qualification (13–18) remain UNVERIFIED under their owners. No real-data onboarding, legal approval, production recovery, encryption or certification is claimed. The next permitted complete prompt is `PHASE_04_LOCAL_AUTH_AND_BOOTSTRAP.md`; it is not executed here.



## First-use sealing repair (0017, 2026-10-13)

Main audit reproduced a same-transaction defect after the 0016 checkpoint: consuming evaluation binding with SET CONSTRAINTS ALL IMMEDIATE allowed later profile evidence or zero-weight rubric children to change the referenced definition. Both new negative tests failed before repair; evidence is `early-definition-0016-failure.log`. The same reviewer confirmed P1, reopened R4 and made R6 closure conditional on this repair. Its interim 0016 approval was explicitly withdrawn; no phase PASS was issued by the main agent.

Forward `0017_used_definition_seals` refuses source/evidence growth once a profile is referenced by an evaluation, occurrence or advisory manifest, and refuses rubric-child growth after any evaluation uses it. Construction remains possible before use. Applied 0001–0016 bytes are unchanged. Thirty-one targeted source/calculation/advisory tests pass, including the two previously failing cases. The full current checkpoint passed all nine commands with 94 real database tests; the same reviewer has now closed all findings at this head.

Gate decision: PASS
