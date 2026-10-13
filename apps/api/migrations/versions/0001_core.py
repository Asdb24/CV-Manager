"""Agency domain, exact version bindings and protected staff persistence."""

from pathlib import Path

from alembic import op

revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    # Empty development rollback only. Production recovery is backup/forward repair.
    op.execute("""
DO $$ DECLARE n bigint; BEGIN
  SELECT count(*) INTO n FROM cv.agency;
  IF n <> 0 THEN RAISE EXCEPTION 'POPULATED_DOWNGRADE_FORBIDDEN'; END IF;
END $$;
DROP SCHEMA cv CASCADE;
""")
