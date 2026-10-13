import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from conftest import AuthWorkspace
from cv_api.app import create_app
from cv_api.authentication import Authentication
from cv_foundation.database import PersistenceError, configured_database
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb


@pytest.mark.parametrize("workspace", ["server"], indirect=True)
def test_server_operator_tls_and_origin_boundary(workspace: AuthWorkspace) -> None:
    assert workspace.client.post("/auth/v1/bootstrap", json={}).status_code == 403
    with workspace.connect("cv_runtime") as connection:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(
                "SELECT cv.auth_bootstrap(%s,%s,%s,%s,%s)",
                (workspace.instance_id, workspace.startup, "SYNTHETIC", "x", "$argon2id$v=19$fake"),
            )
    workspace.bootstrap()
    login = workspace.login()
    headers = {"Authorization": "Bearer " + login["token"]}
    assert workspace.client.get("/auth/v1/session", headers=headers).status_code == 200
    assert (
        workspace.client.get(
            "/auth/v1/session",
            headers={**headers, "Origin": workspace.settings.network.native_desktop_origin},
        ).status_code
        == 403
    )
    with TestClient(create_app(workspace.settings), base_url="http://testserver") as client:
        assert client.get("/auth/v1/session", headers=headers).status_code == 403
        assert (
            client.get(
                "/auth/v1/session", headers={**headers, "X-Forwarded-Proto": "https"}
            ).status_code
            == 403
        )


def test_policy_activation_revocation_and_purpose_grants(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    login = workspace.login()
    headers = {"Authorization": "Bearer " + login["token"], "Idempotency-Key": str(uuid4())}
    body = {
        "kind": "purpose",
        "version": "synthetic-purpose-v1",
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "definition": {
            "synthetic_only": True,
            "production_approval": False,
            "clock": "database-utc",
            "description": "SYNTHETIC recruitment review",
        },
    }
    response = workspace.client.post("/staff/v1/policies", headers=headers, json=body)
    assert response.status_code == 200, response.json().get("code")
    policy_id = response.json()["policy_id"]
    assert (
        workspace.client.post("/staff/v1/policies", headers=headers, json=body).json()
        == response.json()
    )
    grant_body = {
        "user_id": login["identity"]["user_id"],
        "purpose_id": policy_id,
        "active": True,
        "expected_revision": 0,
    }
    grant_headers = {**headers, "Idempotency-Key": str(uuid4())}
    granted = workspace.client.post(
        "/staff/v1/purpose-grants", headers=grant_headers, json=grant_body
    )
    assert granted.status_code == 200, granted.json().get("code")
    assert granted.json()["revision"] == 1
    assert (
        workspace.client.post(
            "/staff/v1/purpose-grants",
            headers={**headers, "Idempotency-Key": str(uuid4())},
            json=grant_body,
        ).status_code
        == 409
    )
    revoked = workspace.client.post(
        "/staff/v1/policies/" + policy_id + "/revoke",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={"reason": "Synthetic verification finished"},
    )
    assert revoked.status_code == 200, revoked.json().get("code")
    assert workspace.client.get("/staff/v1/policies", headers=headers).json()[0]["revoked"] is True
    assert (
        workspace.client.post(
            "/staff/v1/purpose-grants",
            headers={**headers, "Idempotency-Key": str(uuid4())},
            json={**grant_body, "expected_revision": 1},
        ).status_code
        == 401
    )


def test_instance_mixup_and_damaged_bootstrap(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    login = workspace.login()
    wrong = workspace.client.post(
        "/auth/v1/login",
        json={
            "instance_id": str(uuid4()),
            "login_name": "synthetic-admin",
            "password": workspace.password,
        },
    )
    assert wrong.status_code == 401
    with workspace.connect() as connection:
        connection.execute("UPDATE cv.staff_user SET active=false")
        connection.execute("UPDATE cv.membership SET active=false")
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={"Authorization": "Bearer " + login["token"]}
        ).status_code
        == 401
    )
    assert (
        workspace.client.post(
            "/auth/v1/bootstrap",
            headers={"X-Bootstrap-Authority": workspace.startup},
            json={
                "instance_id": workspace.instance_id,
                "login_name": "replacement",
                "password": workspace.password,
                "agency_name": "SYNTHETIC",
            },
        ).status_code
        == 401
    )
    assert workspace.client.get("/auth/v1/instance").json()["state"] == "initialized"


def test_session_cap_and_same_connection_context_isolation(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    sessions = [workspace.login() for _ in range(3)]
    denied = workspace.client.post(
        "/auth/v1/login",
        json={
            "instance_id": workspace.instance_id,
            "login_name": "synthetic-admin",
            "password": workspace.password,
        },
    )
    assert denied.status_code == 401
    with workspace.connect("cv_runtime") as connection:
        connection.execute(
            "SELECT cv.auth_bind(%s,%s)", (workspace.instance_id, sessions[0]["token"])
        )
        assert connection.execute("SELECT count(*) FROM cv.current_authority()").fetchone() == (1,)
        connection.commit()
        assert connection.execute("SELECT count(*) FROM cv.current_authority()").fetchone() == (0,)
        connection.rollback()
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(
                "SELECT cv.auth_bind(%s,%s)", (workspace.instance_id, secrets.token_urlsafe(32))
            )
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM cv.current_authority()").fetchone() == (0,)


def test_final_expiry_rolls_back_staff_write(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    session = workspace.login()
    auth = Authentication(configured_database(workspace.settings), workspace.settings)
    encoded = auth.passwords.hash(workspace.password)
    with workspace.connect() as connection:
        connection.execute(
            "UPDATE cv.staff_session SET expires_at=clock_timestamp()+interval '0.5 seconds' "
            "WHERE id=%s",
            (session["identity"]["session_id"],),
        )
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with auth.staff(session["token"]) as tx:
            tx.execute(
                "SELECT cv.auth_staff_write(%s,%s,%s,%s)",
                (
                    "staff-create",
                    uuid4(),
                    "f" * 64,
                    Jsonb(
                        {
                            "login_name": "will-rollback",
                            "role": "recruiter",
                            "credential_hash": encoded,
                        }
                    ),
                ),
            )
            tx.validate_constraints()
            tx.execute("SELECT pg_sleep(0.6)")
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.staff_user").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM cv.auth_command").fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM cv.auth_audit WHERE action='staff-create'"
        ).fetchone() == (0,)
