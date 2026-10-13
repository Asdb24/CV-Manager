# Phase 03 status

Date: 2026-10-13. Current head: `0017_used_definition_seals`, seventeen frozen forward migrations. Predecessor: exact Phase 02 `Gate decision: PASS`; all 253 recorded source/evidence hashes were verified before Phase 03 edits. The full supplied Phase 03 prompt governs this run.

The current nine-command checkpoint passed: formatting, lint, strict typing (36 files), tests (59 Python plus actual API/worker lifecycle), generated clients, database (94 real PostgreSQL tests plus query plans/catalog), migration lifecycle, infrastructure config and desktop/web builds. Commands/timestamps/logs are in evidence-03. This is main verification, not independent approval.

The single reviewer Copernicus (`01a13300-1440-7733-87f9-04521f464566`) reported seven defects at 0010. Forward 0011–0017 now address all seven: exact decimal arithmetic, required revision/public pins, occurrence/history bindings, adapter-owned finalization with private non-consumable obligations for reads/mutations/replays, and full source/evidence calculation identity. All affected and full current checks pass. The same reviewer must verify repairs; no second reviewer exists. Gate remains STOP pending that review and final evidence audit.

Skills read and applied: project-spec-no-slop, no-ai-slop and eval, create-specification, and the complete Supabase PostgreSQL best-practices skill when it became available, with selected security/index/locking references and official PostgreSQL 18 documentation. No visible UI work was added.

The dedicated synthetic database uses installed native PostgreSQL 18.6. Docker engine is unavailable; no existing workstation database/service was changed. Authentication orchestration (04), visible workflows (05–12), physical document finalization (08), parsing (09), actual scorer/product AI (10), E2E/native/releases/HTTPS/100-CV qualification (13–18) remain UNVERIFIED under their owners. No real-data onboarding, legal approval, production recovery, encryption or certification is claimed. The next prompt after actual PASS is `PHASE_04_LOCAL_AUTH_AND_BOOTSTRAP.md`; it is not executed here.



## First-use sealing repair (0017, 2026-10-13)

Main audit reproduced a same-transaction defect after the 0016 checkpoint: consuming evaluation binding with SET CONSTRAINTS ALL IMMEDIATE allowed later profile evidence or zero-weight rubric children to change the referenced definition. Both new negative tests failed before repair; evidence is `early-definition-0016-failure.log`. The same reviewer confirmed P1, reopened R4 and made R6 closure conditional on this repair. Its interim 0016 approval was explicitly withdrawn; no phase PASS was issued by the main agent.

Forward `0017_used_definition_seals` refuses source/evidence growth once a profile is referenced by an evaluation, occurrence or advisory manifest, and refuses rubric-child growth after any evaluation uses it. Construction remains possible before use. Applied 0001–0016 bytes are unchanged. Thirty-one targeted source/calculation/advisory tests pass, including the two previously failing cases. The full current checkpoint passed all nine commands with 94 real database tests; the same reviewer's final follow-up remains pending.

Gate decision: STOP
