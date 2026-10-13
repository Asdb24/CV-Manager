# Data flow and authority

Date: 2026-10-13. Phase work began 2026-10-12; Phase 01 baseline remains dated 2026-10-12. This Phase 02 contract supports DAT-001–008, SEC-001–008, PUB-001–008, SCR-001–008 and AI-001–013. Runtime remains with each requirement's owner in [the phase index](../phases/PHASE_INDEX.md).

## Current shell paths

Desktop selects a centrally validated developer configuration, compiles only its allowlisted projection, and requests actual `/live` through the generated staff transport. A response establishes service liveness only. The UI explicitly states login/data/documents unavailable, disables repeated checks while pending, aborts old selection work and rejects stale replies.

Public Next.js renders a labeled empty shell. Its browser calls same-origin `/api/status`; that server route uses the separately generated public binding for `/public/capabilities`. The unavailable jobs/application result is shown truthfully. No upload, candidate contact, staff session or native module is exposed. Server forwarding has a configured timeout, omits browser credentials and refuses redirects.

## Staff command contract

1. Resolve the selected native realm and current staff session. The server/local API authenticates staff before deriving tenant context.
2. Resolve current membership/role and record scope, source, permitted purpose, consent and privacy epoch. PDFs, CV text, AI output, headers and client identifiers are data, never commands or grants.
3. Enter one whole-command transaction. Check revision guards and scoped idempotency; persist related writes/history/result/audit together.
4. Recheck current authority at final commit. Conflict, revocation, erasure or payload mismatch prevents every related write.
5. Return a safe projection of committed state. UI success requires backend confirmation; retries retain the same operation key and cannot revive a revoked realm/view.

These are required future service behaviors. Current staff contracts deny requests and create no tenant/session or business record.

## Publication and intake contract

Connected staff authorize an allowlisted publication from a current position/JD version. The server resolves anonymous job authority from the current publication, never a caller tenant header. Public responses include only approved agency/company/job/application fields. Candidate existence, equality digests, CVs, private counts, scores and staff DTOs are excluded.

Anonymous intake resolves current publication/expiry, configured quota/resource bounds and versioned consent/purpose, issues an opaque upload intent, and validates a text-PDF in protected staging. Final acceptance rechecks publication, authority, consent, limits and scoped idempotency in the same guarded persistence boundary, then finalizes durable files through intents/recovery. A receipt is emitted only for durable acceptance. A connection-uncertain request offers a same-key retry.

Connected staff review intake under current authority before explicit candidate/application linking. No automatic person merge or staff authority bypass exists. Browse is owner 06; review contracts 07; upload/intake/inbox 08. Phase 02 routes return unavailable and never fake a receipt.

## Windows-local advice contract

The employee selects an authorized application, current confirmed profile facts and pinned JD/rubric/evidence. Owner 09 builds an approved input manifest containing realm/person/privacy epoch, purpose/consent, application/profile/JD revisions, evidence locators, opaque input handle, digest and expiry. Standalone resolves local authority; connected retrieves only a currently authorized snapshot from this application's own server.

The trusted Windows owner stores the snapshot under a separate local 64-hex handle in a protected realm-specific input store, preserving the server manifest and its original opaque handle, capped by approved expiry and configured local lifetime/bytes. Startup authority is fresh per process and sent privately to the local binding. The browser and hosted API never load the model. The task DTO cannot choose a path, command, process, provider or remote destination.

Owner 10 runs the pinned CPU module on demand using bounded settings. It returns separately scoped semantic evidence, conservative to-verify findings and editable Vietnamese template questions, with input/model/tokenizer/runtime/rule/template/ranking/device-session provenance. Similarity is finite advisory floating-point data; it cannot populate canonical ratings/weights/thresholds, move stage or prove skill/fraud. A staff-confirmed fact creates a new profile/evaluation revision.

On cancel, completion, expiry, revocation, failure or owner shutdown, remove owned inputs and derived task artifacts according to policy. The foundation verifies synthetic handle revocation/expiry/restart cleanup on Windows; actual inference/task lifecycle is UNVERIFIED owner 10 and native wiring 15.

## Final advisory attachment contract

The authenticated staff endpoint receives a typed advisory attachment, never an execution-authority assertion. Within one transaction the server rechecks membership/role/record/purpose/consent, current application/profile/JD/evidence versions, approved input manifest/digest, privacy epoch and expiry, allowed model/rule/template/ranking versions and authenticated device session. It bounds all advisory content and references; rejects stale/tampered/foreign data; records immutable provenance, idempotent attachment result and audit together.

`execution_mode` and claimed device/model fields cannot authenticate or prove where computation occurred. Server capability is attachment validation/storage only, not local model execution. Current `/staff/advisory-attachments` requires future staff authority and denies all requests; final authorization/persistence is UNVERIFIED owners 04/10/15.

## Scoring and erasure

Calculation input freezes confirmed facts, rubric/evidence semantics and any reference date. Exact canonical math is independent of advisory model versions, timestamps, upload/request IDs, language and transport. Advisory provenance is persisted outside canonical score identity. Both modes use the same frozen definition; their databases and equality caches remain independent.

Erasure invalidates the current privacy epoch and removes personal source/derived content, private scores/advice and equality caches. Restoring a removed record or backup cannot recover erased data under a prior epoch. Local OS administrators or physical workspace copies are outside app-level protection; no encryption/certification or absolute confidentiality claim is made. Connected authorized CV/snapshot transmission to this application's server must be disclosed before real onboarding. No personal dataset or external AI provider is used here.
