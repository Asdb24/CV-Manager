from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import psycopg
import pytest
from cv_foundation.settings import DatabaseTestSettings
from psycopg.types.json import Jsonb


def identity(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, "synthetic-cv-phase03/" + name)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def extraction_definition(c: psycopg.Connection[Any]) -> tuple[str, str, Jsonb]:
    definition = {
        "format": "cv-extraction-v1",
        "parser": {"implementation": "synthetic-parser", "version": 1, "rules": {}},
        "normalization": {"version": 1, "rules": {"whitespace": "preserve"}},
    }
    row = c.execute(
        "SELECT cv.canonical_digest_v1(%s),cv.canonical_digest_v1(%s)",
        (Jsonb(definition["parser"]), Jsonb(definition["normalization"])),
    ).fetchone()
    assert row is not None and isinstance(row[0], str) and isinstance(row[1], str)
    return row[0], row[1], Jsonb(definition)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--database-config", required=True)


@pytest.fixture(scope="session")
def db_config(pytestconfig: pytest.Config) -> DatabaseTestSettings:
    return DatabaseTestSettings.model_validate_json(
        Path(pytestconfig.getoption("database_config")).read_text()
    )


class Credentials(dict[str, str]):
    def __repr__(self) -> str:
        return "Credentials([REDACTED])"


@pytest.fixture(scope="session")
def passwords(db_config: DatabaseTestSettings) -> dict[str, str]:
    return Credentials(json.loads(Path(db_config.credential_file).read_text()))


def connect(
    config: DatabaseTestSettings, passwords: dict[str, str], role: str
) -> psycopg.Connection[Any]:
    return psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.database,
        user=role,
        password=passwords[role],
        connect_timeout=config.connect_timeout_seconds,
        options=f"-c statement_timeout={config.statement_timeout_ms} "
        f"-c lock_timeout={config.lock_timeout_ms}",
    )


@pytest.fixture(scope="session", autouse=True)
def seed(db_config: DatabaseTestSettings, passwords: dict[str, str]) -> None:
    seed_synthetic(db_config, passwords)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        for label in ("a/person1", "a/person2", "b/person1", "b/person2"):
            profile = identity(label + "/profile-v2")
            if c.execute("SELECT 1 FROM cv.profile_revision WHERE id=%s", (profile,)).fetchone():
                continue
            c.execute(
                "INSERT INTO cv.profile_revision SELECT tenant_id,scope_id,%s,2,id,"
                "factual_content,factual_digest,author_id,reason,created_at "
                "FROM cv.profile_revision WHERE id=%s",
                (profile, identity(label + "/profile")),
            )
            synthetic_source(c, identity(label[0]), identity(label + "/scope"), profile, label)


def synthetic_source(
    c: psycopg.Connection[Any], tenant: UUID, scope: UUID, profile: UUID, content: str
) -> tuple[UUID, UUID, UUID]:
    """Source fixture only: no file/parser execution or production records."""
    intent, document, extraction, evidence = uuid4(), uuid4(), uuid4(), uuid4()
    content_hash = digest(content)
    c.execute(
        "INSERT INTO cv.file_intent SELECT tenant_id,id,%s,%s,'resume','finalized',100,%s,"
        "consent_expires_at,1 FROM cv.privacy_scope WHERE (tenant_id,id)=(%s,%s)",
        (intent, uuid4(), content_hash, tenant, scope),
    )
    c.execute(
        "INSERT INTO cv.document_version VALUES(%s,%s,%s,%s,1,%s,'application/pdf',100,"
        "clock_timestamp(),clock_timestamp())",
        (tenant, scope, document, intent, content_hash),
    )
    c.execute(
        "INSERT INTO cv.extraction VALUES(%s,%s,%s,%s,%s,%s,%s,'claimed',NULL)",
        (tenant, scope, extraction, content_hash, *extraction_definition(c)),
    )
    c.execute(
        "INSERT INTO cv.extraction_document VALUES(%s,%s,%s,%s)",
        (tenant, scope, extraction, document),
    )
    c.execute(
        "INSERT INTO cv.evidence_span VALUES(%s,%s,%s,%s,1,0,6,'page1:0:6','Python',%s)",
        (tenant, scope, evidence, extraction, digest("Python")),
    )
    c.execute("UPDATE cv.extraction SET state='complete' WHERE id=%s", (extraction,))
    c.execute(
        "INSERT INTO cv.profile_source VALUES(%s,%s,%s,%s)", (tenant, scope, profile, extraction)
    )
    c.execute(
        "INSERT INTO cv.profile_evidence VALUES(%s,%s,%s,%s,'synthetic_fact')",
        (tenant, scope, profile, evidence),
    )
    return extraction, evidence, document


