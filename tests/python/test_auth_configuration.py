import json
from pathlib import Path
from typing import Any

import pytest
from cv_api.app import create_app
from cv_foundation.auth_contracts import AuthenticationPolicy, PolicyActivate
from cv_foundation.settings import Settings
from fastapi.testclient import TestClient
from pydantic import ValidationError


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_limit", 0),
        ("session_ttl_seconds", 0),
        ("account_attempt_limit", 0),
        ("global_attempt_limit", 0),
        ("startup_ttl_seconds", 901),
        ("argon_memory_kib", 100),
        ("argon_time_cost", 1),
        ("password_min_characters", 1),
        ("hash_concurrency", 0),
        ("request_max_bytes", 0),
        ("owner", "anyone"),
    ],
)
def test_authentication_policy_rejects_unsafe_values(field: str, value: object) -> None:
    raw = json.loads(Path("infra/config/authentication-test.json").read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        AuthenticationPolicy.model_validate({**raw, field: value})
    del raw[field]
    with pytest.raises(ValidationError):
        AuthenticationPolicy.model_validate(raw)


def test_public_schema_has_no_authentication_graph() -> None:
    public = json.loads(Path("contracts/generated/public.openapi.json").read_text(encoding="utf-8"))
    serialized = json.dumps(public)
    assert all(path.startswith("/public/") for path in public["paths"])
    assert not any(
        word in serialized
        for word in [
            "LoginResult",
            "credential_hash",
            "StaffIdentity",
            "BootstrapCreate",
            "auth/v1",
            "StaffRecord",
        ]
    )


def test_request_limits_and_validation_never_echo_secrets() -> None:
    settings = Settings.model_validate_json(
        Path("infra/config/test.json").read_text(encoding="utf-8")
    )
    policy = AuthenticationPolicy.model_validate_json(
        Path(settings.dependencies.authentication_policy_file).read_text(encoding="utf-8")
    )
    with TestClient(create_app(settings)) as client:
        response = client.post("/auth/v1/login", content=b"x" * (policy.request_max_bytes + 1))
        assert response.status_code == 413
        response = client.post(
            "/auth/v1/login",
            json={"password": "SYNTHETIC secret input", "unexpected": "private payload"},
        )
        assert response.status_code == 422
        assert "SYNTHETIC" not in response.text and "private payload" not in response.text
        assert (
            client.get("/auth/v1/session", headers={"Cookie": "session=synthetic"}).status_code
            == 403
        )


def test_personal_policy_and_missing_retention_rejected() -> None:
    raw: dict[str, Any] = {
        "kind": "retention",
        "version": "synthetic-v1",
        "expires_at": "2099-01-01T00:00:00Z",
        "definition": {
            "synthetic_only": True,
            "production_approval": False,
            "clock": "database-utc",
            "description": "Synthetic fixture",
        },
    }
    with pytest.raises(ValidationError):
        PolicyActivate.model_validate(raw)
    raw["definition"]["synthetic_only"] = False
    with pytest.raises(ValidationError):
        PolicyActivate.model_validate(raw)
