// Capture actual canonical command results. A failure terminates this checkpoint.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { root } from "./config.mjs";
// Current Phase 04 checkpoint preserves earlier evidence.
const configIndex = process.argv.indexOf("--database-config");
const databaseConfig =
  configIndex < 0 ? undefined : process.argv[configIndex + 1];
if (!databaseConfig) throw new Error("EXPLICIT_DATABASE_TEST_CONFIG_REQUIRED");
const databaseArgs = ["--config", databaseConfig];
const directory = path.join(root, "docs/phases/evidence-04");
mkdirSync(directory, { recursive: true });
const checks = [
  ["format", "tasks.mjs", ["format:check"]],
  ["lint", "tasks.mjs", ["lint"]],
  ["typecheck", "tasks.mjs", ["typecheck"]],
  ["test", "tasks.mjs", ["test"]],
  ["client", "clients.mjs", ["check"]],
  ["database", "tasks.mjs", ["database:check", ...databaseArgs]],
  ["authentication", "tasks.mjs", ["auth:check", ...databaseArgs]],
  ["migration", "tasks.mjs", ["migration:check", ...databaseArgs]],
  ["infra", "tasks.mjs", ["infra:check"]],
  [
    "build",
    "tasks.mjs",
    [
      "build",
      "--config",
      "infra/config/development.json",
      "--profile",
      "development",
    ],
  ],
];
const results = [];
for (const [name, entry, args] of checks) {
  const startedAt = new Date().toISOString();
  const result = spawnSync(
    process.execPath,
    [path.join(root, "scripts", entry), ...args],
    {
      cwd: root,
      env: process.env,
      encoding: "utf8",
      shell: false,
      maxBuffer: 32 * 1024 * 1024,
    },
  );
  writeFileSync(
    path.join(directory, `${name}.log`),
    `${result.stdout ?? ""}${result.stderr ?? ""}`,
  );
  results.push({
    name,
    command: `node scripts/${entry} ${args.join(" ")}`,
    startedAt,
    finishedAt: new Date().toISOString(),
    exitCode: result.status,
  });
  writeFileSync(
    path.join(directory, "commands.json"),
    JSON.stringify(results, null, 2) + "\n",
  );
  console.log(`${name}: exit=${result.status}`);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
