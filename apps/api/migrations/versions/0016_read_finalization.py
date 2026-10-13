"""Track authorized RLS reads until trusted transaction finalization."""

from pathlib import Path

from alembic import op

revision = "0016_read_finalization"
down_revision = "0015_source_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0016_read_finalization_down.sql").read_text("utf-8"))
