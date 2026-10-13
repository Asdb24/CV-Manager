"""Explicit terminal operator provisioning; no anonymous server bootstrap route."""

import argparse
import getpass
import json
import os
import secrets
from pathlib import Path

import psycopg
from cv_foundation.auth_contracts import AuthenticationPolicy, BootstrapCreate
from cv_foundation.settings import Component, DatabaseConnectionSettings, Profile, load_settings
from psycopg.types.json import Jsonb
from pydantic import SecretStr

from cv_api.authentication import AuthenticationError, Passwords, token_digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", type=Profile, required=True)
    parser.add_argument("--operator-secret-env", required=True)
    parser.add_argument("--agency", required=True)
    parser.add_argument("--login", required=True)
    args = parser.parse_args()
    try:
        settings = load_settings(args.config, args.profile, Component.API)
        if settings.profile not in {Profile.DEVELOPMENT, Profile.TEST, Profile.SERVER}:
            raise ValueError("OPERATOR_PROFILE_INVALID")
        if not args.operator_secret_env.isidentifier() or not args.operator_secret_env.isupper():
            raise ValueError("OPERATOR_SECRET_REFERENCE_INVALID")
        raw = json.loads(os.environ[args.operator_secret_env])
        if raw.pop("user") != "cv_migrator":
            raise ValueError("OPERATOR_ROLE_REQUIRED")
        # Reuse every transport/timeout validation; the operator login is fixed below.
        endpoint = DatabaseConnectionSettings.model_validate({**raw, "user": "cv_runtime"})
        if settings.realm == "local" and endpoint.host not in {"127.0.0.1", "::1"}:
            raise ValueError("LOCAL_DATABASE_REQUIRED")
        policy = AuthenticationPolicy.model_validate_json(
            Path(settings.dependencies.authentication_policy_file).read_text(encoding="utf-8")
        )
        if policy.owner != ("workspace-admin" if settings.realm == "local" else "server-operator"):
            raise ValueError("AUTH_POLICY_OWNER_MISMATCH")
        password = getpass.getpass("New administrator password: ")
        if password != getpass.getpass("Repeat administrator password: "):
            raise ValueError("PASSWORD_CONFIRMATION_MISMATCH")
        passwords = Passwords(policy)
        passwords.validate(password)
        encoded = passwords.hash(password)
        startup = secrets.token_urlsafe(32)
        with psycopg.connect(
            host=endpoint.host,
            port=endpoint.port,
            dbname=endpoint.database,
            user="cv_migrator",
            password=endpoint.password.get_secret_value(),
            sslmode=endpoint.sslmode,
            sslrootcert=endpoint.sslrootcert,
            connect_timeout=endpoint.connect_timeout_seconds,
            options=f"-c statement_timeout={endpoint.statement_timeout_ms} "
            f"-c lock_timeout={endpoint.lock_timeout_ms}",
        ) as connection:
            row = connection.execute(
                "SELECT cv.auth_configure(%s,%s,%s,%s,%s)",
                (
                    settings.realm,
                    settings.realm_key,
                    Jsonb(policy.model_dump(mode="json")),
                    token_digest(startup),
                    secrets.token_urlsafe(32),
                ),
            ).fetchone()
            if row is None:
                raise ValueError("BOOTSTRAP_DENIED")
            body = BootstrapCreate(
                instance_id=row[0],
                login_name=args.login,
                password=SecretStr(password),
                agency_name=args.agency,
            )
            connection.execute(
                "SELECT cv.auth_bootstrap(%s,%s,%s,%s,%s)",
                (body.instance_id, startup, body.agency_name, body.login_name, encoded),
            )
        print("BOOTSTRAP_COMMITTED: authenticate through the matching instance API.")
    except (AuthenticationError, ValueError, KeyError, OSError, psycopg.Error):
        parser.exit(
            2,
            "OPERATOR_PROVISIONING_FAILED: verify credentials and workspace configuration.\n",
        )


if __name__ == "__main__":
    main()
