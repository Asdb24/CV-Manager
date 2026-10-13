import createClient from "openapi-fetch";
import type { paths } from "./generated/public";

export function publicClient(origin: string, timeoutMs: number) {
  return createClient<paths>({
    baseUrl: origin,
    fetch: (request: Request) =>
      fetch(request, {
        credentials: "omit",
        redirect: "error",
        signal: request.signal.aborted
          ? request.signal
          : AbortSignal.any([request.signal, AbortSignal.timeout(timeoutMs)]),
      }),
  });
}
