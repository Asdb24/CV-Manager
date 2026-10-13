"""Published snapshots, explicit intake review and separate advisory history."""

from pathlib import Path

from alembic import op

revision = "0005_public_advisory"
down_revision = "0004_command_parameters"
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
    op.execute(Path(__file__).with_name("0005_public_advisory_down.sql").read_text(encoding="utf-8"))
