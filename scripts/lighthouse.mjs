import lighthouse from "lighthouse";
import { launch } from "chrome-launcher";
import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { projection, root } from "./config.mjs";

const args = process.argv.slice(2);
const config = args[args.indexOf("--config") + 1];
const profile = args[args.indexOf("--profile") + 1];
const kind = args[args.indexOf("--kind") + 1];
if (!["desktop", "public"].includes(kind))
  throw new Error("EXPLICIT_AUDIT_COMPONENT_REQUIRED");
const client = projection(
  kind === "desktop" ? "desktop" : "web",
  config,
  profile,
);
// Use the exact headless executable actually launched by pinned Playwright;
// the separate full-Chrome executable cannot spawn on this host.
const inspectedBrowser = await chromium.launchServer({ headless: true });
const chromePath = inspectedBrowser.process().spawnfile;
await inspectedBrowser.close();
if (!path.isAbsolute(chromePath))
  throw new Error("QUALIFIED_BROWSER_EXECUTABLE_REQUIRED");
const chrome = await launch({
  chromePath,
  chromeFlags: ["--headless"],
});
try {
  const result = await lighthouse(
    kind === "desktop" ? client.desktop_origin : client.web_origin,
    {
      port: chrome.port,
      logLevel: "error",
      output: "json",
      onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
      formFactor: kind === "desktop" ? "desktop" : "mobile",
      screenEmulation: {
        mobile: kind === "public",
        width: kind === "desktop" ? 1280 : 390,
        height: kind === "desktop" ? 800 : 844,
        deviceScaleFactor: 1,
        disabled: false,
      },
      throttlingMethod: "provided",
      maxWaitForLoad: client.request_timeout_ms * 6,
    },
  );
  if (!result || result.lhr.runtimeError)
    throw new Error("LIGHTHOUSE_RUNTIME_FAILED");
  const directory = path.join(root, ".local/lighthouse");
  mkdirSync(directory, { recursive: true });
  writeFileSync(
    path.join(directory, `${kind}.json`),
    JSON.stringify(result.lhr, null, 2),
  );
  const failedAccessibility = result.lhr.categories.accessibility.auditRefs
    .filter((ref) => ref.weight > 0 && result.lhr.audits[ref.id].score === 0)
    .map((ref) => ref.id);
  const summary = {
    kind,
    at: result.lhr.fetchTime,
    lighthouseVersion: result.lhr.lighthouseVersion,
    browser: result.lhr.environment.hostUserAgent,
    scores: Object.fromEntries(
      Object.entries(result.lhr.categories).map(([key, value]) => [
        key,
        value.score,
      ]),
    ),
    failedAccessibility,
    limits:
      "Developer shell and this host only; not product performance or complete accessibility qualification",
  };
  writeFileSync(
    path.join(directory, `${kind}-summary.json`),
    JSON.stringify(summary, null, 2),
  );
  console.log(JSON.stringify(summary));
  if (failedAccessibility.length) process.exitCode = 1;
} finally {
  chrome.kill();
}
