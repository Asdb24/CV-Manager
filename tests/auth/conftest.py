from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from cv_api.app import create_app
from cv_api.authentication import Passwords
from cv_foundation.auth_contracts import AuthenticationPolicy
from cv_foundation.settings import DatabaseTestSettings, Settings
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.types.json import Jsonb
from sqlalchemy import URL, create_engine
from sqlalchemy.pool import NullPool


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--database-config", required=True)


@dataclass(repr=False)
class AuthWorkspace:
    configuration: DatabaseTestSettings
    credentials: dict[str, str] = field(repr=False)
    settings: Settings
    client: TestClient = field(repr=False)
    instance_id: str
    startup: str = field(repr=False)
    password: str = field(repr=False)

    def connect(self, role: str = "cv_cluster_admin") -> psycopg.Connection[Any]:
        return psycopg.connect(
            host=self.configuration.host,
            port=self.configuration.port,
            dbname=self.configuration.database,
            user=role,
            password=self.credentials[role],
            connect_timeout=self.configuration.connect_timeout_seconds,
            options=f"-c statement_timeout={self.configuration.statement_timeout_ms} "
            f"-c lock_timeout={self.configuration.lock_timeout_ms}",
        )

    def bootstrap(self) -> None:
        if self.settings.realm == "server":
            policy = AuthenticationPolicy.model_validate_json(
                Path(self.settings.dependencies.authentication_policy_file).read_text(
                    encoding="utf-8"
                )
            )
            encoded = Passwords(policy).hash(self.password)
            with self.connect("cv_migrator") as connection:
                connection.execute(
                    "SELECT cv.auth_bootstrap(%s,%s,%s,%s,%s)",
                    (
                        self.instance_id,
                        self.startup,
                        "SYNTHETIC server",
                        "synthetic-admin",
                        encoded,
                    ),
                )
            return
        response = self.client.post(
            "/auth/v1/bootstrap",
            headers={"X-Bootstrap-Authority": self.startup},
            json={
                "instance_id": self.instance_id,
                "login_name": "synthetic-admin",
                "password": self.password,
                "agency_name": "SYNTHETIC authentication agency",
            },
        )
        assert response.status_code == 200, response.json().get("code")

    def login(self, login: str = "synthetic-admin", password: str | None = None) -> dict[str, Any]:
        response = self.client.post(
            "/auth/v1/login",
            json={
                "instance_id": self.instance_id,
                "login_name": login,
                "password": password or self.password,
            },
        )
        assert response.status_code == 200, response.json().get("code")
        result: dict[str, Any] = response.json()
        return result


@contextmanager
def make_workspace(
    pytestconfig: pytest.Config,
    monkeypatch: pytest.MonkeyPatch,
    realm: str,
    tmp_path: Path,
) -> Iterator[AuthWorkspace]:
    configuration = DatabaseTestSettings.model_validate_json(
        Path(pytestconfig.getoption("database_config")).read_text(encoding="utf-8")
    )
    credentials = json.loads(Path(configuration.credential_file).read_text(encoding="utf-8"))
    suffix = secrets.token_hex(8).translate(str.maketrans("0123456789", "ghijklmnop"))
    name = "cv_phase03_auth_" + suffix
    admin = psycopg.connect(
        host=configuration.host,
        port=configuration.port,
        dbname="postgres",
        user="cv_cluster_admin",
        password=credentials["cv_cluster_admin"],
        autocommit=True,
    )
    admin.execute(sql.SQL("CREATE DATABASE {} OWNER cv_migrator").format(sql.Identifier(name)))
    engine = create_engine(
        URL.create(
            "postgresql+psycopg",
            username="cv_migrator",
            password=credentials["cv_migrator"],
            host=configuration.host,
            port=configuration.port,
            database=name,
        ),
        poolclass=NullPool,
        hide_parameters=True,
    )
    try:
        with engine.begin() as connection:
            config = Config("apps/api/alembic.ini")
            config.attributes.update(connection=connection, direction="upgrade")
            command.upgrade(config, "head")
        raw = json.loads(Path("infra/config/test.json").read_text(encoding="utf-8"))
        raw["dependencies"]["database_secret_env"] = "AUTH04_DATABASE"  # noqa: S105
        raw["realm_key"] = "synthetic-auth-" + suffix
        if realm == "server":
            raw["realm"] = "server"
            raw["execution_mode"] = "connected"
            raw["profile"] = "server"
            raw["network"]["api_origin"] = "https://synthetic-api.example.invalid"
            raw["network"]["approved_server_origin"] = raw["network"]["api_origin"]
            raw["network"]["web_origin"] = "https://synthetic-jobs.example.invalid"
            raw["network"]["cors_origins"] = [
                raw["network"]["desktop_origin"],
                raw["network"]["native_desktop_origin"],
                raw["network"]["web_origin"],
            ]
            raw["dependencies"]["document_root"] = str(tmp_path / "documents")
            server_policy = json.loads(
                Path(raw["dependencies"]["authentication_policy_file"]).read_text(encoding="utf-8")
            )
            server_policy["owner"] = "server-operator"
            policy_path = tmp_path / "auth-policy.json"
            policy_path.write_text(json.dumps(server_policy), encoding="utf-8")
            raw["dependencies"]["authentication_policy_file"] = str(policy_path)
        settings = Settings.model_validate(raw)
        connection_settings = {
            "host": configuration.host,
            "port": configuration.port,
            "database": name,
            "user": "cv_runtime",
            "password": credentials["cv_runtime"],
            "sslmode": "disable",
            "sslrootcert": None,
            "connect_timeout_seconds": configuration.connect_timeout_seconds,
            "statement_timeout_ms": configuration.statement_timeout_ms,
            "lock_timeout_ms": configuration.lock_timeout_ms,
            "connection_limit": 4,
        }
        monkeypatch.setenv("AUTH04_DATABASE", json.dumps(connection_settings))
        policy = AuthenticationPolicy.model_validate_json(
            Path(settings.dependencies.authentication_policy_file).read_text(encoding="utf-8")
        )
        startup = secrets.token_urlsafe(32)
        with psycopg.connect(
            host=configuration.host,
            port=configuration.port,
            dbname=name,
            user="cv_migrator",
            password=credentials["cv_migrator"],
        ) as connection:
            row = connection.execute(
                "SELECT cv.auth_configure(%s,%s,%s,%s,%s)",
                (
                    settings.realm,
                    settings.realm_key,
                    Jsonb(policy.model_dump(mode="json")),
                    hashlib.sha256(startup.encode()).hexdigest(),
                    secrets.token_urlsafe(32),
                ),
            ).fetchone()
            assert row is not None
            instance_id = str(row[0])
        with TestClient(create_app(settings), base_url=settings.network.api_origin) as client:
            yield AuthWorkspace(
                configuration.model_copy(update={"database": name}),
                credentials,
                settings,
                client,
                instance_id,
                startup,
                secrets.token_urlsafe(32),
            )
    finally:
        engine.dispose()
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        admin.close()


@pytest.fixture
def workspace(
    pytestconfig: pytest.Config,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> Iterator[AuthWorkspace]:
    with make_workspace(
        pytestconfig, monkeypatch, getattr(request, "param", "local"), tmp_path
    ) as value:
        yield value
