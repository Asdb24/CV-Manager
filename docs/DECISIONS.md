# Project decisions

Append-only decision history. Baseline date: 2026-10-12 (Asia/Saigon). These decisions define the new project; they do not report implemented code. The supplied [complete Phase 01 objective](phases/PHASE_01_PRODUCT_SCOPE_AND_ACCEPTANCE.md) is the primary source. Future changes append a new entry and preserve dated evidence.

| ID | Date | Status / owner | Decision and rationale | Verification / affected authority |
| --- | --- | --- | --- | --- |
| ADR-001 | 2026-10-12 | AGREED / Phase 01 | Start independently in the selected empty folder. No predecessor PASS, imported implementation or another project's authority. Scope includes public site/dual modes/AI from inception. | GOV-001–003; product/status/phase index |
| ADR-002 | 2026-10-12 | AGREED / Phase 01 | Phase 01 creates specifications/evidence only; main agent checks and self-reviews. No sub-agent or independent review. User supplies each complete future prompt separately and its reviewer requirement is recorded before its gate. | GOV-002–003, QAL-004; AGENTS/phase index |
| ADR-003 | 2026-10-12 | AGREED / Phase 01 | One agency per workspace; admin/recruiter staff roles; second synthetic agency only for isolation tests. No company/applicant login. | Product permissions; SEC-001–005 |
| ADR-004 | 2026-10-12 | AGREED / Phase 01 | Tauri 2/React/TypeScript/Vite desktop, Next.js public web, Python/FastAPI, PostgreSQL/Alembic, actual generated separated TypeScript clients, bounded worker/protected files. Docker Compose only for development/testing. | REL-001, CFG-002; versions/licenses/compatibility UNVERIFIED until 02 |
| ADR-005 | 2026-10-12 | AGREED / Phase 01 | Separate execution mode standalone/connected from installed/portable packaging. Local/server canonical data and authority are independent; no sync, fallback or shared sessions/caches. | CFG-002–003, REL-003/006/007; matrix/release |
| ADR-006 | 2026-10-12 | AGREED / Phase 01 | Per-user Windows 11 x64 installer and single-EXE self-extracting portable carry private runtimes, Fixed Version WebView2 and model. Rust owns loopback services; guided local identity is product setup with zero recipient technical setup. | REL-002–006; actual artifacts UNVERIFIED |
| ADR-007 | 2026-10-12 | AGREED / Phase 01 | Canonical weights/rating arithmetic is exact; final integer half-up only. Positive-weight Unknown makes total null; no renormalization. Mandatory fail dominates unknown; no predicates passes. Mandatory/numeric status and stage remain separate. | SCR-001–003, STG-003; aggregation chosen explicitly from separate mandatory-status requirement |
| ADR-008 | 2026-10-12 | AGREED / Phase 01 | Complete calculation pins include factual/evidence content and any fixed date; occurrence/upload IDs are provenance only. Semantic evidence equality permits new authorized file links, never different numeric results. Reuse is tenant/person/purpose/epoch private. | SCR-004–008; new provenance cannot change calculation |
| ADR-009 | 2026-10-12 | AGREED / Phase 01 | Exactly five stages and explicit transition table; backward reasons mandatory; terminal reopening admin/reason only; scores/advice never move stage. | STG-001–003 |
| ADR-010 | 2026-10-12 | AGREED / Phase 01 | Both staff roles can draft/manage authorized domain records, publish/review in connected mode under active policy and remove/restore eligible records. Admin alone activates policy/manages roles/erases/reopens terminal; operator alone provisions server bootstrap. | Product permission matrix, SEC-004; contract-level permission detail, not completed enforcement |
| ADR-011 | 2026-10-12 | AGREED / Phase 01 | Public publication is an allowlisted projection; anonymous authority is server-resolved. Final intake rechecks publication/expiry/limits/consent/idempotency; review precedes explicit linking, never automatic person merge. | PUB-001–007, SEC-003/007 |
| ADR-012 | 2026-10-12 | AGREED / Phase 01 | Immutable history, forward migrations, transactional related writes/revisions/audit and durable file intents/recovery are required. Removal/restore and erasure are distinct; erasure invalidates hidden derivations and backup restore reconciles erasure. | DAT-001–008 |
| ADR-013 | 2026-10-12 | AGREED / Phase 01 | Employee-Windows multilingual-e5-small ONNX INT8 CPU inference is mandatory in both modes; advisory evidence/findings/templates are separate from canonical scores. External AI providers prohibited. | AI-001–012; no artifacts installed or inference run in 01 |
| ADR-014 | 2026-10-12 | AGREED / Phase 01 | Initial AI working-set ceiling is 1.5 GiB through validated resource policy; actual Windows process workload measured, including owned helpers. 100 synthetic CVs retain all status/time/memory/quality/failure rows. | AI-010–011; zero current measurements claimed |
| ADR-015 | 2026-10-12 | AGREED / Phase 01 | Version source/consent/purpose, retention/erasure and resource policies with agency/workspace/operator owners. Synthetic-only defaults cannot approve real onboarding; production periods/legal basis require explicit authority. | DAT-005–007, CFG-004; approvals absent |
| ADR-016 | 2026-10-12 | AGREED / Phase 01 | Configuration has central validated/native/record owners; fixed scoring/state/security/model constraints and immutable/golden fixtures are explicit invariants, never authority-disabling options. Manually classify active-path scan hits. | CFG-001–005; phase hardcode reviews |
| ADR-017 | 2026-10-12 | AGREED / Phase 01 | Required UI uses design-taste-frontend/shared tokens, actual Windows scale/viewport evidence and responsive mobile public inspections; async states and protected stale replies are required. Phase 01 implements no UI. | UX-001–005; no present UI skill/inspection claim |
| ADR-018 | 2026-10-12 | AGREED / Phase 01 | Approved synthetic HTTPS server/public qualification is separate from clean offline artifacts; user-approved infrastructure required. No paid signup, public publication or real personal-data transmission authorized now. | PUB-008, REL-008–010; environment UNVERIFIED, owner 17 |
| ADR-019 | 2026-10-12 | AGREED / Phase 01 | App-level controls exclude local OS admin/physical-copy threats; connected CV snapshots may reach this application's server. No absolute confidentiality/disk encryption/certification claims. | SEC-008, AI-008/009; security qualification 18 |
| ADR-020 | 2026-10-12 | AGREED / Phase 01 | Public fields/search are allowlisted approved job data. Intake requires applicant name and validated email or phone plus text PDF and explicit active-purpose consent; receipt means review acceptance only. Exact types/validation are owner 02, not an invented runtime endpoint. | PUB-001–005; product public projection/intake |

