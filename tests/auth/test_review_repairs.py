import json
import secrets
import time
from uuid import uuid4

import pytest
from conftest import AuthWorkspace
from cv_api.authentication import Passwords


def test_rejected_login_reservations_skip_argon2(
    workspace: AuthWorkspace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace.bootstrap()
    calls: list[bool] = []
    original = Passwords.verify

    def observed(self: Passwords, encoded: str | None, value: str) -> bool:
        calls.append(encoded is None)
        return original(self, encoded, value)

    monkeypatch.setattr(Passwords, "verify", observed)
    for login in ("synthetic-admin", "synthetic-absent"):
        before = len(calls)
        for _ in range(6):
            response = workspace.client.post(
                "/auth/v1/login",
                json={
                    "instance_id": workspace.instance_id,
                    "login_name": login,
                    "password": "Wrong synthetic password",
                },
            )
            assert response.status_code == 401
            assert response.json()["code"] == "AUTH_DENIED"
        # Five admitted attempts include actual Argon2; the sixth reservation is refused.
        assert len(calls) - before == 5
    assert calls.count(True) == 5  # Unknown admitted users retain dummy verification.
    with workspace.connect() as connection:
        connection.execute(
            "UPDATE cv.auth_installation SET attempts=(policy->>'global_attempt_limit')::integer"
        )
    before = len(calls)
    denied = workspace.client.post(
        "/auth/v1/login",
        json={
            "instance_id": workspace.instance_id,
            "login_name": "different-unknown",
            "password": workspace.password,
        },
    )
    assert denied.status_code == 401 and len(calls) == before
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.staff_session").fetchone() == (0,)
        assert connection.execute("SELECT max(attempts) FROM cv.auth_attempt").fetchone() == (5,)


def test_global_rejections_leave_current_staff_session_usable(
    workspace: AuthWorkspace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace.bootstrap()
    session = workspace.login()
    calls: list[bool] = []
    original = Passwords.verify

    def observed(self: Passwords, encoded: str | None, value: str) -> bool:
        calls.append(True)
        return original(self, encoded, value)

    monkeypatch.setattr(Passwords, "verify", observed)
    with workspace.connect() as connection:
        connection.execute(
            "UPDATE cv.auth_installation SET attempts=(policy->>'global_attempt_limit')::integer"
        )
    for _ in range(3):
        assert (
            workspace.client.post(
                "/auth/v1/login",
                json={
                    "instance_id": workspace.instance_id,
                    "login_name": "synthetic-unknown",
                    "password": workspace.password,
                },
            ).status_code
            == 401
        )
    current = workspace.client.get(
        "/auth/v1/session", headers={"Authorization": "Bearer " + session["token"]}
    )
    assert current.status_code == 200 and current.json() == session["identity"]
    assert calls == []


def test_bootstrap_rechecks_expiry_after_actual_hash(
    workspace: AuthWorkspace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with workspace.connect() as connection:
        connection.execute(
            "UPDATE cv.auth_installation "
            "SET startup_expires_at=clock_timestamp()+interval '0.5 seconds'"
        )
    original = Passwords.hash

    def delayed(self: Passwords, value: str) -> str:
        result = original(self, value)  # Genuine Argon2, then controlled elapsed time.
        time.sleep(0.6)
        return result

    monkeypatch.setattr(Passwords, "hash", delayed)
    response = workspace.client.post(
        "/auth/v1/bootstrap",
        headers={"X-Bootstrap-Authority": workspace.startup},
        json={
            "instance_id": workspace.instance_id,
            "login_name": "synthetic-admin",
            "password": workspace.password,
            "agency_name": "SYNTHETIC delayed bootstrap",
        },
    )
    assert response.status_code == 401
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.agency").fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM cv.auth_audit").fetchone() == (0,)
    assert workspace.client.get("/auth/v1/instance").json()["state"] == "new"


@pytest.mark.parametrize("reason", ["forged", "expired", "foreign", "closed"])
def test_bootstrap_denial_precedes_password_hash(
    workspace: AuthWorkspace,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    if reason == "closed":
        workspace.bootstrap()
    if reason == "expired":
        with workspace.connect() as connection:
            connection.execute(
                "UPDATE cv.auth_installation "
                "SET startup_expires_at=clock_timestamp()-interval '1 second'"
            )
    calls: list[bool] = []
    original = Passwords.hash

    def observed(self: Passwords, value: str) -> str:
        calls.append(True)
        return original(self, value)

    monkeypatch.setattr(Passwords, "hash", observed)
    response = workspace.client.post(
        "/auth/v1/bootstrap",
        headers={
            "X-Bootstrap-Authority": secrets.token_urlsafe(32)
            if reason == "forged"
            else workspace.startup
        },
        json={
            "instance_id": str(uuid4()) if reason == "foreign" else workspace.instance_id,
            "login_name": "synthetic-admin",
            "password": workspace.password,
            "agency_name": "SYNTHETIC authority admission",
        },
    )
    assert response.status_code == 401 and calls == []
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.staff_user").fetchone() == (
            1 if reason == "closed" else 0,
        )


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_invalid_unicode_passwords_have_safe_validation_errors(
    workspace: AuthWorkspace,
    surrogate: str,
) -> None:
    malformed = "Synthetic password " + surrogate
    bootstrap_body = {
        "instance_id": workspace.instance_id,
        "login_name": "synthetic-admin",
        "password": malformed,
        "agency_name": "SYNTHETIC unicode",
    }
    response = workspace.client.post(
        "/auth/v1/bootstrap",
        headers={"Content-Type": "application/json", "X-Bootstrap-Authority": "forged"},
        content=json.dumps(bootstrap_body, ensure_ascii=True).encode("ascii"),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INPUT_INVALID"
    assert "password" not in response.text
    workspace.bootstrap()
    session = workspace.login()
    for path, body in [
        (
            "/auth/v1/login",
            {
                "instance_id": workspace.instance_id,
                "login_name": "synthetic-admin",
                "password": malformed,
            },
        ),
        (
            "/staff/v1/users",
            {"login_name": "synthetic-second", "password": malformed, "role": "recruiter"},
        ),
    ]:
        response = workspace.client.post(
            path,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + session["token"],
                "Idempotency-Key": str(uuid4()),
            },
            content=json.dumps(body, ensure_ascii=True).encode("ascii"),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "INPUT_INVALID"
        assert "password" not in response.text


def test_valid_vietnamese_and_unicode_password_remains_accepted(workspace: AuthWorkspace) -> None:
    workspace.password = "Mật khẩu tuyển dụng tổng hợp thử nghiệm 🌱" + secrets.token_urlsafe(8)
    workspace.bootstrap()
    session = workspace.login()
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={"Authorization": "Bearer " + session["token"]}
        ).status_code
        == 200
    )
