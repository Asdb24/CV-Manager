from typing import Any
from uuid import uuid4

import psycopg
import pytest
from cv_foundation.settings import DatabaseTestSettings
from psycopg.types.json import Jsonb

from .conftest import connect, digest, extraction_definition, identity
from .test_core import bind
from .test_public import grant, submit


@pytest.mark.parametrize("tamper", ["parser", "normalization", "upload_id"])
def test_extraction_definition_cannot_disagree_with_claim(
    runtime: psycopg.Connection[Any], tamper: str
) -> None:
    bind(runtime)
    parser, normalization, encoded = extraction_definition(runtime)
    definition = dict(encoded.obj)
    if tamper == "upload_id":
        definition[tamper] = str(uuid4())
    else:
        definition[tamper] = {"version": "different"}
    with pytest.raises(psycopg.errors.CheckViolation, match="EXTRACTION_BINDING_MISMATCH"):
        runtime.execute(
            "SELECT cv.claim_extraction(%s,%s,%s,%s,%s)",
            (
                identity("a/person1/scope"),
                digest(str(uuid4())),
                parser,
                normalization,
                Jsonb(definition),
            ),
        )


@pytest.mark.parametrize("invalid", ["missing", "wrong-kind", "real-data"])
def test_invalid_policy_scope_cannot_be_created(
    owner: psycopg.Connection[Any], invalid: str
) -> None:
    source = (
        uuid4()
        if invalid == "missing"
        else identity("a/consent" if invalid == "wrong-kind" else "a/source")
    )
    with pytest.raises(psycopg.errors.CheckViolation, match="POLICY_SCOPE_INVALID"):
        owner.execute(
            "INSERT INTO cv.privacy_scope SELECT tenant_id,%s,candidate_id,purpose_id,"
            "gen_random_uuid(),%s,consent_policy_id,retention_policy_id,erasure_policy_id,"
            "resource_policy_id,consent_at,consent_expires_at,NULL,%s,created_at "
            "FROM cv.privacy_scope WHERE id=%s",
            (uuid4(), source, invalid != "real-data", identity("a/person1/scope")),
        )


def test_expired_policy_does_not_prevent_irreversible_revocation(
    owner: psycopg.Connection[Any],
) -> None:
    source, scope = uuid4(), uuid4()
    owner.execute(
        "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
        "synthetic_only,activated_at,clock_timestamp()+interval '1 second',definition "
        "FROM cv.policy_version WHERE id=%s",
        (source, str(source), identity("a/source")),
    )
    owner.execute(
        "INSERT INTO cv.privacy_scope SELECT s.tenant_id,%s,candidate_id,purpose_id,"
        "gen_random_uuid(),%s,consent_policy_id,retention_policy_id,erasure_policy_id,"
        "resource_policy_id,consent_at,p.expires_at,NULL,synthetic,created_at "
        "FROM cv.privacy_scope s JOIN cv.policy_version p ON p.id=%s WHERE s.id=%s",
        (scope, source, source, identity("a/person1/scope")),
    )
    owner.execute("SELECT pg_sleep(1)")
    owner.execute("UPDATE cv.privacy_scope SET revoked_at=clock_timestamp() WHERE id=%s", (scope,))
    assert owner.execute(
        "SELECT revoked_at IS NOT NULL FROM cv.privacy_scope WHERE id=%s",
        (scope,),
    ).fetchone() == (True,)
    with pytest.raises(psycopg.errors.CheckViolation):
        owner.execute("UPDATE cv.privacy_scope SET revoked_at=NULL WHERE id=%s", (scope,))


def test_staff_expiry_at_commit_rolls_back_mutation_and_audit(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    proof, key = str(uuid4()), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        c.execute(
            "INSERT INTO cv.staff_session VALUES(%s,%s,%s,%s,"
            "clock_timestamp()+interval '2 seconds',NULL,clock_timestamp())",
            (identity("a"), uuid4(), identity("a/admin"), digest(proof)),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="AUTH_REVOKED"):
        with connect(db_config, passwords, "cv_runtime") as c:
            bind(c, proof)
            c.execute(
                "SELECT cv.rename_company(%s,1,'SYNTHETIC expired mutation',%s,%s)",
                (identity("a/company"), identity("a/purpose"), key),
            )
            c.execute("SELECT pg_sleep(2)")
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


@pytest.mark.parametrize(
    "proof,candidate",
    [
        ("a/admin/proof", "b/person1"),
        ("b/admin/proof", "b/person1"),
    ],
)
def test_intake_cannot_link_foreign_person_or_tenant(
    db_config: DatabaseTestSettings,
    passwords: dict[str, str],
    publication: dict[str, Any],
    proof: str,
    candidate: str,
) -> None:
    upload_proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, upload_proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id,id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope, intake = row
        c.execute(
            "UPDATE cv.file_intent SET state='finalized',revision=revision+1 WHERE scope_id=%s",
            (scope,),
        )
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c, proof)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute(
                "SELECT cv.review_intake(%s,%s,1,'link',%s,'Synthetic review',%s)",
                (scope, intake, identity(candidate), uuid4()),
            )
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT state,revision FROM cv.intake WHERE id=%s", (intake,)
        ).fetchone() == ("pending", 1)
        assert c.execute(
            "SELECT candidate_id FROM cv.privacy_scope WHERE id=%s", (scope,)
        ).fetchone() == (None,)


