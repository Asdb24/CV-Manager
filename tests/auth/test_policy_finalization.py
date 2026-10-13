from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from conftest import AuthWorkspace
from cv_api.authentication import Authentication
from cv_foundation.database import PersistenceError, configured_database
from psycopg.types.json import Jsonb


def test_policy_expiring_before_commit_rolls_back(workspace: AuthWorkspace) -> None:
    workspace.bootstrap()
    session = workspace.login()
    auth = Authentication(configured_database(workspace.settings), workspace.settings)
    body = {
        "kind": "purpose",
        "version": "synthetic-expiring-v1",
        "expires_at": (datetime.now(UTC) + timedelta(seconds=0.5)).isoformat(),
        "definition": {
            "synthetic_only": True,
            "production_approval": False,
            "clock": "database-utc",
            "description": "SYNTHETIC expiry test",
        },
    }
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with auth.staff(session["token"]) as tx:
            tx.execute(
                "SELECT cv.auth_policy_write(%s,%s,%s,%s)",
                ("policy-activate", uuid4(), "e" * 64, Jsonb(body)),
            )
            tx.validate_constraints()
            tx.execute("SELECT pg_sleep(0.6)")
    with workspace.connect() as connection:
        assert connection.execute("SELECT count(*) FROM cv.policy_version").fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM cv.auth_command").fetchone() == (0,)
