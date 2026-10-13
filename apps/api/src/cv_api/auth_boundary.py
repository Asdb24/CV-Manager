"""Origin, transport and bounded-body admission before private route execution."""

import asyncio

from cv_foundation.settings import Profile, Settings
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class AuthenticationBoundary:
    def __init__(self, app: ASGIApp, settings: Settings, max_bytes: int) -> None:
        self.app = app
        self.settings = settings
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        private = path.startswith(("/auth/", "/staff/"))
        public = path.startswith("/public/")
        headers = {key.lower(): value for key, value in scope["headers"]}
        origin = headers.get(b"origin", b"").decode("latin-1")
        code = None
        if private:
            allowed = (
                {self.settings.network.desktop_origin, self.settings.network.native_desktop_origin}
                if self.settings.profile in {Profile.DEVELOPMENT, Profile.TEST}
                and self.settings.realm == "local"
                else set()
            )
            # Connected staff uses the native typed HTTPS transport, never public-web CORS.
            if origin and origin not in allowed:
                code = "ORIGIN_DENIED"
            if self.settings.profile == Profile.SERVER and scope.get("scheme") != "https":
                code = "HTTPS_REQUIRED"
            if path == "/auth/v1/bootstrap" and self.settings.realm != "local":
                code = "BOOTSTRAP_DENIED"
            if b"cookie" in headers:
                code = "COOKIE_AUTH_FORBIDDEN"
        if public and (b"authorization" in headers or b"x-bootstrap-authority" in headers):
            code = "PUBLIC_AUTHORITY_ISOLATED"
        if private or public:
            if any(name in headers for name in (b"x-tenant-id", b"x-agency-id", b"x-workspace-id")):
                code = "CLIENT_SCOPE_FORBIDDEN"
        if code:
            await JSONResponse(
                {"code": code, "message": "Yêu cầu không có quyền truy cập hợp lệ."},
                status_code=403,
                headers={"Cache-Control": "no-store"},
            )(scope, receive, send)
            return
        replay = receive
        if private and scope["method"] in {"POST", "PUT", "PATCH"}:
            data = bytearray()
            deadline = (
                asyncio.get_running_loop().time() + self.settings.network.request_timeout_ms / 1000
            )
            while True:
                try:
                    message = await asyncio.wait_for(
                        receive(), max(0, deadline - asyncio.get_running_loop().time())
                    )
                except TimeoutError:
                    await JSONResponse(
                        {"code": "REQUEST_TIMEOUT", "message": "Hết thời gian nhận yêu cầu."},
                        status_code=408,
                        headers={"Cache-Control": "no-store"},
                    )(scope, receive, send)
                    return
                if message["type"] == "http.disconnect":
                    return
                data.extend(message.get("body", b""))
                if len(data) > self.max_bytes:
                    await JSONResponse(
                        {"code": "REQUEST_LIMIT", "message": "Yêu cầu vượt giới hạn kích thước."},
                        status_code=413,
                        headers={"Cache-Control": "no-store"},
                    )(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
            delivered = False

            async def body_receive() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(data), "more_body": False}
                return await receive()

            replay = body_receive

        async def guarded_send(message: Message) -> None:
            if message["type"] == "http.response.start" and (private or public):
                response_headers = list(message.get("headers", []))
                response_headers.extend(
                    [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]
                )
                message = {**message, "headers": response_headers}
            await send(message)

        await self.app(scope, replay, guarded_send)
