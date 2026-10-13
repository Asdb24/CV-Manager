"""Real isolated migration lifecycle; production downgrade is never recovery."""

import hashlib
import json
from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
from cv_foundation.settings import DatabaseTestSettings
from database_migrate import migrate
from psycopg import sql


def snapshot(connection: psycopg.Connection[Any], tables: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for table in tables:
        # Compare every pre-existing logical value. The later construction_xid
        # is new internal sealing metadata, not an old business value.
        rows = connection.execute(
            sql.SQL("SELECT (to_jsonb(t)-'construction_xid')::text FROM cv.{} t ORDER BY 1").format(
                sql.Identifier(table)
            )
        ).fetchall()
        result[table] = [row[0] for row in rows]
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    settings = DatabaseTestSettings.model_validate_json(args.config.read_text())
    passwords = json.loads(Path(settings.credential_file).read_text())
    suffix = uuid4().hex.translate(str.maketrans("0123456789", "ghijklmnop"))
    database_name = "cv_phase03_migration_" + suffix
    config_file = Path(settings.cluster_directory).parent / "migration-check-config.json"
    test_settings = settings.model_dump()
    test_settings["database"] = database_name
    config_file.write_text(DatabaseTestSettings.model_validate(test_settings).model_dump_json())
    admin = psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname="postgres",
        user="cv_cluster_admin",
        password=passwords["cv_cluster_admin"],
        connect_timeout=settings.connect_timeout_seconds,
        autocommit=True,
    )
    manifest_path = Path("contracts/migration-state.json")
    manifest = json.loads(manifest_path.read_text())
    results: dict[str, object] = {
        "observed_at": datetime.now(UTC).isoformat(),
        "head": manifest["head"],
        "migration_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    created = False
    try:
        admin.execute(
            sql.SQL("CREATE DATABASE {} OWNER cv_migrator").format(sql.Identifier(database_name))
        )
        created = True
        migrate(config_file, "upgrade", "head")
        results["empty_upgrade"] = "PASS"
        migrate(config_file, "downgrade", "base")
        results["empty_downgrade"] = "PASS"
        migrate(config_file, "upgrade", "head")
        results["empty_reupgrade"] = "PASS"
        migrate(config_file, "downgrade", "base")
        migrate(config_file, "upgrade", "0004_command_parameters")
        # Reuse the same explicit synthetic seed without invoking a pytest fixture.
        fixture_path = Path(__file__).resolve().parents[1] / "tests/database/conftest.py"
        spec = spec_from_file_location("phase03_seed_fixture", fixture_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("SYNTHETIC_FIXTURE_MODULE_MISSING")
        fixture = module_from_spec(spec)
        spec.loader.exec_module(fixture)
        fixture.seed_synthetic(DatabaseTestSettings.model_validate(test_settings), passwords)
        with psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname=database_name,
            user="cv_cluster_admin",
            password=passwords["cv_cluster_admin"],
            connect_timeout=settings.connect_timeout_seconds,
        ) as connection:
            tenant, company = uuid4(), uuid4()
            connection.execute(
                "INSERT INTO cv.agency(id,realm_key,name) VALUES(%s,%s,%s)",
                (tenant, "synthetic-migration", "SYNTHETIC preserved agency"),
            )
            connection.execute(
                "INSERT INTO cv.company VALUES(%s,%s,%s,1,NULL)",
                (tenant, company, "SYNTHETIC preserved company"),
            )
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='cv' ORDER BY tablename"
                ).fetchall()
            ]
            before = snapshot(connection, tables)
            results["preserved_table_row_counts"] = {
                name: len(rows) for name, rows in before.items()
            }
        migrate(config_file, "upgrade", "head")
        with psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname=database_name,
            user="cv_cluster_admin",
            password=passwords["cv_cluster_admin"],
            connect_timeout=settings.connect_timeout_seconds,
        ) as connection:
            after = snapshot(connection, tables)
        if before != after:
            raise RuntimeError("FORWARD_MIGRATION_DATA_CHANGED")
        results["populated_forward_preservation"] = "PASS"
        results["preserved_snapshot_sha256"] = hashlib.sha256(
            json.dumps(after).encode()
        ).hexdigest()
        try:
            migrate(config_file, "downgrade", "base")
        except RuntimeError as error:
            if str(error) != "POPULATED_DOWNGRADE_FORBIDDEN":
                raise
            results["populated_downgrade_denied"] = "PASS"
        else:
            raise RuntimeError("POPULATED_DOWNGRADE_NOT_DENIED")
    finally:
        if created:
            # Exact database created by this invocation; no existing user's database.
            admin.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
            )
        admin.close()
        config_file.unlink(missing_ok=True)
    Path("docs/phases/evidence-04/migration-lifecycle.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(results))


if __name__ == "__main__":
    main()
