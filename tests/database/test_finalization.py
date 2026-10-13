"""Real adapter finalization after callers force every deferred check early."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Event
from typing import Any
from uuid import UUID, uuid4

import pytest
from cv_foundation.database import Database, PersistenceError, Transaction
from cv_foundation.settings import DatabaseTestSettings
from pydantic import SecretStr

from .conftest import connect, digest, extraction_definition, identity
from .test_adapter import configuration
from .test_public import grant


def public_database(config: DatabaseTestSettings, passwords: dict[str, str]) -> Database:
    return Database(
        configuration(config, passwords).model_copy(
            update={"user": "cv_public", "password": SecretStr(passwords["cv_public"])}
        )
    )


def intake(transaction: Transaction, publication: dict[str, Any], proof: str, key: UUID) -> UUID:
    row = transaction.execute(
        "SELECT cv.accept_intake(%s,%s,%s,%s,%s,%s,NULL,true,%s)",
        (
            proof,
            publication["id"],
            publication["snapshot"],
            identity("a/consent"),
            "SYNTHETIC finalization",
            "finalization@example.invalid",
            key,
        ),
    ).fetchone()
    assert row is not None and isinstance(row[0], UUID)
    return row[0]


def expire_after_early_checks(transaction: Transaction, expiry: datetime) -> None:
    transaction.validate_constraints()
    transaction.execute("SELECT cv.validate_transaction()")
    # The database's own deadline, not an assumption about host clock/scheduling.
    transaction.execute("SELECT pg_sleep_until(%s)", (expiry,))


@pytest.mark.parametrize(
    "statement", ["COMMIT", "ROLLBACK", "SET ROLE cv_guard", "DELETE FROM cv.company"]
)
def test_adapter_does_not_expose_transaction_control(
    db_config: DatabaseTestSettings, passwords: dict[str, str], statement: str
) -> None:
    db = Database(configuration(db_config, passwords))
    assert not hasattr(db, "connection")
    with db.staff_transaction("a/admin/proof") as transaction:
        result = transaction.execute("SELECT 1")
        for obj in (transaction, result):
            for attribute in ("commit", "rollback", "autocommit", "connection", "cursor"):
                assert not hasattr(obj, attribute)
        with pytest.raises(PersistenceError, match="TRANSACTION_STATEMENT_DENIED"):
            transaction.execute(statement)
        for forbidden in ("commit", "rollback", "autocommit", "connection", "cursor"):
            with pytest.raises(AttributeError):
                setattr(transaction, forbidden, True)
    with pytest.raises(PersistenceError, match="TRANSACTION_CLOSED"):
        transaction.execute("SELECT 1")


def test_prepared_select_cannot_commit_a_partial_command(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    key = uuid4()
    with pytest.raises(PersistenceError, match="DATABASE_UNAVAILABLE"):
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            t.execute(
                "SELECT cv.rename_company(%s,1,'SYNTHETIC must roll back',%s,%s)",
                (identity("a/company"), identity("a/purpose"), key),
            )
            t.execute("SELECT 1; COMMIT")
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (key,)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
        ).fetchone() == (1,)


def test_finalization_rejects_expired_session_after_early_validation(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    proof, key = str(uuid4()), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.staff_session VALUES(%s,%s,%s,%s,"
            "clock_timestamp()+interval '2 seconds',NULL,clock_timestamp()) RETURNING expires_at",
            (identity("a"), uuid4(), identity("a/admin"), digest(proof)),
        ).fetchone()
        assert row is not None
        expiry = row[0]
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction(proof) as t:
            t.execute(
                "SELECT cv.rename_company(%s,1,'SYNTHETIC expired',%s,%s)",
                (identity("a/company"), identity("a/purpose"), key),
            )
            expire_after_early_checks(t, expiry)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (key,)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT count(*) FROM cv.audit_event WHERE action='company.rename' AND record_id=%s",
            (identity("a/company"),),
        ).fetchone() == (0,)


def test_replay_obligation_survives_early_validation_and_rolls_back_other_writes(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    purpose, company, first_key, second_key = uuid4(), uuid4(), uuid4(), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
            "synthetic_only,activated_at,clock_timestamp()+interval '3 seconds',definition "
            "FROM cv.policy_version WHERE id=%s RETURNING expires_at",
            (purpose, str(purpose), identity("a/purpose")),
        ).fetchone()
        assert row is not None
        expiry = row[0]
        c.execute(
            "INSERT INTO cv.purpose_grant VALUES(%s,%s,%s,true)",
            (identity("a"), identity("a/admin"), purpose),
        )
        c.execute(
            "INSERT INTO cv.company VALUES(%s,%s,'SYNTHETIC replay',1,NULL)",
            (identity("a"), company),
        )
    db = Database(configuration(db_config, passwords))
    query = "SELECT cv.rename_company(%s,1,'SYNTHETIC committed',%s,%s)"
    with db.staff_transaction("a/admin/proof") as t:
        original = t.execute(query, (company, purpose, first_key)).fetchone()
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with db.staff_transaction("a/admin/proof") as t:
            assert t.execute(query, (company, purpose, first_key)).fetchone() == original
            t.execute(
                "SELECT cv.rename_company(%s,2,'SYNTHETIC rollback',%s,%s)",
                (company, identity("a/purpose"), second_key),
            )
            expire_after_early_checks(t, expiry)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute("SELECT revision FROM cv.company WHERE id=%s", (company,)).fetchone() == (
            2,
        )
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (first_key,)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (second_key,)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT count(*) FROM cv.audit_event WHERE record_id=%s", (company,)
        ).fetchone() == (1,)


def test_every_scope_is_validated_not_only_last_command(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    first, second = uuid4(), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        definition = extraction_definition(c)
        for scope, short in ((first, True), (second, False)):
            row = c.execute(
                "INSERT INTO cv.privacy_scope SELECT tenant_id,%s,candidate_id,purpose_id,%s,"
                "source_policy_id,consent_policy_id,retention_policy_id,erasure_policy_id,resource_policy_id,"
                "consent_at,CASE WHEN %s THEN clock_timestamp()+interval '2 seconds' "
                "ELSE consent_expires_at END,NULL,synthetic,clock_timestamp() "
                "FROM cv.privacy_scope WHERE id=%s RETURNING consent_expires_at",
                (scope, uuid4(), short, identity("a/person1/scope")),
            ).fetchone()
            assert row is not None
            if short:
                expiry = row[0]
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            for scope in (first, second):
                t.execute(
                    "SELECT cv.claim_extraction(%s,%s,%s,%s,%s)",
                    (scope, digest(str(scope)), *definition),
                )
            expire_after_early_checks(t, expiry)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.extraction WHERE scope_id IN (%s,%s)", (first, second)
        ).fetchone() == (0,)


@pytest.mark.parametrize("replay", [False, True])
def test_public_finalization_after_early_checks(
    db_config: DatabaseTestSettings,
    passwords: dict[str, str],
    publication: dict[str, Any],
    replay: bool,
) -> None:
    key = uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "UPDATE cv.publication SET expires_at=clock_timestamp()+interval '3 seconds' "
            "WHERE id=%s RETURNING expires_at",
            (publication["id"],),
        ).fetchone()
        assert row is not None
        expiry = row[0]
    proof = grant(db_config, passwords, publication)
    db = public_database(db_config, passwords)
    if replay:
        with db.public_transaction() as t:
            intake(t, publication, proof, key)
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with db.public_transaction() as t:
            intake(t, publication, proof, key)
            expire_after_early_checks(t, expiry)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.intake WHERE operation_key=%s", (key,)
        ).fetchone() == (int(replay),)
        assert c.execute(
            "SELECT count(*) FROM cv.public_upload_grant "
            "WHERE proof_digest=%s AND scope_id IS NOT NULL",
            (digest(proof),),
        ).fetchone() == (int(replay),)


def test_erasure_obligation_survives_scope_deletion(
    db_config: DatabaseTestSettings, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    policy, request = uuid4(), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
            "synthetic_only,activated_at,clock_timestamp()+interval '2 seconds',definition "
            "FROM cv.policy_version WHERE id=%s RETURNING expires_at",
            (policy, str(policy), identity("a/erasure")),
        ).fetchone()
        assert row is not None
        expiry = row[0]
        c.execute(
            "UPDATE cv.publication SET erasure_policy_id=%s WHERE id=%s",
            (policy, publication["id"]),
        )
    proof = grant(db_config, passwords, publication)
    with public_database(db_config, passwords).public_transaction() as t:
        receipt = intake(t, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope = row[0]
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            t.execute("SELECT cv.erase_scope(%s,%s)", (scope, request))
            expire_after_early_checks(t, expiry)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.intake WHERE receipt=%s", (receipt,)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.erasure_request WHERE id=%s", (request,)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT count(*) FROM cv.erasure_file WHERE request_id=%s", (request,)
        ).fetchone() == (0,)


def test_successful_adapter_erasure_does_not_require_revoked_recruitment_consent(
    db_config: DatabaseTestSettings, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with public_database(db_config, passwords).public_transaction() as t:
        receipt = intake(t, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope = row[0]
        c.execute("UPDATE cv.privacy_scope SET revoked_at=clock_timestamp() WHERE id=%s", (scope,))
    request = uuid4()
    with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
        assert t.execute("SELECT cv.erase_scope(%s,%s)", (scope, request)).fetchone() == (request,)
        t.validate_constraints()
        t.execute("SELECT cv.validate_transaction()")
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.intake WHERE receipt=%s", (receipt,)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT scope_id,status FROM cv.erasure_request WHERE id=%s", (request,)
        ).fetchone() == (None, "files_pending")
        # The private queue leaves neither a persistent scope ID nor a cache after commit.
        assert c.execute(
            "SELECT count(*) FROM pg_class WHERE relname='cv_authority_obligations'"
        ).fetchone() == (0,)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM pg_temp.cv_authority_obligations",
        "SELECT cv.register_obligation('purpose',NULL,NULL,NULL)",
    ],
)
def test_caller_cannot_read_or_replace_private_obligations(
    db_config: DatabaseTestSettings, passwords: dict[str, str], query: str
) -> None:
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            t.execute("SELECT cv.validate_transaction()")
            t.execute(query)


def test_finalization_clock_is_sampled_after_blocking_policy_lock(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    purpose, key = uuid4(), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
            "synthetic_only,activated_at,clock_timestamp()+interval '3 seconds',definition "
            "FROM cv.policy_version WHERE id=%s RETURNING expires_at",
            (purpose, str(purpose), identity("a/purpose")),
        ).fetchone()
        assert row is not None
        expiry = row[0]
        c.execute(
            "INSERT INTO cv.purpose_grant VALUES(%s,%s,%s,true)",
            (identity("a"), identity("a/admin"), purpose),
        )
    finishing = Event()
    backend: list[int] = []

    def attempt() -> None:
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            row = t.execute("SELECT pg_backend_pid()").fetchone()
            assert row is not None
            backend.append(row[0])
            t.execute(
                "SELECT cv.rename_company(%s,1,'SYNTHETIC lock expiry',%s,%s)",
                (identity("a/company"), purpose, key),
            )
            t.validate_constraints()
            finishing.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        with connect(db_config, passwords, "cv_cluster_admin") as blocker:
            blocker.execute(
                "SELECT 1 FROM cv.policy_version WHERE id=%s FOR NO KEY UPDATE", (purpose,)
            )
            pending = executor.submit(attempt)
            assert finishing.wait(timeout=db_config.connect_timeout_seconds)
            # Wait for the observed backend to enter the actual final validator lock.
            while True:
                blocker.execute("SELECT pg_stat_clear_snapshot()")
                row = blocker.execute(
                    "SELECT wait_event_type,query,query_start<%s,clock_timestamp()<%s "
                    "FROM pg_stat_activity WHERE pid=%s",
                    (expiry, expiry, backend[0]),
                ).fetchone()
                assert row is not None and row[3], (
                    "finalization did not block before fixture expiry"
                )
                if row[0] == "Lock":
                    assert row[1] == "SELECT cv.validate_transaction()" and row[2]
                    break
                blocker.execute("SELECT pg_sleep(0.01)")
            blocker.execute("SELECT pg_sleep_until(%s)", (expiry,))
        with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
            pending.result(timeout=db_config.connect_timeout_seconds)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (key,)
        ).fetchone() == (0,)


def test_private_read_must_revalidate_scope_even_without_mutation(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    scope = uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.privacy_scope SELECT tenant_id,%s,candidate_id,purpose_id,%s,"
            "source_policy_id,consent_policy_id,retention_policy_id,erasure_policy_id,resource_policy_id,"
            "consent_at,clock_timestamp()+interval '2 seconds',NULL,synthetic,clock_timestamp() "
            "FROM cv.privacy_scope WHERE id=%s RETURNING consent_expires_at",
            (scope, uuid4(), identity("a/person1/scope")),
        ).fetchone()
        assert row is not None
        expiry = row[0]
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction("a/admin/proof") as t:
            assert t.execute(
                "SELECT id FROM cv.privacy_scope WHERE id=%s", (scope,)
            ).fetchone() == (scope,)
            expire_after_early_checks(t, expiry)


def test_company_read_must_revalidate_selected_purpose_without_mutation(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    user, purpose, proof = uuid4(), uuid4(), str(uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute(
            "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
            "synthetic_only,activated_at,clock_timestamp()+interval '2 seconds',definition "
            "FROM cv.policy_version WHERE id=%s RETURNING expires_at",
            (purpose, str(purpose), identity("a/purpose")),
        ).fetchone()
        assert row is not None
        expiry = row[0]
        c.execute(
            "INSERT INTO cv.staff_user "
            "VALUES(%s,%s,%s,'synthetic-unusable-hash',true,clock_timestamp())",
            (identity("a"), user, str(user)),
        )
        c.execute(
            "INSERT INTO cv.membership VALUES(%s,%s,'recruiter',true,1)", (identity("a"), user)
        )
        c.execute(
            "INSERT INTO cv.purpose_grant VALUES(%s,%s,%s,true)", (identity("a"), user, purpose)
        )
        c.execute(
            "INSERT INTO cv.staff_session SELECT tenant_id,%s,%s,%s,expires_at,NULL,created_at "
            "FROM cv.staff_session WHERE id=%s",
            (uuid4(), user, digest(proof), identity("a/admin/session")),
        )
    with pytest.raises(PersistenceError, match="ACCESS_DENIED"):
        with Database(configuration(db_config, passwords)).staff_transaction(proof) as t:
            assert t.execute(
                "SELECT id FROM cv.company WHERE id=%s", (identity("a/company"),)
            ).fetchone() == (identity("a/company"),)
            expire_after_early_checks(t, expiry)
