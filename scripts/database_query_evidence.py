"""Populate explicit synthetic volume and measure real restricted-role queries."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg
from cv_foundation.settings import DatabaseTestSettings


def identity(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, "synthetic-cv-phase03/" + name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = DatabaseTestSettings.model_validate_json(args.config.read_text())
    credentials = json.loads(Path(config.credential_file).read_text())

    def connect(role: str) -> psycopg.Connection[Any]:
        return psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.database,
            user=role,
            password=credentials[role],
            connect_timeout=config.connect_timeout_seconds,
            options=f"-c statement_timeout={config.statement_timeout_ms} "
            f"-c lock_timeout={config.lock_timeout_ms}",
        )

    tenant = identity("b")
    with connect("cv_cluster_admin") as c:
        if c.execute("SELECT name FROM cv.agency WHERE id=%s", (tenant,)).fetchone() != (
            "SYNTHETIC agency b",
        ):
            raise RuntimeError("ISOLATED_SYNTHETIC_SEED_REQUIRED")
        with c.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO cv.company VALUES(%s,%s,%s,1,NULL) ON CONFLICT DO NOTHING",
                [
                    (tenant, identity(f"b/query/company/{i}"), f"SYNTHETIC query company {i:06d}")
                    for i in range(config.synthetic_company_count)
                ],
            )
            cursor.executemany(
                "INSERT INTO cv.candidate VALUES(%s,%s,1,NULL) ON CONFLICT DO NOTHING",
                [
                    (tenant, identity(f"b/query/person/{i}"))
                    for i in range(config.synthetic_person_count)
                ],
            )
            cursor.executemany(
                "INSERT INTO cv.privacy_scope SELECT tenant_id,%s,%s,purpose_id,%s,"
                "source_policy_id,consent_policy_id,retention_policy_id,erasure_policy_id,"
                "resource_policy_id,consent_at,consent_expires_at,NULL,synthetic,created_at "
                "FROM cv.privacy_scope WHERE id=%s ON CONFLICT DO NOTHING",
                [
                    (
                        identity(f"b/query/scope/{i}"),
                        identity(f"b/query/person/{i}"),
                        identity(f"b/query/epoch/{i}"),
                        identity("b/person1/scope"),
                    )
                    for i in range(config.synthetic_person_count)
                ],
            )
            cursor.executemany(
                "INSERT INTO cv.application VALUES(%s,%s,%s,%s,%s,'received',1,NULL) "
                "ON CONFLICT DO NOTHING",
                [
                    (
                        tenant,
                        identity(f"b/query/scope/{i}"),
                        identity(f"b/query/application/{i}"),
                        identity(f"b/query/person/{i}"),
                        identity("b/position"),
                    )
                    for i in range(config.synthetic_person_count)
                ],
            )
        for table in (
            "company",
            "candidate",
            "privacy_scope",
            "application",
            "purpose_grant",
            "policy_version",
            "staff_session",
            "membership",
        ):
            c.execute(psycopg.sql.SQL("ANALYZE cv.{}").format(psycopg.sql.Identifier(table)))
        version = c.execute("SELECT version()").fetchone()
        revision = c.execute("SELECT version_num FROM public.alembic_version").fetchone()
        counts = {
            table: c.execute(
                psycopg.sql.SQL("SELECT count(*) FROM cv.{} WHERE tenant_id=%s").format(
                    psycopg.sql.Identifier(table)
                ),
                (tenant,),
            ).fetchone()
            for table in ("company", "candidate", "privacy_scope", "application")
        }
    queries = {
        "company_page": (
            "SELECT id,name,revision FROM cv.company WHERE tenant_id=%s AND removed_at IS NULL "
            "ORDER BY id LIMIT %s",
            (tenant, config.query_page_size),
        ),
        "pipeline_page": (
            "SELECT id,candidate_id,scope_id,stage,revision FROM cv.application "
            "WHERE tenant_id=%s AND position_id=%s AND stage='received' AND removed_at IS NULL "
            "ORDER BY id LIMIT %s",
            (tenant, identity("b/position"), config.query_page_size),
        ),
        "person_applications": (
            "SELECT id,position_id,stage FROM cv.application WHERE tenant_id=%s AND "
            "candidate_id=%s ORDER BY id LIMIT %s",
            (tenant, identity("b/query/person/0"), config.query_page_size),
        ),
    }
    measured: dict[str, Any] = {}
    with connect("cv_runtime") as c:
        c.execute("SELECT cv.bind_session(%s)", ("b/admin/proof",))
        for name, (query, params) in queries.items():
            row = c.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query, params).fetchone()
            if row is None:
                raise RuntimeError("QUERY_PLAN_MISSING")
            measured[name] = {"query": query, "plan": row[0]}
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "postgresql": version,
        "revision": revision,
        "role": "cv_runtime",
        "scope": "synthetic agency b",
        "counts": counts,
        "page_size": config.query_page_size,
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "queries": measured,
        "limits": "Single local synthetic sample. No production latency or throughput claim.",
    }
    Path("docs/phases/evidence-04/query-plans.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"counts": counts, "measured_queries": list(measured)}))


if __name__ == "__main__":
    main()
