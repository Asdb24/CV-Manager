"""Canonical source equality and immutable provenance, on real PostgreSQL."""

from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb

from .conftest import identity, synthetic_source
from .test_calculation import calculation, claim
from .test_core import bind


def clone_profile(c: psycopg.Connection[Any]) -> UUID:
    profile = uuid4()
    c.execute(
        "INSERT INTO cv.profile_revision SELECT p.tenant_id,p.scope_id,%s,"
        "(SELECT max(version)+1 FROM cv.profile_revision v WHERE "
        "(v.tenant_id,v.scope_id)=(p.tenant_id,p.scope_id)),p.id,p.factual_content,"
        "p.factual_digest,p.author_id,'SYNTHETIC new occurrence',clock_timestamp() "
        "FROM cv.profile_revision p WHERE p.id=%s",
        (profile, identity("a/person1/profile-v2")),
    )
    return profile


def copy_sources(c: psycopg.Connection[Any], profile: UUID, fact: str = "synthetic_fact") -> None:
    c.execute(
        "INSERT INTO cv.profile_source SELECT tenant_id,scope_id,%s,extraction_id "
        "FROM cv.profile_source WHERE profile_id=%s",
        (profile, identity("a/person1/profile-v2")),
    )
    c.execute(
        "INSERT INTO cv.profile_evidence SELECT tenant_id,scope_id,%s,evidence_id,%s "
        "FROM cv.profile_evidence WHERE profile_id=%s",
        (profile, fact, identity("a/person1/profile-v2")),
    )


def evaluation(c: psycopg.Connection[Any], profile: UUID) -> UUID:
    row = c.execute(
        "SELECT cv.claim_evaluation(p.scope_id,r.position_id,r.id,r.jd_id,r.engine_id,"
        "cv.canonical_digest_v1(p.factual_content),"
        "cv.canonical_digest_v1(cv.calculation_snapshot_v2(p.tenant_id,p.scope_id,r.id,p.id)),"
        "cv.calculation_snapshot_v2(p.tenant_id,p.scope_id,r.id,p.id),p.id) "
        "FROM cv.profile_revision p JOIN cv.rubric_version r ON r.tenant_id=p.tenant_id "
        "WHERE p.id=%s AND r.id=%s",
        (profile, identity("a/rubric")),
    ).fetchone()
    assert row is not None and isinstance(row[0], UUID)
    return row[0]


@pytest.mark.parametrize("change", ["bytes", "parser", "normalization", "reviewed_evidence"])
def test_changed_source_definition_cannot_reuse_old_canonical_result(
    owner: psycopg.Connection[Any], change: str
) -> None:
    bind(owner)
    original = evaluation(owner, identity("a/person1/profile-v2"))
    profile = clone_profile(owner)
    if change == "bytes":
        synthetic_source(owner, identity("a"), identity("a/person1/scope"), profile, str(profile))
    elif change == "reviewed_evidence":
        copy_sources(owner, profile, "synthetic_fact.reviewed")
    else:
        row = owner.execute(
            "SELECT x.id,x.definition,d.document_id FROM cv.profile_source p "
            "JOIN cv.extraction x ON (x.tenant_id,x.scope_id,x.id)="
            "(p.tenant_id,p.scope_id,p.extraction_id) JOIN cv.extraction_document d "
            "ON (d.tenant_id,d.scope_id,d.extraction_id)=(x.tenant_id,x.scope_id,x.id) "
            "WHERE p.profile_id=%s ORDER BY d.document_id LIMIT 1",
            (identity("a/person1/profile-v2"),),
        ).fetchone()
        assert row is not None
        old, definition, document = row
        definition[change]["version"] = 2
        extraction, evidence = uuid4(), uuid4()
        owner.execute(
            "INSERT INTO cv.extraction SELECT tenant_id,scope_id,%s,content_digest,"
            "cv.canonical_digest_v1(%s),cv.canonical_digest_v1(%s),%s,'claimed',NULL "
            "FROM cv.extraction WHERE id=%s",
            (
                extraction,
                Jsonb(definition["parser"]),
                Jsonb(definition["normalization"]),
                Jsonb(definition),
                old,
            ),
        )
        owner.execute(
            "INSERT INTO cv.evidence_span SELECT tenant_id,scope_id,%s,%s,page,start_offset,"
            "end_offset,semantic_locator,text_content,content_digest FROM cv.evidence_span "
            "WHERE extraction_id=%s",
            (evidence, extraction, old),
        )
        owner.execute("UPDATE cv.extraction SET state='complete' WHERE id=%s", (extraction,))
        owner.execute(
            "INSERT INTO cv.extraction_document VALUES(%s,%s,%s,%s)",
            (identity("a"), identity("a/person1/scope"), extraction, document),
        )
        owner.execute(
            "INSERT INTO cv.profile_source VALUES(%s,%s,%s,%s)",
            (identity("a"), identity("a/person1/scope"), profile, extraction),
        )
        owner.execute(
            "INSERT INTO cv.profile_evidence VALUES(%s,%s,%s,%s,'synthetic_fact')",
            (identity("a"), identity("a/person1/scope"), profile, evidence),
        )
    updated = evaluation(owner, profile)
    assert updated != original
    assert owner.execute(
        "SELECT a.factual_digest=b.factual_digest,a.calculation_digest<>b.calculation_digest "
        "FROM cv.evaluation a,cv.evaluation b WHERE a.id=%s AND b.id=%s",
        (original, updated),
    ).fetchone() == (True, True)


