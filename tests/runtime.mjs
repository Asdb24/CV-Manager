import { spawn } from "node:child_process";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { once } from "node:events";
import { setTimeout as delay } from "node:timers/promises";
import { python, root, projection } from "../scripts/config.mjs";

const results = [];
for (const profile of ["development", "test"]) {
  const configFile = `infra/config/${profile}.json`;
  projection("api", configFile, profile);
  const settings = JSON.parse(await readFile(configFile, "utf8"));
  const processes = [];
  try {
    for (const component of ["api", "worker"]) {
      const child = spawn(
        python,
        [
          "-m",
          `cv_${component}`,
          "--config",
          configFile,
          "--profile",
          profile,
          "--owned-stdio",
        ],
        { cwd: root, stdio: ["pipe", "pipe", "pipe"] },
      );
      const output = [];
      child.stderr.on("data", (data) => {
        output.push(data.toString());
      });
      processes.push({ child, component, output });
      const origin = settings.network[`${component}_origin`];
      const deadline = Date.now() + settings.network.request_timeout_ms;
      let live;
      while (Date.now() < deadline && child.exitCode === null) {
        try {
          live = await fetch(`${origin}/live`, {
            signal: AbortSignal.timeout(settings.network.request_timeout_ms),
          });
          break;
        } catch {
          await delay(settings.network.request_timeout_ms / 100);
        }
      }
      if (!live?.ok || !(await live.json()).alive)
        throw new Error(`${component}: REAL_LIVENESS_FAILED`);
      const ready = await fetch(`${origin}/ready`);
      const status = await ready.json();
      if (
        ready.status !== 503 ||
        status.ready ||
        JSON.stringify(status.implemented_dependencies) !== '["database"]' ||
        status.capabilities.database.state !== "unavailable" ||
        status.capabilities.document.state !== "unavailable"
      )
        throw new Error("FALSE_DEPENDENCY_READINESS");
      const collision = spawn(
        python,
        [
          "-m",
          `cv_${component}`,
          "--config",
          configFile,
          "--profile",
          profile,
          "--owned-stdio",
        ],
        { cwd: root, stdio: ["pipe", "pipe", "pipe"] },
      );
      let collisionOutput = "";
      collision.stderr.on("data", (data) => {
        collisionOutput += data.toString();
      });
      const collisionExit = await Promise.race([
        once(collision, "exit"),
        delay(settings.network.shutdown_timeout_ms).then(() => {
          throw new Error("STRICT_PORT_NOT_FAILED");
        }),
      ]);
      if (
        collisionExit[0] === 0 ||
        !collisionOutput.includes("OWNED_PORT_UNAVAILABLE")
      )
        throw new Error("STRICT_PORT_NOT_FAILED");
      results.push({
        profile,
        component,
        pid: child.pid,
        liveness: "PASS",
        readiness: "503_UNAVAILABLE",
        strictPort: "PASS",
      });
    }
  } finally {
    for (const { child, component } of processes) {
      if (child.exitCode === null) child.stdin.end("STOP\n");
      const exited =
        child.exitCode !== null
          ? [child.exitCode]
          : await Promise.race([
              once(child, "exit"),
              delay(settings.network.shutdown_timeout_ms).then(() => {
                throw new Error("OWNED_SHUTDOWN_TIMEOUT");
              }),
            ]);
      if (exited[0] !== 0) throw new Error("OWNED_PROCESS_EXIT_FAILED");
      let closed = false;
      try {
        await fetch(`${settings.network[`${component}_origin`]}/live`, {
          signal: AbortSignal.timeout(settings.network.request_timeout_ms),
        });
      } catch {
        closed = true;
      }
      if (!closed) throw new Error("OWNED_PORT_LEFT_OPEN");
      const record = results.find(
        (x) => x.profile === profile && x.component === component,
      );
      if (record) record.shutdown = "PASS";
    }
  }
}
await mkdir(".local", { recursive: true });
await writeFile(
  ".local/runtime-check-results.json",
  JSON.stringify(
    {
      actualProcesses: results,
      databaseImplementation: "UNVERIFIED owner 03",
      documentAndAI: "UNAVAILABLE, no fake processing",
    },
    null,
    2,
  ) + "\n",
);
console.log(
  "REAL API/WORKER START, UNAVAILABLE READINESS, STRICT PORT AND OWNED STOP: PASS",
);
