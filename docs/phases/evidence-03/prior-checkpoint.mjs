// Capture actual canonical command results. A failure terminates this checkpoint.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { root } from "./config.mjs";
const directory = path.join(root, "docs/phases/evidence-02");
mkdirSync(directory, { recursive: true });
const checks = [
  ["install-frozen", "tasks.mjs", ["install:frozen"]],
  ["format", "tasks.mjs", ["format:check"]],
  ["lint", "tasks.mjs", ["lint"]],
  ["typecheck", "tasks.mjs", ["typecheck"]],
  ["test", "tasks.mjs", ["test"]],
  ["client", "clients.mjs", ["check"]],
  ["migration", "tasks.mjs", ["migration:check"]],
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
  [
    "ui-dev",
    "tasks.mjs",
    [
      "verify:ui:dev",
      "--config",
      "infra/config/development.json",
      "--profile",
      "development",
    ],
  ],
  [
    "ui",
    "tasks.mjs",
    [
      "verify:ui",
      "--config",
      "infra/config/development.json",
      "--profile",
      "development",
    ],
  ],
  [
    "audit",
    "tasks.mjs",
    [
      "verify:audit",
      "--config",
      "infra/config/development.json",
      "--profile",
      "development",
    ],
  ],
  ["model", "tasks.mjs", ["model:check"]],
  [
    "model-fetch",
    "fetch_model.mjs",
    ["--config", "infra/config/development.json", "--profile", "development"],
  ],
  ["licenses", "tasks.mjs", ["licenses:record"]],
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
