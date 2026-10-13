import json
from pathlib import Path
from typing import Any

import pytest
from cv_api.app import create_app
from cv_foundation.database import Database, PersistenceError, configured_database
from cv_foundation.settings import DatabaseConnectionSettings, Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr

from .conftest import connect, identity


def configuration(db_config: Any, passwords: dict[str, str]) -> DatabaseConnectionSettings:
    return DatabaseConnectionSettings(
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        user="cv_runtime",
        password=SecretStr(passwords["cv_runtime"]),
        sslmode="disable",
        sslrootcert=None,
        connect_timeout_seconds=db_config.connect_timeout_seconds,
        statement_timeout_ms=db_config.statement_timeout_ms,
        lock_timeout_ms=db_config.lock_timeout_ms,
        connection_limit=2,
    )


def test_adapter_actual_database_and_safe_failure(
    db_config: Any, passwords: dict[str, str]
) -> None:
    db = Database(configuration(db_config, passwords))
    assert db.ready()
    with db.staff_transaction("a/admin/proof") as connection:
        assert connection.execute("SELECT DISTINCT tenant_id FROM cv.company").fetchall() == [
            (identity("a"),)
        ]
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with db.staff_transaction("wrong-proof"):
            pytest.fail("invalid session admitted")
    with connect(db_config, passwords, "cv_runtime") as connection:
        assert connection.execute("SELECT DISTINCT tenant_id FROM cv.company").fetchall() == []


def test_api_actual_database_readiness(
    db_config: Any, passwords: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = json.loads(Path("infra/config/test.json").read_text())
    # Environment-variable reference only, not a password value.
    settings["dependencies"]["database_secret_env"] = "CV_PHASE03_TEST_CONNECTION"  # noqa: S105
    connection = configuration(db_config, passwords).model_dump(mode="json")
    connection["password"] = passwords["cv_runtime"]
    monkeypatch.setenv("CV_PHASE03_TEST_CONNECTION", json.dumps(connection))
    app = create_app(Settings.model_validate(settings))
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["implemented_dependencies"] == ["database"]
        assert response.json()["capabilities"]["database"]["state"] == "ready"
        assert response.json()["capabilities"]["document"]["state"] == "unavailable"
        assert response.json()["capabilities"]["authentication"]["state"] == "unavailable"
        assert response.json()["capabilities"]["company"]["state"] == "unavailable"


def test_declared_missing_configuration_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = json.loads(Path("infra/config/test.json").read_text())
    # Deliberately absent environment-variable reference, not a password.
    settings["dependencies"]["database_secret_env"] = "CV_PHASE03_MISSING_CONNECTION"  # noqa: S105
    monkeypatch.delenv("CV_PHASE03_MISSING_CONNECTION", raising=False)
    with pytest.raises(PersistenceError, match="DATABASE_CONFIGURATION_REQUIRED"):
        configured_database(Settings.model_validate(settings))
