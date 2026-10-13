import json
from pathlib import Path
from typing import Any

import pytest
from cv_api.app import create_app
from cv_foundation.ai_contract import create_contract_app
from cv_foundation.settings import (
    Component,
    Profile,
    Settings,
    client_projection,
    load_settings,
    origin_parts,
)
from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def raw_config() -> dict[str, Any]:
    raw: dict[str, Any] = json.loads((ROOT / "infra/config/test.json").read_text(encoding="utf-8"))
    return raw


@pytest.mark.parametrize("profile", [Profile.DEVELOPMENT, Profile.TEST])
@pytest.mark.parametrize("component", list(Component))
def test_explicit_valid_configuration(profile: Profile, component: Component) -> None:
    config = load_settings(ROOT / f"infra/config/{profile}.json", profile, component)
    assert config.profile == profile
    assert config.resources.ai_peak_working_set_bytes == 1610612736


@pytest.mark.parametrize(
    "field", ["profile", "realm", "execution_mode", "resources", "network", "privacy"]
)
def test_missing_required(field: str) -> None:
    raw = raw_config()
    del raw[field]
    with pytest.raises(ValidationError):
        Settings.model_validate(raw)


@pytest.mark.parametrize(
    "case",
    [
        "profile",
        "mode",
        "origin",
        "cors",
        "tls",
        "redirect",
        "memory",
        "page_size",
        "real_data",
        "port",
        "path",
    ],
)
def test_invalid_configurations(case: str) -> None:
    raw = raw_config()
    if case == "profile":
        raw["profile"] = "unknown"
    elif case == "mode":
        raw["execution_mode"] = "connected"
    elif case == "origin":
        raw["network"]["api_origin"] = "http://0.0.0.0:8237"
    elif case == "cors":
        raw["network"]["cors_origins"] = ["*"]
    elif case == "tls":
        raw["network"]["tls_verify"] = False
    elif case == "redirect":
        raw["network"]["redirect_policy"] = "follow"
    elif case == "memory":
        raw["resources"]["ai_peak_working_set_bytes"] += 1
    elif case == "page_size":
        raw["resources"]["public_page_size"] = 0
    elif case == "real_data":
        raw["privacy"]["real_onboarding_approved"] = True
    elif case == "port":
        raw["network"]["api_binding"]["port"] += 1
    elif case == "path":
        raw["network"]["api_origin"] += "/private"
    with pytest.raises(ValidationError):
        Settings.model_validate(raw)


def test_explicit_profile_not_inferred() -> None:
    with pytest.raises(ValueError, match="EXPLICIT_PROFILE_MISMATCH"):
        load_settings(ROOT / "infra/config/test.json", Profile.DEVELOPMENT, Component.API)


@pytest.mark.parametrize("profile", [Profile.STANDALONE, Profile.SERVER, Profile.CONNECTED])
@pytest.mark.parametrize("component", list(Component))
def test_release_component_matrix_and_manifest(
    tmp_path: Path, profile: Profile, component: Component
) -> None:
    raw = raw_config()
    raw["profile"] = profile
    if profile != Profile.STANDALONE:
        raw["realm"] = "server"
        raw["execution_mode"] = "connected"
        raw["network"]["api_origin"] = "https://synthetic-api.example.invalid"
        raw["network"]["approved_server_origin"] = raw["network"]["api_origin"]
        raw["network"]["web_origin"] = "https://synthetic-jobs.example.invalid"
        raw["network"]["cors_origins"] = [
            raw["network"]["desktop_origin"],
            raw["network"]["native_desktop_origin"],
            raw["network"]["web_origin"],
        ]
        # Environment-variable name only; this fixture contains no credential.
        raw["dependencies"]["database_secret_env"] = "SYNTHETIC_DATABASE_URL"  # noqa: S105
        raw["dependencies"]["document_root"] = str(tmp_path / "synthetic-documents")
    manifest = tmp_path / "release.json"
    if profile != Profile.SERVER:
        manifest.write_text(
            json.dumps(
                {
                    "manifest_version": "synthetic-v1",
                    "release_kind": "portable",
                    "owner": "native-release",
                }
            ),
            encoding="utf-8",
        )
        raw["release_manifest"] = str(manifest)
    config = tmp_path / "config.json"
    config.write_text(json.dumps(raw), encoding="utf-8")
    allowed = (
        (profile == Profile.STANDALONE and component != Component.WEB)
        or (
            profile == Profile.SERVER
            and component in {Component.WEB, Component.API, Component.WORKER}
        )
        or (profile == Profile.CONNECTED and component in {Component.DESKTOP, Component.LOCAL_AI})
    )
    if not allowed:
        with pytest.raises(ValueError, match="COMPONENT_PROFILE_INCOMPATIBLE"):
            load_settings(config, profile, component)
        return
    settings = load_settings(config, profile, component)
    assert client_projection(settings).release_kind == (
        None if profile == Profile.SERVER else "portable"
    )
    if profile != Profile.SERVER:
        manifest.write_text(
            json.dumps(
                {
                    "manifest_version": "synthetic-v1",
                    "release_kind": "installed",
                    "owner": "native-release",
                }
            ),
            encoding="utf-8",
        )
        assert (
            client_projection(load_settings(config, profile, component)).release_kind == "installed"
        )
        manifest.write_text(
            '{"manifest_version":"synthetic-v1","release_kind":"standalone","owner":"native-release"}',
            encoding="utf-8",
        )
        with pytest.raises(ValidationError):
            load_settings(config, profile, component)


