"""Guarded transactional commands and current-authority checks."""

from pathlib import Path

from alembic import op

revision = "0002_commands"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("""
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM cv.agency) THEN RAISE EXCEPTION 'POPULATED_DOWNGRADE_FORBIDDEN'; END IF;
END $$;
""")
    op.execute(Path(__file__).with_name("0002_commands_down.sql").read_text(encoding="utf-8"))
