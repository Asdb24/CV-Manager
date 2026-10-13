---
title: Quality, security and qualification acceptance
version: 1.0
date_created: 2026-10-12
owner: Project quality authority; implementation owners listed per requirement
tags: [quality, security, privacy, configuration]
---

# Quality acceptance

This is an acceptance plan, not runtime evidence. Every requirement below starts runtime UNVERIFIED. Definitions and G/W/T acceptance follow [the product specification](PRODUCT_SPEC.md). [Release](RELEASE_CONTRACT.md) and [AI](LOCAL_AI_CONTRACT.md) add required artifact and inference gates. Phase 01 cannot claim security, performance, UI or offline execution from these documents.

## 1. Identity and restricted authority

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| SEC-001 | 04 | Staff authenticates in the chosen realm; server/local API validates current membership/role before establishing tenant context. | Caller tenant/header/local OS identity cannot select arbitrary agency or skip staff authentication. | G anonymous/revoked/foreign identity; W staff read/write attempted; T access denied before current tenant context exists. |
| SEC-002 | 04 | Every staff read/write/list/count/file/task/export checks current record, membership, role, purpose and consent; final mutation rechecks current authority. | Authority revoked while task/dialog is open prevents read/final commit and protected data revival. | G granted then revoked access; W preview/finalize/retry; T no protected response or commit after revocation. |
| SEC-003 | 04 | Anonymous APIs use restricted server-resolved publication/submission authority independent of staff context. | Header/job/agency tampering cannot expose staff route or private record authority. | G public request with foreign tenant header/private ID; W list/detail/intake; T only valid approved publication projection or safe rejection. |
| SEC-004 | 04 | Admin/recruiter/operator permissions follow the product matrix; local bootstrap creates local identity only and central bootstrap is operator-only. | Recruiter policy/erasure/reopening and native server-admin creation are rejected. | G each actor and operation; W permission matrix exercised; T only listed current grants succeed and audit records author. |
| SEC-005 | 13 | Test owner exercises second synthetic agency across records, lists/counts, files, tasks, evaluation/cache, advice, exports and intake links. | Guessed identifiers or equal file bytes must not reveal existence or reusable private derivations. | G two synthetic tenants; W cross-tenant probes on actual API/DB/files; T denial and no private payload/count/hash/cache signal. |
| SEC-006 | 17 | Approved server/public deployment verifies HTTPS, approved origins/CORS, safe HTML rendering, private/no-store cache rules and applicable CSRF controls. | Untrusted origin/HTML/script or unauthorized browser credentials cannot retrieve/commit private data. | G actual staging; W origin, forged request, cached/private-route and HTML probes; T explicit applicable controls pass with evidence and justified nonapplicable cases. |
| SEC-007 | 08 | Public intake bounds abuse with central quotas, request/file/task limits and idempotency; guarded acceptance never enumerates candidates. | Exhaustion/repeated/hostile uploads yield safe limit/errors and no private disclosure or unbounded resource use. | G synthetic excessive and duplicate intake; W limit/race tests; T configured limits hold, guarded duplicates resolve safely and worker/storage recover. |
| SEC-008 | 18 | Security qualification describes actual app/file/device protections and limits; stable errors/logs omit secrets, SQL and CV text. | No whole-disk encryption, administrator-proof protection, certification or absolute confidentiality claim without implemented evidence. | G deliberately failing requests/tasks; W inspect UI/logs/reports and threat boundary; T safe codes/metadata only and documented OS-admin/copy limit. |

App-level access controls do not protect against a local OS administrator or a physical copy of the workspace. Connected CVs and approved snapshots may pass through this application's server; staff must see this accurate disclosure. External AI providers remain prohibited. Server operator status does not grant unrestricted recruitment access.

