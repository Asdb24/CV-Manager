import { test, expect } from "@playwright/test";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { root, projection } from "../../scripts/config.mjs";

const config = process.env["APP_CONFIG_FILE"];
const profile = process.env["APP_PROFILE"];
if (!config || !profile) throw new Error("EXPLICIT_AUDIT_CONFIG_REQUIRED");
const client = projection("desktop", config, profile);
for (const kind of ["desktop", "public"]) {
  test(`${kind} actual Lighthouse audit`, () => {
    test.setTimeout(client.request_timeout_ms * 12);
    const result = spawnSync(
      process.execPath,
      [
        path.join(root, "scripts/lighthouse.mjs"),
        "--config",
        config,
        "--profile",
        profile,
        "--kind",
        kind,
      ],
      {
        cwd: root,
        encoding: "utf8",
        timeout: client.request_timeout_ms * 12,
      },
    );
    console.log(result.stdout);
    expect(result.status, result.stderr).toBe(0);
  });
}
