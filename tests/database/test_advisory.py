"""Persistence evidence only; no model execution or device attestation is implied."""

from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest
from cv_foundation.settings import DatabaseTestSettings

from .conftest import connect, digest, extraction_definition, identity
from .test_core import bind


@pytest.fixture
def advisory_graph(db_config: DatabaseTestSettings, passwords: dict[str, str]) -> dict[str, UUID]:
    ids = {
        key: uuid4()
        for key in (
            "scope",
            "person",
            "profile",
            "application",
            "extraction",
            "evidence",
            "manifest",
            "task",
            "run",
            "finding",
            "questions",
            "question",
            "review",
            "evaluation",
            "document",
            "intent",
        )
    }
    # All content is synthetic. Privileged fixture construction is deliberately
    # separate from the actual restricted logins used to verify visibility.
    params: dict[str, Any] = dict(ids)
    params.update(
        tenant=identity("a"), actor=identity("a/admin"), digest=digest("advisory-fixture")
    )
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        parser, normalizer, definition = extraction_definition(c)
        params.update(parser=parser, normalizer=normalizer, definition=definition)
        c.execute("INSERT INTO cv.candidate VALUES(%(tenant)s,%(person)s,1,NULL)", params)
        c.execute(
            "INSERT INTO cv.privacy_scope SELECT tenant_id,%(scope)s,%(person)s,purpose_id,"
            "gen_random_uuid(),source_policy_id,consent_policy_id,retention_policy_id,"
            "erasure_policy_id,resource_policy_id,consent_at,consent_expires_at,NULL,synthetic,"
            "created_at FROM cv.privacy_scope WHERE id=%(original)s",
            params | {"original": identity("a/person1/scope")},
        )
        c.execute(
            "INSERT INTO cv.profile_revision SELECT tenant_id,%(scope)s,%(profile)s,1,NULL,"
            "factual_content,factual_digest,author_id,reason,created_at FROM cv.profile_revision "
            "WHERE id=%(original)s",
            params | {"original": identity("a/person1/profile")},
        )
        c.execute(
            "INSERT INTO cv.application SELECT tenant_id,%(scope)s,%(application)s,%(person)s,"
            "position_id,'received',1,NULL FROM cv.application WHERE id=%(original)s",
            params | {"original": identity("a/person1/application")},
        )
        c.execute(
            "INSERT INTO cv.extraction VALUES(%(tenant)s,%(scope)s,%(extraction)s,%(digest)s,"
            "%(parser)s,%(normalizer)s,%(definition)s,'claimed',NULL)",
            params,
        )
        c.execute(
            "INSERT INTO cv.evidence_span VALUES(%(tenant)s,%(scope)s,%(evidence)s,"
            "%(extraction)s,1,0,9,'page1:0:9','SYNTHETIC',%(digest)s)",
            params,
        )
        c.execute(
            "UPDATE cv.extraction SET state='complete',semantic_digest=%(digest)s "
            "WHERE id=%(extraction)s",
            params,
        )
        c.execute(
            "INSERT INTO cv.file_intent SELECT tenant_id,id,%(intent)s,gen_random_uuid(),"
            "'resume','finalized',100,%(digest)s,consent_expires_at,1 "
            "FROM cv.privacy_scope WHERE id=%(scope)s",
            params,
        )
        c.execute(
            "INSERT INTO cv.document_version VALUES(%(tenant)s,%(scope)s,%(document)s,"
            "%(intent)s,1,%(digest)s,'application/pdf',100,clock_timestamp(),clock_timestamp())",
            params,
        )
        c.execute(
            "INSERT INTO cv.extraction_document "
            "VALUES(%(tenant)s,%(scope)s,%(extraction)s,%(document)s)",
            params,
        )
        c.execute(
            "INSERT INTO cv.profile_source VALUES(%(tenant)s,%(scope)s,%(profile)s,%(extraction)s)",
            params,
        )
        c.execute(
            "INSERT INTO cv.profile_evidence "
            "VALUES(%(tenant)s,%(scope)s,%(profile)s,%(evidence)s,'synthetic_fact')",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_manifest SELECT %(tenant)s,%(scope)s,%(manifest)s,"
            "%(application)s,a.position_id,%(profile)s,j.id,%(digest)s,%(digest)s,%(digest)s,"
            "%(digest)s,%(digest)s,%(digest)s,%(digest)s,'{}',%(actor)s,s.consent_expires_at "
            "FROM cv.application a JOIN cv.jd_version j "
            "ON (j.tenant_id,j.position_id)=(a.tenant_id,a.position_id) "
            "JOIN cv.privacy_scope s ON (s.tenant_id,s.id)=(a.tenant_id,a.scope_id) "
            "WHERE a.id=%(application)s",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_manifest_evidence "
            "VALUES(%(tenant)s,%(scope)s,%(manifest)s,%(evidence)s)",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_task SELECT tenant_id,scope_id,%(task)s,id,%(actor)s,"
            "'completed',expires_at,1 FROM cv.advisory_manifest WHERE id=%(manifest)s",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_run VALUES(%(tenant)s,%(scope)s,%(run)s,%(task)s,"
            "%(manifest)s,1,'synthetic-device-claim','synthetic-runtime-claim','{}',%(actor)s,"
            "clock_timestamp(),'unattested-client-claim',%(digest)s,"
            '\'{"tie_break":"semantic_locator_ascending"}\',clock_timestamp())',
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_evidence VALUES(%(tenant)s,%(scope)s,%(run)s,"
            "%(manifest)s,%(evidence)s,'synthetic-criterion',1,0.5)",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_finding VALUES(%(tenant)s,%(scope)s,%(finding)s,%(run)s,"
            "'synthetic-rule','information-to-verify','Thông tin cần xác minh')",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_finding_evidence VALUES(%(tenant)s,%(scope)s,%(finding)s,"
            "%(run)s,'synthetic-criterion',%(evidence)s)",
            params,
        )
        c.execute(
            "INSERT INTO cv.question_set VALUES(%(tenant)s,%(scope)s,%(questions)s,"
            "%(run)s,%(digest)s)",
            params,
        )
        c.execute(
            "INSERT INTO cv.question_revision VALUES(%(tenant)s,%(scope)s,%(question)s,"
            "%(questions)s,%(run)s,'experience',1,NULL,%(finding)s,"
            "'Bạn có thể mô tả kinh nghiệm liên quan?',NULL,NULL)",
            params,
        )
        c.execute(
            "INSERT INTO cv.advisory_review VALUES(%(tenant)s,%(scope)s,%(review)s,%(run)s,"
            "%(finding)s,%(actor)s,'needs-verification','Synthetic review',clock_timestamp())",
            params,
        )
        c.execute(
            "INSERT INTO cv.evaluation(tenant_id,scope_id,id,position_id,rubric_id,jd_id,engine_id,"
            "factual_digest,calculation_digest,calculation_definition,state,source_profile_id) "
            "SELECT r.tenant_id,%(scope)s,%(evaluation)s,r.position_id,r.id,r.jd_id,r.engine_id,"
            "cv.canonical_digest_v1(p.factual_content),"
            "cv.canonical_digest_v1(cv.calculation_snapshot_v2(r.tenant_id,p.scope_id,r.id,p.id)),"
            "cv.calculation_snapshot_v2(r.tenant_id,p.scope_id,r.id,p.id),'claimed',p.id "
            "FROM cv.rubric_version r "
            "JOIN cv.profile_revision p ON (p.tenant_id,p.id)=(r.tenant_id,%(profile)s) "
            "WHERE r.id=%(rubric)s",
            params | {"rubric": identity("a/rubric")},
        )
        c.execute(
            "INSERT INTO cv.evaluation_component(tenant_id,scope_id,evaluation_id,rubric_id,"
            "criterion_key,rating,weight,mandatory_status) SELECT tenant_id,%(scope)s,"
            "%(evaluation)s,rubric_id,criterion_key,3,weight,'pass' FROM cv.rubric_criterion "
            "WHERE rubric_id=%(rubric)s",
            params | {"rubric": identity("a/rubric")},
        )
        c.execute(
            "UPDATE cv.evaluation SET state='complete',exact_total=75,total=75,"
            "mandatory_status='pass' "
            "WHERE id=%(evaluation)s",
            params,
        )
    return ids


def test_advisory_is_private_and_claim_is_not_attestation(
    db_config: DatabaseTestSettings, passwords: dict[str, str], advisory_graph: dict[str, UUID]
) -> None:
    with connect(db_config, passwords, "cv_runtime") as c:
        assert c.execute("SELECT * FROM cv.advisory_run").fetchall() == []
        bind(c)
        assert c.execute(
            "SELECT execution_verification,authorization_verified_by FROM cv.advisory_run "
            "WHERE id=%s",
            (advisory_graph["run"],),
        ).fetchone() == ("unattested-client-claim", identity("a/admin"))
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c, "b/admin/proof")
        assert (
            c.execute(
                "SELECT * FROM cv.advisory_run WHERE id=%s", (advisory_graph["run"],)
            ).fetchall()
            == []
        )


def test_advisory_question_edits_preserve_history(
    owner: psycopg.Connection[Any], advisory_graph: dict[str, UUID]
) -> None:
    g = advisory_graph
    second = uuid4()
    owner.execute(
        "INSERT INTO cv.question_revision SELECT tenant_id,scope_id,%s,question_set_id,run_id,"
        "question_key,2,id,finding_id,'Vui lòng nêu một ví dụ cụ thể.',%s,'Synthetic edit' "
        "FROM cv.question_revision WHERE id=%s",
        (second, identity("a/admin"), g["question"]),
    )
    rows = owner.execute(
        "SELECT version,previous_id FROM cv.question_revision WHERE question_set_id=%s "
        "ORDER BY version",
        (g["questions"],),
    ).fetchall()
    assert rows == [(1, None), (2, g["question"])]
    assert owner.execute(
        "SELECT exact_total,total,mandatory_status FROM cv.evaluation WHERE id=%s",
        (g["evaluation"],),
    ).fetchone() == (75, 75, "pass")
    assert owner.execute(
        "SELECT stage,revision FROM cv.application WHERE id=%s",
        (g["application"],),
    ).fetchone() == ("received", 1)
    with pytest.raises(psycopg.errors.CheckViolation, match="IMMUTABLE_HISTORY"):
        owner.execute(
            "UPDATE cv.question_revision SET vietnamese_text='changed' WHERE id=%s",
            (g["question"],),
        )


def test_advisory_foreign_person_evidence_is_rejected(
    owner: psycopg.Connection[Any], advisory_graph: dict[str, UUID]
) -> None:
    g = advisory_graph
    # Sealing rejects additions before a foreign child can reach its FK check.
    with pytest.raises(psycopg.errors.CheckViolation, match="ADVISORY_CHILD_SET_SEALED"):
        owner.execute(
            "INSERT INTO cv.advisory_manifest_evidence VALUES(%s,%s,%s,%s)",
            (identity("a"), identity("a/person2/scope"), g["manifest"], g["evidence"]),
        )


@pytest.mark.parametrize(
    "table", ["advisory_manifest_evidence", "advisory_evidence", "advisory_finding"]
)
def test_committed_advisory_sets_cannot_grow(
    owner: psycopg.Connection[Any], advisory_graph: dict[str, UUID], table: str
) -> None:
    g = advisory_graph
    with pytest.raises(psycopg.errors.CheckViolation, match="ADVISORY_CHILD_SET_SEALED"):
        if table == "advisory_manifest_evidence":
            owner.execute(
                "INSERT INTO cv.advisory_manifest_evidence VALUES(%s,%s,%s,%s)",
                (identity("a"), g["scope"], g["manifest"], uuid4()),
            )
        elif table == "advisory_evidence":
            owner.execute(
                "INSERT INTO cv.advisory_evidence VALUES(%s,%s,%s,%s,%s,'late',1,0.5)",
                (identity("a"), g["scope"], g["run"], g["manifest"], g["evidence"]),
            )
        else:
            owner.execute(
                "INSERT INTO cv.advisory_finding VALUES(%s,%s,%s,%s,'late',"
                "'information-to-verify','Synthetic late finding')",
                (identity("a"), g["scope"], uuid4(), g["run"]),
            )


def test_question_edit_cannot_skip_revision(
    owner: psycopg.Connection[Any], advisory_graph: dict[str, UUID]
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation, match="QUESTION_REVISION_GAP"):
        owner.execute(
            "INSERT INTO cv.question_revision SELECT tenant_id,scope_id,%s,question_set_id,"
            "run_id,question_key,3,id,finding_id,'Synthetic gap',%s,'Synthetic edit' "
            "FROM cv.question_revision WHERE id=%s",
            (uuid4(), identity("a/admin"), advisory_graph["question"]),
        )


@pytest.mark.parametrize("mismatch", ["job", "facts", "document"])
def test_occurrence_must_match_evaluation_job_and_facts(
    owner: psycopg.Connection[Any], advisory_graph: dict[str, UUID], mismatch: str
) -> None:
    g = advisory_graph
    intent, document = uuid4(), uuid4()
    owner.execute(
        "INSERT INTO cv.file_intent SELECT tenant_id,id,%s,%s,'resume','finalized',100,"
        "repeat('1',64),consent_expires_at,1 FROM cv.privacy_scope WHERE id=%s",
        (intent, uuid4(), g["scope"]),
    )
    owner.execute(
        "INSERT INTO cv.document_version VALUES(%s,%s,%s,%s,1,repeat('1',64),'application/pdf',"
        "100,clock_timestamp(),clock_timestamp())",
        (identity("a"), g["scope"], document, intent),
    )
    foreign_document, document = document, g["document"]
    application, profile = g["application"], g["profile"]
    valid_occurrence = uuid4()
    owner.execute(
        "INSERT INTO cv.evaluation_occurrence VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            identity("a"),
            g["scope"],
            valid_occurrence,
            g["evaluation"],
            application,
            profile,
            document,
            identity("a/admin"),
        ),
    )
    assert owner.execute(
        "SELECT id FROM cv.evaluation_occurrence WHERE id=%s", (valid_occurrence,)
    ).fetchone() == (valid_occurrence,)
    if mismatch == "job":
        position, application = uuid4(), uuid4()
        owner.execute(
            "INSERT INTO cv.position VALUES(%s,%s,%s,'Synthetic different job',1,NULL)",
            (identity("a"), position, identity("a/company")),
        )
        owner.execute(
            "INSERT INTO cv.application VALUES(%s,%s,%s,%s,%s,'received',1,NULL)",
            (identity("a"), g["scope"], application, g["person"], position),
        )
    elif mismatch == "document":
        document = foreign_document
    else:
        profile = uuid4()
        owner.execute(
            "INSERT INTO cv.profile_revision VALUES(%s,%s,%s,2,%s,'{\"different\":true}',"
            "repeat('2',64),%s,'Synthetic facts',clock_timestamp())",
            (identity("a"), g["scope"], profile, g["profile"], identity("a/admin")),
        )
    with pytest.raises(psycopg.errors.CheckViolation, match="EVALUATION_OCCURRENCE_MISMATCH"):
        owner.execute(
            "INSERT INTO cv.evaluation_occurrence VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                identity("a"),
                g["scope"],
                uuid4(),
                g["evaluation"],
                application,
                profile,
                document,
                identity("a/admin"),
            ),
        )


def test_advisory_graph_is_removed_by_authorized_erasure(
    db_config: DatabaseTestSettings, passwords: dict[str, str], advisory_graph: dict[str, UUID]
) -> None:
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        c.execute("SELECT cv.erase_scope(%s,%s)", (advisory_graph["scope"], uuid4()))
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        for table in (
            "advisory_manifest",
            "advisory_manifest_evidence",
            "advisory_task",
            "advisory_run",
            "advisory_evidence",
            "advisory_finding",
            "advisory_finding_evidence",
            "question_set",
            "question_revision",
            "advisory_review",
            "profile_revision",
            "profile_source",
            "profile_evidence",
            "extraction_document",
            "evidence_span",
            "extraction",
            "evaluation",
            "document_version",
            "file_intent",
            "evaluation_component",
            "evaluation_evidence",
            "evaluation_explanation",
        ):
            assert c.execute(
                psycopg.sql.SQL("SELECT count(*) FROM cv.{} WHERE scope_id=%s").format(
                    psycopg.sql.Identifier(table)
                ),
                (advisory_graph["scope"],),
            ).fetchone() == (0,)