def test_new_profile_upload_ids_and_times_preserve_semantic_reuse(
    owner: psycopg.Connection[Any],
) -> None:
    bind(owner)
    original = evaluation(owner, identity("a/person1/profile-v2"))
    profile = clone_profile(owner)
    copy_sources(owner, profile)
    row = owner.execute(
        "SELECT x.extraction_id,d.id,d.intent_id FROM cv.profile_source x "
        "JOIN cv.extraction_document b ON (b.tenant_id,b.scope_id,b.extraction_id)="
        "(x.tenant_id,x.scope_id,x.extraction_id) JOIN cv.document_version d "
        "ON (d.tenant_id,d.scope_id,d.id)=(b.tenant_id,b.scope_id,b.document_id) "
        "WHERE x.profile_id=%s ORDER BY d.id LIMIT 1",
        (profile,),
    ).fetchone()
    assert row is not None
    extraction, old_document, old_intent = row
    intent, document = uuid4(), uuid4()
    owner.execute(
        "INSERT INTO cv.file_intent SELECT tenant_id,scope_id,%s,%s,purpose,state,byte_count,"
        "content_digest,expires_at,1 FROM cv.file_intent WHERE id=%s",
        (intent, uuid4(), old_intent),
    )
    owner.execute(
        "INSERT INTO cv.document_version SELECT tenant_id,scope_id,%s,%s,version+1,"
        "content_digest,media_type,byte_count,clock_timestamp(),clock_timestamp() "
        "FROM cv.document_version WHERE id=%s",
        (document, intent, old_document),
    )
    owner.execute(
        "INSERT INTO cv.extraction_document VALUES(%s,%s,%s,%s)",
        (identity("a"), identity("a/person1/scope"), extraction, document),
    )
    assert evaluation(owner, profile) == original
    owner.execute(
        "INSERT INTO cv.evaluation_occurrence VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            identity("a"),
            identity("a/person1/scope"),
            uuid4(),
            original,
            identity("a/person1/application"),
            profile,
            document,
            identity("a/admin"),
        ),
    )
    row = owner.execute(
        "SELECT calculation_definition FROM cv.evaluation WHERE id=%s", (original,)
    ).fetchone()
    assert row is not None
    assert all(
        str(value) not in str(row[0])
        for value in (profile, document, old_document, extraction, intent)
    )


@pytest.mark.parametrize("table", ["profile_source", "profile_evidence"])
def test_published_profile_cannot_gain_source_or_evidence(
    owner: psycopg.Connection[Any], table: str
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation, match="PROFILE_SOURCE_SET_SEALED"):
        owner.execute(
            psycopg.sql.SQL("INSERT INTO cv.{} SELECT * FROM cv.{} WHERE profile_id=%s").format(
                psycopg.sql.Identifier(table), psycopg.sql.Identifier(table)
            ),
            (identity("a/person1/profile-v2"),),
        )


def test_legacy_evaluation_claim_cannot_bypass_source_binding(
    owner: psycopg.Connection[Any],
) -> None:
    bind(owner)
    with pytest.raises(psycopg.errors.CheckViolation, match="PROFILE_SOURCE_REQUIRED"):
        owner.execute(
            "SELECT cv.claim_evaluation(%s,%s,%s,%s,%s,repeat('1',64),repeat('2',64),'{}')",
            (
                identity("a/person1/scope"),
                identity("a/position"),
                identity("a/rubric"),
                identity("a/jd"),
                identity("a/engine"),
            ),
        )


def test_source_snapshot_cannot_expose_foreign_person(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    assert runtime.execute(
        "SELECT cv.profile_source_snapshot_v1(%s,%s,%s)",
        (identity("b"), identity("b/person1/scope"), identity("b/person1/profile-v2")),
    ).fetchone() == (None,)


def test_profile_evidence_cannot_change_after_evaluation_consumes_early_check(
    owner: psycopg.Connection[Any],
) -> None:
    bind(owner)
    profile = clone_profile(owner)
    copy_sources(owner, profile, "synthetic_fact.current")
    evaluation(owner, profile)
    owner.execute("SET CONSTRAINTS ALL IMMEDIATE")
    with pytest.raises(psycopg.errors.CheckViolation, match="PROFILE_SOURCE_ALREADY_USED"):
        owner.execute(
            "INSERT INTO cv.profile_evidence SELECT tenant_id,scope_id,profile_id,evidence_id,"
            "'synthetic_fact.late' FROM cv.profile_evidence WHERE profile_id=%s",
            (profile,),
        )


def test_rubric_cannot_change_after_evaluation_consumes_early_check(
    owner: psycopg.Connection[Any],
) -> None:
    bind(owner)
    rubric = uuid4()
    owner.execute(
        "INSERT INTO cv.rubric_version(tenant_id,id,position_id,jd_id,engine_id,version,"
        "reference_date,definition,definition_digest,author_id) "
        "SELECT tenant_id,%s,position_id,jd_id,engine_id,version+1,reference_date,definition,"
        "definition_digest,author_id FROM cv.rubric_version WHERE id=%s",
        (rubric, identity("a/rubric")),
    )
    owner.execute(
        "INSERT INTO cv.rubric_criterion SELECT tenant_id,%s,criterion_key,ordinal,weight,"
        "adapter,mandatory_definition FROM cv.rubric_criterion WHERE rubric_id=%s",
        (rubric, identity("a/rubric")),
    )
    claim(owner, calculation(owner, rubric))
    owner.execute("SET CONSTRAINTS ALL IMMEDIATE")
    with pytest.raises(psycopg.errors.CheckViolation, match="PUBLISHED_RUBRIC_IMMUTABLE"):
        owner.execute(
            "INSERT INTO cv.rubric_criterion VALUES(%s,%s,'late',2,0,'{}',NULL)",
            (identity("a"), rubric),
        )
