"""Trusted Phase 10 module injection contract; no fake model module or public launcher."""

import hashlib
import os
import secrets
import socket
from collections.abc import Callable
from pathlib import Path

import uvicorn
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from cv_foundation.ai_harness import (
    OwnedInputStore,
    StartupContext,
    WindowsModelModule,
    startup_context,
    validate_manifest,
)
from cv_foundation.settings import Component, Profile, Settings, origin_parts


def run_windows_model_module(
    module: WindowsModelModule,
    settings: Settings,
    asset_root: Path,
    publish_to_owner: Callable[[StartupContext, Callable[[], None]], None],
) -> None:
    """Owner calls a real Phase 10 module in-process; startup token stays on a private channel."""
    settings.for_component(Component.LOCAL_AI)
    if os.name != "nt" or settings.profile not in {Profile.DEVELOPMENT, Profile.TEST}:
        raise ValueError("WINDOWS_DEVELOPMENT_MODEL_HARNESS_REQUIRED")
    validate_manifest(Path(settings.dependencies.model_manifest), asset_root)
    _, host, port = origin_parts(settings.network.ai_origin)
    family = socket.AF_INET6 if host == "::1" else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    store: OwnedInputStore | None = None
    try:
        # Bind ownership first: a colliding launcher cannot clear a live owner's files.
        sock.bind((host, port))
        namespace = hashlib.sha256(settings.realm_key.encode("utf-8")).hexdigest()
        store = OwnedInputStore(
            Path(settings.dependencies.temporary_root) / namespace,
            settings.resources.temp_capacity_bytes,
            settings.resources.temp_expiry_seconds,
            settings.realm_key,
        )
        store.recover()
        context = startup_context(settings, store, asset_root)
        app = module.create_app(context)

        @app.middleware("http")
        async def private_startup_authority(
            request: Request, call_next: RequestResponseEndpoint
        ) -> Response:
            expected = f"Bearer {context.startup_authority}"
            if not secrets.compare_digest(
                request.headers.get("Authorization", "").encode("utf-8"), expected.encode("utf-8")
            ):
                return JSONResponse(
                    {
                        "code": "STARTUP_AUTHORITY_REQUIRED",
                        "message": "Quyền khởi động không hợp lệ.",
                    },
                    status_code=401,
                )
            return await call_next(request)

        server = uvicorn.Server(
            uvicorn.Config(
                app,
                log_level="warning",
                access_log=False,
                timeout_keep_alive=settings.network.keep_alive_seconds,
                timeout_graceful_shutdown=settings.network.shutdown_timeout_ms // 1000,
            )
        )

        def stop_owned_process() -> None:
            server.should_exit = True

        publish_to_owner(context, stop_owned_process)
        server.run(sockets=[sock])
    finally:
        sock.close()
        if store is not None:
            store.recover()