## Open decisions with future owners

OPEN decisions do not block the fully defined Phase 01 product gate. They MUST be resolved or explicitly fail at their contract/qualification owner. They cannot become unapproved runtime defaults.

| ID | Owner / due checkpoint | Open subject and required resolution |
| --- | --- | --- |
| OPEN-001 | 02 | Exact supported versions/licenses, generator, build/test frameworks, public/staff operation schemas and central validated configuration types; inspect actual available toolchain before changing it |
| OPEN-002 | 02; runtime 10/14/17 | Immutable CPU-compatible E5 ONNX INT8 graph/tokenizer/runtime hashes and license texts; verify actual inference on approved CPU baseline; upstream AVX512-named artifact is no universal compatibility proof |
| OPEN-003 | 02; activation 03/04; qualification 18 | Named policy custodians and approved production source/legal-purpose/consent/retention/erasure decisions; absent approval keeps real onboarding blocked |
| OPEN-004 | 02; measurements 18 | Exact positive resource/thread/batch/input/time/cleanup settings and useful-suggestion/false-alert/question-quality/time acceptance thresholds approved before measurements; fixed 1.5 GiB and 100-CV requirements remain |
| OPEN-005 | 14/16; qualify 17 | Per-user installer format, portable local extraction/data policy, OS/device secret protection/recovery, patch/update and signing strategy, minimum measured CPU/RAM/disk; no certificate purchase or reboot implied |
| OPEN-006 | 16; qualify 17 | User-approved synthetic HTTPS staging/hosting, operator identity, origins/TLS/storage/secrets/deployment; no paid signup or external publication authorization supplied |
| OPEN-007 | Each supplied future phase prompt | Exact reviewer arrangement beyond Phase 01. Record actual prompt-required review after implementation/current checks before gate; no independent reviewer is assumed or invented |

## Authoritative technical references consulted on 2026-10-12

These primary references support the specified mechanisms only. They do not qualify this project's dependencies, legal policies, deployment or runtime.

