import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseDocument } from "yaml";

const root = path.resolve(import.meta.dirname, "..");
const approved = "Asdb24/CV-Manager";
const actionNames = [
  "actions/checkout",
  "actions/setup-node",
  "actions/setup-python",
  "astral-sh/setup-uv",
];

export function validateQuality(manifest, workflowText) {
  const required = [
    "version",
    "repository",
    "repository_url",
    "git_remote",
    "runner",
    "job_timeout_minutes",
    "log_capture_max_bytes",
    "ref_prefix",
    "tools",
    "actions",
    "quality_tasks",
    "cache_policy",
    "release_packaging_owner",
    "payload_recipe_owner",
    "offline_qualification_owner",
    "https_qualification_owner",
  ];
  assert.deepEqual(
    Object.keys(manifest).sort(),
    required.sort(),
    "CLOSED_CI_MANIFEST_REQUIRED",
  );
  assert.equal(manifest.version, "quality-ci-v1");
  assert.equal(manifest.repository, approved);
  assert.equal(manifest.repository_url, `https://github.com/${approved}`);
  assert.equal(manifest.git_remote, `https://github.com/${approved}.git`);
  assert.equal(manifest.runner, "windows-2025");
  assert.equal(manifest.ref_prefix, "refs/heads/codex/");
  assert.equal(manifest.cache_policy, "disabled");
  assert(
    Number.isInteger(manifest.job_timeout_minutes) &&
      manifest.job_timeout_minutes > 0 &&
      manifest.job_timeout_minutes <= 120,
  );
  assert(
    Number.isInteger(manifest.log_capture_max_bytes) &&
      manifest.log_capture_max_bytes > 0 &&
      manifest.log_capture_max_bytes <= 128 * 1024 * 1024,
  );
  assert.deepEqual(
    Object.keys(manifest.actions).sort(),
    [...actionNames].sort(),
  );
  for (const sha of Object.values(manifest.actions))
    assert.match(sha, /^[0-9a-f]{40}$/);
  assert.deepEqual(Object.keys(manifest.tools).sort(), [
    "node",
    "npm",
    "python",
    "rust",
    "uv",
  ]);
  for (const version of Object.values(manifest.tools))
    assert.match(version, /^\d+\.\d+\.\d+$/);
  assert.equal(manifest.release_packaging_owner, "40");
  assert.equal(manifest.payload_recipe_owner, "34");
  assert.equal(manifest.offline_qualification_owner, "41");
  assert.equal(manifest.https_qualification_owner, "42");
  assert.deepEqual(manifest.quality_tasks, [
    "format:check",
    "lint",
    "typecheck",
    "test",
  ]);
  const document = parseDocument(workflowText, { uniqueKeys: true });
  assert.equal(document.errors.length, 0, "WORKFLOW_YAML_INVALID");
  const workflow = document.toJS({ maxAliasCount: 0 });
  assert.deepEqual(Object.keys(workflow.on), ["workflow_dispatch"]);
  assert.deepEqual(workflow.permissions, { contents: "read" });
  assert.deepEqual(workflow.on.workflow_dispatch.inputs, {
    source_sha: {
      description: "Reviewed full commit SHA; must equal the dispatched ref",
      required: true,
      type: "string",
    },
  });
  assert.deepEqual(Object.keys(workflow.jobs), ["quality"]);
  const job = workflow.jobs.quality;
  assert.equal(job["runs-on"], manifest.runner);
  assert.equal(job["timeout-minutes"], manifest.job_timeout_minutes);
  assert.equal(job.defaults.run.shell, "pwsh");
  assert.equal(workflow.concurrency["cancel-in-progress"], false);
  const actions = job.steps.filter((step) => step.uses);
  assert.equal(actions.length, actionNames.length);
  for (const step of actions) {
    const [name, sha] = step.uses.split("@");
    assert.equal(sha, manifest.actions[name], "ACTION_PIN_MISMATCH");
  }
  assert.equal(actions[0].with["persist-credentials"], false);
  assert.equal(actions[0].with.ref, "${{ github.sha }}");
  assert.equal(actions[1].with["node-version"], manifest.tools.node);
  assert.equal(actions[2].with["python-version"], manifest.tools.python);
  assert.equal(actions[3].with.version, manifest.tools.uv);
  assert.equal(actions[3].with["enable-cache"], false);
  assert(
    actions.every((step) => !("cache" in step.with)),
    "UNVERIFIED_CACHE_FORBIDDEN",
  );
  const admission = job.steps[0];
  assert.equal(admission.env.REQUESTED_SHA, "${{ inputs.source_sha }}");
  assert.equal(admission.env.RESOLVED_SHA, "${{ github.sha }}");
  assert(
    admission.run.includes("SOURCE_SHA_MISMATCH") &&
      admission.run.includes("REVIEWED_WORK_BRANCH_REQUIRED"),
  );
  assert(admission.run.includes(approved));
  assert(
    !job.steps.some((step) => step.run?.includes("${{")),
    "SHELL_EXPRESSION_INTERPOLATION_FORBIDDEN",
  );
  assert(
    !workflowText.includes("secrets.") && !workflowText.includes("self-hosted"),
  );
  const install = job.steps.find(
    (step) => step.name === "Install frozen development tools",
  ).run;
  assert(
    install.includes(`npm@${manifest.tools.npm}`) &&
      install.includes("npm.cmd ci"),
  );
  assert(
    install.includes(
      `rustup toolchain install ${manifest.tools.rust}-x86_64-pc-windows-msvc`,
    ),
  );
  assert(
    install.includes(
      `uv sync --frozen --group dev --python ${manifest.tools.python}`,
    ),
  );
  assert(install.includes("cargo fetch --locked"));
  const assets = job.steps.find(
    (step) => step.name === "Prepare existing desktop assets for Rust checks",
  );
  assert.equal(assets["working-directory"], "apps/desktop");
  assert.equal(assets.run, "node ../../node_modules/vite/bin/vite.js build");
  assert.deepEqual(assets.env, {
    APP_CONFIG_FILE: "${{ github.workspace }}/infra/config/test.json",
    APP_PROFILE: "test",
  });
  for (const task of manifest.quality_tasks)
    assert(
      job.steps.some((step) => step.run === `node scripts/tasks.mjs ${task}`),
    );
  return {
    valid: true,
    repository: approved,
    runner: manifest.runner,
    actions: actions.length,
    tasks: manifest.quality_tasks,
  };
}

if (
  process.argv[1] &&
  fileURLToPath(import.meta.url) === path.resolve(process.argv[1])
) {
  try {
    assert.equal(process.argv[2], "validate");
    assert.equal(process.argv[3], "--manifest");
    assert(process.argv[4], "CI_MANIFEST_REQUIRED");
    const manifest = JSON.parse(
      readFileSync(path.resolve(root, process.argv[4]), "utf8"),
    );
    const result = validateQuality(
      manifest,
      readFileSync(path.join(root, ".github/workflows/quality.yml"), "utf8"),
    );
    const pkg = JSON.parse(
      readFileSync(path.join(root, "package.json"), "utf8"),
    );
    assert.equal(pkg.engines.node, manifest.tools.node);
    assert.equal(pkg.engines.npm, manifest.tools.npm);
    assert.equal(
      readFileSync(path.join(root, ".python-version"), "utf8").trim(),
      manifest.tools.python,
    );
    console.log(JSON.stringify(result));
  } catch {
    console.error("QUALITY_CI_CONFIGURATION_INVALID");
    process.exitCode = 1;
  }
}
