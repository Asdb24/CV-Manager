import json
import secrets
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
import uvicorn
from conftest import AuthWorkspace, make_workspace
from cv_api.app import create_app
from cv_api.operator import main as operator_main
from cv_foundation.settings import DatabaseConnectionSettings
from fastapi.testclient import TestClient
from pydantic import SecretStr


def test_separate_server_and_workspace_reject_credentials_and_proofs(
    workspace: AuthWorkspace,
    pytestconfig: pytest.Config,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace.bootstrap()
    local = workspace.login()
    with make_workspace(pytestconfig, monkeypatch, "server", tmp_path) as server:
        server.bootstrap()
        remote = server.login()
        for target, foreign, password in [
            (server, local, workspace.password),
            (workspace, remote, server.password),
        ]:
            assert (
                target.client.get(
                    "/auth/v1/session", headers={"Authorization": "Bearer " + foreign["token"]}
                ).status_code
                == 401
            )
            assert (
                target.client.post(
                    "/auth/v1/login",
                    json={
                        "instance_id": target.instance_id,
                        "login_name": "synthetic-admin",
                        "password": password,
                    },
                ).status_code
                == 401
            )
        assert (
            server.client.post(
                "/auth/v1/bootstrap", headers={"X-Bootstrap-Authority": workspace.startup}, json={}
            ).status_code
            == 403
        )


@pytest.mark.parametrize("expired", [False, True])
def test_bootstrap_invalid_authority_cannot_create_account(
    workspace: AuthWorkspace, expired: bool
) -> None:
    if expired:
        with workspace.connect() as connection:
            connection.execute(
                "UPDATE cv.auth_installation "
                "SET startup_expires_at=clock_timestamp()-interval '1 second'"
            )
    response = workspace.client.post(
        "/auth/v1/bootstrap",
        headers={
            "X-Bootstrap-Authority": workspace.startup if expired else secrets.token_urlsafe(32)
        },
        json={
            "instance_id": workspace.instance_id,
            "login_name": "synthetic-admin",
            "password": workspace.password,
            "agency_name": "SYNTHETIC",
        },
    )
    assert response.status_code == 401
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.staff_user").fetchone() == (0,)
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={"Authorization": "Bearer " + workspace.startup}
        ).status_code
        == 401
    )


def test_attempts_are_shared_across_instances_and_restart(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    body = {
        "instance_id": workspace.instance_id,
        "login_name": "synthetic-admin",
        "password": "Wrong synthetic password",
    }
    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(
            pool.map(
                lambda _: workspace.client.post("/auth/v1/login", json=body).status_code, range(6)
            )
        )
    assert statuses == [401] * 6
    with TestClient(create_app(workspace.settings)) as restarted:
        assert (
            restarted.post(
                "/auth/v1/login", json={**body, "password": workspace.password}
            ).status_code
            == 401
        )
    with workspace.connect() as connection:
        assert connection.execute("SELECT attempts FROM cv.auth_attempt").fetchone() == (5,)
        connection.execute(
            "UPDATE cv.auth_installation SET window_started=clock_timestamp()-interval '2 minutes'"
        )
        connection.execute(
            "UPDATE cv.auth_attempt SET window_started=clock_timestamp()-interval '2 minutes'"
        )
    assert workspace.login()["identity"]["role"] == "admin"


def test_self_escalation_foreign_scope_and_public_database_grants(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    admin = workspace.login()
    headers = {"Authorization": "Bearer " + admin["token"], "Idempotency-Key": str(uuid4())}
    assert (
        workspace.client.post(
            "/staff/v1/users/" + admin["identity"]["user_id"],
            headers=headers,
            json={"expected_revision": 1, "role": "recruiter", "active": False},
        ).status_code
        == 401
    )
    created = workspace.client.post(
        "/staff/v1/users",
        headers=headers,
        json={
            "login_name": "synthetic-second",
            "password": workspace.password,
            "role": "recruiter",
        },
    ).json()
    second = workspace.login("synthetic-second")
    denied_headers = {"Authorization": "Bearer " + second["token"], "Idempotency-Key": str(uuid4())}
    assert (
        workspace.client.post(
            "/staff/v1/users/" + created["user_id"],
            headers=denied_headers,
            json={"expected_revision": 1, "role": "admin", "active": True},
        ).status_code
        == 401
    )
    assert (
        workspace.client.post(
            "/auth/v1/revoke",
            headers=denied_headers,
            json={"session_id": admin["identity"]["session_id"]},
        ).status_code
        == 401
    )
    assert workspace.client.get("/staff/v1/policies", headers=denied_headers).status_code == 401
    with workspace.connect("cv_public") as connection:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("SELECT cv.auth_current()")
        connection.rollback()
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("SELECT * FROM cv.staff_user")


def test_real_operator_entrypoint_and_http_socket(
    workspace: AuthWorkspace,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Only terminal prompting is substituted; the entrypoint executes real operator SQL.
    endpoint = DatabaseConnectionSettings(
        host=workspace.configuration.host,
        port=workspace.configuration.port,
        database=workspace.configuration.database,
        user="cv_runtime",
        password=SecretStr(workspace.credentials["cv_migrator"]),
        sslmode="disable",
        sslrootcert=None,
        connect_timeout_seconds=workspace.configuration.connect_timeout_seconds,
        statement_timeout_ms=workspace.configuration.statement_timeout_ms,
        lock_timeout_ms=workspace.configuration.lock_timeout_ms,
        connection_limit=1,
    )
    operator_secret = endpoint.model_dump(mode="json")
    operator_secret.update(user="cv_migrator", password=workspace.credentials["cv_migrator"])
    monkeypatch.setenv("SYNTHETIC_OPERATOR_SECRET", json.dumps(operator_secret))
    config_file = tmp_path / "runtime.json"
    config_file.write_text(workspace.settings.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "operator",
            "--config",
            str(config_file),
            "--profile",
            "test",
            "--operator-secret-env",
            "SYNTHETIC_OPERATOR_SECRET",
            "--agency",
            "SYNTHETIC operator agency",
            "--login",
            "synthetic-admin",
        ],
    )
    monkeypatch.setattr("getpass.getpass", lambda _prompt: workspace.password)
    operator_main()
    output = capsys.readouterr()
    assert "BOOTSTRAP_COMMITTED" in output.out
    assert workspace.password not in output.out + output.err
    with pytest.raises(SystemExit) as refused:
        operator_main()
    assert refused.value.code == 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((workspace.settings.network.api_binding.host, 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(workspace.settings),
            log_level="critical",
            access_log=False,
            proxy_headers=False,
        )
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + workspace.settings.network.request_timeout_ms / 1000
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started
        with httpx.Client(
            base_url=f"http://{workspace.settings.network.api_binding.host}:{port}",
            timeout=workspace.settings.network.request_timeout_ms / 1000,
            trust_env=False,
        ) as client:
            logged = client.post(
                "/auth/v1/login",
                json={
                    "instance_id": workspace.instance_id,
                    "login_name": "synthetic-admin",
                    "password": workspace.password,
                },
            )
            assert logged.status_code == 200
            headers = {"Authorization": "Bearer " + logged.json()["token"]}
            assert client.get("/auth/v1/session", headers=headers).status_code == 200
            assert client.post("/auth/v1/logout", headers=headers).status_code == 200
            assert client.get("/auth/v1/session", headers=headers).status_code == 401
    finally:
        server.should_exit = True
        thread.join(workspace.settings.network.shutdown_timeout_ms / 1000)
        sock.close()
        assert not thread.is_alive()
