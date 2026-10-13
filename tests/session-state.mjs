import assert from "node:assert/strict";
import { MemorySessionState } from "../packages/api-client/src/session.ts";

const context = {
  instanceId: "synthetic-instance-a",
  realmKey: "synthetic-workspace-a",
  mode: "standalone",
  origin: "http://127.0.0.1:8237",
  timeoutMs: 1000,
};
const result = {
  token: "synthetic-test-token-not-a-real-session",
  identity: {
    instance_id: context.instanceId,
    tenant_id: "synthetic-tenant",
    user_id: "synthetic-user",
    session_id: "synthetic-session",
    login_name: "synthetic-user",
    role: "recruiter",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  },
};
const state = new MemorySessionState(context);
const old = state.ticket();
assert.equal(state.accept(old, result), true);
result.token = "changed-caller-copy";
assert.equal(state.identity().user_id, "synthetic-user");
const identity = state.identity();
identity.user_id = "changed";
assert.equal(state.identity().user_id, "synthetic-user");
state.clear();
assert.equal(state.accept(old, result), false);
assert.equal(state.identity(), undefined);
assert.equal(
  state.accept(state.ticket(), {
    ...result,
    identity: { ...result.identity, instance_id: "foreign" },
  }),
  false,
);
assert.equal(
  state.accept(state.ticket(), {
    ...result,
    identity: { ...result.identity, expires_at: "invalid" },
  }),
  false,
);
assert.equal(
  state.accept(state.ticket(), {
    ...result,
    identity: { ...result.identity, expires_at: new Date(0).toISOString() },
  }),
  false,
);
assert.throws(
  () => new MemorySessionState({ ...context, mode: "connected" }),
  /SESSION_TRANSPORT_INVALID/,
);
assert.throws(
  () =>
    new MemorySessionState({ ...context, origin: "http://foreign.invalid" }),
  /SESSION_TRANSPORT_INVALID/,
);
assert.throws(
  () =>
    new MemorySessionState({
      ...context,
      origin: "http://127.0.0.1:8237/path",
    }),
  /SESSION_TRANSPORT_INVALID/,
);
const server = new MemorySessionState({
  ...context,
  instanceId: "synthetic-server",
  mode: "connected",
  origin: "https://synthetic.example.invalid",
});
assert.equal(server.accept(old, result), false);
assert.equal(server.identity(), undefined);
console.log(
  "MEMORY_SESSION_REALM_EXPIRY_AND_STALE_REPLY_CONTRACT: PASS (no native keyring claim)",
);
