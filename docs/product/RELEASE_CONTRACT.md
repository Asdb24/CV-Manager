---
title: Windows dual-mode release and public-server qualification
version: 1.0
date_created: 2026-10-12
owner: Release authority; implementation and qualification owners per requirement
tags: [windows, release, offline, public-web]
---

# Release contract

The agreed release targets Windows 11 x64 with a per-user installer and a single-EXE self-extracting portable distribution. Both launch standalone offline with zero recipient technical setup. Connected work requires one approved configured HTTPS server; the public website requires the central deployment. None of these artifacts or deployments exists at the Phase 01 baseline. All runtime/artifact evidence starts UNVERIFIED.

## 1. Execution and packaging axes

| Axis | Selection and authority |
| --- | --- |
| Execution mode: standalone | Local workspace identity, private local PostgreSQL/API/worker/files, employee-Windows AI; independently offline |
| Execution mode: connected | Central staff identity and canonical server database/files; native Windows AI uses approved snapshots; approved HTTPS server required |
| Packaging: installed | Per-user installer with private manifest/runtimes and per-user mutable storage resolved by native context |
| Packaging: portable | Single EXE self-extracts verified private runtime payload into owned local storage and launches supervised processes; portable data/secrets path policy resolved by native manifest/context |

Packaging is selected by release manifest and cannot silently select or change the execution realm. Each distribution must permit explicit standalone or connected selection without sharing sessions/caches/data. Connected mode never falls back to a local database. Standalone remains qualified when the server is absent. “Both work offline” means both distributions execute all required standalone workflows and local AI offline; it cannot mean that the central server is reachable without a network.

Zero recipient technical setup means the recipient needs no Python, PostgreSQL, Docker, Node.js, Rust, terminal command, port setup, external WebView install or model download. First-run local admin identity and workspace/password establishment is an ordinary guided product action, not an operator deployment step. Do not preseed a sample account, hardcoded credentials or automatic central-server administrator. The server is provisioned separately by its operator on approved infrastructure.

## 2. Private runtime and storage boundary

Rust owns private Python, PostgreSQL, local API, bounded document worker and Windows AI lifecycle, loopback discovery, readiness, cancellation and cleanup. Manifest pins runtime/model/tokenizer/license/WebView hashes, executable roles, compatible versions and authorized arguments. Native context resolves paths and ports; UI/business code consumes validated context. Service readiness must be observed from actual owned processes, not fake health or arbitrary service reuse. Bind only approved loopback, isolate process/device sessions, and protect local secrets/files with verified OS mechanisms within the app-level threat boundary.