## 2. Persistence, revisions and privacy

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| DAT-001 | 03 | Database persists tenant-consistent relational references and immutable versions/history with new forward Alembic migrations. | No applied migration edits/startup create_all; foreign parent links and history mutation fail. | G existing schema/history; W forward upgrade and invalid link/mutation attempted; T migration lineage intact and constraints preserve scoped immutable records. |
| DAT-002 | 03 | Related writes, optimistic revision guards, idempotency result and audit commit in one DB transaction; idempotency is scoped by realm/authority/purpose/operation and payload. | Conflict/replay with different payload or failed check rolls back all related writes; idempotency never bypasses current authorization. | G concurrent/stale/repeated authorized operations; W race/failure injected; T one complete result or no mutation, with no duplicate audit/entity. |
| DAT-003 | 08 | External PDF/export storage uses durable intents, protected staging, finalization state and restart recovery separate from SQL atomicity. | Crash before/after DB/file step leaves no falsely complete record or unowned final file. | G actual file store; W crash at intent/write/commit/finalize boundaries; T recovery completes or safely removes pending files and reports status. |
| DAT-004 | 07 | Operational removal/restore preserves scoped history and prevents unsupported parent restoration/link leakage. | Removed records cannot silently act as current; restore cannot reverse privacy erasure. | G removed/erased candidates and linked records; W read/link/restore; T permitted history/restore respects policy and erased payload cannot return. |
| DAT-005 | 03 | Versioned source, permitted purpose, consent, retention/erasure and resource-policy records have attributed owners and immutable activated revisions. | Missing/expired/unapproved applicable policy blocks personal-data intake/processing; synthetic-only authority cannot onboard real persons. | G missing or synthetic-only policy; W real onboarding attempted; T blocked with safe explanation and no personal durable payload. |
| DAT-006 | 18 | Authorized admin erasure verifies removal of personal CV/contact/facts/evidence/scores/advice/embeddings/hashes/caches/temp/exports and privacy-epoch invalidation. | No hidden reusable personal derivation; failed purge remains incomplete and cannot claim verified erasure. | G synthetic person's complete footprint; W erase and equality probes; T verified inventory/purge receipt has no recoverable personal payload and later reupload cannot revive history. |
| DAT-007 | 16 | Backup/restore/upgrade incorporates erasure journal/policy so retained backup copies cannot silently restore erased personal data; physical residual limits are disclosed. | Restore with missing erasure authority stops before personal-data availability. | G backup predates erasure; W restore/upgrade; T journal reconciliation reapplies erasure before serving data or explicitly stops. |
| DAT-008 | 09 | Extraction/evidence/facts distinguish missing, malformed, conflicting and unconfirmed content with versioned locators and review provenance. | No guessed parsing success/skill verification or silent overwrite of correction. | G uncertain/contradictory PDF evidence; W extract/review; T Unknown/review-needed with source spans and new revision on confirmation. |

Policy owners are roles, not invented named personnel. Workspace admin owns local activation; agency admin owns connected recruitment-purpose/source/consent activation; central operator owns deployment/resource configuration within agency privacy authority. Phase 02 defines validated schemas, Phase 03 persists versions, Phase 04 enforces activation/authorization, Phase 08 applies intake/file expiry, Phase 18 qualifies privacy. Real source/legal basis/retention approval is absent at baseline.

Synthetic coursework policy must be explicit, isolated and reject real onboarding. It may contain only generated fake identities/documents labeled synthetic. Phase 02 defines bounded, versioned test resource values; Phase 03 defines the policy records. No production retention period is agreed. Retention/expiry must specify clock authority, scope, time unit, task/revocation cleanup, backups/exports and recovery; missing mandatory values fail validation. Erasure is a distinct authorized workflow and must account for offline backups and physical-storage limitations without overstating sanitization.

