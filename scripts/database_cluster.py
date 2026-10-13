"""Manage only the explicit project-owned synthetic PostgreSQL cluster."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import socket
import subprocess
from pathlib import Path

import psycopg
from cv_foundation.settings import DatabaseTestSettings
from cv_foundation.windows_privacy import protect_directory
from psycopg import sql


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    settings = DatabaseTestSettings.model_validate_json(args.config.read_text())
    directory = Path(settings.cluster_directory).resolve()
    credential_file = Path(settings.credential_file).resolve()
    owner = directory.parent
    owner.mkdir(parents=True, exist_ok=True)
    protect_directory(owner)
    tools: dict[str, str] = {}
    for name in ["initdb", "pg_ctl", "postgres"]:
        found = shutil.which(name)
        if found is None:
            raise RuntimeError("POSTGRESQL_TOOL_MISSING")
        tools[name] = str(Path(found).resolve())

    def run(name: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        # Resolved installed binary and argument vector; no shell or caller command.
        # pg_ctl children can inherit anonymous pipes on Windows. A log file does
        # not require waiting for the long-lived server to close a captured pipe.
        log = owner / "control-command.log"
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run(  # noqa: S603
                [tools[name], *arguments],
                stdout=output,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=settings.startup_timeout_seconds,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        return subprocess.CompletedProcess(
            result.args, result.returncode, log.read_text(encoding="utf-8"), ""
        )

    marker = owner / "cluster-owner.json"
    identity = {"project": str(Path.cwd().resolve()), "cluster": str(directory)}
    if marker.exists() and json.loads(marker.read_text()) != identity:
        raise RuntimeError("DATABASE_CLUSTER_OWNERSHIP_MISMATCH")
    if directory.exists() and not marker.exists():
        raise RuntimeError("UNOWNED_DATABASE_CLUSTER")
    status = run("pg_ctl", ["status", "-D", str(directory)])
    if args.action == "status":
        print(json.dumps({"running": status.returncode == 0, "owned": marker.exists()}))
        return
    if args.action == "stop":
        if not marker.exists():
            raise RuntimeError("UNOWNED_DATABASE_CLUSTER")
        if status.returncode == 0:
            result = run("pg_ctl", ["stop", "-D", str(directory), "-m", "fast", "-w"])
            if result.returncode:
                raise RuntimeError("DATABASE_STOP_FAILED")
        print("OWNED_DATABASE_STOPPED")
        return
    if not credential_file.exists():
        if directory.exists():
            raise RuntimeError("DATABASE_CREDENTIALS_MISSING")
        passwords = {
            name: secrets.token_urlsafe(32)
            for name in ["cv_cluster_admin", "cv_migrator", "cv_runtime", "cv_public", "cv_probe"]
        }
        credential_file.write_text(json.dumps(passwords), encoding="utf-8")
    else:
        passwords = json.loads(credential_file.read_text())
    if not directory.exists():
        with socket.socket() as probe:
            probe.bind((settings.host, settings.port))
        marker.write_text(json.dumps(identity), encoding="utf-8")
        password_file = owner / "init-password"
        password_file.write_text(passwords["cv_cluster_admin"], encoding="utf-8")
        try:
            result = run(
                "initdb",
                [
                    "-D",
                    str(directory),
                    "-U",
                    "cv_cluster_admin",
                    "--pwfile",
                    str(password_file),
                    "--auth=scram-sha-256",
                    "--encoding=UTF8",
                    "--locale-provider=builtin",
                    "--locale=C",
                ],
            )
            (owner / "initdb.log").write_text(result.stdout + result.stderr, encoding="utf-8")
            if result.returncode:
                raise RuntimeError("DATABASE_INITIALIZATION_FAILED")
        finally:
            password_file.unlink(missing_ok=True)
        with (directory / "postgresql.conf").open("a", encoding="utf-8") as stream:
            stream.write(
                f"\nlisten_addresses = '{settings.host}'\nport = {settings.port}\n"
                "timezone = 'UTC'\nlog_statement = 'none'\nlog_min_error_statement = 'panic'\n"
                "password_encryption = 'scram-sha-256'\n"
            )
    if status.returncode != 0:
        result = run(
            "pg_ctl",
            [
                "start",
                "-D",
                str(directory),
                "-l",
                str(owner / "server.log"),
                "-w",
                "-t",
                str(settings.startup_timeout_seconds),
            ],
        )
        if result.returncode:
            raise RuntimeError("DATABASE_START_FAILED")
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname="postgres",
        user="cv_cluster_admin",
        password=passwords["cv_cluster_admin"],
        connect_timeout=settings.connect_timeout_seconds,
        autocommit=True,
    ) as connection:
        for name in ["cv_migrator", "cv_runtime", "cv_public", "cv_probe", "cv_guard"]:
            if connection.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (name,)).fetchone():
                continue
            definition = "NOLOGIN" if name == "cv_guard" else "LOGIN PASSWORD {}"
            query = sql.SQL(
                "CREATE ROLE {} "
                + definition
                + " NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"
            )
            values: list[sql.Composable] = [sql.Identifier(name)]
            if name != "cv_guard":
                values.append(sql.Literal(passwords[name]))
            connection.execute(query.format(*values))
        # The schema owner must maintain/drop guarded functions during migrations.
        # Runtime/public/probe logins receive no membership in either owner role.
        connection.execute("GRANT cv_guard TO cv_migrator WITH INHERIT TRUE, SET TRUE")
        if not connection.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", (settings.database,)
        ).fetchone():
            connection.execute(
                sql.SQL("CREATE DATABASE {} OWNER cv_migrator").format(
                    sql.Identifier(settings.database)
                )
            )
        connection.execute(
            sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(
                sql.Identifier(settings.database)
            )
        )
        connection.execute(
            sql.SQL(
                "GRANT CONNECT ON DATABASE {} TO cv_migrator, cv_runtime, cv_public, cv_probe"
            ).format(sql.Identifier(settings.database))
        )
        version = connection.execute("SELECT version()").fetchone()
    evidence = Path("docs/phases/evidence-04")
    evidence.mkdir(parents=True, exist_ok=True)
    inventory = {
        "server": version[0] if version else None,
        "host": settings.host,
        "port": settings.port,
        "database": settings.database,
        "authentication": "scram-sha-256",
        "isolated_project_cluster": True,
        "binaries": {
            name: {"path": path, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}
            for name, path in tools.items()
        },
    }
    (evidence / "postgresql-environment.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print("OWNED_POSTGRESQL_RUNNING: roles ready; this command does not apply migrations")


if __name__ == "__main__":
    main()
