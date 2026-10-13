"""Trusted authentication service; no raw DB handle or credential crosses HTTP."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any
from uuid import UUID

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from cv_foundation.auth_contracts import (
    AuthenticationPolicy,
    BootstrapCreate,
    InstanceStatus,
    LoginRequest,
    LoginResult,
    PolicyActivate,
    PolicyRecord,
    PolicyRevoke,
    PurposeGrant,
    StaffCreate,
    StaffIdentity,
    StaffRecord,
    StaffUpdate,
)
from cv_foundation.database import Database, PersistenceError, Transaction
from cv_foundation.settings import Settings
from psycopg.types.json import Jsonb


class AuthenticationError(RuntimeError):
    """Only stable safe codes, never an underlying diagnostic."""


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Passwords:
    def __init__(self, policy: AuthenticationPolicy) -> None:
        self.policy = policy
        self.hasher = PasswordHasher(
            time_cost=policy.argon_time_cost,
            memory_cost=policy.argon_memory_kib,
            parallelism=policy.argon_parallelism,
            type=Type.ID,
        )
        self.slots = BoundedSemaphore(policy.hash_concurrency)
        # Random non-account hash supports the same expensive verification for absent users.
        self.dummy = self.hash(secrets.token_urlsafe(32))

    @contextmanager
    def admitted(self) -> Iterator[None]:
        if not self.slots.acquire(timeout=self.policy.hash_wait_seconds):
            raise AuthenticationError("AUTH_BUSY")
        try:
            yield
        finally:
            self.slots.release()

    def validate(self, value: str) -> None:
        self.validate_unicode(value)
        if (
            not self.policy.password_min_characters
            <= len(value)
            <= self.policy.password_max_characters
        ):
            raise AuthenticationError("PASSWORD_POLICY")
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise AuthenticationError("PASSWORD_POLICY")

    @staticmethod
    def validate_unicode(value: str) -> None:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise AuthenticationError("PASSWORD_POLICY") from None

    def hash(self, value: str) -> str:
        self.validate_unicode(value)
        with self.admitted():
            return self.hasher.hash(value)

    def verify(self, encoded: str | None, value: str) -> bool:
        self.validate_unicode(value)
        with self.admitted():
            try:
                correct = self.hasher.verify(encoded or self.dummy, value)
            except (VerificationError, InvalidHashError):
                return False
        return correct and encoded is not None


class Authentication:
    def __init__(self, database: Database | None, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self.policy = AuthenticationPolicy.model_validate_json(
            Path(settings.dependencies.authentication_policy_file).read_text(encoding="utf-8")
        )
        expected_owner = "workspace-admin" if settings.realm == "local" else "server-operator"
        if self.policy.owner != expected_owner:
            raise AuthenticationError("AUTH_POLICY_OWNER_MISMATCH")
        self.passwords = Passwords(self.policy)

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        if self.database is None or self.database.settings.user != "cv_runtime":
            raise AuthenticationError("AUTH_UNAVAILABLE")
        # Service owns completion. Failed-password counters commit before HTTP denial.
        with self.database._connection() as connection:
            tx = Transaction(connection)
            try:
                yield tx
            finally:
                tx._close()

    def descriptor(self, tx: Transaction) -> InstanceStatus:
        row = tx.execute(
            "SELECT cv.auth_descriptor(%s,%s)", (self.settings.realm_key, self.settings.realm)
        ).fetchone()
        if row is None:
            raise AuthenticationError("AUTH_UNAVAILABLE")
        return InstanceStatus.model_validate(row[0])

    def configuration(self, tx: Transaction) -> bytes:
        row = tx.execute(
            "SELECT cv.auth_private_configuration(%s,%s)",
            (self.settings.realm_key, self.settings.realm),
        ).fetchone()
        if row is None or row[0]["policy"] != self.policy.model_dump(mode="json"):
            raise AuthenticationError("AUTH_POLICY_MISMATCH")
        secret = row[0]["command_secret"]
        if not isinstance(secret, str) or len(secret) < 43:
            raise AuthenticationError("AUTH_UNAVAILABLE")
        return secret.encode("utf-8")

    def status(self) -> InstanceStatus:
        with self.transaction() as tx:
            result = self.descriptor(tx)
        return result

    def bootstrap(self, body: BootstrapCreate, proof: str) -> None:
        if self.settings.realm != "local":
            raise AuthenticationError("BOOTSTRAP_DENIED")
        with self.transaction() as tx:
            self.configuration(tx)
            if self.descriptor(tx).instance_id != body.instance_id:
                raise AuthenticationError("BOOTSTRAP_DENIED")
            tx.execute("SELECT cv.auth_bootstrap_admit(%s,%s)", (body.instance_id, proof))
            self.passwords.validate(body.password.get_secret_value())
            credential = self.passwords.hash(body.password.get_secret_value())
            tx.execute(
                "SELECT cv.auth_bootstrap(%s,%s,%s,%s,%s)",
                (body.instance_id, proof, body.agency_name, body.login_name, credential),
            )

    def login(self, body: LoginRequest) -> LoginResult:
        result = None
        proof = secrets.token_urlsafe(32)
        with self.transaction() as tx:
            self.configuration(tx)
            status = self.descriptor(tx)
            if status.instance_id != body.instance_id:
                raise AuthenticationError("AUTH_DENIED")
            row = tx.execute(
                "SELECT cv.auth_login_begin(%s,%s)", (body.instance_id, body.login_name)
            ).fetchone()
            reservation: dict[str, Any] | None = row[0] if row else None
            candidate = reservation.get("credential") if reservation else None
            valid = False
            if reservation and reservation.get("admitted") is True:
                valid = self.passwords.verify(
                    candidate["credential_hash"] if candidate else None,
                    body.password.get_secret_value(),
                )
            if valid and candidate:
                row = tx.execute(
                    "SELECT cv.auth_login_finish(%s,%s,%s,%s)",
                    (
                        body.instance_id,
                        UUID(candidate["user_id"]),
                        candidate["credential_hash"],
                        token_digest(proof),
                    ),
                ).fetchone()
                if row and row[0]:
                    result = LoginResult(token=proof, identity=StaffIdentity.model_validate(row[0]))
                    tx.execute("SELECT cv.auth_bind(%s,%s)", (body.instance_id, proof))
                    tx.validate_constraints()
                    tx.execute("SELECT cv.auth_validate_transaction()")
        if result is None:
            raise AuthenticationError("AUTH_DENIED")
        return result

    @contextmanager
    def staff(self, proof: str) -> Iterator[Transaction]:
        if self.database is None:
            raise AuthenticationError("AUTH_DENIED")
        with self.transaction() as tx:
            instance = self.descriptor(tx)
            self.configuration(tx)
            tx.execute("SELECT cv.auth_bind(%s,%s)", (instance.instance_id, proof))
            yield tx
            tx.validate_constraints()
            tx.execute("SELECT cv.auth_validate_transaction()")

    def current(self, proof: str) -> StaffIdentity:
        with self.staff(proof) as tx:
            row = tx.execute("SELECT cv.auth_current()").fetchone()
            if row is None:
                raise AuthenticationError("AUTH_DENIED")
            result = StaffIdentity.model_validate(row[0])
        return result

    def logout(self, proof: str) -> None:
        with self.transaction() as tx:
            instance = self.descriptor(tx)
            tx.execute("SELECT cv.auth_bind(%s,%s)", (instance.instance_id, proof))
            tx.validate_constraints()
            tx.execute("SELECT cv.auth_logout()")
            # No response/caller work after self-revocation and before commit.

    def revoke(self, proof: str, session_id: UUID) -> None:
        with self.staff(proof) as tx:
            tx.execute("SELECT cv.auth_revoke(%s)", (session_id,))

    def list_staff(self, proof: str, after: UUID | None) -> list[StaffRecord]:
        with self.staff(proof) as tx:
            row = tx.execute("SELECT cv.auth_staff_list(%s)", (after,)).fetchone()
            if row is None:
                raise AuthenticationError("AUTH_DENIED")
            result = [StaffRecord.model_validate(value) for value in row[0]]
        return result

    def write_staff(
        self, proof: str, key: UUID, body: StaffCreate | StaffUpdate, user_id: UUID | None = None
    ) -> StaffRecord:
        with self.staff(proof) as tx:
            row = tx.execute("SELECT cv.auth_current()").fetchone()
            if row is None or row[0]["role"] != "admin":
                raise AuthenticationError("ACCESS_DENIED")
            # A keyed digest makes password-containing retry payloads non-dictionary-searchable.
            secret = self.configuration(tx)
            payload = body.model_dump(mode="json")
            if isinstance(body, StaffCreate):
                value = body.password.get_secret_value()
                self.passwords.validate(value)
                payload["password"] = value
                operation = "staff-create"
            else:
                payload["user_id"] = str(user_id)
                operation = "staff-update"
            fingerprint = hmac.new(
                secret,
                json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if isinstance(body, StaffCreate):
                payload.pop("password")
                payload["credential_hash"] = self.passwords.hash(value)
            row = tx.execute(
                "SELECT cv.auth_staff_write(%s,%s,%s,%s)",
                (operation, key, fingerprint, Jsonb(payload)),
            ).fetchone()
            if row is None:
                raise PersistenceError("DATABASE_UNAVAILABLE")
            result = StaffRecord.model_validate(row[0])
        return result

    def list_policies(self, proof: str, after: UUID | None) -> list[PolicyRecord]:
        with self.staff(proof) as tx:
            row = tx.execute("SELECT cv.auth_policy_list(%s)", (after,)).fetchone()
            if row is None:
                raise AuthenticationError("ACCESS_DENIED")
            result = [PolicyRecord.model_validate(value) for value in row[0]]
        return result

    def policy_command(
        self,
        proof: str,
        key: UUID,
        body: PolicyActivate | PolicyRevoke | PurposeGrant,
        policy_id: UUID | None = None,
    ) -> dict[str, Any]:
        with self.staff(proof) as tx:
            payload = body.model_dump(mode="json")
            if isinstance(body, PolicyActivate):
                operation = "policy-activate"
            elif isinstance(body, PolicyRevoke):
                operation = "policy-revoke"
                payload["policy_id"] = str(policy_id)
            else:
                operation = "purpose-grant"
            fingerprint = hmac.new(
                self.configuration(tx),
                json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            row = tx.execute(
                "SELECT cv.auth_policy_write(%s,%s,%s,%s)",
                (operation, key, fingerprint, Jsonb(payload)),
            ).fetchone()
            if row is None or not isinstance(row[0], dict):
                raise AuthenticationError("ACCESS_DENIED")
            result: dict[str, Any] = row[0]
        return result
