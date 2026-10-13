from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest
from cv_foundation.settings import DatabaseTestSettings
from psycopg.types.json import Jsonb

from .conftest import connect, extraction_definition, identity
from .test_core import bind


def calculation(c: psycopg.Connection[Any], rubric: UUID | None = None) -> tuple[Any, ...]:
    rubric = rubric or identity("a/rubric")
    row = c.execute(
        "SELECT cv.canonical_digest_v1(factual_content),"
        "cv.calculation_snapshot_v2(tenant_id,scope_id,%s,id) FROM cv.profile_revision WHERE id=%s",
        (rubric, identity("a/person1/profile-v2")),
    ).fetchone()
    assert row is not None
    facts, definition = row
    hashed = c.execute("SELECT cv.canonical_digest_v1(%s)", (Jsonb(definition),)).fetchone()
    assert hashed is not None
    return (
        identity("a/person1/scope"),
        identity("a/position"),
        rubric,
        identity("a/jd"),
        identity("a/engine"),
        facts,
        hashed[0],
        Jsonb(definition),
        identity("a/person1/profile-v2"),
    )


def claim(c: psycopg.Connection[Any], args: tuple[Any, ...]) -> Any:
    row = c.execute("SELECT cv.claim_evaluation(%s,%s,%s,%s,%s,%s,%s,%s,%s)", args).fetchone()
    assert row is not None
    return row[0]


def test_canonical_json_numeric_and_key_normalization(runtime: psycopg.Connection[Any]) -> None:
    assert runtime.execute(
        'SELECT cv.canonical_digest_v1(\'{"b":[1.000,2],"a":null}\')='
        'cv.canonical_digest_v1(\'{"a":null,"b":[1,2.0]}\')'
    ).fetchone() == (True,)
    assert runtime.execute(
        "SELECT cv.canonical_digest_v1('[1,2]')<>cv.canonical_digest_v1('[2,1]')"
    ).fetchone() == (True,)


def test_atomic_evaluation_claims_use_actual_content(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    def attempt() -> Any:
        with connect(db_config, passwords, "cv_runtime") as c:
            bind(c)
            return claim(c, calculation(c))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt(), range(2)))
    assert results[0] == results[1]
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        assert claim(c, calculation(c)) == results[0]
        assert c.execute(
            "SELECT count(*) FROM cv.audit_event WHERE action='evaluation.claim' AND record_id=%s",
            (results[0],),
        ).fetchone() == (1,)


@pytest.mark.parametrize("extra", [{"upload_id": "synthetic-upload"}, {"clock": "2030-01-01"}])
def test_transient_inputs_cannot_redefine_calculation(
    runtime: psycopg.Connection[Any], extra: dict[str, str]
) -> None:
    bind(runtime)
    args = calculation(runtime)
    definition = args[-2].obj | extra
    hashed = runtime.execute("SELECT cv.canonical_digest_v1(%s)", (Jsonb(definition),)).fetchone()
    assert hashed is not None
    with pytest.raises(psycopg.errors.CheckViolation, match="CALCULATION_BINDING_MISMATCH"):
        claim(runtime, (*args[:6], hashed[0], Jsonb(definition), args[-1]))


def test_published_rubric_cannot_gain_zero_weight_criterion(owner: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.CheckViolation, match="PUBLISHED_RUBRIC_IMMUTABLE"):
        owner.execute(
            "INSERT INTO cv.rubric_criterion VALUES(%s,%s,'late',2,0,'{}',NULL)",
            (identity("a"), identity("a/rubric")),
        )


@pytest.mark.parametrize(
    ("ratings", "exact", "total", "mandatory", "state"),
    [
        ((1, 0), Decimal("12.5"), 13, "pass", "complete"),
        ((3, 3), Decimal("75"), 75, "fail", "complete"),
        ((None, 4), None, None, "unknown", "incomplete"),
    ],
)
def test_exact_components_unknown_and_final_half_up(
    owner: psycopg.Connection[Any],
    ratings: tuple[int | None, int | None],
    exact: Decimal | None,
    total: int | None,
    mandatory: str,
    state: str,
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
        "adapter,'{\"synthetic_required\":true}' FROM cv.rubric_criterion WHERE rubric_id=%s",
        (rubric, identity("a/rubric")),
    )
    evaluation = claim(owner, calculation(owner, rubric))
    for ordinal, rating in enumerate(ratings):
        owner.execute(
            "INSERT INTO cv.evaluation_component(tenant_id,scope_id,evaluation_id,rubric_id,"
            "criterion_key,rating,weight,mandatory_status) VALUES(%s,%s,%s,%s,%s,%s,50,%s)",
            (
                identity("a"),
                identity("a/person1/scope"),
                evaluation,
                rubric,
                f"criterion{ordinal}",
                rating,
                mandatory,
            ),
        )
    owner.execute(
        "UPDATE cv.evaluation SET state=%s,exact_total=%s,total=%s,mandatory_status=%s WHERE id=%s",
        (state, exact, total, mandatory, evaluation),
    )
    owner.execute("SET CONSTRAINTS ALL IMMEDIATE")
    assert owner.execute(
        "SELECT exact_total,total,mandatory_status FROM cv.evaluation WHERE id=%s",
        (evaluation,),
    ).fetchone() == (exact, total, mandatory)
    with pytest.raises(psycopg.errors.CheckViolation, match="IMMUTABLE_RESULT"):
        owner.execute("UPDATE cv.evaluation SET total=70 WHERE id=%s", (evaluation,))


def test_sealed_extraction_cannot_gain_evidence(owner: psycopg.Connection[Any]) -> None:
    extraction = uuid4()
    owner.execute(
        "INSERT INTO cv.extraction VALUES(%s,%s,%s,repeat('1',64),%s,%s,%s,'claimed',NULL)",
        (identity("a"), identity("a/person2/scope"), extraction, *extraction_definition(owner)),
    )
    owner.execute("UPDATE cv.extraction SET state='failed' WHERE id=%s", (extraction,))
    with pytest.raises(psycopg.errors.CheckViolation, match="SEALED_RESULT_CHILD"):
        owner.execute(
            "INSERT INTO cv.evidence_span VALUES(%s,%s,%s,%s,1,0,3,'page1','PDF',repeat('4',64))",
            (identity("a"), identity("a/person2/scope"), uuid4(), extraction),
        )
