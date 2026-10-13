import { spawnSync } from "node:child_process";
import path from "node:path";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { python, projection, root } from "./config.mjs";

const [task, ...args] = process.argv.slice(2);
function run(command, argv, cwd = root, env = process.env) {
  const result = spawnSync(command, argv, {
    cwd,
    env,
    stdio: "inherit",
    shell: false,
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
// Use Node entry points directly on Windows, never a string-composed cmd invocation.
function js(entry, argv, cwd = root, env = process.env) {
  run(
    process.execPath,
    [path.join(root, "node_modules", entry), ...argv],
    cwd,
    env,
  );
}
const positions = {
  config: args.indexOf("--config"),
  profile: args.indexOf("--profile"),
};
function configured(component) {
  return projection(
    component,
    positions.config < 0 ? undefined : args[positions.config + 1],
    positions.profile < 0 ? undefined : args[positions.profile + 1],
  );
}
function appEnvironment(component) {
  const config = configured(component);
  if (!["development", "test"].includes(config.profile))
    throw new Error("DEVELOPER_RUNTIME_REQUIRES_DEVELOPMENT_OR_TEST_PROFILE");
  return {
    ...process.env,
    APP_CONFIG_FILE: path.resolve(root, args[positions.config + 1]),
    APP_PROFILE: args[positions.profile + 1],
    CV_CLIENT_CONFIG: JSON.stringify(config),
    CV_DESKTOP_ORIGIN: config.desktop_origin,
    CV_WEB_ORIGIN: config.web_origin,
    CV_PUBLIC_API_ORIGIN: config.api_origin,
    CV_REQUEST_TIMEOUT_MS: String(config.request_timeout_ms),
  };
}
switch (task) {
  case "install:frozen":
    run(process.execPath, [process.env.npm_execpath, "ci"]);
    run("uv", ["sync", "--frozen", "--all-groups", "--python", "3.13.15"]);
    run("cargo", [
      "fetch",
      "--locked",
      "--manifest-path",
      "apps/desktop/src-tauri/Cargo.toml",
    ]);
    break;
  case "format":
  case "format:check":
    js("prettier/bin/prettier.cjs", [
      task === "format" ? "--write" : "--check",
      "apps/**/*.{ts,tsx,mjs,json,html}",
      "packages/**/*.{ts,tsx,css,json}",
      "scripts/*.{mjs,mts}",
      "infra/**/*.{json,yaml}",
      "tests/**/*.{ts,mjs,json}",
      "package.json",
      "tsconfig.base.json",
      "eslint.config.mjs",
    ]);
    run(python, [
      "-m",
      "ruff",
      "format",
      ...(task === "format:check" ? ["--check"] : []),
      "apps",
      "packages/foundation",
      "tests/python",
      "tests/database",
      "tests/auth",
      "scripts",
    ]);
    run("cargo", [
      "fmt",
      "--manifest-path",
      "apps/desktop/src-tauri/Cargo.toml",
      "--",
      ...(task === "format:check" ? ["--check"] : []),
    ]);
    break;
  case "lint":
    js("eslint/bin/eslint.js", ["apps", "packages", "tests/ui"]);
    run(python, [
      "-m",
      "ruff",
      "check",
      "apps",
      "packages/foundation",
      "tests/python",
      "tests/database",
      "tests/auth",
      "scripts",
    ]);
    run("cargo", [
      "clippy",
      "--locked",
      "--manifest-path",
      "apps/desktop/src-tauri/Cargo.toml",
      "--",
      "-D",
      "warnings",
    ]);
    break;
  case "typecheck":
    // Explicit isolated test fixture for framework route generation, not runtime fallback.
    js("next/dist/bin/next", ["typegen"], path.join(root, "apps/web"), {
      ...process.env,
      APP_CONFIG_FILE: path.join(root, "infra/config/test.json"),
      APP_PROFILE: "test",
    });
    for (const pkg of [
      "packages/api-client",
      "packages/ui",
      "apps/desktop",
      "apps/web",
      "tests/ui",
    ])
      js("typescript/bin/tsc", ["-p", path.join(pkg, "tsconfig.json")]);
    run(python, ["-m", "mypy"]);
    break;
  case "test":
    run(python, ["-m", "pytest"]);
    run(process.execPath, ["tests/session-state.mjs"]);
    run(process.execPath, ["tests/quality-ci.mjs"]);
    run(process.execPath, ["tests/runtime.mjs"]);
    run(process.execPath, ["scripts/clients.mjs", "check"]);
    break;
  case "auth:check":
    if (positions.config < 0 || !args[positions.config + 1])
      throw new Error("EXPLICIT_DATABASE_TEST_CONFIG_REQUIRED");
    run(python, [
      "-m",
      "pytest",
      "tests/auth",
      "--database-config",
      args[positions.config + 1],
      "-q",
    ]);
    break;
  case "migration:check":
    run(python, ["scripts/migration_check.py"]);
    run(python, ["scripts/database_migration_check.py", ...args]);
    run(python, ["scripts/database_legacy_precision_check.py", ...args]);
    break;
  case "database:check":
    run(python, ["scripts/migration_check.py"]);
    run(python, ["scripts/database_cluster.py", "start", ...args]);
    run(python, ["scripts/database_migrate.py", "upgrade", "head", ...args]);
    if (positions.config < 0 || !args[positions.config + 1])
      throw new Error("EXPLICIT_DATABASE_TEST_CONFIG_REQUIRED");
    run(python, [
      "-m",
      "pytest",
      "tests/database",
      "--database-config",
      args[positions.config + 1],
      "-q",
    ]);
    run(python, ["scripts/database_query_evidence.py", ...args]);
    run(python, ["scripts/database_catalog.py", ...args]);
    break;
  case "infra:check":
    run(python, ["scripts/infra_check.py"]);
    break;
  case "model:check":
    run(python, ["scripts/model_check.py"]);
    break;
  case "licenses:record":
    run(python, ["scripts/licenses.py"]);
    break;
  case "build": {
    const desktopEnv = appEnvironment("desktop");
    const webEnv = appEnvironment("web");
    js(
      "vite/bin/vite.js",
      ["build"],
      path.join(root, "apps/desktop"),
      desktopEnv,
    );
    js(
      "next/dist/bin/next",
      ["build", "--webpack"],
      path.join(root, "apps/web"),
      webEnv,
    );
    mkdirSync(path.join(root, ".local"), { recursive: true });
    const base = JSON.parse(
      readFileSync(path.join(root, "apps/desktop/src-tauri/tauri.conf.json")),
    );
    base.app.security.csp += `; connect-src 'self' ${JSON.parse(desktopEnv.CV_CLIENT_CONFIG).api_origin}`;
    const overlay = path.join(root, ".local/tauri.build.json");
    writeFileSync(overlay, JSON.stringify(base));
    js(
      "@tauri-apps/cli/tauri.js",
      ["build", "--debug", "--no-bundle", "--config", overlay],
      path.join(root, "apps/desktop"),
      desktopEnv,
    );
    break;
  }
  case "dev:desktop":
    js(
      "vite/bin/vite.js",
      [],
      path.join(root, "apps/desktop"),
      appEnvironment("desktop"),
    );
    break;
  case "dev:web": {
    const env = appEnvironment("web");
    const client = configured("web");
    js(
      "next/dist/bin/next",
      [
        "dev",
        "--webpack",
        "--hostname",
        client.web_host,
        "--port",
        String(client.web_port),
      ],
      path.join(root, "apps/web"),
      env,
    );
    break;
  }
  case "verify:ui":
  case "verify:ui:dev":
  case "verify:audit":
    appEnvironment("desktop");
    js(
      "@playwright/test/cli.js",
      [
        "test",
        "-c",
        task === "verify:ui"
          ? "tests/ui/playwright.config.ts"
          : task === "verify:ui:dev"
            ? "tests/ui/playwright.dev.config.ts"
            : "tests/ui/playwright.audit.config.ts",
      ],
      root,
      appEnvironment("web"),
    );
    break;
  default:
    throw new Error("UNKNOWN_REQUIRED_TASK");
}
