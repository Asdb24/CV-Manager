import createClient from "openapi-fetch";
import type { paths } from "./generated/staff";

export function staffClient(origin: string, timeoutMs: number) {
  return createClient<paths>({
    baseUrl: origin,
    fetch: (request: Request) =>
      fetch(request, {
        redirect: "error",
        signal: AbortSignal.any([
          request.signal,
          AbortSignal.timeout(timeoutMs),
        ]),
      }),
  });
}
