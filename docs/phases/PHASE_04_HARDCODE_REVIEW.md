# Phase 04 operational-value review

Date: 2026-10-14. Main active-path review complete; ten-command checkpoint and final affected checks passed. Independent reviewer pending. Relevant active paths are API factory/middleware/routes/authentication/operator, foundation settings/database/server, SQL identity/policy functions and generated client/session transport.

| Candidate | Owner / classification | Disposition and evidence |
| --- | --- | --- |
| API/server origins, realm key, database path/role/password, timeouts | Validated Settings/DatabaseConnectionSettings and explicit operator environment | No request tenant selection, localhost/default credential fallback; negative settings and two-real-database tests |
| Session/attempt/staff/page/body/hash bounds | Required versioned AuthenticationPolicy persisted at bootstrap and compared at runtime | Synthetic policy is an isolated fixture; no real onboarding/retention approval; negative zero/missing/unsafe fields tested |
| Random proof 32-byte length, SHA-256/HMAC, Argon2id type and minimum guards | Sourced security definitions | Security invariants, not disable-auth switches. Argon2id parameters supplied by policy; no external identity provider |
| auth-v1 route version, admin/recruiter roles, new/initialized/closed states, safe codes | Explicit protocol/domain invariants | Generated staff schema and SQL checks; public graph pruned from actual OpenAPI |
| SQL function names, role names and trusted static SELECT | Persistence boundary from Phase 03 | Parameterized request values; migration owner separate from runtime/public; no arbitrary SQL endpoint |
| 0001–0020 migration source values | Frozen applied schema/history | Hash ledger verifies every applied byte. Repairs use new revisions only |
| Synthetic usernames, fake passwords, dates/UUIDs/ports, pg_sleep in tests | Labeled isolated negative/golden fixtures | Disposable owned test databases; no runtime account or fake product records; real Argon2/session transactions |
| Loopback addresses, HTTP/HTTPS schemes, 443/80, Tauri virtual origin | Network protocol/native context restrictions | Exact configured origins, TLS required connected transport, no alternate fallback |
| Operator future/native keyring identifiers | Contract only | Documented UNVERIFIED owner 15; no implementation claim |

Manual tracing confirms identity is bound before staff data queries; route DTOs do not accept tenant/role assertions for ordinary session authority. Staff creation role is an admin-only requested change, not caller authentication. Public DTOs carry no staff credentials. Passwords, startup/session proofs and database credentials are never emitted in routine logs. Dependency additions were inventoried first and pinned in pyproject/uv locks. Generated contract separation/checks and current checkpoint passed. Final credential/source evidence audit is in evidence-04/main-audit.json; independent review is required before PASS.

Gate decision: STOP

## Review repair paths

Reviewed0021 admission branches, shared PasswordInput/UTF8Text validators and bounded hash service calls. The new admitted flag is an internal server-derived result, never a client authority input or disable-auth option. SQL limits still come from the locked persisted policy. Bootstrap pre-admission uses the same instance/startup proof/state/expiry as final create. Invalid Unicode is an input encoding invariant; valid Vietnamese/Unicode remains supported. New test delays/surrogates are labeled synthetic negative fixtures. Current checkpoint and same-reviewer follow-up remain pending.

Gate decision: STOP

The repaired current checkpoint passed all10 commands. Final source/evidence secret scan and manual review of the affected admission/Unicode paths passed in main-audit-0021.json. The same-reviewer closure remains pending.

Gate decision: STOP

## Final disposition

Current active-path manual review, ten-command checkpoint and final safe-credential/source audit are complete. The same reviewer closed all findings at 0021. Required operational values remain supplied by validated settings, native context or authorized records; static security/protocol/schema and synthetic-fixture values are explicitly classified above. No regex-count cleanliness claim is made.

Gate decision: PASS
