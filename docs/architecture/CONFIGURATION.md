# Configuration

Date: 2026-10-13. Phase work began 2026-10-12; Phase 01 baseline remains dated 2026-10-12. Primary IDs: CFG-001–004, CFG-006. `packages/foundation/src/cv_foundation/settings.py` owns the closed, frozen Pydantic configuration models and component/profile rules. `scripts/config.mjs` invokes that owner and returns its explicit browser allowlist. It does not duplicate validation or invent defaults.

## Selection and compatibility

Every runnable developer service requires `--config` and `--profile`. Profile mismatch, unknown/extra fields and required missing/invalid settings fail before startup. Developer API/worker/frontend launchers refuse release/server startup because those runtimes have not been qualified.

| Component | development | test | standalone | server | connected |
| --- | --- | --- | --- | --- | --- |
| Desktop | allowed | allowed | allowed contract | rejected | allowed contract |
| Public Next.js | allowed | allowed | rejected | allowed contract | rejected |
| API | allowed | allowed | allowed contract | allowed contract | rejected |
| Worker | allowed | allowed | allowed contract | allowed contract | rejected |
| Employee Windows AI | allowed contract | allowed contract | allowed contract | rejected | allowed contract |

Allowed contract means structural settings validation, not completed runtime. Tests exercise all 25 combinations, including rejected release combinations and both manifest distribution kinds.

`realm=local` pairs with `execution_mode=standalone`; `realm=server` pairs with `connected`. The explicit `realm_key` namespaces future identities, requests and caches, and cannot authenticate a caller. Native release manifests require a nonempty version, owner `native-release` and kind `installed` or `portable`. A release manifest cannot select execution mode. Development/test prohibit release manifests.

The two committed configurations are isolated synthetic fixtures. Their configured API/desktop/web/worker/AI ports are respectively 8127/1427/3027/8137/8147 and 8237/1527/3127/8247/8257. These numbers occur in fixture settings and matching negative tests, never as a UI/service fallback. Required settings do not inherit values from these files.

## Network and secrets

Origins require HTTP/HTTPS, an explicit canonical origin with no credentials/path/query/fragment/trailing slash, and valid ports. Development/test network origins are numeric HTTP loopback and mutually distinct. Worker and AI are always owned HTTP loopback. API/worker binding host/port must match their applicable local origin; Vite uses strictPort and Uvicorn binds once.

The Windows virtual WebView origin is a framework invariant declared in settings and included alongside the exact Vite desktop and web origins in CORS. Wildcard/foreign origins are rejected; credentials are not browser-attached. This does not grant staff authentication. Framework virtual-origin behavior is separate from DNS/service discovery.

Server/connected require an approved HTTPS server origin identical to the configured API origin, plus HTTPS public origin. Server additionally requires an environment-variable reference for PostgreSQL credentials and a document root. The structural validator checks reference names and required values; actual secret resolution/connection/storage adapters remain owners 03/16. Secret values never enter the browser projection. Operator approval/current identity cannot be established by a JSON label.

TLS verification is the literal true security invariant. Redirects are denied by generated transports; the developer JS entry points also reject `NODE_TLS_REJECT_UNAUTHORIZED=0`. There is no alternate server or mode. Public browser requests go to the same-origin Next.js route; only Next's server calls the restricted public API client. The public client contains no staff/native/AI operation exports.

Production public CSP uses self plus per-request script nonce, object/base/frame restrictions, same-origin connections and form action. Fluent requires inline styles; the documented `style-src 'unsafe-inline'` exception does not permit inline scripts. Next's development process alone adds `script-src 'unsafe-eval'` for framework debugging, following [official Next guidance](https://nextjs.org/docs/app/guides/content-security-policy); actual development/production header and browser checks assert the separation. Desktop CSP permits bundled scripts and only the centrally validated developer API connection. Native bridge CSP/HTTPS staging qualification remain owners 15/17.

## Units, limits and policy

All operational values below are required fields with positive, strict integer bounds. Upper validator guards are foundation safety bounds, not performance, legal or onboarding approval.

| Group | Central fields / units | Current synthetic policy |
| --- | --- | --- |
| HTTP lifecycle | request/shutdown milliseconds; keep-alive seconds | 10000/5000 ms, 5 s; shutdown must convert exactly to whole Uvicorn seconds |
| AI process | working-set bytes, threads, batch, concurrency, timeout ms, tokens/chunks | 1610612736-byte ceiling (1.5 GiB), 2 threads, batch 4, concurrency 1, 60000 ms, 512 tokens, 128 chunks |
| Documents | byte/page/text-character bounds | 10 MiB, 100 pages, 500000 characters; runtime owner 08/09 |
| Worker | queue items, concurrency, per-task ms | 16, 1, 60000 ms; no document runner currently |
| Temporary input | lifetime seconds, total stored bytes | 900 s and 256 MiB, metadata included; synthetic task retention only |
| Public API | page size, submission quota | 20/10; future enforcement owner 06/08 |

Model dimensions/token ceiling/prefixes and ranking definitions are pinned model-contract facts. Canonical ratings, weight sum, rounding, stages and authority checks are fixed domain/security invariants. None is a switch that disables permission or scoring rules.

Every sample names `synthetic-resource-v1` and `synthetic-only-v1`, with source/consent/purpose/retention/erasure versions and an explicit workspace/agency-admin custodian role. Real onboarding is false and data class synthetic-only. Real policy approval, custodian identity, activation and legal-purpose decisions remain UNVERIFIED owners 03/04/18; synthetic task lifetime cannot be used as a production retention policy.

Paths resolve from configured values in the project developer context; future release paths resolve from owned native workspace manifests. No personal workstation path is in an application default. DB/startup/staff secret values are backend/native-only. The browser projection includes only profile, execution mode, realm key, approved endpoint origins, request timeout distribution kind and centrally derived bind hosts/ports (including IPv6 and protocol default ports). It omits paths, DB references, policies, model resources and startup authority.

## Development infrastructure

`InfrastructureSettings` in the same settings owner validates `infra/config/compose.json`, exclusively for development/test. It supplies separate synthetic project/database/role/host-port identifiers, timing/memory settings and the name of an explicitly supplied secret environment variable. `scripts/compose.py` combines those settings with the immutable image digest in `infra/postgresql-image.lock.json`. It cannot select standalone/server/connected infrastructure.

Compose defines only PostgreSQL, an owned loopback host port and a persistent development volume. Container port 5432 and PostgreSQL 18's `/var/lib/postgresql` mount are upstream protocol/image facts. Passwords are never committed or printed by config checks. `check` validates the rendered definition without requiring an engine; `up` and `stop` require an actual development engine. This is not release storage or DB schema qualification.
