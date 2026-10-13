"""Explicit migration runner for the isolated developer database."""

import argparse
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from cv_foundation.settings import DatabaseTestSettings
from sqlalchemy import URL, create_engine
from sqlalchemy.pool import NullPool


def migrate(config_path: Path, direction: str, revision: str) -> None:
    settings = DatabaseTestSettings.model_validate_json(config_path.read_text())
    secrets = json.loads(Path(settings.credential_file).read_text())
    engine = create_engine(
        URL.create(
            "postgresql+psycopg",
            username="cv_migrator",
            password=secrets["cv_migrator"],
            host=settings.host,
            port=settings.port,
            database=settings.database,
        ),
        poolclass=NullPool,
        connect_args={
            "connect_timeout": settings.connect_timeout_seconds,
            "options": f"-c statement_timeout={settings.statement_timeout_ms} "
            f"-c lock_timeout={settings.lock_timeout_ms}",
        },
        hide_parameters=True,
    )
    try:
        with engine.begin() as connection:
            configuration = Config("apps/api/alembic.ini")
            configuration.attributes["connection"] = connection
            configuration.attributes["direction"] = direction
            if direction == "upgrade":
                command.upgrade(configuration, revision)
            else:
                command.downgrade(configuration, revision)
    finally:
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("direction", choices=["upgrade", "downgrade"])
    parser.add_argument("revision")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    migrate(args.config, args.direction, args.revision)
    print("MIGRATION_COMMITTED")
