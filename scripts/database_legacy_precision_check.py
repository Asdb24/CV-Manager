"""Prove the precision repair refuses silently changing existing rounded history."""

import argparse
import json
from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
from cv_foundation.settings import DatabaseTestSettings
from database_migrate import migrate
from psycopg import sql
from sqlalchemy.exc import DBAPIError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    settings = DatabaseTestSettings.model_validate_json(args.config.read_text(encoding="utf-8"))
    passwords = json.loads(Path(settings.credential_file).read_text(encoding="utf-8"))
    suffix = uuid4().hex.translate(str.maketrans("0123456789", "ghijklmnop"))
    database = "cv_phase03_precision_" + suffix
    config_path = Path(settings.cluster_directory).parent / (database + ".json")
    config = settings.model_copy(update={"database": database})
    config_path.write_text(config.model_dump_json(), encoding="utf-8")

    def connect(name: str, *, autocommit: bool = False) -> psycopg.Connection[Any]:
        return psycopg.connect(
            host=config.host,
            port=config.port,
            user="cv_cluster_admin",
            password=passwords["cv_cluster_admin"],
            connect_timeout=config.connect_timeout_seconds,
            dbname=name,
            autocommit=autocommit,
        )

    created = False
    with connect("postgres", autocommit=True) as admin:
        try:
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER cv_migrator").format(sql.Identifier(database))
            )
            created = True
            migrate(config_path, "upgrade", "0010_final_command_authority")
            spec = spec_from_file_location(
                "phase03_legacy_seed", Path("tests/database/conftest.py")
            )
            if spec is None or spec.loader is None:
                raise RuntimeError("SYNTHETIC_FIXTURE_MODULE_MISSING")
            fixture = module_from_spec(spec)
            spec.loader.exec_module(fixture)
            fixture.seed_synthetic(config, passwords)
            rubric = uuid4()
            with connect(database) as c:
                c.execute("SELECT cv.bind_session('a/admin/proof')")
                c.execute(
                    "INSERT INTO cv.rubric_version(tenant_id,id,position_id,jd_id,engine_id,"
                    "version,"
                    "reference_date,definition,definition_digest,author_id) SELECT tenant_id,%s,"
                    "position_id,jd_id,engine_id,version+1,reference_date,definition,definition_digest,"
                    "author_id FROM cv.rubric_version WHERE id=%s",
                    (rubric, fixture.identity("a/rubric")),
                )
                c.execute(
                    "INSERT INTO cv.rubric_criterion SELECT tenant_id,%s,criterion_key,ordinal,"
                    "CASE ordinal WHEN 0 THEN 49.9999999999999999999999999999::numeric "
                    "ELSE 50.0000000000000000000000000001::numeric END,adapter,"
                    "mandatory_definition "
                    "FROM cv.rubric_criterion WHERE rubric_id=%s",
                    (rubric, fixture.identity("a/rubric")),
                )
                row = c.execute(
                    "SELECT cv.claim_evaluation(p.scope_id,r.position_id,r.id,r.jd_id,r.engine_id,"
                    "cv.canonical_digest_v1(p.factual_content),"
                    "cv.canonical_digest_v1(cv.calculation_snapshot_v1(r.tenant_id,r.id)),"
                    "cv.calculation_snapshot_v1(r.tenant_id,r.id)) FROM cv.rubric_version r "
                    "JOIN cv.profile_revision p ON p.tenant_id=r.tenant_id "
                    "WHERE r.id=%s AND p.id=%s",
                    (rubric, fixture.identity("a/person1/profile")),
                ).fetchone()
                if row is None:
                    raise RuntimeError("LEGACY_EVALUATION_MISSING")
                evaluation = row[0]
                c.execute(
                    "INSERT INTO cv.evaluation_component(tenant_id,scope_id,evaluation_id,"
                    "rubric_id,criterion_key,rating,weight,mandatory_status) "
                    "SELECT tenant_id,%s,%s,rubric_id,"
                    "criterion_key,CASE ordinal WHEN 0 THEN 1 ELSE 0 END,weight,'pass' "
                    "FROM cv.rubric_criterion WHERE rubric_id=%s",
                    (fixture.identity("a/person1/scope"), evaluation, rubric),
                )
                c.execute(
                    "UPDATE cv.evaluation SET state='complete',exact_total=12.5,total=13,"
                    "mandatory_status='pass' WHERE id=%s",
                    (evaluation,),
                )
            try:
                migrate(config_path, "upgrade", "head")
            except DBAPIError as error:
                if "LEGACY_ROUNDED_COMPONENT_REQUIRES_EXPLICIT_REPAIR" not in str(error.orig):
                    raise RuntimeError("UNEXPECTED_PRECISION_MIGRATION_FAILURE") from None
            else:
                raise RuntimeError("LEGACY_ROUNDED_HISTORY_WAS_NOT_REJECTED")
            with connect(database) as c:
                revision = c.execute("SELECT version_num FROM public.alembic_version").fetchone()
                result = c.execute(
                    "SELECT exact_total,total FROM cv.evaluation WHERE id=%s", (evaluation,)
                ).fetchone()
                if (
                    revision != ("0010_final_command_authority",)
                    or result is None
                    or result[1] != 13
                ):
                    raise RuntimeError("REJECTED_MIGRATION_CHANGED_HISTORY")
                components = c.execute(
                    "SELECT count(*) FROM cv.evaluation_component WHERE evaluation_id=%s "
                    "AND contribution IS DISTINCT FROM weight*rating/4",
                    (evaluation,),
                ).fetchone()
                if components != (0,):
                    raise RuntimeError("REJECTED_MIGRATION_CHANGED_COMPONENTS")
            evidence = {
                "observed_at": datetime.now(UTC).isoformat(),
                "attempted_head": json.loads(Path("contracts/migration-state.json").read_text())[
                    "head"
                ],
                "legacy_precision_upgrade_denied": "PASS",
                "old_revision_preserved": "PASS",
                "legacy_total_preserved": str(result[0]),
                "legacy_final_integer_preserved": result[1],
                "legacy_components_preserved": "PASS",
                "data": "isolated synthetic only",
            }
            Path("docs/phases/evidence-04/legacy-precision.json").write_text(
                json.dumps(evidence, indent=2) + "\n",
                encoding="utf-8",
            )
            print("LEGACY_PRECISION_UPGRADE_REFUSED_WITH_HISTORY_PRESERVED: PASS")
        finally:
            if created:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
                )
            config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
