import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parse, stringify } from "yaml";
import { validateQuality } from "../scripts/quality-ci.mjs";

const manifest = JSON.parse(readFileSync("contracts/quality-ci.json", "utf8"));
const text = readFileSync(".github/workflows/quality.yml", "utf8");
assert.equal(validateQuality(manifest, text).valid, true);
const second = structuredClone(manifest);
const secondWorkflow = parse(text);
second.job_timeout_minutes = 20;
second.log_capture_max_bytes = 16 * 1024 * 1024;
secondWorkflow.jobs.quality["timeout-minutes"] = 20;
assert.equal(validateQuality(second, stringify(secondWorkflow)).valid, true);
for (const field of Object.keys(manifest)) {
  const invalid = structuredClone(manifest);
  delete invalid[field];
  assert.throws(() => validateQuality(invalid, text));
}
for (const change of [
  (m) => {
    m.repository = "foreign/project";
  },
  (m) => {
    m.job_timeout_minutes = 0;
  },
  (m) => {
    m.log_capture_max_bytes = 0;
  },
  (m) => {
    m.log_capture_max_bytes = 129 * 1024 * 1024;
  },
  (m) => {
    m.cache_policy = "trust-any-hit";
  },
  (m) => {
    m.actions["actions/checkout"] = "v7";
  },
  (m) => {
    m.runner = "self-hosted";
  },
  (m) => {
    m.tools.python = "3.x";
  },
]) {
  const invalid = structuredClone(manifest);
  change(invalid);
  assert.throws(() => validateQuality(invalid, text));
}
for (const change of [
  (w) => {
    w.on.push = {};
  },
  (w) => {
    w.permissions.contents = "write";
  },
  (w) => {
    w.jobs.quality.steps[1].with["persist-credentials"] = true;
  },
  (w) => {
    w.jobs.quality.steps[4].with["enable-cache"] = true;
  },
  (w) => {
    w.jobs.quality.steps[1].uses = "actions/checkout@v7";
  },
]) {
  const invalid = parse(text);
  change(invalid);
  assert.throws(() => validateQuality(manifest, stringify(invalid)));
}
assert.throws(() => validateQuality(manifest, "name: [invalid\n"));
console.log(
  "QUALITY_CI_MANIFEST_AND_WORKFLOW: PASS; two valid configurations and missing/unsafe cases rejected",
);
