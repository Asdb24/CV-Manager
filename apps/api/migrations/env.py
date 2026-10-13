"""Alembic runs only on an explicitly provided migration-owner connection."""

from alembic import context
from sqlalchemy.engine import Connection

connection = context.config.attributes.get("connection")
if context.is_offline_mode() or not isinstance(connection, Connection):
    raise RuntimeError("EXPLICIT_MIGRATION_CONNECTION_REQUIRED")
if connection.exec_driver_sql("SELECT current_user").scalar_one() != "cv_migrator":
    raise RuntimeError("MIGRATION_OWNER_REQUIRED")
direction = context.config.attributes.get("direction")
if direction not in {"upgrade", "downgrade"}:
    raise RuntimeError("EXPLICIT_MIGRATION_DIRECTION_REQUIRED")
if (
    direction == "downgrade"
    and connection.exec_driver_sql("SELECT to_regclass('cv.agency') IS NOT NULL").scalar_one()
):
    # Forced RLS must not make a populated database appear empty to its owner.
    connection.exec_driver_sql("SET LOCAL ROLE cv_guard")
    populated = connection.exec_driver_sql("SELECT EXISTS(SELECT 1 FROM cv.agency)").scalar_one()
    connection.exec_driver_sql("RESET ROLE")
    if populated:
        raise RuntimeError("POPULATED_DOWNGRADE_FORBIDDEN")
    # Historical down revisions restore guard-owned functions. Permit creation
    # only inside this empty-database migration transaction, then revoke below.
    connection.exec_driver_sql("GRANT CREATE ON SCHEMA cv TO cv_guard")


def maintain_empty_downgrade_privilege(**_kwargs: object) -> None:
    # Each frozen revision may revoke its temporary grant. Restore it for the
    # next empty-only down step; the outer transaction revokes it at the end.
    if (
        direction == "downgrade"
        and connection.exec_driver_sql(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='cv')"
        ).scalar_one()
    ):
        connection.exec_driver_sql("GRANT CREATE ON SCHEMA cv TO cv_guard")


context.configure(
    connection=connection,
    transactional_ddl=True,
    on_version_apply=maintain_empty_downgrade_privilege,
)
with context.begin_transaction():
    context.run_migrations()
    if (
        direction == "downgrade"
        and connection.exec_driver_sql(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='cv')"
        ).scalar_one()
    ):
        connection.exec_driver_sql("REVOKE CREATE ON SCHEMA cv FROM cv_guard")
