import { spawn } from "node:child_process";
import path from "node:path";
import { projection, root } from "./config.mjs";
const args = process.argv.slice(2);
const config = args[args.indexOf("--config") + 1];
const profile = args[args.indexOf("--profile") + 1];
const client = projection("web", config, profile);
const env = {
  ...process.env,
  APP_CONFIG_FILE: path.resolve(root, config),
  APP_PROFILE: profile,
  CV_WEB_ORIGIN: client.web_origin,
  CV_PUBLIC_API_ORIGIN: client.api_origin,
  CV_REQUEST_TIMEOUT_MS: String(client.request_timeout_ms),
};
const child = spawn(
  process.execPath,
  [
    path.join(root, "node_modules/next/dist/bin/next"),
    "start",
    "--hostname",
    client.web_host,
    "--port",
    String(client.web_port),
  ],
  { cwd: path.join(root, "apps/web"), env, stdio: "inherit" },
);
child.on("exit", (code) => {
  process.exitCode = code ?? 1;
});