def test_expired_erasing_session_cannot_commit_scope_deletion(
    db_config: DatabaseTestSettings, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    upload_proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, upload_proof, uuid4())
    proof, request = str(uuid4()), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope = row[0]
        c.execute(
            "INSERT INTO cv.staff_session VALUES(%s,%s,%s,%s,"
            "clock_timestamp()+interval '2 seconds',NULL,clock_timestamp())",
            (identity("a"), uuid4(), identity("a/admin"), digest(proof)),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="ERASURE_AUTH_REVOKED"):
        with connect(db_config, passwords, "cv_runtime") as c:
            bind(c, proof)
            c.execute("SELECT cv.erase_scope(%s,%s)", (scope, request))
            c.execute("SELECT pg_sleep(2)")
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT count(*) FROM cv.intake WHERE receipt=%s", (receipt,)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.erasure_request WHERE id=%s", (request,)
        ).fetchone() == (0,)


def test_exact_command_purpose_expiry_cannot_use_another_active_purpose(
    db_config: DatabaseTestSettings, passwords: dict[str, str]
) -> None:
    purpose, key = uuid4(), uuid4()
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        c.execute(
            "INSERT INTO cv.policy_version SELECT tenant_id,%s,kind,%s,owner_user_id,owner_role,"
            "synthetic_only,activated_at,clock_timestamp()+interval '2 seconds',definition "
            "FROM cv.policy_version WHERE id=%s",
            (purpose, str(purpose), identity("a/purpose")),
        )
        c.execute(
            "INSERT INTO cv.purpose_grant VALUES(%s,%s,%s,true)",
            (identity("a"), identity("a/admin"), purpose),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="COMMAND_PURPOSE_REVOKED"):
        with connect(db_config, passwords, "cv_runtime") as c:
            bind(c)
            c.execute(
                "SELECT cv.rename_company(%s,1,'SYNTHETIC purpose expiry',%s,%s)",
                (identity("a/company"), purpose, key),
            )
            c.execute("SELECT pg_sleep(2)")
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        assert c.execute(
            "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
        ).fetchone() == (1,)
        assert c.execute(
            "SELECT count(*) FROM cv.command_result WHERE operation_key=%s", (key,)
        ).fetchone() == (0,)


def test_explicit_existing_person_link_is_idempotent(
    db_config: DatabaseTestSettings, passwords: dict[str, str], publication: dict[str, Any]
) -> None:
    proof = grant(db_config, passwords, publication)
    with connect(db_config, passwords, "cv_public") as c:
        receipt = submit(c, publication, proof, uuid4())
    with connect(db_config, passwords, "cv_cluster_admin") as c:
        row = c.execute("SELECT scope_id,id FROM cv.intake WHERE receipt=%s", (receipt,)).fetchone()
        assert row is not None
        scope, intake = row
        c.execute(
            "UPDATE cv.file_intent SET state='finalized',revision=revision+1 WHERE scope_id=%s",
            (scope,),
        )
    args = (scope, intake, identity("a/person1"), uuid4())
    with connect(db_config, passwords, "cv_runtime") as c:
        bind(c)
        query = "SELECT cv.review_intake(%s,%s,1,'link',%s,'Synthetic explicit link',%s)"
        first = c.execute(query, args).fetchone()
        assert c.execute(query, args).fetchone() == first
        assert c.execute(
            "SELECT candidate_id FROM cv.privacy_scope WHERE id=%s", (scope,)
        ).fetchone() == (identity("a/person1"),)
        assert c.execute(
            "SELECT count(*) FROM cv.intake_review WHERE intake_id=%s", (intake,)
        ).fetchone() == (1,)


def test_changed_payload_and_stale_revision_rollback(runtime: psycopg.Connection[Any]) -> None:
    bind(runtime)
    key = uuid4()
    args = (identity("a/company"), identity("a/purpose"), key)
    runtime.execute("SELECT cv.rename_company(%s,1,'SYNTHETIC first',%s,%s)", args)
    with pytest.raises(psycopg.errors.CheckViolation, match="IDEMPOTENCY_CONFLICT"):
        runtime.execute("SELECT cv.rename_company(%s,1,'SYNTHETIC different',%s,%s)", args)
    runtime.rollback()
    bind(runtime)
    assert runtime.execute(
        "SELECT revision FROM cv.company WHERE id=%s", (identity("a/company"),)
    ).fetchone() == (1,)
    with pytest.raises(psycopg.errors.SerializationFailure, match="REVISION_CONFLICT"):
        runtime.execute(
            "SELECT cv.move_stage(%s,%s,99,'evaluating',NULL,%s)",
            (identity("a/person1/scope"), identity("a/person1/application"), uuid4()),
        )


def test_current_membership_revocation_hides_staff_rows(owner: psycopg.Connection[Any]) -> None:
    owner.execute(
        "UPDATE cv.membership SET active=false,revision=revision+1 WHERE user_id=%s",
        (identity("a/recruiter"),),
    )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="AUTH_REQUIRED"):
        bind(owner, "a/recruiter/proof")


def test_revoked_policy_denies_scope_reuse(owner: psycopg.Connection[Any]) -> None:
    owner.execute(
        "INSERT INTO cv.policy_revocation VALUES(%s,%s,clock_timestamp(),%s,%s)",
        (identity("a"), identity("a/source"), identity("a/admin"), "Synthetic revocation"),
    )
    bind(owner)
    assert owner.execute(
        "SELECT cv.scope_allowed(%s,%s)", (identity("a"), identity("a/person1/scope"))
    ).fetchone() == (False,)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="SCOPE_DENIED"):
        owner.execute(
            "SELECT cv.claim_extraction(%s,%s,%s,%s,%s)",
            (identity("a/person1/scope"), digest(str(uuid4())), *extraction_definition(owner)),
        )