Fixed Version WebView2 is packaged app-private. Microsoft's [distribution documentation](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution) describes app-managed bundled fixed-version runtime updates and a network-location limitation; Tauri's [Windows installer documentation](https://v2.tauri.app/distribute/windows-installer/) describes bundling the fixed runtime. Phase 02/14 select compatible licensed versions; Phase 16 builds; Phase 17 verifies actual launch from approved local locations. Portable extraction must select an owned local location rather than assume Fixed Version runs from a network/UNC path. No documentation example version/path is adopted as a product pin.

Mutable workspace data is separate from replaceable runtime payload. Installed per-user storage and portable storage/extraction policies must explicitly resolve to native-owned locations with permissions, space validation, locks, integrity/recovery and privacy behavior. Portable copies cannot carry reusable server sessions or silently authenticate a new device; local workspace identity secrets remain governed by device/OS protection and recovery policy. A local OS administrator or physical copy is outside app-level protection. This contract does not claim whole-disk encryption or copy-proof secrets.

## 3. Requirements and acceptance

Acceptance notation and IDs follow [product](PRODUCT_SPEC.md).

| ID | Owner | Actor/precondition and required behavior | Failure behavior | Acceptance |
| --- | --- | --- | --- | --- |
| REL-001 | 02 | Architecture/toolchain retains required desktop/web/API/PostgreSQL/Alembic/generated clients/worker/protected-storage technologies and locks supported versions/licenses. | No alternative external AI provider, hand-written client masquerading as generated, or recipient Docker dependency. | G official sources/tool inventory; W architecture reviewed; T compatible explicit contracts/pins and development-only Compose boundary. |
| REL-002 | 14 | Rust manifest/supervisor owns private runtimes, loopback services, model resources and Fixed Version WebView2 with integrity/readiness/lifecycle checks. | Invalid asset, collision/unowned service, failed readiness or orphan process stops safely with actionable error. | G runtime manifest and failed child scenarios; W start/stop/restart; T only owned validated processes and observed readiness, bounded recovery. |
| REL-003 | 15 | Native bootstrap establishes protected local staff identity/storage/session before tenant context, automatically starts local services and separates connected server/device sessions. | No silent sample/dev fallback or native bootstrap of server administrator. | G clean offline machine and approved server realm; W guided local setup and explicit mode changes; T local identity works offline and cross-realm authority is absent. |
| REL-004 | 16 | Build owner creates actual per-user Windows 11 x64 installer and single-EXE self-extracting portable with all private runtimes/model/WebView/licenses. | Missing runtime/downloader-only package cannot claim complete offline artifact. | G pinned manifests; W build/hash/inspect artifacts; T both complete artifacts and license inventory exist with repeatable source/build provenance. |
| REL-005 | 16 | Backup/restore/upgrade orders task quiescence, DB/files/policy snapshot, forward migration/verification and restart with recovery/erasure reconciliation. | Failed backup/migration/integrity check preserves recoverable state and cannot report success. | G synthetic data plus pending task/erasure; W interrupted upgrade/restore; T coherent DB/files/version history and erased data not served. |
| REL-006 | 17 | Clean Windows recipient runs both distributions without dev tools/admin technical setup/network/model downloads; core flow and genuine local AI work offline. | External runtime/service/download requirement or inference failure is standalone qualification STOP. | G clean Windows 11 x64, network blocked, artifact hashes; W install/portable launch and core/AI flows; T actual standalone completion on each with environment/process/file evidence. |
| REL-007 | 15 | Explicit connected mode uses one centrally approved HTTPS origin/server-owned data and employee-Windows inference; no synchronization/session/cache sharing/outage fallback. | Missing/unreachable server blocks connected work and discards stale replies; standalone qualification stays separate. | G connected outage and mode switch; W read/write/AI attachment attempted; T no local fallback/cross-realm leakage and bounded pending-input cleanup. |
| REL-008 | 16 | Operator deployment configuration independently validates central API/database/durable worker/files/public web origins/TLS/secrets/public-client boundary. | Missing/invalid server setting fails; local bootstrap cannot provision server administrators. | G approved deployment config and invalid variants; W validate/build/start in owner phase; T explicit rejected invalid config and qualified operator/bootstrap boundary. |
| REL-009 | 17 | Approved HTTPS staging/hosting qualifies public browse/search/detail/intake and connected publication/inbox/local-AI attachment using synthetic data. | Missing approved environment remains explicit network qualification STOP; no paid signup/public external publication without approval. | G authorized infrastructure and versions; W complete positive/race/revocation/origin flows; T actual deployed evidence independent of offline artifacts. |
| REL-010 | 18 | Handoff includes artifact hashes/manifests/licenses, measured hardware/resource/AI quality limits, user/operator guides, backup/privacy/recovery and current requirement ledger. | No fabricated production/legal/security certification or unmeasured minimum hardware/speed/accuracy claim. | G all required qualifications; W handoff reconciled; T exact verified limits and unresolved restrictions match evidence. |

## 4. Owner checkpoints and evidence conditions

Phase 02 contracts and compatible dependency/license pins are prerequisites for implementation, not release evidence. Phase 14 supervises private processes/resources. Phase 15 implements actual dual-mode native identity/bridge/inference. Phase 16 builds artifacts and separate server/web deployment configuration. Phase 17 qualifies BOTH actual distributions on clean offline Windows and approved public/connected HTTPS environment. Phase 18 measures security and 100-CV resources/quality and reconciles handoff.

Record clean-machine OS build/CPU/RAM/storage, Windows display scale, artifact and manifest hashes, mode, packaging axis, current settings/policy version, blocked network condition, process owners/peaks, services/files and actual checks. Inspect UI at the required dimensions in [quality](QUALITY_ACCEPTANCE.md). Test first launch, subsequent launch, interrupted extraction/startup, user path with spaces/non-ASCII, missing/corrupt private asset, cancellation, clean shutdown, backup/upgrade/restore and device/session isolation. Operator deployment evidence separately records approved origin/TLS/server build/storage, no exposed secrets, public/staff generated client separation and publication/expiry/final-commit behavior.

Code signing, exact installer technology, portable extraction strategy, minimum CPU/RAM/disk and update distribution are OPEN Phase 02/14/16 decisions, not claims of absent Windows prompts or a completed signed build. No automatic reboot or paid certificate purchase is authorized. These choices cannot weaken the agreed offline/private-runtime/per-user/single-EXE outcomes. Missing approved network infrastructure can block Phase 17/18 network qualification; it does not block complete Phase 01 definitions.

## Phase 05 amendment (2026-10-14)

The separately supplied Phase 05 prompt and user roadmap choice supersede remaining 18-phase numbers. Original definitions/IDs/dated evidence above remain intact. Current owner mappings are in [ACCEPTANCE_LEDGER](ACCEPTANCE_LEDGER.md) and exact order in [PHASE_ROADMAP](../architecture/PHASE_ROADMAP.md). Release payload recipes are Phase 34, GitHub-hosted Windows x64 builds Phase 40, clean offline qualification Phase 41, approved HTTPS Phase 42, and final measurements/handoff Phases 43–45. Packaging is per-user NSIS with retained LocalAppData data and single-EXE portable with a writable local NTFS sibling workspace. No local/self-hosted recipient-PC release packaging, automatic public Release or deployment is authorized. Runtime behavior remains UNVERIFIED at its new owner.
