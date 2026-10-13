import createClient from "openapi-fetch";
import type { paths } from "./generated/local-ai";

export function localAITransport(
  ownedOrigin: string,
  startupAuthority: string,
  timeoutMs: number,
) {
  const parsed = new URL(ownedOrigin);
  if (
    !["127.0.0.1", "[::1]"].includes(parsed.hostname) ||
    parsed.protocol !== "http:" ||
    !startupAuthority
  )
    throw new Error("OWNED_AI_STARTUP_CONTEXT_REQUIRED");
  return createClient<paths>({
    baseUrl: ownedOrigin,
    headers: { Authorization: `Bearer ${startupAuthority}` },
    fetch: (request: Request) =>
      fetch(request, {
        credentials: "omit",
        redirect: "error",
        signal: AbortSignal.any([
          request.signal,
          AbortSignal.timeout(timeoutMs),
        ]),
      }),
  });
}
