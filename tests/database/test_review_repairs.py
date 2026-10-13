from decimal import Decimal
from typing import Any
from uuid import uuid4

import psycopg
import pytest

from .conftest import connect, identity
from .test_core import bind
from .test_public import grant, submit


def test_long_decimal_weights_do_not_round_before_final_total(
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
        "INSERT INTO cv.rubric_criterion SELECT tenant_id,%s,criterion_key,ordinal,"
        "CASE ordinal WHEN 0 THEN 49.9999999999999999999999999999::numeric "
        "ELSE 50.0000000000000000000000000001::numeric END,adapter,mandatory_definition "
        "FROM cv.rubric_criterion WHERE rubric_id=%s",
        (rubric, identity("a/rubric")),
    )
    # Keep the exact SQL JSON numbers on the server; Python's default JSON
    # float decoding would lose the long-decimal fixture before validation.
    row = owner.execute(
        "SELECT cv.claim_evaluation(p.scope_id,r.position_id,r.id,r.jd_id,r.engine_id,"
        "cv.canonical_digest_v1(p.factual_content),"
        "cv.canonical_digest_v1(cv.calculation_snapshot_v2(r.tenant_id,p.scope_id,r.id,p.id)),"
        "cv.calculation_snapshot_v2(r.tenant_id,p.scope_id,r.id,p.id),p.id) "
        "FROM cv.rubric_version r "
        "JOIN cv.profile_revision p ON p.tenant_id=r.tenant_id WHERE r.id=%s AND p.id=%s",
        (rubric, identity("a/person1/profile-v2")),
    ).fetchone()
    assert row is not None
    evaluation = row[0]
    owner.execute(
        "INSERT INTO cv.evaluation_component(tenant_id,scope_id,evaluation_id,rubric_id,"
        "criterion_key,rating,weight,mandatory_status) SELECT tenant_id,%s,%s,rubric_id,"
        "criterion_key,CASE ordinal WHEN 0 THEN 1 ELSE 0 END,weight,'pass' "
        "FROM cv.rubric_criterion WHERE rubric_id=%s",
        (identity("a/person1/scope"), evaluation, rubric),
    )
    exact = Decimal("12.499999999999999999999999999975")
    owner.execute(
        "UPDATE cv.evaluation SET state='complete',exact_total=%s,total=12,mandatory_status='pass' "
        "WHERE id=%s",
        (exact, evaluation),
    )
    owner.execute("SET CONSTRAINTS ALL IMMEDIATE")
    assert owner.execute(
        "SELECT sum(contribution) FROM cv.evaluation_component WHERE evaluation_id=%s",
        (evaluation,),
    ).fetchone() == (exact,)
    assert owner.execute(
        "SELECT exact_total,total FROM cv.evaluation WHERE id=%s", (evaluation,)
    ).fetchone() == (exact, 12)


def test_missing_stage_revision_is_denied(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    with pytest.raises(psycopg.errors.SerializationFailure, match="REVISION_CONFLICT"):
        runtime.execute(
            "SELECT cv.move_stage(%s,%s,NULL,'evaluating',NULL,%s)",
            (identity("a/person1/scope"), identity("a/person1/application"), uuid4()),
        )


def test_missing_review_revision_is_denied(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id,id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        with pytest.raises(psycopg.errors.CheckViolation, match="REVIEW_CONFLICT"):
            c.execute(
                "SELECT cv.review_intake(%s,%s,NULL,'reject',NULL,'Synthetic review',%s)",
                (*row, uuid4()),
            )


@pytest.mark.parametrize("missing", ["publication", "snapshot", "consent"])
def test_missing_displayed_public_version_is_denied(
    db_config: Any, passwords: dict[str, str], publication: dict[str, Any], missing: str
) -> None:
    proof = grant(db_config, passwords, publication)
    pins = [publication["id"], publication["snapshot"], identity("a/consent")]
    pins[["publication", "snapshot", "consent"].index(missing)] = None
    with connect(db_config, passwords, "cv_public") as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege, match="INTAKE_UNAVAILABLE"):
            c.execute(
                "SELECT cv.accept_intake(%s,%s,%s,%s,'SYNTHETIC','test@example.invalid',"
                "NULL,true,%s)",
                (proof, *pins, uuid4()),
            )