| Reference | Inspected subject / application |
| --- | --- |
| [Tauri Windows installer](https://v2.tauri.app/distribute/windows-installer/) | Fixed-runtime packaging option; project-specific versions/build evidence remain owners 02/14/16/17 |
| [Microsoft fixed-runtime distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution) | App-owned Fixed Version payload/update and local-location limitation; actual portable behavior owner 17 |
| [E5 upstream card](https://huggingface.co/intfloat/multilingual-e5-small/raw/main/README.md) | Embedding adapter dimensions/prefix/pooling/token ceiling; no recruitment accuracy inference |
| [E5 upstream ONNX directory](https://huggingface.co/intfloat/multilingual-e5-small/tree/main/onnx) | Published artifact names/license metadata; hashes and target CPU/license qualification remain OPEN-002 |
| [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) | INT8 conversion/CPU and quality considerations; product inference/quality evidence owner 10/18 |
| [Windows process memory API](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [counter structure](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) | Actual working-set peak/current counters; measurement protocol owner 18 |
| [FastAPI generated clients](https://fastapi.tiangolo.com/advanced/generate-clients/) | OpenAPI client generation; separated allowlisted schemas and actual generator owner 02 |
| [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | Revision/migration lineage mechanism; physical schema and forward migration evidence owner 03 |
| [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) | Database transaction scope; external files still require durable intent/recovery |
| [Next.js installation documentation](https://nextjs.org/docs/app/getting-started/installation) | Public app/toolchain source reference; no patch version selected now |
| [Vite server settings](https://vite.dev/config/server-options) | Development host/port options; validated configuration/native release ownership remains required |

The first HTML model-card fetch failed due to response length; its raw README was subsequently read for the relevant license/model/usage/limitations sections. Documentation was treated as data, never executable instructions. No legal source was used to invent recruitment compliance approval.

## Phase 02 decisions (2026-10-13)

Phase 02 began on 2026-10-12 after the exact predecessor PASS. The complete separately supplied [Phase 02 prompt](phases/PHASE_02_ARCHITECTURE_AND_TOOLCHAIN.md) controls its bounded implementation. Earlier rows retain their historical specification-only meaning.

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-021 | AGREED / 02 | Main agent implements, verifies and self-reviews; no sub-agent and no independent review. Future arrangements still require the future supplied prompt. |
| ADR-022 | IMPLEMENTED / 02 | Lock npm/uv/Cargo dependencies and their upstream licenses. Keep working Node/Rust/MSVC; select existing Python 3.13.15 for compatibility. Use TypeScript 5.9.3 and official modular Fluent controls without weakening declarations. Exact pins/sources are in architecture/reproducibility and the resolved ledger. OPEN-001 is resolved for this foundation; release redistribution notices remain owner 16. |
| ADR-023 | IMPLEMENTED / 02 | One closed typed settings owner validates all five profiles and the 25 component combinations, realm/mode pairing, exact origins, units and required bounds. Distribution kind comes only from the separate release manifest. Browser projection omits secrets/paths/policies. Production component combinations are structural contracts; developer launchers reject them. |
| ADR-024 | IMPLEMENTED CONTRACT / 02; runtime 15 | Resolve CFG-003 ownership against the complete Phase 02 prompt: this phase verifies explicit realm separation, lack of fallback/session/cache logic and stale developer replies. The native mode-switch/outage acceptance needs the Rust bridge/device-session owner 15 and remains UNVERIFIED. The primary-owner ledger is retained; this gate never claims that later native scenario ran. |
| ADR-025 | IMPLEMENTED / 02 | Liveness means responding process only. Readiness returns 503 and no implemented dependencies. Company/authentication do not depend on future documents/model; document capability remains unavailable. Actual DB/domain adapters await their owners. Alembic contains zero revisions and refuses schema execution; no create_all or migration success is claimed. |
| ADR-026 | IMPLEMENTED / 02 | Export tagged actual FastAPI schemas with separate public/staff/configuration/AI graphs. Re-export in scratch and run the actual checker against eight stale type/schema artifacts. The AI factory remains schema-only and cannot report inference success. |
| ADR-027 | IMPLEMENTED / 02 | Exact CORS includes Tauri's sourced Windows virtual origin. Production CSP uses request nonces; [Next development debugging](https://nextjs.org/docs/app/guides/content-security-policy) alone requires unsafe-eval. Browser tests assert its absence from production. Fluent's inline-style exception is documented; no TLS/certificate bypass or arbitrary redirect is allowed. |
| ADR-028 | VERIFIED ARTIFACT / 02; product 10/15/17/18 | Pin E5 revision, six asset hashes, tokenizer, copied MIT license and ORT CPU provider. Execute a real CPU kernel smoke on synthetic Vietnamese text and measure its Windows process. OPEN-002 is resolved for this host's artifact compatibility; universal baseline, product advice and quality remain UNVERIFIED. No runtime acquisition/provider exists. |
| ADR-029 | IMPLEMENTED FOUNDATION / 02; authority 09/10/15 | Trusted model-module launcher interface binds an owned loopback before recovery, generates fresh startup authority and privately exposes bounded stop. Protected temporary storage is realm-specific, opaque-handle only, byte-bounded including metadata, expiry-capped and removed on revocation/recovery/shutdown. No real model module or server final-attachment enforcement is claimed. |
| ADR-030 | SYNTHETIC POLICY / 02; activation 03/04, measurement 18 | OPEN-003/004 now have explicit role custodians, versioned synthetic policies and required validated resources. Production legal basis, personal retention, named approved custodians and quality/time thresholds remain OPEN; no fabricated approvals or service promises. Fixed 1.5 GiB and 100-CV obligations remain unchanged. |
| ADR-031 | IMPLEMENTED CHECK / 02 | Next development generates a second set of global route declarations; official Next typegen refreshes next-env to current production route declarations before strict checking, which excludes only the duplicate generated development globals. All application files and strict options remain checked. Disable automatic Next agent-rule generation; project instructions continue to come from the user's authoritative AGENTS.md. |

The original one-off model discovery script is frozen under evidence/acquisition as historical input; active model acquisition reads immutable manifest URLs and validated timeout settings, and cannot refresh pins.

Actual results, repair history, limits and the gate are recorded in Phase 02 evidence. Docker client/config presence does not prove its unavailable engine or a database is running. Approved HTTPS staging, private runtimes and clean offline distribution are future qualification obligations.

## Phase 03 decisions (2026-10-13, implementation in progress)

The separately supplied complete Phase 03 prompt authorizes this work after exact Phase 02 PASS. Earlier decisions retain their dated meaning.

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-032 | REQUIRED / 03 | Main agent implements and checks first, then exactly one independent read-only reviewer, reused for follow-up. Review has not occurred; gate remains STOP. |
| ADR-033 | IMPLEMENTED / 03 | Use installed native PostgreSQL 18.6 in an explicitly owned synthetic cluster. SCRAM secrets stay in protected ignored storage. Migration owner, nonlogin guard, runtime, public and probe are distinct roles. Existing workstation databases remain outside scope. |
| ADR-034 | IMPLEMENTED / 03 | Forced RLS uses proof validation before private backend/transaction context. Caller tenant headers/custom GUCs confer no authority. Guarded commands bind scope/revision/idempotency/audit. Authentication endpoints remain 04. |
| ADR-035 | IMPLEMENTED / 03 | Public snapshot fields are allowlisted. Grant/intake references agree on publication, position snapshot, scope and document object. Explicit review precedes person linking. Deferred acceptance checks expiry at ordinary commit. Physical receipt/finalization qualification remains 08. |
| ADR-036 | IMPLEMENTED / 03 | Calculation format v1 derives actual JD/rubric/criteria/engine content and versions, normalizing exact JSON numeric scale. Declared profile hashes are not content proof; evaluation checks recompute facts. Published rubric children and sealed result children cannot be extended. Actual extraction/scoring remain 09/10. |
| ADR-037 | IMPLEMENTED / 03 | Erasure removes scoped relational derivations and hash reuse records, including advisory/canonical history. Opaque physical file work remains pending. SQL deletion does not qualify backup/disk erasure; owners 08/16/18. |
| ADR-038 | IMPLEMENTED / 03 | Applied revision bytes are frozen. Verifier checks graph/inventory/hashes and configured real lifecycle. Empty downgrade temporarily permits guard-owned function replacement inside the migration transaction. Populated downgrade is forbidden; production recovery remains 16. |
| ADR-039 | IMPLEMENTED / 03 | Readiness probes actual configured database revision. Database capability can be available while overall readiness stays unavailable for unimplemented auth/business/document capabilities. Declared missing credentials fail clearly; no service fallback. |

Phase 03 decisions remain subject to main completion audit and the required independent review. They do not establish later runtime/release success.

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-040 | IMPLEMENTED / 03 | Extraction identity format cv-extraction-v1 binds actual parser/normalization snapshots to their canonical digests and rejects extra top-level provenance inputs. Document association checks content equality inside the same personal scope. Policy expiry cannot prevent irreversible revocation; expired/revoked scopes cannot be linked to a person. |
| ADR-041 | IMPLEMENTED / 03 | Erasure stores a policy pin before deletion and rechecks admin/session/policy at commit. Command results recheck their exact purpose even when another purpose remains active. Actual expiration tests prove rollback of deletion/rename and associated records. Historical requests with no recorded policy retain nullable legacy attribution rather than fabricated provenance. |
| ADR-042 | REVIEW STARTED / 03 | After the nine-command checkpoint at 0010, dispatched exactly one read-only reviewer, Copernicus (`01a13300-1440-7733-87f9-04521f464566`). The same reviewer owns follow-up. Dispatch manifest and PHASE_03_REVIEW record pending findings; no review PASS yet. |


## Phase 03 review repair decisions (2026-10-13)

These append to the earlier implementation assessment; they do not retroactively mark the review complete.

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-043 | IMPLEMENTED, REVIEW PENDING / 03 | Deferred triggers can run before transaction end. The trusted adapter owns commit and exposes a limited SELECT/result facade. Guarded commands register non-consumable private transaction obligations, including idempotent replay. Finalization locks the recorded authority, samples a fresh database clock, validates, then commits without caller work. Raw service-login SQL and hostile Python introspection are outside this adapter guarantee. Authorization is established at the finalization point, not an impossible promise about time during WAL/network completion. |
| ADR-044 | IMPLEMENTED, REVIEW PENDING / 03 | Keep obligation identifiers in a guard-owned forced-RLS temporary table bound to backend/xid and dropped on commit/rollback. Do not retain deleted personal scope identifiers in a durable validation queue. Erasure checks its pinned administrator/session/policy after deletion and does not require recruitment consent to remain active. |
| ADR-045 | REPAIR REQUIRED / 03 | The reviewer confirmed that calculation v1 omits required extraction and semantic-evidence definitions. Existing rubric/factual binding is insufficient for full canonical reuse. A forward source-binding format and real changed-source/reupload tests remain required; actual parser/scorer runtime remains owners 09/10. |


| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-046 | IMPLEMENTED, REVIEW PENDING / 03 | Calculation v2 binds sealed profile sources, full parser/normalization definitions, actual semantic spans and approved fact-evidence mappings alongside exact job calculation definitions. Facts remain separately canonical. New claims need a scoped source profile; legacy v1 history is preserved without fabricated source attribution or silent reuse. Reupload provenance IDs do not alter semantic identity. Targeted source-variation and reupload tests pass. |
| ADR-047 | IMPLEMENTED, REVIEW PENDING / 03 | Successful private RLS reads register their exact scope or selected purpose in the same private transaction obligation protocol. Predicates are explicitly VOLATILE; anonymous/foreign denied reads do not acquire authority. Adapter completion revalidates reads after early checks and expiry. Scope/source data remain protected even in invoker projection functions. |


| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-048 | IMPLEMENTED, REVIEW PENDING / 03 | Construction-transaction seals alone are insufficient after a definition has already been used and deferred checks run early. Seal profile source/evidence at first evaluation/occurrence/advisory-manifest reference, and rubric criteria at first evaluation reference. Main real-DB reproduction and the same reviewer confirm the defect; 0017 repairs it without changing applied bytes. |


| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-049 | VERIFIED / 03 | The same and only reviewer Copernicus closed R1–R7 and the additional construction-time P1 at 0017 with PASS after the current nine-command checkpoint (94 PostgreSQL / 59 Python / 36 strict-mypy files). The interim 0016 approval remains withdrawn. Final authorization, migration coverage and future-runtime limits remain explicit. Phase 03 handoff authorizes only the next separately supplied Phase 04 prompt; it does not execute Phase 04. |

## Phase 04 decisions (2026-10-14; work began 2026-10-13)

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-050 | IMPLEMENTED, REVIEW PENDING / 04 | New installation sentinel and immutable instance/realm configuration distinguish a verified empty database from old/damaged data. Operator generates transient startup proof; bootstrap atomically consumes it and creates one real agency/admin. Server provisioning has no HTTP authority. |
| ADR-051 | IMPLEMENTED, REVIEW PENDING / 04 | Use Argon2id with explicit versioned synthetic policy, bounded verification and random 256-bit session proofs. Persistent account/global counters and live-session caps are serialized per installation. No default account or password-reset backdoor. |
| ADR-052 | IMPLEMENTED, REVIEW PENDING / 04 | Identity administration has its own narrow authenticated admin purpose; it must operate before recruitment policy activation and after revocation. Domain RLS/current purpose/consent checks remain required. Staff/policy writes use guarded revisions, keyed idempotency and separate immutable auth audit in one transaction. |
| ADR-053 | IMPLEMENTED, REVIEW PENDING / 04 | Connected staff uses explicit bearer HTTPS/native transport with no browser-origin CORS or cookies. Development memory sessions are instance-bound and generation-guarded. Device Credential Manager/native launch remains UNVERIFIED 15; approved deployed TLS remains 17. |
| ADR-054 | REPAIRED, REVIEW PENDING / 04 | Main reproduced policy expiry after early constraint validation at 0019. Forward 0020 adds nonconsumable private transaction policy obligations and final fresh-clock checks, including retry. All applied 0001–0019 bytes stay frozen. |

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-055 | REPAIRED, REVIEW FOLLOW-UP PENDING / 04 | The sole reviewer Einstein found three real defects at0020; seven main tests reproduced all. Forward0021 separates rejected login admission from admitted unknown-user verification and admits startup authority before bootstrap hashing under the same lock, with final checks retained. Shared password and relevant text validators reject invalid Unicode. Applied0001–0020 remain frozen; current affected/full verification and same-reviewer follow-up precede PASS. |

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-056 | VERIFIED / 04 | The same and only reviewer Einstein closed R1–R3 at 0021 with PASS after the repaired ten-command checkpoint (27 auth,73 Python,94 DB,48 typing files). The usage interruption resumed the same reviewer. Final owned requirement/source/evidence audit and forward migration integrity pass. Native/device15 and deployed HTTPS17 remain UNVERIFIED. Next is only a separately supplied complete Phase05 prompt. |

## Phase 05 decisions (2026-10-14)

| ID | Status/owner | Decision and evidence |
| --- | --- | --- |
| ADR-057 | AGREED/05 | Supplied Phase 05 supersedes remaining 18-phase numbering. User chose main-defined 45-phase roadmap constrained by 06/34/40/41/42. 86 stable IDs/history remain; individual current owners are in ACCEPTANCE_LEDGER. No authentication replay or migration change. |
| ADR-058 | AGREED/05 | Release packaging exclusively GitHub-hosted Windows x64: recipes 34, real remote builds/artifacts 40, clean offline 41, approved HTTPS 42. NSIS/per-user/retained LocalAppData and single-EXE portable/local NTFS sibling workspace are required. Local development checks/inference qualification remain allowed; no local release substitution. |
| ADR-059 | IMPLEMENTED, CI PENDING/05 | Approved new-project repo is Asdb24/CV-Manager. Existing main history contains only README at 0d8ce319b6e462785d0b1e8b4a87f3dac85f6041 and is preserved. Local root was not Git; 185 Phase 04 hashes matched. Scoped quality CI uses manual dispatch, explicit SHA, a codex branch, hosted Windows, read permissions, pinned actions/tools and disabled caches. No public Release/deployment. |

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-060 | IMPLEMENTED / 05 | Fresh hosted lint requires real Vite shell assets because Tauri code generation embeds the configured frontend directory. Prepare them with the validated synthetic test profile before existing Rust Clippy. This adds no UI feature, installer or runtime payload. CI timeout/capture values are central settings; safe admission ranges are 1–120 minutes and up to 128 MiB of local captured output. |

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-061 | REPAIRED, CI PENDING / 05 | The deliberately reduced CI dev profile omitted httpx2, while Starlette 1.7.0 imports it for TYPE_CHECKING. Its runtime httpx fallback explains the isolated unit success and type failure. Pin the already locked httpx2 2.13.1 directly in dev; no package version, auth/test source or assertion changes. Fresh dev-only mypy without cache and 73 tests pass; actual hosted re-verification remains required. |

| ID | Status / owner | Decision and evidence |
| --- | --- | --- |
| ADR-062 | VERIFIED / 05 | Actual manual run 38453840035, attempt 1, succeeded at reviewed `e5905a5e603cd9055b5025e77966db9c1dca0997` on the approved codex work branch. Existing main history/default-branch registration, explicit staging/exclusions, local/fresh dev-profile checks and main self-review pass. Two earlier failed runs are preserved. Release/runtime qualification stays UNVERIFIED at owners 34/40/41/42 and the ledger; only separately supplied Phase 06 may follow. |
