import { environment } from "../../scripts/config.mjs";
const client = environment("web");
export default {
  agentRules: false,
  poweredByHeader: false,
  transpilePackages: ["@cv/ui", "@cv/api-client"],
  env: { NEXT_PUBLIC_REQUEST_TIMEOUT_MS: String(client.request_timeout_ms) },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Cache-Control", value: "no-store" },
        ],
      },
    ];
  },
};
