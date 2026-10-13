# Reproducibility and toolchain

Date: 2026-10-13. Phase work began 2026-10-12; Phase 01 baseline remains dated 2026-10-12. These are developer commands for the Phase 02 foundation. They do not install a recipient-ready release. Run from the project root on Windows 11 x64; keep the complete current phase prompt and dated evidence.

## Inventory and compatible pins

The host already had PowerShell 7.6.5, Node 26.8.2/npm 12.0.2, uv 0.12.19, Python 3.14.7 plus managed Python 3.13.15, Rust/Cargo 1.98.1, MSVC Build Tools 17.14.41 and Docker client 29.8.2/Compose 5.5.1. Python 3.13.15 was selected for the pinned model/tool ecosystem without replacing the host default Python. The host's Evergreen WebView2 is 154.0.4258.62; it is a development dependency and no Fixed Version release payload is qualified. No reboot was performed or required by these additions; the Build Tools inventory reported no pending reboot.

Docker engine was unavailable at inventory (missing daemon named pipe). Compose syntax/configuration can still be checked. Actual DB operations are UNVERIFIED owner 03; do not claim Docker or PostgreSQL runtime health from tool presence or rendered YAML.

| Family | Exact selected pins | Licensing/source |
| --- | --- | --- |
| UI | React/react-dom 19.3.0; Fluent provider 9.22.21, button 9.11.1, text 9.6.20, theme 9.2.2; Radix icons 1.3.2 | MIT upstream metadata; official modular Fluent API |
| Frontends | Next.js 16.4.0; Vite 8.3.4; React plugin 6.1.2; TypeScript 5.9.3 | MIT/Apache-2.0 as recorded in dependency ledger |
| Native | Tauri CLI 2.12.2; Rust tauri 2.12.3 and tauri-build 2.7.2 | MIT/Apache-2.0 upstream |
| API/DB | FastAPI 0.143.0, Uvicorn 0.54.0, Pydantic 2.14.1, Alembic 1.20.0, SQLAlchemy 2.1.4, psycopg 3.3.6 | MIT/BSD/LGPL expressions recorded per distribution |
| Model compatibility | ONNX Runtime 1.31.0; tokenizers 0.23.3; frozen E5 assets | MIT/Apache-2.0 and pinned copied model license |
| Checks/generation | openapi-typescript 7.13.0, openapi-fetch 0.17.0, ESLint 10.12.0, typescript-eslint 8.71.1, Prettier 3.9.10, pytest 9.1.1, Ruff 0.17.0, mypy 2.4.0 | Upstream lock/installed metadata |
| Browser inspection | Playwright 1.64.0, its pinned Chromium 156.0.8078.4 revision 1248; Lighthouse 13.5.0 | Apache-2.0/tool and browser bundled notices |
| Development DB image | PostgreSQL 18.6-bookworm, digest in image lock | PostgreSQL License plus upstream Debian/bundled notices; engine/runtime not qualified |

[Official registry snapshots](TOOLCHAIN_SOURCES.json), [resolved dependency/license ledger](DEPENDENCY_LICENSES.json), `package-lock.json`, `uv.lock`, Rust `Cargo.lock` and the model/image manifests identify the selected sources. Version choice followed peer/support compatibility rather than replacing working tools for novelty. TypeScript 7 was excluded by generator/lint support ranges. The aggregate Fluent package conflicted with strict exact-optional declaration checks; official modular Fluent packages compile without weakening typing. The typecheck command first runs official Next typegen with an explicit isolated test configuration, refreshing next-env references after development. Production route declarations are retained in strict checks; the alternate `.next/dev` global declarations are excluded to avoid compiling duplicate framework `LayoutProps` types after a development run. No application source or strict option is excluded. A local URLPattern declaration alias uses official Node types for Next's global declaration requirement; skipLibCheck remains false.

The dependency ledger includes noninstalled foreign-platform optional npm packages as lock records. It is not a legal redistribution opinion. Complete bundled notices, MSVC/WebView redistribution and final release licensing review belong to 16; personal-data policy approval is separate.