def seed_synthetic(db_config: DatabaseTestSettings, passwords: dict[str, str]) -> None:
    """Fixed identities and content; current expiry is fixture authority, never score input."""
    now = datetime.now(UTC)
    end = now + timedelta(seconds=db_config.seed_validity_seconds)
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        if c.execute(
            "SELECT count(*) FROM cv.agency WHERE id IN (%s,%s)", (identity("a"), identity("b"))
        ).fetchone() == (2,):
            # Reuse only the immutable, still-valid synthetic policy snapshot.
            assert c.execute(
                "SELECT bool_and(expires_at>clock_timestamp()) FROM cv.policy_version "
                "WHERE version='synthetic-v1'"
            ).fetchone() == (True,)
            return
        for label in ["a", "b"]:
            t = identity(label)
            admin = identity(label + "/admin")
            recruiter = identity(label + "/recruiter")
            c.execute(
                "INSERT INTO cv.agency VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (t, "synthetic-test-workspace", "SYNTHETIC agency " + label, now),
            )
            for user, role in [(admin, "admin"), (recruiter, "recruiter")]:
                c.execute(
                    "INSERT INTO cv.staff_user VALUES(%s,%s,%s,%s,true,%s) ON CONFLICT DO NOTHING",
                    (t, user, "synthetic-" + role, "synthetic-not-a-password-hash", now),
                )
                c.execute(
                    "INSERT INTO cv.membership VALUES(%s,%s,%s,true,1) ON CONFLICT DO NOTHING",
                    (t, user, role),
                )
                c.execute(
                    (
                        "INSERT INTO cv.staff_session VALUES(%s,%s,%s,%s,%s,NULL,%s) ON "
                        "CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        identity(label + "/" + role + "/session"),
                        user,
                        digest(label + "/" + role + "/proof"),
                        end,
                        now,
                    ),
                )
            for kind in ["purpose", "source", "consent", "retention", "erasure", "resource"]:
                c.execute(
                    (
                        "INSERT INTO cv.policy_version "
                        "VALUES(%s,%s,%s,%s,%s,%s,true,%s,%s,%s) ON CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        identity(label + "/" + kind),
                        kind,
                        "synthetic-v1",
                        admin,
                        "workspace-admin",
                        now,
                        end,
                        Jsonb(
                            {
                                "synthetic_only": True,
                                "fixture_validity_seconds": db_config.seed_validity_seconds,
                                "clock": "database-utc",
                                "owner": "synthetic-test",
                                "production_approval": False,
                            }
                        ),
                    ),
                )
            for user in [admin, recruiter]:
                c.execute(
                    "INSERT INTO cv.purpose_grant VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                    (t, user, identity(label + "/purpose")),
                )
            company = identity(label + "/company")
            position = identity(label + "/position")
            jd = identity(label + "/jd")
            engine = identity(label + "/engine")
            rubric = identity(label + "/rubric")
            c.execute(
                "INSERT INTO cv.company VALUES(%s,%s,%s,1,NULL) ON CONFLICT DO NOTHING",
                (t, company, "SYNTHETIC company " + label),
            )
            c.execute(
                "INSERT INTO cv.position VALUES(%s,%s,%s,%s,1,NULL) ON CONFLICT DO NOTHING",
                (t, position, company, "Synthetic developer"),
            )
            c.execute(
                "INSERT INTO cv.jd_version VALUES(%s,%s,%s,1,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (t, jd, position, "Synthetic JD", digest("Synthetic JD"), admin, now),
            )
            c.execute(
                (
                    "INSERT INTO cv.engine_definition VALUES(%s,%s,%s,%s,%s,%s,%s) ON "
                    "CONFLICT DO NOTHING"
                ),
                (
                    t,
                    engine,
                    "synthetic-v1",
                    Jsonb({"arithmetic": "exact", "rating_max": 4}),
                    digest("synthetic-engine"),
                    "final-integer-half-up",
                    "positive-weight-unknown-blocks-total",
                ),
            )
            c.execute(
                (
                    "INSERT INTO cv.rubric_version "
                    "VALUES(%s,%s,%s,%s,%s,1,NULL,%s,%s,%s) ON CONFLICT DO NOTHING"
                ),
                (
                    t,
                    rubric,
                    position,
                    jd,
                    engine,
                    Jsonb({"synthetic": True}),
                    digest("synthetic-rubric"),
                    admin,
                ),
            )
            for ordinal in [0, 1]:
                c.execute(
                    (
                        "INSERT INTO cv.rubric_criterion VALUES(%s,%s,%s,%s,50,%s,NULL) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        rubric,
                        "criterion" + str(ordinal),
                        ordinal,
                        Jsonb({"type": "synthetic-ordinal", "values": [0, 1, 2, 3, 4]}),
                    ),
                )
            for person in ["person1", "person2"]:
                candidate = identity(label + "/" + person)
                scope = identity(label + "/" + person + "/scope")
                c.execute(
                    "INSERT INTO cv.candidate VALUES(%s,%s,1,NULL) ON CONFLICT DO NOTHING",
                    (t, candidate),
                )
                c.execute(
                    """INSERT INTO cv.privacy_scope(
                tenant_id,id,candidate_id,purpose_id,privacy_epoch,
                source_policy_id,consent_policy_id,retention_policy_id,
                erasure_policy_id,resource_policy_id,
                consent_at,consent_expires_at,revoked_at,synthetic)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,true)
                ON CONFLICT DO NOTHING""",
                    (
                        t,
                        scope,
                        candidate,
                        identity(label + "/purpose"),
                        identity(label + "/" + person + "/epoch"),
                        *[
                            identity(label + "/" + k)
                            for k in ["source", "consent", "retention", "erasure", "resource"]
                        ],
                        now,
                        end,
                    ),
                )
                c.execute(
                    (
                        "INSERT INTO cv.contact_revision VALUES(%s,%s,%s,1,%s,%s,NULL,%s) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        scope,
                        identity(label + "/" + person + "/contact"),
                        "SYNTHETIC " + person,
                        person + "@example.invalid",
                        admin,
                    ),
                )
                c.execute(
                    (
                        "INSERT INTO cv.profile_revision "
                        "VALUES(%s,%s,%s,1,NULL,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        scope,
                        identity(label + "/" + person + "/profile"),
                        Jsonb({"synthetic_fact": "Python"}),
                        digest("same-facts"),
                        admin,
                        "Synthetic fixture",
                        now,
                    ),
                )
                c.execute(
                    (
                        "INSERT INTO cv.application "
                        "VALUES(%s,%s,%s,%s,%s,'received',1,NULL) ON CONFLICT DO NOTHING"
                    ),
                    (
                        t,
                        scope,
                        identity(label + "/" + person + "/application"),
                        candidate,
                        position,
                    ),
                )


