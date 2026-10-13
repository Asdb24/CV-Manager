// Development/build artifact fetch. Product processes never import this module.
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { root, projection } from "./config.mjs";
const args = process.argv.slice(2);
const client = projection(
  "local_ai",
  args[args.indexOf("--config") + 1],
  args[args.indexOf("--profile") + 1],
);
if (!["development", "test"].includes(client.profile))
  throw new Error("DEVELOPMENT_ARTIFACT_ACQUISITION_REQUIRED");
if (process.env.NODE_TLS_REJECT_UNAUTHORIZED === "0")
  throw new Error("TLS_VERIFICATION_REQUIRED");
const manifestBytes = await readFile(
  path.join(root, "contracts/model-manifest.json"),
);
const expected = (
  await readFile(path.join(root, "contracts/model-manifest.sha256"), "utf8")
).trim();
if (createHash("sha256").update(manifestBytes).digest("hex") !== expected)
  throw new Error("MODEL_MANIFEST_DRIFT");
const manifest = JSON.parse(manifestBytes);
const assetRoot = path.join(root, "artifacts/models");
for (const asset of manifest.assets) {
  const target = path.resolve(assetRoot, asset.path);
  if (
    !target.startsWith(assetRoot + path.sep) ||
    !asset.source.includes(`/resolve/${manifest.upstream_revision}/`)
  )
    throw new Error("PINNED_MODEL_REFERENCE_REQUIRED");
  let bytes;
  try {
    bytes = await readFile(target);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
    const response = await fetch(asset.source, {
      signal: AbortSignal.timeout(client.request_timeout_ms),
    });
    if (!response.ok) throw new Error("MODEL_ARTIFACT_DOWNLOAD_FAILED");
    bytes = Buffer.from(await response.arrayBuffer());
  }
  if (
    bytes.length !== asset.bytes ||
    createHash("sha256").update(bytes).digest("hex") !== asset.sha256
  )
    throw new Error("MODEL_ARTIFACT_INTEGRITY_FAILED");
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, bytes);
}
console.log("PINNED_MODEL_ASSETS_PRESENT_AND_VERIFIED; DEVELOPMENT/BUILD ONLY");
