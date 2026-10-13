"""Real Compose config checks without starting a database or exposing secrets."""

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

from cv_foundation.settings import Component, InfrastructureSettings, Profile, load_settings

root = Path(__file__).resolve().parent.parent
fixtures = json.loads((root / "infra/config/compose.json").read_text(encoding="utf-8"))
settings = load_settings(root / "infra/config/test.json", Profile.TEST, Component.API)
results = []
for profile in ["development", "test"]:
    config = InfrastructureSettings.model_validate(fixtures[profile])
    for supplied in [False, True]:
        env = dict(os.environ)
        env.pop(config.password_environment, None)
        if supplied:
            env[config.password_environment] = secrets.token_urlsafe(32)
        # Resolved current Python, fixed repo script and enumerated arguments; no shell.
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(root / "scripts/compose.py"), "--profile", profile, "check"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.network.request_timeout_ms * 6 / 1000,
        )
        expected = 0 if supplied else 2
        if result.returncode != expected or (
            not supplied and "EXPLICIT_DEVELOPMENT_DATABASE_SECRET_REQUIRED" not in result.stderr
        ):
            raise RuntimeError("COMPOSE_CONFIGURATION_CHECK_FAILED")
        results.append(
            {
                "profile": profile,
                "secret_supplied": supplied,
                "exit_code": result.returncode,
                "expected_exit_code": expected,
            }
        )
(root / ".local").mkdir(exist_ok=True)
(root / ".local/compose-check-results.json").write_text(
    json.dumps({"checks": results, "database_runtime": "UNVERIFIED owner 03"}, indent=2) + "\n",
    encoding="utf-8",
)
print("COMPOSE_VALID_CONFIG_AND_MISSING_SECRET_CHECKS: PASS; DATABASE NOT STARTED")
