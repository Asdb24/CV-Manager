import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { validateQuality } from "./quality-ci.mjs";
import { root } from "./config.mjs";

const manifest = JSON.parse(
  readFileSync(path.join(root, "contracts/quality-ci.json"), "utf8"),
);
validateQuality(
  manifest,
  readFileSync(path.join(root, ".github/workflows/quality.yml"), "utf8"),
);
const evidence = path.join(root, "docs/phases/evidence-05");
mkdirSync(evidence, { recursive: true });
const results = [];
for (const task of manifest.quality_tasks) {
  const startedAt = new Date().toISOString();
  const result = spawnSync(process.execPath, ["scripts/tasks.mjs", task], {
    cwd: root,
    encoding: "utf8",
    shell: false,
    maxBuffer: 32 * 1024 * 1024,
  });
  writeFileSync(
    path.join(evidence, `${task.replace(":", "-")}.log`),
    `${result.stdout ?? ""}${result.stderr ?? ""}`,
  );
  results.push({
    command: `node scripts/tasks.mjs ${task}`,
    startedAt,
    finishedAt: new Date().toISOString(),
    exitCode: result.status,
  });
  writeFileSync(
    path.join(evidence, "local-commands.json"),
    JSON.stringify(results, null, 2) + "\n",
  );
  console.log(`${task}: exit=${result.status}`);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
