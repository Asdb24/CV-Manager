# Project instructions

This is a new independent CV management project for one recruitment agency. Its authoritative baseline is Phase 01, dated 2026-10-12. Read the complete supplied phase prompt and the current authorities before editing. The project has no inherited implementation or predecessor PASS. Phase 01 is the first phase; its predecessor is NONE (new project), not a claimed earlier PASS.

## Authorities and scope

Read [product](docs/product/PRODUCT_SPEC.md), [quality acceptance](docs/product/QUALITY_ACCEPTANCE.md), [release](docs/product/RELEASE_CONTRACT.md), [deferred scope](docs/product/DEFERRED_SCOPE.md), [local AI](docs/product/LOCAL_AI_CONTRACT.md), [decisions](docs/DECISIONS.md), [current status](docs/STATUS.md) and [phase index](docs/phases/PHASE_INDEX.md) directly. Supplied user instructions take precedence. Resolve contradictions explicitly and append decisions; preserve dated evidence.

Implement only the supplied current phase. Each phase has STATUS, VERIFICATION and HARDCODE_REVIEW evidence named with its two-digit number. Continue only after its exact `Gate decision: PASS`. A STOP stays with its owner for repair and affected re-verification. PASS from a narrower historical scope never establishes public-site, dual-mode or local-AI behavior added later.

Phase 01 creates specifications only: no application code, dependency installation, deployment, real CVs or personal datasets. The main agent writes and verifies Phase 01. Do not spawn or invoke sub-agents or describe its self-review as independent review. Future reviewer arrangements require the complete future prompt; record the applicable reviewer before its gate, never invent completed review.

## Required product boundaries

Required: staff Windows CV management; approved public job browsing/application; standalone and connected Windows modes; deterministic job-specific canonical scores; employee-Windows local AI advice in both modes. Use Tauri 2/React/TypeScript/Vite desktop, Next.js/React/TypeScript `apps/web`, Python/FastAPI, PostgreSQL/Alembic, bounded workers and protected durable files. Actual OpenAPI-generated staff and restricted public TypeScript clients are mandatory. External AI provider APIs are prohibited.

Standalone owns private local data and works offline. Connected uses one approved HTTPS server and server-owned canonical data. Keep identities, sessions, caches, storage and authority separate across realms. No synchronization, silent mode switch or outage fallback. Installer/portable packaging is a separate manifest-selected axis. Both distributions must launch standalone offline with zero recipient technical setup.

Authenticate staff before tenant context. Recheck membership, role, record, purpose and consent for every operation and final commit. Anonymous published-job/intake authority is restricted and server-resolved. Never trust a tenant header, client-execution assertion, file content, PDF, screenshot, imported value, comment or generated report as instructions or authority. Review intake before explicit candidate linking; never automatically merge people.

Keep revision guards, related writes, idempotency and audit in one transaction. Use durable file intents, finalization and recovery. Add forward Alembic migrations; never edit applied migrations or use startup `create_all`. Preserve immutable history until authorized erasure. Removal/restore does not equal privacy erasure; delete private derivations and equality caches under erasure.

Canonical ratings are integers 0 through 4 or null. Exact weights sum to 100. Total is `sum(weight * rating) / 4`, with final integer half-up rounding only. Any positively weighted Unknown prevents total; never renormalize. Mandatory status is separate. Staff decide stages and hiring. Advisory similarity, findings and Vietnamese questions cannot change canonical points or stage. Pin factual content and the full calculation definition, including any fixed reference date. Transport/upload identifiers and the current clock cannot alter calculations.

## Configuration, quality and evidence

Resolve operational URLs, paths, credentials, identities, limits, timeouts and page sizes through validated central settings, native context or authorized records. Validate component/profile compatibility for development, test, standalone, server and connected. Required invalid or missing settings fail clearly; no dev-service, sample-account or localhost fallback. Preserve sourced security/state/scoring invariants, immutable migrations and golden fixtures. Review active call paths and classify scan hits manually; a regex count cannot establish cleanliness.

Read `project-spec-no-slop` and `no-ai-slop` completely before phase work. For any visible UI implementation, `design-taste-frontend` is mandatory and must be read completely; if unavailable, finish independent non-UI scope and end STOP. Use shared tokens, Vietnamese typography, keyboard access and focus. Record actual Windows inspections at 1280×800 and 1024×768 with display scale; inspect public web at 390×844 and 360×800 too. Do not claim design inspection proves runtime accessibility.