## 3. Configuration and hardcode ownership

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| CFG-001 | 02 | Central validated settings own operational origins/URLs, paths, credentials/identity references, limits, timeouts and page sizes; native context/authorized records supply scoped dynamic values. | Missing/invalid required values fail clearly; no sample account, silent localhost/dev service or embedded workstation path. | G missing/invalid settings and two valid environments; W start/use operations; T rejection or validated owner resolution without business/UI literals. |
| CFG-002 | 02 | Profile schema explicitly includes development/test/standalone/server/connected and rejects incompatible component/profile combinations. | Unknown/mixed profile cannot start with partial authority. | G full component/profile matrix; W validate all entries; T allowed combinations documented and every forbidden combination fails. |
| CFG-003 | 02 | Desktop execution mode standalone/connected is separate from installed/portable packaging selection; realm/context is explicit and caches/sessions/data isolated. | No automatic sync, cross-realm credential/cache sharing, outage fallback or silent mode switch. | G connected outage and mode switch; W native context validates; T connected blocks, standalone remains independently available and stale realm replies are discarded. |
| CFG-004 | 02 | Local AI resources/server origins/secrets have validated central owners; bounds cover bytes/pages/text/tokens/queue/threads/batch/time/memory/storage/cleanup. | Invalid bounds/model/reference cannot disable required inference or bypass policy. | G invalid or absent bound and valid AI budget; W validate; T explicit configuration error or bounded owned execution contract. |
| CFG-005 | 18 | Each phase scans affected active call paths, manually classifies hits and records owner/disposition/repair/current evidence. | Regex-only assertion or silently exempted active broken feature cannot establish clean configuration. | G affected source and scan candidates; W trace callers/settings; T every relevant hit is classified with repair/test or justified invariant/fixture status. |
| CFG-006 | 02 | Toolchain owner inventories available tools before supported official installation, pins compatibility/licenses and reports reboot needs without rebooting. | Unsupported/incompatible/unlicensed/unverified tool cannot be presented as qualified. | G host inventory; W dependency decisions recorded; T only needed tools added and actual pinned compatibility evidence plus reboot report exist. |

### Component/profile contract baseline

Phase 02 turns this matrix into executable validation and defines component-specific schemas. Development/test may configure synthetic local or central flows explicitly and label their realm; they do not grant release fallback.

| Component | Allowed profiles | Required authority/context |
| --- | --- | --- |
| Desktop UI/native host | development, test, standalone, connected | Explicit execution mode + separate packaging manifest; native-owned local services or approved configured HTTPS realm |
| Local API/DB/document worker | development, test, standalone | Private workspace identity/storage/service manifest, loopback only |
| Central API/DB/document worker | development, test, server | Operator-owned origins/secrets/durable storage; server staff and public publication authority |
| Public Next.js web | development, test, server | Restricted configured public API origin/schema; never standalone/connected staff context |
| Employee Windows AI process | development, test, standalone, connected | Local model/resource manifest and approved scoped input; never central server/browser inference |

A server-profile component cannot accept native-local bootstrap authority. A connected desktop cannot own central database canonical data. Required operational settings have no implicit sample defaults. Fixed rating/state/rounding rules, sourced model dimensions/token ceiling, required qualification viewports, immutable migrations and isolated golden fixtures are explicit definitions, not configurable authority-disabling switches.

## 4. Visible UX, tasks and observability

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| UX-001 | 05 | UI owner uses fully read design-taste-frontend and shared tokens for restrained professional Vietnamese typography/tables/forms, keyboard navigation and visible focus. | Missing mandatory skill stops visible UI work after independent non-UI scope; no unread skill claim. | G actual implemented screens; W keyboard/form/table inspection; T readable labels/errors, usable focus and shared token evidence. |
| UX-002 | 05 | Owner inspects actual Windows content at 1280×800 and 1024×768 with display scale recorded; public site at 390×844 and 360×800. | Screenshot/mockup alone cannot prove actual viewport/scale; clipping or inaccessible actions require repair. | G measured Windows/mobile browser environments; W each required screen/state inspected; T screenshots plus scale/viewport/action results saved. |
| UX-003 | 11 | Staff UI handles loading, empty, backend-confirmed success, error, expiry/revocation, revision conflict and connection loss; repeated submit blocked. | Stale replies cannot overwrite a new selection or revive a protected view after logout/mode switch/revocation. | G two selections and pending mutation; W reverse replies/logout/conflict; T current protected state only and one confirmed operation. |
| UX-004 | 08 | Public form/inbox handles loading/empty/error/expiry/duplicate/connection loss and truthful receipt/task status accessibly. | Optimistic upload/scheduled task cannot show final success; uncertain connection offers safe same-key retry. | G delayed/failing intake; W submit/retry/expiry; T one durable acceptance or explicit safe failure/pending status. |
| UX-005 | 10 | Long extraction/AI/report tasks are bounded with actual progress/cancellation/status; errors expose safe actionable codes. | Timeout/cancel does not fabricate completed output; worker termination/revocation cleans owned inputs. | G long/failing/cancelled actual task; W observe/cancel; T truthful state and bounded cleanup without secrets/CV text in logs. |

