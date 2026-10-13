# Phase 03 independent review

Date: 2026-10-13. Reviewer: Copernicus, agent `01a13300-1440-7733-87f9-04521f464566`. Exactly one independent reviewer was dispatched after the main checkpoint at 0010 and reused for every repair follow-up. No second reviewer or delegated reviewer was used.

Final reviewed head: `0017_used_definition_seals`. The reviewer closed R1–R7 and the additional construction-time P1 with PASS and identified no remaining material finding. It inspected source and saved evidence only; it ran no tests, performed no database/file mutation and invoked no other agent. The final response is recorded in [independent-review-0017.json](evidence-03/independent-review-0017.json).

| Finding | Verified repair and final disposition |
| --- | --- |
| R1 / P1, intermediate rounding | RESOLVED. 0011 multiplies by exact 0.25 and rejects upgrades that would change a legacy result. Boundary arithmetic and legacy refusal preservation pass. |
| R2 / P1, early/drainable authorization | RESOLVED within the stated adapter boundary. 0013/0014/0016 retain read/mutation/replay obligations until final validation after locks and a fresh clock sample. Early checks, scope/purpose/public/session expiry, blocked-lock timing and erasure cases pass. |
| R3 / P1, nullable public pins | RESOLVED. 0011 uses null-safe required publication/snapshot/consent comparisons. |
| R4 / P1, incomplete canonical source identity | RESOLVED. 0015/0017 bind actual source/evidence content, require a source profile, reject the legacy claim and seal definitions on first use. |
| R5 / P2, nullable revision guards | RESOLVED. NULL stage/review revisions are rejected. |
| R6 / P2, mismatched occurrence | RESOLVED. Job, facts, source definition and associated document are checked; occurrence use seals profile children. |
| R7 / P2, advisory child growth | RESOLVED. Committed child sets are sealed and question edits append the next version. |
| Additional P1, construction after early validation | RESOLVED. 0017 immediate guards refuse profile source/evidence growth after evaluation/occurrence/manifest use and rubric growth after evaluation use. Both original reproductions now pass. |

The reviewer verified 75 packet hashes and 44 frozen migration hashes without mismatches. Current evidence records all nine commands exiting 0, 94 PostgreSQL tests, 59 Python tests, actual API/worker lifecycle and 36 strict-mypy files. [review-start-0017.json](evidence-03/review-start-0017.json) identifies the reviewed source/evidence; final status-only edits are main handoff bookkeeping, not unreviewed implementation changes.

An interim 0016 approval was withdrawn after the main agent reproduced the construction-time defect; the reviewer confirmed it and required the 0017 follow-up. The only final review approval is for 0017. Earlier dated assessments remain under [history-before-final-0017](evidence-03/history-before-final-0017/PHASE_03_REVIEW.md) and the earlier review snapshots. The initial usage-limit interruption did not cause a reviewer replacement.

Authorization is verified at the finalization point immediately before trusted adapter commit. This excludes raw-service bypass, deliberately hostile Python inspection of private attributes and subsequent WAL/network clock passage. Migration preservation proves the recorded populated fixtures and explicit invalid-legacy rejection, not production recovery. Future business APIs, identity/bootstrap, physical files, parser/scorer/model execution, UI, HTTPS and release remain UNVERIFIED under their owners.

Gate decision: PASS