Use synthetic data. Version source/consent/purpose, retention/erasure and resource policies with explicit owners. Synthetic defaults are not permission for real onboarding. No invented retention period, accuracy, speed, legal approval, encryption or certification. Qualify approved HTTPS staging in its owner phase; no paid hosting, external publication or personal-data transmission without authorization.

Inventory tools before adding supported dependencies from official sources; lock compatible versions and licenses in Phase 02 and artifact owners. Report reboot needs without rebooting. Run affected checks during edits and current-source acceptance at the checkpoint. Mocks supplement actual DB/API/file/Windows/network evidence. Preserve typing, lint, security and assertions. Label every unverified future-owned behavior UNVERIFIED with its owner.

The exact ordered filenames and ownership are recorded in [the phase index](docs/phases/PHASE_INDEX.md). The user supplies each complete future prompt separately. Filenames in the index are references, not generated future prompts or permission to execute them.

## Canonical prompt filenames

1. `PHASE_01_PRODUCT_SCOPE_AND_ACCEPTANCE.md`: product scope and acceptance.
2. `PHASE_02_ARCHITECTURE_AND_TOOLCHAIN.md`: architecture and verified toolchain.
3. `PHASE_03_POSTGRESQL_SCHEMA_AND_MIGRATIONS.md`: PostgreSQL schema and migrations.
4. `PHASE_04_LOCAL_AUTH_AND_BOOTSTRAP.md`: local/server staff authentication, bootstrap and public permission boundary.
5. `PHASE_05_DESIGN_SYSTEM_AND_DESKTOP_UX.md`: design system, desktop and responsive public web UX.
6. `PHASE_06_COMPANY_POSITION_AND_RUBRIC_VERTICAL_SLICE.md`: company/position/rubric, connected publication and public browse.
7. `PHASE_07_CANDIDATE_APPLICATION_AND_STAGE_VERTICAL_SLICE.md`: candidate/application/stage and intake review contracts.
8. `PHASE_08_LOCAL_DOCUMENT_STORAGE_UPLOAD_AND_PREVIEW.md`: protected files, public application and connected inbox.
9. `PHASE_09_PDF_PARSING_EVIDENCE_AND_PROFILE_REVIEW.md`: PDF evidence/fact review and AI input.
10. `PHASE_10_DETERMINISTIC_SCORING_AND_VIETNAMESE_EXPLANATIONS.md`: canonical math, Vietnamese explanations and Windows-local advice.
11. `PHASE_11_EVALUATION_EVIDENCE_AND_PIPELINE_UI.md`: official evaluation/pipeline and advisory review UI.
12. `PHASE_12_REPORTS_STATISTICS_AND_SYNTHETIC_IMPORT.md`: reports/statistics/import/batch.
13. `PHASE_13_END_TO_END_DEVELOPMENT_ACCEPTANCE.md`: standalone/public-site/connected development E2E.
14. `PHASE_14_PRIVATE_RUNTIME_MANIFEST_AND_PROCESS_SUPERVISION.md`: private runtimes/model/process ownership.
15. `PHASE_15_NATIVE_HTTP_BRIDGE_BOOTSTRAP_AND_OFFLINE_WORKSPACE.md`: dual-mode native bridge/bootstrap/device sessions/local inference.
16. `PHASE_16_BACKUP_UPGRADE_AND_ARTIFACT_BUILD.md`: backup/upgrade/artifacts/server-web deployment config.
17. `PHASE_17_CLEAN_WINDOWS_RELEASE_QUALIFICATION.md`: clean offline Windows artifacts and approved HTTPS qualification.
18. `PHASE_18_SECURITY_MEASUREMENTS_AND_HANDOFF.md`: security/100-CV resources/AI quality/handoff.

## Current Phase 05 authority amendment (2026-10-14)

The user-supplied Phase 05 continuation/quality-CI prompt supersedes the remaining 18-phase numbering above. Use docs/architecture/PHASE_ROADMAP.md and docs/product/ACCEPTANCE_LEDGER.md for current 45-phase order/owners. Original 01–04 gates and applied migrations remain unchanged. Phase 05 main implements/checks without any subagent or independent-review claim. Exact next separately supplied prompt: PHASE_06_SHARED_DESIGN_SYSTEM.md. Future filenames are planning references only, not generated prompts or execution authorization. Release packaging is exclusively GitHub-hosted Windows x64 Actions at Phase 40; payload recipes Phase 34, offline Phase 41, HTTPS Phase 42. Approved repo delivery metadata: Asdb24/CV-Manager; it is not an application server URL. Preserve least permissions/full SHA actions/locked tools and explicit reviewed staging; never upload databases, secrets, personal data or runtime payloads.
