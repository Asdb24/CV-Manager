import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
import { root } from "../../scripts/config.mjs";
import path from "node:path";

if (!Array.isArray(base.webServer))
  throw new Error("REQUIRED_UI_SERVICES_MISSING");
const configFile = process.env["APP_CONFIG_FILE"];
const profile = process.env["APP_PROFILE"];
if (!configFile || !profile)
  throw new Error("EXPLICIT_UI_TEST_CONFIG_REQUIRED");
export default defineConfig({
  ...base,
  projects: [{ name: "development" }],
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(root, ".local/ui-dev-results.json") }],
  ],
  webServer: base.webServer.map((service, index) =>
    index === 2
      ? {
          ...service,
          command: `node scripts/tasks.mjs dev:web --config "${configFile}" --profile ${profile}`,
        }
      : service,
  ),
});