@pytest.fixture
def runtime(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> Iterator[psycopg.Connection[Any]]:
    c = connect(db_config, passwords, "cv_runtime")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture
def owner(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> Iterator[psycopg.Connection[Any]]:
    c = connect(db_config, passwords, "cv_cluster_admin")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture
def publication(db_config: Any, passwords: dict[str, str]) -> dict[str, Any]:
    now = datetime.now(UTC)
    t = identity("a")
    snap, pub, resource, retention = (uuid4() for _ in range(4))
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        expiry_row = c.execute(
            "SELECT min(expires_at) FROM cv.policy_version "
            "WHERE tenant_id=%s AND version='synthetic-v1'",
            (t,),
        ).fetchone()
        assert expiry_row is not None
        expiry = expiry_row[0]
        for kind, policy, definition in [
            (
                "resource",
                resource,
                {
                    "public_submission_quota": 10,
                    "max_pdf_bytes": 10485760,
                    "contact_max_characters": 256,
                },
            ),
            ("retention", retention, {"retention_seconds": db_config.seed_validity_seconds}),
        ]:
            c.execute(
                "INSERT INTO cv.policy_version VALUES(%s,%s,%s,%s,%s,%s,true,%s,%s,%s)",
                (
                    t,
                    policy,
                    kind,
                    str(policy),
                    identity("a/admin"),
                    "workspace-admin",
                    now,
                    expiry,
                    Jsonb(definition),
                ),
            )
        # A unique fixture position avoids conflicting immutable snapshot versions.
        position, jd = uuid4(), uuid4()
        c.execute(
            "INSERT INTO cv.position VALUES(%s,%s,%s,'SYNTHETIC public position',1,NULL)",
            (t, position, identity("a/company")),
        )
        c.execute(
            "INSERT INTO cv.jd_version VALUES(%s,%s,%s,1,'Synthetic published JD',%s,%s,%s)",
            (t, jd, position, digest("public-jd"), identity("a/admin"), now),
        )
        c.execute(
            (
                "INSERT INTO cv.publication_snapshot "
                "VALUES(%s,%s,%s,%s,1,'Synthetic agency',NULL,'Synthetic "
                "role','Vietnam','remote','full-time','Synthetic JD','Synthetic "
                "instructions',%s,%s)"
            ),
            (t, snap, position, jd, identity("a/admin"), now),
        )
        c.execute(
            ("INSERT INTO cv.publication VALUES(%s,%s,%s,%s,'published',%s,1,%s,%s,%s,%s,%s,%s)"),
            (
                t,
                pub,
                position,
                snap,
                expiry,
                identity("a/purpose"),
                identity("a/source"),
                identity("a/consent"),
                retention,
                identity("a/erasure"),
                resource,
            ),
        )
    return {"id": pub, "snapshot": snap, "expiry": expiry, "tenant": t, "position": position}
