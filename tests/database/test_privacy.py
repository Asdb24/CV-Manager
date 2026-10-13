from typing import Any
from uuid import uuid4

import psycopg
import pytest

from .conftest import connect, identity
from .test_core import bind
from .test_public import grant, submit


def test_erasure_cascades_intake_contact_and_hashes(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope = row[0]
    request = uuid4()
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        assert c.execute("SELECT cv.erase_scope(%s,%s)", (scope, request)).fetchone() == (request,)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        for table in [
            "contact_revision",
            "file_intent",
            "document_version",
            "intake",
            "public_upload_grant",
        ]:
            query = psycopg.sql.SQL("SELECT count(*) FROM cv.{} WHERE scope_id=%s").format(
                psycopg.sql.Identifier(table)
            )
            assert c.execute(query, (scope,)).fetchone() == (0,)
        assert c.execute(
            "SELECT scope_id,status FROM cv.erasure_request WHERE id=%s", (request,)
        ).fetchone() == (None, "files_pending")
        assert c.execute(
            "SELECT count(*) FROM cv.erasure_file WHERE request_id=%s", (request,)
        ).fetchone() == (1,)


def test_recruiter_cannot_erase(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime, "a/recruiter/proof")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        runtime.execute("SELECT cv.erase_scope(%s,%s)", (identity("a/person1/scope"), uuid4()))


def test_scope_revocation_hides_private_data(owner: psycopg.Connection[Any]) -> None:
    owner.execute(
        "UPDATE cv.privacy_scope SET revoked_at=clock_timestamp() WHERE id=%s",
        (identity("a/person2/scope"),),
    )
    # The policy function tests a real revoked record in the same database transaction.
    owner.execute("SELECT cv.bind_session('a/admin/proof')")
    assert owner.execute(
        "SELECT cv.scope_allowed(%s,%s)", (identity("a"), identity("a/person2/scope"))
    ).fetchone() == (False,)
