import createClient from "openapi-fetch";
import type { components, paths } from "./generated/staff";

type LoginResult = components["schemas"]["LoginResult"];
export type SessionIdentity = components["schemas"]["StaffIdentity"];
export type RealmTransport = Readonly<{
  instanceId: string;
  realmKey: string;
  mode: "standalone" | "connected";
  origin: string;
  timeoutMs: number;
}>;
export type SessionTicket = Readonly<{
  generation: number;
  instanceId: string;
}>;

/** Development memory only. Native Credential Manager is owned by Phase 15. */
export class MemorySessionState {
  readonly context: RealmTransport;
  #generation = 0;
  #value: LoginResult | undefined;
  #abort = new AbortController();

  constructor(context: RealmTransport) {
    const parsed = new URL(context.origin);
    const loopback = ["127.0.0.1", "[::1]"].includes(parsed.hostname);
    if (
      parsed.origin !== context.origin ||
      parsed.username ||
      parsed.password ||
      !context.instanceId ||
      !context.realmKey ||
      !Number.isInteger(context.timeoutMs) ||
      context.timeoutMs <= 0 ||
      context.timeoutMs > 120_000 ||
      (context.mode === "connected" && parsed.protocol !== "https:") ||
      (context.mode === "standalone" &&
        (!loopback || parsed.protocol !== "http:"))
    ) {
      throw new Error("SESSION_TRANSPORT_INVALID");
    }
    this.context = Object.freeze({ ...context });
  }

  ticket(): SessionTicket {
    return Object.freeze({
      generation: this.#generation,
      instanceId: this.context.instanceId,
    });
  }

  isCurrent(ticket: SessionTicket): boolean {
    return (
      ticket.generation === this.#generation &&
      ticket.instanceId === this.context.instanceId
    );
  }

  accept(ticket: SessionTicket, result: LoginResult): boolean {
    if (
      !this.isCurrent(ticket) ||
      result.identity.instance_id !== this.context.instanceId
    )
      return false;
    const expires = Date.parse(result.identity.expires_at);
    if (!Number.isFinite(expires) || expires <= Date.now() || !result.token)
      return false;
    this.#value = structuredClone(result);
    return true;
  }

  clear(): void {
    this.#value = undefined;
    this.#generation += 1;
    this.#abort.abort();
    this.#abort = new AbortController();
  }

  identity(): SessionIdentity | undefined {
    if (
      this.#value &&
      Date.parse(this.#value.identity.expires_at) <= Date.now()
    )
      this.clear();
    return this.#value ? structuredClone(this.#value.identity) : undefined;
  }

  client() {
    return createClient<paths>({
      baseUrl: this.context.origin,
      fetch: async (request: Request) => {
        if (new URL(request.url).origin !== this.context.origin)
          throw new Error("REALM_MISMATCH");
        this.identity();
        const ticket = this.ticket();
        const headers = new Headers(request.headers);
        if (this.#value)
          headers.set("Authorization", `Bearer ${this.#value.token}`);
        const response = await fetch(request, {
          headers,
          credentials: "omit",
          redirect: "error",
          cache: "no-store",
          signal: AbortSignal.any([
            request.signal,
            this.#abort.signal,
            AbortSignal.timeout(this.context.timeoutMs),
          ]),
        });
        if (!this.isCurrent(ticket)) throw new Error("STALE_SESSION_REPLY");
        if (response.status === 401) this.clear();
        return response;
      },
    });
  }
}
