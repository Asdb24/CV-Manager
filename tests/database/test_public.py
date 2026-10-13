from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
import pytest

from .conftest import connect, digest, identity
from .test_core import bind


def grant(config: Any, passwords: dict[str, str], publication: dict[str, Any]) -> str:
    proof = str(uuid4())
    with connect(config, passwords, "cv_cluster_admin") as c:
        c.execute(
            ("INSERT INTO cv.public_upload_grant VALUES(%s,%s,%s,%s,%s,%s,%s,100,%s,%s,true,NULL)"),
            (
                publication["tenant"],
                uuid4(),
                publication["id"],
                publication["snapshot"],
                digest(proof),
                uuid4(),
                digest("synthetic-pdf"),
                datetime.now(UTC),
                publication["expiry"],
            ),
        )
    return proof


def submit(c: psycopg.Connection[Any], publication: dict[str, Any], proof: str, key: Any) -> Any:
    row = c.execute(
        "SELECT cv.accept_intake(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            proof,
            publication["id"],
            publication["snapshot"],
            identity("a/consent"),
            "SYNTHETIC applicant",
            "same@example.invalid",
            None,
            True,
            key,
        ),
    ).fetchone()
    assert row is not None
    return row[0]


def test_public_projection_and_direct_denial(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    with connect(db_config, passwords, "cv_public") as c:
        cursor = c.execute("SELECT * FROM cv.public_job(%s)", (publication["id"],))
        columns = [d.name for d in cursor.description or []]
        assert columns == [
            "publication",
            "snapshot",
            "agency_name",
            "company_name",
            "title",
            "location",
            "work_arrangement",
            "employment_type",
            "jd",
            "instructions",
            "expires_at",
            "consent_version",
        ]
        assert len(cursor.fetchall()) == 1
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("SELECT count(*) FROM cv.candidate")


@pytest.mark.parametrize("state", ["withdrawn", "expired"])
def test_closed_publication_denied(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any], state: str
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        if state == "expired":
            c.execute(
                "UPDATE cv.publication SET expires_at=%s WHERE id=%s",
                (datetime.now(UTC) - timedelta(seconds=1), publication["id"]),
            )
        else:
            c.execute(
                "UPDATE cv.publication SET state='withdrawn' WHERE id=%s", (publication["id"],)
            )
    with connect(db_config, passwords, "cv_public") as c:
        assert c.execute("SELECT * FROM cv.public_job(%s)", (publication["id"],)).fetchall() == []
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            submit(c, publication, proof, uuid4())


def test_intake_concurrency_and_explicit_identity(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    key = uuid4()

    def attempt() -> Any:
        with connect(db_config, passwords, "cv_public") as c:
            return submit(c, publication, proof, key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt(), range(2)))
    assert results[0] == results[1]
    other_proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        second = submit(c, publication, other_proof, uuid4())
    assert second != results[0]
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        scopes = c.execute(
            (
                "SELECT s.candidate_id FROM cv.intake i JOIN cv.privacy_scope s "
                "ON (s.tenant_id,s.id)=(i.tenant_id,i.scope_id) WHERE "
                "i.publication_id=%s"
            ),
            (publication["id"],),
        ).fetchall()
        assert scopes == [(None,), (None,)]


def test_review_requires_finalized_file_then_is_idempotent(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id,id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope, intake = row
    args = (scope, intake, 1, "create", None, "Synthetic explicit review", uuid4())
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        with pytest.raises(psycopg.errors.CheckViolation):
            c.execute("SELECT cv.review_intake(%s,%s,%s,%s,%s,%s,%s)", args)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        # Synthetic database fixture only. Physical-file qualification remains Phase 08.
        c.execute(
            ("UPDATE cv.file_intent SET state='finalized',revision=revision+1 WHERE scope_id=%s"),
            (scope,),
        )
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        first = c.execute("SELECT cv.review_intake(%s,%s,%s,%s,%s,%s,%s)", args).fetchone()
        assert c.execute("SELECT cv.review_intake(%s,%s,%s,%s,%s,%s,%s)", args).fetchone() == first
        assert c.execute(
            "SELECT state,revision FROM cv.intake WHERE id=%s", (intake,)
        ).fetchone() == ("linked", 2)


def test_expiry_between_acceptance_and_commit_rolls_back(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        c.execute(
            "UPDATE cv.publication SET expires_at=clock_timestamp()+interval '2 seconds' "
            "WHERE id=%s",
            (publication["id"],),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="INTAKE_UNAVAILABLE"):
        with connect(db_config, passwords, "cv_public") as c:
            submit(c, publication, proof, uuid4())
            # A deliberately slow synthetic transaction crosses the publication expiry.
            c.execute("SELECT pg_sleep(2)")
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.intake WHERE publication_id=%s", (publication["id"],)
        ).fetchone() == (0,)
        assert c.execute(
            "SELECT scope_id FROM cv.public_upload_grant WHERE proof_digest=%s", (digest(proof),)
        ).fetchone() == (None,)


def test_foreign_position_snapshot_is_rejected(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        foreign_snapshot = uuid4()
        c.execute(
            "INSERT INTO cv.publication_snapshot "
            "VALUES(%s,%s,%s,%s,1,'Synthetic',NULL,'Different role',NULL,NULL,NULL,"
            "'Other JD','Apply',%s,clock_timestamp())",
            (
                identity("a"),
                foreign_snapshot,
                identity("a/position"),
                identity("a/jd"),
                identity("a/admin"),
            ),
        )
        with pytest.raises(psycopg.errors.CheckViolation, match="PUBLICATION_SNAPSHOT_MISMATCH"):
            c.execute(
                "INSERT INTO cv.public_upload_grant VALUES(%s,%s,%s,%s,%s,%s,%s,100,"
                "clock_timestamp(),%s,true,NULL)",
                (
                    identity("a"),
                    uuid4(),
                    publication["id"],
                    foreign_snapshot,
                    digest(str(uuid4())),
                    uuid4(),
                    digest("synthetic-pdf"),
                    publication["expiry"],
                ),
            )


def test_intake_source_cannot_be_rebound(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        with pytest.raises(psycopg.errors.CheckViolation, match="INTAKE_SOURCE_IMMUTABLE"):
            c.execute("UPDATE cv.intake SET receipt=%s WHERE receipt=%s", (uuid4(), receipt))
