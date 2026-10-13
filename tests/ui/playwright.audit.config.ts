import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
import path from "node:path";
import { root } from "../../scripts/config.mjs";
export default defineConfig({
  ...base,
  testMatch: "audit.spec.ts",
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(root, ".local/audit-results.json") }],
  ],
});
