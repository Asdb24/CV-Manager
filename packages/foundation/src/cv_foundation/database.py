"""Restricted, bounded PostgreSQL connections and whole-command transactions."""

from __future__ import annotations

import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from threading import BoundedSemaphore
from typing import Any, Literal

import psycopg
from pydantic import ValidationError

from cv_foundation.contracts import Capability, Readiness, unavailable_capabilities
from cv_foundation.settings import DatabaseConnectionSettings, Settings

SCHEMA_REVISION = "0021_auth_hash_admission"


class PersistenceError(RuntimeError):
    """Safe code only; database diagnostics must not cross the API boundary."""


def _safe_error(error: psycopg.Error) -> PersistenceError:
    code = {
        "42501": "ACCESS_DENIED",
        "23503": "REFERENCE_INVALID",
        "23505": "CONFLICT",
        "23514": "CONSTRAINT_REJECTED",
        "40001": "REVISION_CONFLICT",
        "40P01": "RETRY_TRANSACTION",
        "57014": "DATABASE_TIMEOUT",
        "55P03": "DATABASE_BUSY",
    }.get(error.sqlstate or "", "DATABASE_UNAVAILABLE")
    return PersistenceError(code)


class QueryResult:
    """Materialized rows, with no cursor or connection that could commit early."""

    __slots__ = ("_rows",)

    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self._rows = iter(rows)

    def fetchone(self) -> tuple[Any, ...] | None:
        return next(self._rows, None)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._rows)


class Transaction:
    """Trusted persistence API; results are provisional until context exit succeeds.

    SQL is application source, never request input. Only one prepared SELECT is
    accepted; mutations use the database's granted command functions. Python
    code deliberately accessing private attributes is outside this API boundary.
    """

    __slots__ = ("_active", "_connection")

    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self._connection = connection
        self._active = True

    def _require_active(self) -> None:
        if not self._active:
            raise PersistenceError("TRANSACTION_CLOSED")

    def execute(self, statement: str, parameters: Sequence[Any] | None = None) -> QueryResult:
        self._require_active()
        if not statement.strip() or statement.lstrip().split(maxsplit=1)[0].upper() != "SELECT":
            raise PersistenceError("TRANSACTION_STATEMENT_DENIED")
        try:
            # Extended protocol rejects multiple statements, including SELECT; COMMIT.
            with self._connection.execute(statement, parameters, prepare=True) as cursor:
                return QueryResult(cursor.fetchall())
        except psycopg.Error as error:
            raise _safe_error(error) from None

    def validate_constraints(self) -> None:
        """Optional early constraint check; never replaces final authorization."""
        self._require_active()
        try:
            self._connection.execute("SET CONSTRAINTS ALL IMMEDIATE")
        except psycopg.Error as error:
            raise _safe_error(error) from None

    def _close(self) -> None:
        self._active = False


class Database:
    def __init__(self, settings: DatabaseConnectionSettings) -> None:
        self.settings = settings
        self._slots = BoundedSemaphore(settings.connection_limit)

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[Any]]:
        if not self._slots.acquire(timeout=self.settings.connect_timeout_seconds):
            raise PersistenceError("DATABASE_BUSY")
        try:
            with psycopg.connect(
                host=self.settings.host,
                port=self.settings.port,
                dbname=self.settings.database,
                user=self.settings.user,
                password=self.settings.password.get_secret_value(),
                sslmode=self.settings.sslmode,
                sslrootcert=self.settings.sslrootcert,
                connect_timeout=self.settings.connect_timeout_seconds,
                options=f"-c statement_timeout={self.settings.statement_timeout_ms} "
                f"-c lock_timeout={self.settings.lock_timeout_ms} -c timezone=UTC",
            ) as connection:
                properties = connection.execute(
                    "SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole,"
                    "pg_has_role(current_user,'cv_guard','MEMBER'),"
                    "pg_has_role(current_user,'cv_migrator','MEMBER') "
                    "FROM pg_roles WHERE rolname=current_user"
                ).fetchone()
                if properties != (False, False, False, False, False, False):
                    raise PersistenceError("DATABASE_ROLE_UNSAFE")
                yield connection
        except psycopg.Error as error:
            raise _safe_error(error) from None
        finally:
            self._slots.release()

    @contextmanager
    def staff_transaction(self, proof: str) -> Iterator[Transaction]:
        if self.settings.user != "cv_runtime" or not proof:
            raise PersistenceError("STAFF_SESSION_REQUIRED")
        with self._connection() as connection:
            connection.execute("SELECT cv.bind_session(%s)", (proof,))
            transaction = Transaction(connection)
            try:
                yield transaction
            finally:
                transaction._close()
            # Run deferred constraint work before the final fresh-clock check.
            connection.execute("SET CONSTRAINTS ALL IMMEDIATE")
            connection.execute("SELECT cv.validate_transaction()")
            # No caller work follows validation. The connection context commits.

    @contextmanager
    def public_transaction(self) -> Iterator[Transaction]:
        if self.settings.user != "cv_public":
            raise PersistenceError("PUBLIC_ROLE_REQUIRED")
        with self._connection() as connection:
            transaction = Transaction(connection)
            try:
                yield transaction
            finally:
                transaction._close()
            connection.execute("SET CONSTRAINTS ALL IMMEDIATE")
            connection.execute("SELECT cv.validate_transaction()")

    def ready(self) -> bool:
        try:
            with self._connection() as connection:
                return connection.execute("SELECT cv.database_ready()").fetchone() == (
                    SCHEMA_REVISION,
                )
        except PersistenceError:
            return False


def configured_database(settings: Settings) -> Database | None:
    reference = settings.dependencies.database_secret_env
    if reference is None:
        return None
    value = os.environ.get(reference)
    if not value:
        raise PersistenceError("DATABASE_CONFIGURATION_REQUIRED")
    try:
        connection_settings = DatabaseConnectionSettings.model_validate_json(value)
    except ValidationError:
        raise PersistenceError("DATABASE_CONFIGURATION_INVALID") from None
    if settings.realm == "local" and connection_settings.host not in {"127.0.0.1", "::1"}:
        raise PersistenceError("LOCAL_DATABASE_REQUIRED")
    return Database(connection_settings)


def database_readiness(component: Literal["api", "worker"], database: Database | None) -> Readiness:
    available = database is not None and database.ready()
    capabilities = unavailable_capabilities()
    capabilities["database"] = Capability(
        state="ready" if available else "unavailable",
        required_dependencies=["database"],
        code="DATABASE_READY" if available else "DATABASE_UNAVAILABLE",
        owner_phase="03",
    )
    capabilities["company"] = Capability(
        state="unavailable",
        required_dependencies=["database"],
        code="COMPANY_API_NOT_IMPLEMENTED",
        owner_phase="06",
    )
    return Readiness(
        component=component,
        ready=False,
        implemented_dependencies=["database"],
        capabilities=capabilities,
    )
