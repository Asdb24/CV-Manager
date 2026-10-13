"""Strict binding and owner-only stdin shutdown for development API/worker processes."""

import argparse
import socket
import sys
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from cv_foundation.settings import Component, Profile, Settings, load_settings


def serve(app: FastAPI, settings: Settings, component: Component, owned_stdio: bool) -> None:
    binding = (
        settings.network.api_binding
        if component == Component.API
        else settings.network.worker_binding
    )
    family = socket.AF_INET6 if binding.host == "::1" else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        # Bind once without reuse or a replacement port. The same owned socket reaches uvicorn.
        sock.bind((binding.host, binding.port))
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host=binding.host,
                port=binding.port,
                log_level="warning",
                access_log=False,
                proxy_headers=False,
                timeout_keep_alive=settings.network.keep_alive_seconds,
                timeout_graceful_shutdown=settings.network.shutdown_timeout_ms // 1000,
            )
        )
        if owned_stdio:

            def watch_owner() -> None:
                command = sys.stdin.readline()
                if command == "STOP\n" or command == "":
                    server.should_exit = True

            threading.Thread(target=watch_owner, daemon=True).start()
        server.run(sockets=[sock])
    finally:
        sock.close()


def arguments(component: Component) -> tuple[Settings, bool]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", type=Profile, required=True)
    parser.add_argument("--owned-stdio", action="store_true")
    args = parser.parse_args()
    try:
        settings = load_settings(args.config, args.profile, component)
    except (ValueError, OSError):
        parser.exit(2, "CONFIGURATION_INVALID\n")
    if settings.profile not in {Profile.DEVELOPMENT, Profile.TEST}:
        parser.exit(2, "NATIVE_OR_SERVER_RUNTIME_NOT_QUALIFIED_IN_PHASE_02\n")
    return settings, args.owned_stdio