@pytest.mark.parametrize(
    "case",
    [
        "zero-origin-port",
        "origin-whitespace",
        "empty-temp-path",
        "invalid-secret-name",
        "shutdown-units",
    ],
)
def test_operational_boundary_validation(case: str) -> None:
    raw = raw_config()
    if case == "zero-origin-port":
        raw["network"]["api_origin"] = "http://127.0.0.1:0"
    elif case == "origin-whitespace":
        raw["network"]["api_origin"] = " " + raw["network"]["api_origin"]
    elif case == "empty-temp-path":
        raw["dependencies"]["temporary_root"] = ""
    elif case == "invalid-secret-name":
        # Deliberately invalid environment-variable name, never an operational secret.
        raw["dependencies"]["database_secret_env"] = "ENV-NAME-INVALID"  # noqa: S105
    else:
        raw["network"]["shutdown_timeout_ms"] = 1
    with pytest.raises(ValidationError):
        Settings.model_validate(raw)


def test_projection_has_no_secret_or_private_runtime_value() -> None:
    value = client_projection(
        load_settings(ROOT / "infra/config/test.json", Profile.TEST, Component.DESKTOP)
    ).model_dump()
    assert (
        not {
            "dependencies",
            "resources",
            "database_secret_env",
            "temporary_root",
            "startup_authority",
            "privacy",
        }
        & value.keys()
    )
    assert value["release_kind"] is None


def test_public_staff_authority_and_safe_errors() -> None:
    config = load_settings(ROOT / "infra/config/test.json", Profile.TEST, Component.API)
    with TestClient(create_app(config)) as client:
        assert client.get("/live").json() == {"component": "api", "alive": True}
        unavailable = client.get("/ready")
        assert unavailable.status_code == 503
        assert unavailable.json()["ready"] is False
        assert unavailable.json()["capabilities"]["document"]["state"] == "unavailable"
        assert unavailable.json()["implemented_dependencies"] == ["database"]
        assert unavailable.json()["capabilities"]["database"]["state"] == "unavailable"
        for token in [None, "synthetic-untrusted-token"]:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            assert client.get("/staff/capabilities", headers=headers).status_code == 401
        assert client.get("/public/capabilities").json() == {
            "jobs": "unavailable",
            "applications": "unavailable",
            "code": "PUBLIC_FEATURES_NOT_IMPLEMENTED",
        }
        assert (
            client.get("/public/jobs", headers={"X-Tenant": "synthetic-agency-b"}).status_code
            == 503
        )
        bad = client.post("/public/applications", json={"cv_text": "SYNTHETIC_SECRET_TEXT"})
        assert bad.status_code == 422
        assert "SYNTHETIC_SECRET_TEXT" not in bad.text
        assert "input" not in bad.json()


def test_ai_is_schema_only_and_no_arbitrary_path_contract() -> None:
    app = create_contract_app()
    schema = app.openapi()
    dto = schema["components"]["schemas"]["AITaskRequest"]
    assert dto["additionalProperties"] is False
    assert not {"path", "process", "destination", "command"} & dto["properties"].keys()
    with TestClient(app) as client:
        assert (
            client.post(
                "/ai/tasks",
                headers={"Authorization": "Bearer synthetic-untrusted"},
                json={"path": "../anything"},
            ).status_code
            == 503
        )


def test_exact_native_origin_and_foreign_origin_denied() -> None:
    config = load_settings(ROOT / "infra/config/test.json", Profile.TEST, Component.API)
    with TestClient(create_app(config)) as client:
        allowed = client.get("/live", headers={"Origin": config.network.native_desktop_origin})
        assert (
            allowed.headers["access-control-allow-origin"] == config.network.native_desktop_origin
        )
        denied = client.get(
            "/live", headers={"Origin": "https://synthetic-foreign.example.invalid"}
        )
        assert "access-control-allow-origin" not in denied.headers


def test_unconfigured_local_tls_and_port_collision_rejected() -> None:
    raw = raw_config()
    raw["network"]["ai_origin"] = raw["network"]["ai_origin"].replace("http:", "https:")
    with pytest.raises(ValidationError, match="OWNED_LOOPBACK_REQUIRED"):
        Settings.model_validate(raw)


def test_canonical_and_ipv6_endpoint_projection() -> None:
    assert origin_parts("http://127.0.0.1") == ("http", "127.0.0.1", 80)
    assert origin_parts("http://[::1]:8127") == ("http", "::1", 8127)
    for invalid in [
        "HTTP://127.0.0.1:8127",
        "http://127.0.0.1:08127",
        "https://SYNTHETIC.example.invalid",
    ]:
        with pytest.raises(ValueError, match="CANONICAL_ORIGIN_REQUIRED"):
            origin_parts(invalid)
    raw = raw_config()
    raw["network"]["ai_origin"] = raw["network"]["worker_origin"]
    with pytest.raises(ValidationError, match="OWNED_SERVICE_PORT_COLLISION"):
        Settings.model_validate(raw)
