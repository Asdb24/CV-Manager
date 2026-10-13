"""Validated development/test infrastructure only; no release storage emulators."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from cv_foundation.settings import InfrastructureSettings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["development", "test"], required=True)
    parser.add_argument("action", choices=["check", "up", "stop"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    config = InfrastructureSettings.model_validate(
        json.loads((root / "infra/config/compose.json").read_text(encoding="utf-8"))[args.profile]
    )
    if config.profile != args.profile:
        parser.exit(2, "INFRASTRUCTURE_PROFILE_MISMATCH\n")
    password = os.environ.get(config.password_environment)
    if not password:
        parser.exit(2, "EXPLICIT_DEVELOPMENT_DATABASE_SECRET_REQUIRED\n")
    image = json.loads((root / "infra/postgresql-image.lock.json").read_text(encoding="utf-8"))
    docker = shutil.which("docker")
    if docker is None:
        parser.exit(2, "DOCKER_DEVELOPMENT_TOOL_REQUIRED\n")
    env = {
        **os.environ,
        "CV_COMPOSE_PROJECT": config.project,
        "CV_POSTGRES_IMAGE": f"{image['repository']}@{image['index_digest']}",
        "CV_POSTGRES_HOST": config.bind_host,
        "CV_POSTGRES_PORT": str(config.port),
        "CV_POSTGRES_DATABASE": config.database,
        "CV_POSTGRES_ROLE": config.role,
        "CV_POSTGRES_PASSWORD": password,
        "CV_POSTGRES_HEALTH_INTERVAL": f"{config.health_interval_seconds}s",
        "CV_POSTGRES_HEALTH_TIMEOUT": f"{config.health_timeout_seconds}s",
        "CV_POSTGRES_HEALTH_RETRIES": str(config.health_retries),
        "CV_POSTGRES_MEMORY_BYTES": str(config.memory_bytes),
    }
    action = {"check": ["config", "--quiet"], "up": ["up", "--detach", "--wait"], "stop": ["stop"]}[
        args.action
    ]
    # Resolved official Docker executable; action is a fixed allowlist, never shell text.
    result = subprocess.run(  # noqa: S603
        [docker, "compose", "-f", str(root / "infra/compose.yaml"), *action],
        cwd=root,
        env=env,
        check=False,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
