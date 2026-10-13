> Current authority (2026-10-14): the supplied Phase 05 continuation prompt supersedes remaining 18-phase numbering. Use [PHASE_ROADMAP](../architecture/PHASE_ROADMAP.md) and [ACCEPTANCE_LEDGER](../product/ACCEPTANCE_LEDGER.md). The 01–04 history below is retained. Next after Phase 05 PASS: `PHASE_06_SHARED_DESIGN_SYSTEM.md`.

# Phase order

Baseline: 2026-10-12, new project with public site, dual modes and Windows-local AI included from inception. Predecessor for Phase 01: NONE (new project). All phases are sequential. The table names the exact future prompt; it does not create that prompt. User-supplied complete prompts govern future implementation and reviewer requirements.

| Phase | Exact prompt filename | Ownership, including amended scope | Checkpoint/reviewer order |
| --- | --- | --- | --- |
| 01 | `PHASE_01_PRODUCT_SCOPE_AND_ACCEPTANCE.md` | Complete product/acceptance, public site, dual modes, AI and release contracts | Main agent writes → checks → self-review → gate. No sub-agent or independent review. |
| 02 | `PHASE_02_ARCHITECTURE_AND_TOOLCHAIN.md` | Desktop/web/API/config/OpenAPI/model contracts; verified compatible toolchain/licenses | Predecessor 01 PASS → supplied prompt implementation → current checks → prompt-required review → gate. |
| 03 | `PHASE_03_POSTGRESQL_SCHEMA_AND_MIGRATIONS.md` | Persistence, publication, intake, advisory schema and forward migrations | Predecessor 02 PASS → implementation → checks → prompt-required review → gate. |
| 04 | `PHASE_04_LOCAL_AUTH_AND_BOOTSTRAP.md` | Local/server staff identity, membership, public permission boundary, bootstrap | Predecessor 03 PASS → implementation → checks → prompt-required review → gate. |
| 05 | `PHASE_05_DESIGN_SYSTEM_AND_DESKTOP_UX.md` | Shared design, Windows and responsive public web UX | Predecessor 04 PASS → implementation → inspections/checks → prompt-required review → gate. |
| 06 | `PHASE_06_COMPANY_POSITION_AND_RUBRIC_VERTICAL_SLICE.md` | Company/position/JD/rubric, connected publication, public browse/search/detail | Predecessor 05 PASS → implementation → checks → prompt-required review → gate. |
| 07 | `PHASE_07_CANDIDATE_APPLICATION_AND_STAGE_VERTICAL_SLICE.md` | Candidate/application/stage APIs, intake review contracts | Predecessor 06 PASS → implementation → checks → prompt-required review → gate. |
| 08 | `PHASE_08_LOCAL_DOCUMENT_STORAGE_UPLOAD_AND_PREVIEW.md` | Protected local/server files, public application, connected inbox | Predecessor 07 PASS → implementation → checks → prompt-required review → gate. |
| 09 | `PHASE_09_PDF_PARSING_EVIDENCE_AND_PROFILE_REVIEW.md` | Text extraction, evidence, fact revisions/review, AI input authority | Predecessor 08 PASS → implementation → checks → prompt-required review → gate. |
| 10 | `PHASE_10_DETERMINISTIC_SCORING_AND_VIETNAMESE_EXPLANATIONS.md` | Exact canonical math, genuine Windows-local AI, findings/questions | Predecessor 09 PASS → implementation → checks → prompt-required review → gate. |
| 11 | `PHASE_11_EVALUATION_EVIDENCE_AND_PIPELINE_UI.md` | Official evaluation/pipeline, evidence and advisory review UI | Predecessor 10 PASS → implementation → checks → prompt-required review → gate. |
| 12 | `PHASE_12_REPORTS_STATISTICS_AND_SYNTHETIC_IMPORT.md` | Reports/statistics, controlled synthetic import/batch | Predecessor 11 PASS → implementation → checks → prompt-required review → gate. |
| 13 | `PHASE_13_END_TO_END_DEVELOPMENT_ACCEPTANCE.md` | Actual standalone plus public-site/connected development E2E | Predecessor 12 PASS → development qualification → checks → prompt-required review → gate. |
| 14 | `PHASE_14_PRIVATE_RUNTIME_MANIFEST_AND_PROCESS_SUPERVISION.md` | Private runtimes/model manifest and Rust process ownership | Predecessor 13 PASS → implementation → checks → prompt-required review → gate. |
| 15 | `PHASE_15_NATIVE_HTTP_BRIDGE_BOOTSTRAP_AND_OFFLINE_WORKSPACE.md` | Dual-mode bridge/bootstrap/device sessions and Windows-local inference | Predecessor 14 PASS → implementation → checks → prompt-required review → gate. |
| 16 | `PHASE_16_BACKUP_UPGRADE_AND_ARTIFACT_BUILD.md` | Ordered backup/upgrade/artifacts and server/web deployment configuration | Predecessor 15 PASS → builds/checks → prompt-required review → gate. |
| 17 | `PHASE_17_CLEAN_WINDOWS_RELEASE_QUALIFICATION.md` | Clean offline Windows artifacts and approved HTTPS public/connected qualification | Predecessor 16 PASS → artifact/network qualification → prompt-required review → gate. |
| 18 | `PHASE_18_SECURITY_MEASUREMENTS_AND_HANDOFF.md` | Security, 100-CV resources and AI-quality measurements, handoff | Predecessor 17 PASS → measurements/checks → prompt-required review → gate. |

At each checkpoint record the reviewer identity/type, scope, date and result actually obtained. No completed independent review is implied by this schedule. Later runtime work cannot block an earlier complete contract gate, but remains UNVERIFIED. The next permitted prompt after Phase 01 PASS is exactly `PHASE_02_ARCHITECTURE_AND_TOOLCHAIN.md`; Phase 01 does not execute it.

## Superseded remaining order (2026-10-14)

The 18-phase table above is preserved historical planning. The user-supplied Phase 05 and explicit roadmap choice replace remaining order with [PHASE_ROADMAP](../architecture/PHASE_ROADMAP.md) and [ACCEPTANCE_LEDGER](../product/ACCEPTANCE_LEDGER.md). Completed 01–04 retain dated gates; current 05 is continuation and quality CI. Next is exactly `PHASE_06_SHARED_DESIGN_SYSTEM.md`.
