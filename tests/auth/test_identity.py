from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from conftest import AuthWorkspace


def test_bootstrap_login_logout_and_argon2(workspace: AuthWorkspace) -> None:
    assert workspace.client.get("/auth/v1/instance").json()["state"] == "new"
    workspace.bootstrap()
    assert workspace.client.get("/auth/v1/instance").json()["state"] == "initialized"
    with workspace.connect() as connection:
        encoded = connection.execute("SELECT credential_hash FROM cv.staff_user").fetchone()
        assert encoded and encoded[0].startswith("$argon2id$v=19$")
    login = workspace.login()
    headers = {"Authorization": "Bearer " + login["token"]}
    result = workspace.client.get("/auth/v1/session", headers=headers)
    assert result.status_code == 200
    assert result.json() == login["identity"]
    assert result.headers["cache-control"] == "no-store"
    assert workspace.client.post("/auth/v1/logout", headers=headers).status_code == 200
    assert workspace.client.get("/auth/v1/session", headers=headers).status_code == 401
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.auth_audit").fetchone() == (3,)


def test_bootstrap_race_and_no_reentry(workspace: AuthWorkspace) -> None:
    def attempt() -> int:
        return workspace.client.post(
            "/auth/v1/bootstrap",
            headers={"X-Bootstrap-Authority": workspace.startup},
            json={
                "instance_id": workspace.instance_id,
                "login_name": "synthetic-admin",
                "password": workspace.password,
                "agency_name": "SYNTHETIC race",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [200, 401]
    assert attempt() == 401
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.agency").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM cv.membership").fetchone() == (1,)


def test_wrong_absent_forged_and_attempt_limits(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    for login in ["missing-user", "synthetic-admin"]:
        responses = []
        for _ in range(6):
            response = workspace.client.post(
                "/auth/v1/login",
                json={
                    "instance_id": workspace.instance_id,
                    "login_name": login,
                    "password": "wrong synthetic password",
                },
            )
            responses.append((response.status_code, response.json()))
        assert all(status == 401 for status, _ in responses)
        assert all(body == responses[0][1] for _, body in responses)
    denied = workspace.client.post(
        "/auth/v1/login",
        json={
            "instance_id": workspace.instance_id,
            "login_name": "synthetic-admin",
            "password": workspace.password,
        },
    )
    assert denied.status_code == 401
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={"Authorization": "Bearer forged"}
        ).status_code
        == 401
    )
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.staff_session").fetchone() == (0,)
        assert connection.execute("SELECT max(attempts) FROM cv.auth_attempt").fetchone() == (5,)


def test_staff_administration_and_idempotency(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    admin = workspace.login()
    headers = {"Authorization": "Bearer " + admin["token"], "Idempotency-Key": str(uuid4())}
    body = {
        "login_name": "synthetic-recruiter",
        "password": workspace.password,
        "role": "recruiter",
    }
    created = workspace.client.post("/staff/v1/users", headers=headers, json=body)
    assert created.status_code == 200, created.json().get("code")
    assert (
        workspace.client.post("/staff/v1/users", headers=headers, json=body).json()
        == created.json()
    )
    assert (
        workspace.client.post(
            "/staff/v1/users", headers=headers, json={**body, "role": "admin"}
        ).status_code
        == 409
    )
    recruiter = workspace.login("synthetic-recruiter")
    recruiter_headers = {
        "Authorization": "Bearer " + recruiter["token"],
        "Idempotency-Key": str(uuid4()),
    }
    assert workspace.client.get("/staff/v1/users", headers=recruiter_headers).status_code == 401
    assert (
        workspace.client.post("/staff/v1/users", headers=recruiter_headers, json=body).status_code
        == 401
    )
    update_headers = {**headers, "Idempotency-Key": str(uuid4())}
    update = workspace.client.post(
        "/staff/v1/users/" + created.json()["user_id"],
        headers=update_headers,
        json={"expected_revision": 1, "role": "recruiter", "active": False},
    )
    assert update.status_code == 200, update.json().get("code")
    assert workspace.client.get("/auth/v1/session", headers=recruiter_headers).status_code == 401
    assert (
        workspace.client.post(
            "/staff/v1/users/" + str(uuid4()),
            headers={**headers, "Idempotency-Key": str(uuid4())},
            json={"expected_revision": 1, "role": "admin", "active": True},
        ).status_code
        == 401
    )


def test_expiry_revocation_and_public_isolation(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    first, second = workspace.login(), workspace.login()
    headers = {"Authorization": "Bearer " + first["token"]}
    second_headers = {"Authorization": "Bearer " + second["token"]}
    assert (
        workspace.client.post(
            "/auth/v1/revoke",
            headers=headers,
            json={"session_id": second["identity"]["session_id"]},
        ).status_code
        == 200
    )
    assert workspace.client.get("/auth/v1/session", headers=second_headers).status_code == 401
    assert workspace.client.get("/public/jobs", headers=headers).status_code == 403
    assert workspace.client.get("/staff/v1/users").status_code == 401
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={**headers, "X-Tenant-Id": str(uuid4())}
        ).status_code
        == 403
    )
    assert (
        workspace.client.get(
            "/auth/v1/session", headers={**headers, "Origin": workspace.settings.network.web_origin}
        ).status_code
        == 403
    )
    with workspace.connect() as connection:
        # Keep the schema's expires-after-created invariant while modeling a past session.
        connection.execute(
            "UPDATE cv.staff_session SET created_at=clock_timestamp()-interval '2 hours',"
            "expires_at=clock_timestamp()-interval '1 hour' WHERE id=%s",
            (first["identity"]["session_id"],),
        )
    assert workspace.client.get("/auth/v1/session", headers=headers).status_code == 401