## Canonical commands

| Command | Required result / behavior |
| --- | --- |
| `npm run install:frozen` | npm ci, uv sync --frozen --all-groups with Python 3.13.15, Cargo fetch --locked; missing tools/lock mismatch fail |
| `npm run format:check` | Prettier, Ruff format check and Rust fmt; generated artifacts/dependencies are excluded intentionally |
| `npm run lint` | Strict typed ESLint for application/UI tests, Ruff including security and Rust Clippy with warnings denied |
| `npm run typecheck` | Strict TypeScript for both apps/shared packages/UI tests, then strict mypy for API/worker/foundation/tests |
| `npm run test` | Foundation and actual Windows file tests, real API/worker process lifecycle/port checks, generated client scratch/negative checks |
| `npm run client:generate` | Export actual tagged FastAPI schemas and generate all four separated bindings |
| `npm run client:check` | Re-export/regenerate in scratch and compare bytes; invoke actual checker against deliberately stale type/schema artifacts |
| `npm run migration:check` | Check complete Alembic scaffold, owner 03 and zero revisions; no upgrade claim |
| `npm run build -- --config infra/config/development.json --profile development` | Build Vite, Next.js/TypeScript and actual Windows Tauri debug executable; no release bundle |
| `npm run verify:ui -- --config infra/config/development.json --profile development` | Start real API, Vite and the completed production Next build; required viewports/themes, keyboard/state checks and screenshots |
| `npm run verify:ui:dev -- --config infra/config/development.json --profile development` | Run the same 10 shell/state/keyboard checks with the actual Next development server |
| `npm run verify:audit -- --config infra/config/development.json --profile development` | Actual Lighthouse audits of desktop/public shell; report automated accessibility findings and measurement limits |
| `npm run infra:check` | Real Compose config checks for both synthetic profiles and rejection of missing secrets; no database starts |
| `npm run model:fetch -- --config infra/config/development.json --profile development` | Development/build-only acquisition of immutable model URLs; verify manifest and every asset hash/size |
| `npm run model:check` | Verify pinned assets/license and Windows CPU artifact compatibility; no product advice service claim |
| `npm run licenses:record` | Save exact installed/locked upstream metadata, including optional platform dependencies |
| `npm run verify:checkpoint` | Run all required commands in order, store actual output/exit codes and stop on the first failure |

The build requires explicit valid settings. Run `node node_modules/@playwright/test/cli.js install chromium` once for the pinned developer browser. Browser installation is not a product runtime requirement. The Windows icon is generated from the project-owned SVG with the pinned Tauri CLI; no mobile product is implied by generic CLI-generated icon assets.

To start developer services, run `.venv/Scripts/python.exe -m cv_api --config infra/config/development.json --profile development` and the equivalent `cv_worker` module. Shell preview uses `npm run dev:desktop -- --config ... --profile development`. Public development/start behavior is checked separately from the production build. All service targets come from validated configuration. Stop developer services with the owning signal/channel; do not leave test processes or ports running.

For Compose use `.venv/Scripts/python.exe scripts/compose.py --profile development check`, then `up` only when an actual development engine is available; `stop` preserves the development volume. Supply a generated developer secret in the named environment variable. There is no sample password, release Compose command, packaged database emulator or production deployment in this phase.

## Evidence and limits

Checkpoint logs are in `docs/phases/evidence-02`. Runtime/client/UI/model structured results and screenshots are generated in ignored `.local` and copied into dated phase evidence for handoff. Source/lock/artifact hashes tie the final report to the inspected snapshot; historical Phase 01 evidence remains preserved. Main-agent self-review is the required Phase 02 arrangement, not an independent review.

The model fetcher never runs from the application; the schema factory never fabricates inference. Actual application data persistence, identity, native bridges, private runtimes, offline artifacts, approved HTTPS staging, real onboarding, product memory and advice-quality measurements remain UNVERIFIED with their owners. The next permitted prompt after Phase 02 PASS is exactly `PHASE_03_POSTGRESQL_SCHEMA_AND_MIGRATIONS.md`.
