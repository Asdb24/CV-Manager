import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

export const root = path.resolve(import.meta.dirname, "..");
export const python = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);

export function projection(component, configFile, profile) {
  if (!configFile || !profile)
    throw new Error("EXPLICIT_CONFIG_AND_PROFILE_REQUIRED");
  if (!existsSync(python)) throw new Error("FROZEN_PYTHON_INSTALL_REQUIRED");
  if (process.env.NODE_TLS_REJECT_UNAUTHORIZED === "0")
    throw new Error("TLS_VERIFICATION_REQUIRED");
  const result = spawnSync(
    python,
    [
      "-m",
      "cv_foundation.settings",
      "--config",
      path.resolve(root, configFile),
      "--profile",
      profile,
      "--component",
      component,
      "--client",
    ],
    { cwd: root, encoding: "utf8" },
  );
  if (result.status !== 0) throw new Error("CONFIGURATION_INVALID");
  return JSON.parse(result.stdout);
}

export function environment(component) {
  return projection(
    component,
    process.env.APP_CONFIG_FILE,
    process.env.APP_PROFILE,
  );
}
