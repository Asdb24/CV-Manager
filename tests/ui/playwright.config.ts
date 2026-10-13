import { defineConfig } from "@playwright/test";
import { projection, root, python } from "../../scripts/config.mjs";
import { readFileSync } from "node:fs";
import path from "node:path";

const configFile = process.env["APP_CONFIG_FILE"];
const profile = process.env["APP_PROFILE"];
if (!configFile || !profile)
  throw new Error("EXPLICIT_UI_TEST_CONFIG_REQUIRED");
const client = projection("desktop", configFile, profile);
const raw: unknown = JSON.parse(readFileSync(configFile, "utf8"));
if (!raw) throw new Error("CONFIGURATION_REQUIRED");
export default defineConfig({
  testDir: ".",
  testMatch: "shell.spec.ts",
  timeout: client.request_timeout_ms * 6,
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(root, ".local/ui-results.json") }],
  ],
  use: { browserName: "chromium", headless: true, deviceScaleFactor: 1 },
  webServer: [
    {
      command: `"${python}" -m cv_api --config "${configFile}" --profile ${profile}`,
      cwd: root,
      url: `${client.api_origin}/live`,
      reuseExistingServer: false,
      timeout: client.request_timeout_ms * 6,
    },
    {
      command: `node scripts/tasks.mjs dev:desktop --config "${configFile}" --profile ${profile}`,
      cwd: root,
      url: client.desktop_origin,
      reuseExistingServer: false,
      timeout: client.request_timeout_ms * 6,
    },
    {
      command: `node scripts/start_web.mjs --config "${configFile}" --profile ${profile}`,
      cwd: root,
      url: client.web_origin,
      reuseExistingServer: false,
      timeout: client.request_timeout_ms * 6,
    },
  ],
});
