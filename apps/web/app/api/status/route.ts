import { publicClient } from "@cv/api-client/public";

export async function GET() {
  const origin = process.env["CV_PUBLIC_API_ORIGIN"];
  const timeout = Number(process.env["CV_REQUEST_TIMEOUT_MS"]);
  if (!origin || !Number.isSafeInteger(timeout) || timeout <= 0)
    return Response.json({ code: "CONFIGURATION_INVALID" }, { status: 503 });
  try {
    const result = await publicClient(origin, timeout).GET(
      "/public/capabilities",
    );
    if (!result.data)
      return Response.json(
        { code: "PUBLIC_SERVICE_UNAVAILABLE" },
        { status: 503 },
      );
    return Response.json(result.data, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return Response.json(
      { code: "PUBLIC_SERVICE_UNAVAILABLE" },
      { status: 503 },
    );
  }
}
