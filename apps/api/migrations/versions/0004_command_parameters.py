"""Qualify parameters that collide with PostgreSQL table row references."""

from pathlib import Path

from alembic import op

revision = "0004_command_parameters"
down_revision = "0003_constraint_repair"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    # Function changes are compatible with the empty predecessor; never undo repairs
    # on populated databases. The following empty down removes commands in 0002.
    op.execute("""
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM cv.agency) THEN RAISE EXCEPTION 'POPULATED_DOWNGRADE_FORBIDDEN'; END IF;
END $$;
""")
