from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

import psycopg
import pytest

from .conftest import connect, digest, extraction_definition, identity


def bind(c: psycopg.Connection[Any], proof: str = "a/admin/proof") -> None:
    c.execute("SELECT cv.bind_session(%s)", (proof,))


def test_service_has_no_staff_authority(runtime: psycopg.Connection[Any]) -> None:
    assert runtime.execute("SELECT * FROM cv.company").fetchall() == []
    runtime.execute("SELECT set_config('app.tenant_id',%s,true)", (str(identity("a")),))
    assert runtime.execute("SELECT * FROM cv.company").fetchall() == []
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        runtime.execute("SELECT * FROM cv.staff_session")


def test_real_role_properties(runtime: psycopg.Connection[Any]) -> None:
    assert runtime.execute(
        "SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM "
        "pg_roles WHERE rolname=current_user"
    ).fetchone() == (False, False, False, False)
    assert runtime.execute(
        "SELECT count(*) FROM pg_tables t JOIN pg_class c ON "
        "c.relname=t.tablename JOIN pg_namespace n ON "
        "n.oid=c.relnamespace WHERE t.schemaname='cv' AND n.nspname='cv' "
        "AND NOT (c.relrowsecurity AND c.relforcerowsecurity)"
    ).fetchone() == (0,)


def test_session_tenant_and_no_transaction_leak(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    assert runtime.execute("SELECT DISTINCT tenant_id FROM cv.company").fetchall() == [
        (identity("a"),)
    ]
    assert (
        runtime.execute("SELECT id FROM cv.company WHERE tenant_id=%s", (identity("b"),)).fetchall()
        == []
    )
    runtime.commit()
    assert runtime.execute("SELECT * FROM cv.company").fetchall() == []


def test_foreign_parent_denied(owner: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        owner.execute(
            "INSERT INTO cv.position VALUES(%s,%s,%s,'Synthetic invalid',1,NULL)",
            (identity("a"), uuid4(), identity("b/company")),
        )


def test_foreign_person_denied(owner: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        owner.execute(
            "INSERT INTO cv.application VALUES(%s,%s,%s,%s,%s,'received',1,NULL)",
            (
                identity("a"),
                identity("a/person1/scope"),
                uuid4(),
                identity("a/person2"),
                identity("a/position"),
            ),
        )


def test_immutable_definitions(owner: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        owner.execute(
            "UPDATE cv.jd_version SET content='changed' WHERE tenant_id=%s", (identity("a"),)
        )


def test_company_atomic_idempotency(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    key = uuid4()
    arguments = (identity("a/company"), 1, "SYNTHETIC renamed", identity("a/purpose"), key)
    first = runtime.execute("SELECT cv.rename_company(%s,%s,%s,%s,%s)", arguments).fetchone()
    assert (
        runtime.execute("SELECT cv.rename_company(%s,%s,%s,%s,%s)", arguments).fetchone() == first
    )
    assert runtime.execute(
        "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
    ).fetchone() == (2,)
    assert runtime.execute(
        "SELECT count(*) FROM cv.audit_event WHERE action='company.rename' AND record_id=%s",
        (identity("a/company"),),
    ).fetchone() == (1,)
    runtime.rollback()
    bind(runtime)
    assert runtime.execute(
        "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
    ).fetchone() == (1,)
    assert runtime.execute(
        "SELECT count(*) FROM cv.audit_event WHERE action='company.rename' AND record_id=%s",
        (identity("a/company"),),
    ).fetchone() == (0,)


def test_stage_guard_history(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    args = (
        identity("a/person1/scope"),
        identity("a/person1/application"),
        1,
        "evaluating",
        None,
        uuid4(),
    )
    runtime.execute("SELECT cv.move_stage(%s,%s,%s,%s,%s,%s)", args)
    assert runtime.execute(
        "SELECT stage,revision FROM cv.application WHERE id=%s",
        (identity("a/person1/application"),),
    ).fetchone() == ("evaluating", 2)
    assert runtime.execute(
        "SELECT from_stage,to_stage,revision FROM cv.stage_event"
    ).fetchall() == [("received", "evaluating", 2)]
    with pytest.raises(psycopg.errors.CheckViolation):
        runtime.execute(
            "SELECT cv.move_stage(%s,%s,%s,%s,%s,%s)",
            (args[0], args[1], 2, "received", "", uuid4()),
        )


def test_invalid_proof(runtime: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        bind(runtime, "a/not-valid")


def test_concurrent_claim(db_config: Any, passwords: dict[str, str]) -> None:
    content = digest(str(uuid4()))

    def claim() -> Any:
        with connect(db_config, passwords, "cv_runtime") as c:
            bind(c)
            return c.execute(
                "SELECT cv.claim_extraction(%s,%s,%s,%s,%s)",
                (
                    identity("a/person1/scope"),
                    content,
                    *extraction_definition(c),
                ),
            ).fetchone()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: claim(), range(2)))
    assert results[0] == results[1]