Design acceptance in Phase 05 covers its current implemented components and states. Domain-specific runtime UI is qualified in Phases 08/11 and E2E 13; artifact behavior in 17. No present Phase 01 design or viewport claim is made.

## 5. Reports, measurements and gate evidence

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| REP-001 | 12 | Staff reads basic counts by permitted company/position/stage and complete/incomplete evaluations under current agency/purpose, with defined snapshot/filter semantics. | No synthetic/runtime mixed or private foreign/removed/erased counts; denominator/missing data explicit. | G synthetic known application set; W filter statistics; T counts match authorized DB snapshot and sum by application stage. |
| REP-002 | 12 | Staff exports CSV/PDF of permitted selected records/evaluation evidence with Vietnamese text, version/filter/snapshot provenance and protected durable export. | CSV formula injection, revoked authority or file finalization failure yields safe failure without leaked artifact. | G malicious contact prefix, Vietnamese labels and current scope; W export/read CSV/PDF; T safe cells/readable PDF match authorized persisted output. |
| REP-003 | 12 | Import/batch owner uses labeled generated synthetic corpus, validates records/policies and records per-item success/failure with bounded progress and no invented outputs. | Personal dataset or failed item is not silently accepted/skipped. | G valid/invalid synthetic items; W import/retry; T statuses and guarded counts agree with actual committed records. |
| QAL-001 | 13 | Current development E2E covers core staff flow, public browse/intake/review, independent realms and genuine Windows-local AI in both modes. | Mocks cannot prove actual DB/API/files/native/AI behavior; required failure stays STOP for its owner. | G current source/tool versions; W required positive/negative flows run; T source-linked logs/artifacts and environment evidence cover all affected paths. |
| QAL-002 | 18 | Every mandatory requirement is mapped to source, actual test/inspection, commands/results, artifact/environment version and data/security limits; future-owned runtime remains UNVERIFIED. | Unmapped acceptance, skipped required failure or summary-only evidence cannot PASS. | G final ledger; W source/results reconciled; T each acceptance has current evidence or a blocking gap at its due owner. |
| QAL-003 | 18 | Quality owner preserves typing/lint/security/assertions and reruns affected checks when source/environment changes invalidate evidence. | Weakening checks or calling an active failure deferred is prohibited. | G affected failure/change; W repair/recheck; T required assertions retained and current evidence replaces only invalidated checks. |
| QAL-004 | 01 | Phase 01 reviewer checks requirement completeness, owners, links, scoring/mode/release coherence and prose without claiming runtime or independent review. | Incomplete owned condition requires repair and STOP if unresolved. | G completed documents; W main-agent structured self-review and machine document checks; T all owned checklist items pass with saved current evidence. |

## 6. Required future test matrix

These are required planned scenarios. They are not tests run in Phase 01. Owners save exact commands, environment/artifact hashes and results in their phase evidence, tied to each stable ID. Testing framework/library choice belongs to Phase 02; no copied framework or arbitrary coverage target is prescribed.

