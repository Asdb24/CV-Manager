---
title: Scope boundaries and deferred work
version: 1.0
date_created: 2026-10-12
owner: Product authority from Phase 01 objective
tags: [scope, deferred]
---

# Deferred scope and prohibited paths

The required scope is defined in [product](PRODUCT_SPEC.md), [quality](QUALITY_ACCEPTANCE.md), [release](RELEASE_CONTRACT.md) and [AI](LOCAL_AI_CONTRACT.md). Deferral is a product decision, not a way to relabel broken active requirements or avoid a failed gate. Scope changes require a dated decision, new/updated stable acceptance and affected earlier-owner verification.

| Deferred capability | Current boundary | Future change authority |
| --- | --- | --- |
| Applicant/employer accounts and portals | Anonymous published-job browse/intake only; companies are internal records | New user-approved scope and identity/privacy design |
| Separate public-web administration portal | Staff publish/unpublish/review from connected Windows | New user-approved scope |
| OCR and DOCX resume intake | Text PDF only; scanned-only/unsupported/encrypted/malformed input gets explicit safe status | New parser/resource/privacy scope |
| Training/fine-tuning models | Use pinned pretrained multilingual-e5-small ONNX INT8 CPU inference; build-time reproducible conversion is not model training | New approved dataset/license/resource scope |
| Free-form local LLM generation | Semantic embeddings, conservative rule-plus-AI findings and versioned editable Vietnamese template questions are required now | New separately reviewed model/resource scope |
| Email/calendar integration | No sending, calendar operations or automated outreach | Explicit user authorization and new integration scope |
| SLA, commercial offers/billing/service packages | No commercial workflows, availability promises or contractual service metrics | New product/legal authority |
| Multi-agency management UI | One agency per workspace; second synthetic agency for isolation tests only | New product/authorization scope |
| Automatic local/server synchronization | No cross-realm sync or sharing; explicit independent execution modes | New product/security/conflict design |

External AI provider APIs are PROHIBITED, not an optional deferred integration. Required local AI failure never authorizes an external fallback. Real personal datasets, paid hosting signups and public external deployment are not authorized by this phase. Final approved synthetic HTTPS qualification remains mandatory in Phase 17; absence there is STOP.

Mandatory future implementation is not deferred: public job browse/search/detail, anonymous text-PDF/contact/consent intake, connected staff publication/inbox/review, standalone/connected identity/data boundaries, genuine employee-Windows AI in both modes, canonical exact scores, five manual stages, reports, private runtimes, installer/portable and offline zero recipient technical setup. All are UNVERIFIED runtime until their primary owners execute acceptance. [The phase index](../phases/PHASE_INDEX.md) records ownership and exact prompt filenames; no future prompt is generated here.

## Phase 05 amendment (2026-10-14)

The separately supplied Phase 05 prompt and user roadmap choice supersede remaining 18-phase numbers. Original definitions/IDs/dated evidence above remain intact. Current owner mappings are in [ACCEPTANCE_LEDGER](ACCEPTANCE_LEDGER.md) and exact order in [PHASE_ROADMAP](../architecture/PHASE_ROADMAP.md). Release payload recipes are Phase 34, GitHub-hosted Windows x64 builds Phase 40, clean offline qualification Phase 41, approved HTTPS Phase 42, and final measurements/handoff Phases 43–45. Packaging is per-user NSIS with retained LocalAppData data and single-EXE portable with a writable local NTFS sibling workspace. No local/self-hosted recipient-PC release packaging, automatic public Release or deployment is authorized. Runtime behavior remains UNVERIFIED at its new owner.
