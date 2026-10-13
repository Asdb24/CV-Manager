"""Export schema metadata only, never credentials or recruitment rows."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg
from cv_foundation.settings import DatabaseTestSettings
from psycopg.rows import dict_row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = DatabaseTestSettings.model_validate_json(args.config.read_text())
    credentials = json.loads(Path(config.credential_file).read_text())
    catalog: dict[str, Any] = {}
    queries = {
        "tables": "SELECT c.relname AS name,c.relrowsecurity AS rls,"
        "c.relforcerowsecurity AS forced,"
        "pg_get_userbyid(c.relowner) AS owner FROM pg_class c JOIN pg_namespace n "
        "ON n.oid=c.relnamespace WHERE n.nspname='cv' AND c.relkind='r' ORDER BY c.relname",
        "columns": "SELECT c.relname AS table_name,a.attname AS name,"
        "format_type(a.atttypid,a.atttypmod) AS data_type,NOT a.attnotnull AS nullable,"
        "pg_get_expr(d.adbin,d.adrelid) AS default_expression,a.attgenerated AS generated "
        "FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n "
        "ON n.oid=c.relnamespace LEFT JOIN pg_attrdef d "
        "ON (d.adrelid,d.adnum)=(a.attrelid,a.attnum) "
        "WHERE n.nspname='cv' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped "
        "ORDER BY c.relname,a.attnum",
        "constraints": "SELECT c.conrelid::regclass::text AS table_name,c.conname AS name,"
        "c.contype AS kind,pg_get_constraintdef(c.oid) AS definition,c.convalidated AS validated "
        "FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace "
        "WHERE n.nspname='cv' ORDER BY table_name,c.conname",
        "indexes": "SELECT tablename,indexname,indexdef FROM pg_indexes "
        "WHERE schemaname='cv' ORDER BY tablename,indexname",
        "policies": "SELECT tablename,policyname,permissive,roles,cmd,qual,with_check "
        "FROM pg_policies WHERE schemaname='cv' ORDER BY tablename,policyname",
        "functions": "SELECT p.oid::regprocedure::text AS identity,p.prosecdef AS security_definer,"
        "pg_get_userbyid(p.proowner) AS owner,p.proconfig AS settings,"
        "pg_get_functiondef(p.oid) AS definition,p.proacl::text AS acl "
        "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
        "WHERE n.nspname='cv' ORDER BY identity",
        "triggers": "SELECT c.relname AS table_name,t.tgname AS name,pg_get_triggerdef(t.oid) "
        "AS definition FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='cv' AND NOT t.tgisinternal "
        "ORDER BY c.relname,t.tgname",
    }
    with psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.database,
        user="cv_migrator",
        password=credentials["cv_migrator"],
        connect_timeout=config.connect_timeout_seconds,
        options=f"-c statement_timeout={config.statement_timeout_ms} "
        f"-c lock_timeout={config.lock_timeout_ms}",
        row_factory=dict_row,
    ) as c:
        catalog["revision"] = c.execute("SELECT version_num FROM public.alembic_version").fetchone()
        for key, query in queries.items():
            catalog[key] = c.execute(query).fetchall()
    serialized = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    evidence = Path("docs/phases/evidence-04/schema-catalog.json")
    evidence.write_text(serialized, encoding="utf-8")
    lines = [
        "# PostgreSQL data dictionary",
        "",
        "Generated from the actual migrated PostgreSQL catalog by `scripts/database_catalog.py`.",
        "No recruitment records or credentials are exported. Read DATABASE_DESIGN.md for nullable "
        "semantics, authority, workflow and deletion limits.",
        "",
        "Catalog SHA-256: `" + hashlib.sha256(serialized.encode()).hexdigest() + "`.",
        "",
    ]
    for table in catalog["tables"]:
        name = table["name"]
        lines.extend(
            [
                "## " + name,
                "",
                f"Owner: `{table['owner']}`. RLS enabled: {table['rls']}; "
                f"forced: {table['forced']}.",
                "",
                "| Column | PostgreSQL type | Nullable | Default / generated expression |",
                "| --- | --- | --- | --- |",
            ]
        )
        for column in catalog["columns"]:
            if column["table_name"] == name:
                expression = (column["default_expression"] or "—").replace("|", "\\|")
                lines.append(
                    f"| {column['name']} | `{column['data_type']}` | {column['nullable']} | "
                    f"{expression} |"
                )
        lines.extend(["", "Constraints:", ""])
        for constraint in catalog["constraints"]:
            if constraint["table_name"] == "cv." + name:
                lines.append(f"- `{constraint['name']}`: `{constraint['definition']}`")
        lines.append("")
    Path("docs/database/DATA_DICTIONARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("SCHEMA_METADATA_EXPORTED: " + str(catalog["revision"]))


if __name__ == "__main__":
    main()