| Scenario group | Requirements covered | Primary owner and supporting checkpoint | Actual evidence required |
| --- | --- | --- | --- |
| DOC | GOV-001–003, QAL-004; every requirement's definition | 01 | All authority files read, complete ID/owner/GWT scan, resolved links, requirement trace, source hashes and same-agent contract/prose review |
| AUTH | SEC-001–004, DAT-005 | 04; 13, 18 requalify affected paths | Actual current identity/membership/revocation/role/public-boundary and final-commit race results |
| DB | DAT-001–002, domain version relationships | 03; 06–12, 16 | Actual PostgreSQL migration lineage, constraints/transaction rollback/conflict/idempotency results |
| FILE | DOM-004, DAT-003–004, PUB-003–007, SEC-007, UX-004 | 07/08; 13, 18 | Protected local and central storage; actual crash recovery, quotas, receipt and explicit linking evidence |
| FACT | DOM-005, SCR-007, DAT-008, AI approved-input requirements | 09; 10/11 | Real text-PDF extraction/review revisions/evidence locators and safe uncertain/unsupported cases |
| SCORE | SCR-001–008, DOM-006, STG-003 | 06/10; 11/13, 18 | Exact golden/Unknown/half-up/mandatory/date/identity cases; actual DB persistence/restart/reupload/private reuse tests |
| STAGE | STG-001–003, DOM-003 | 07/11; 13 | Exhaustive allowed/forbidden role/reason/revision transitions; no score or advice event changes stage |
| WEB | PUB-001–008, SEC-003/006/007, UX-004 | 06/08; 13 then approved staging 17 | Actual generated public bundle, publication races, browse/search/detail/intake/review and deployed boundary checks |
| CONFIG | CFG-001–006, realm isolation and no fallback | 02; each changed phase then 14/15/18 | Validated component/profile settings, native context and active-call-path classification, missing/invalid negative cases |
| UI | UX-001–005 | 05/08/10/11; 13/17 | Actual required Windows/mobile viewport/scale/keyboard/state/async inspections |
| AI | All AI requirements | 02/09/10; 14/15/17/18 | Actual pinned CPU inference offline on employee Windows in both modes; provenance, memory, quality, cleanup and attachment checks |
| REPORT | REP-001–003 | 12; 13/18 | Actual filtered counts, safe CSV, rendered inspected PDF, guarded synthetic import and per-item batch results |
| RELEASE | All REL requirements, DAT-007 | 14–17; 18 | Built hash-identified artifacts, private process/manifest ownership, backup/upgrade and clean Windows offline/approved HTTPS runs |
| PRIVACY | DAT-005–007, SCR-008, SEC-008, AI storage/revocation | 18; implementation 03/04/08/10/16 | Actual synthetic erasure-footprint search, equality probes, restore reconciliation, secret/log and security limits |

Phase 18 must measure the 100-synthetic-CV offline batch including per-CV status, elapsed time, actual Windows process peak memory, failures, evidence suggestion relevance, false alerts and interview-question quality. The 1.5 GiB AI working-set ceiling is agreed; other numeric performance/quality thresholds are not yet approved and must be versioned by the named owners before qualification. No speed/accuracy promise is accepted from model marketing, fixture output or artifact size. See [local AI](LOCAL_AI_CONTRACT.md) for the exact measurement schema and safety floors.

## Phase 05 amendment (2026-10-14)

The separately supplied Phase 05 prompt and user roadmap choice supersede remaining 18-phase numbers. Original definitions/IDs/dated evidence above remain intact. Current owner mappings are in [ACCEPTANCE_LEDGER](ACCEPTANCE_LEDGER.md) and exact order in [PHASE_ROADMAP](../architecture/PHASE_ROADMAP.md). Release payload recipes are Phase 34, GitHub-hosted Windows x64 builds Phase 40, clean offline qualification Phase 41, approved HTTPS Phase 42, and final measurements/handoff Phases 43–45. Packaging is per-user NSIS with retained LocalAppData data and single-EXE portable with a writable local NTFS sibling workspace. No local/self-hosted recipient-PC release packaging, automatic public Release or deployment is authorized. Runtime behavior remains UNVERIFIED at its new owner.
