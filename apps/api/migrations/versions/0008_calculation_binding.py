"""Derive canonical content identity and seal definition/result children."""

from pathlib import Path

from alembic import op

revision = "0008_calculation_binding"
down_revision = "0007_intake_commit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0008_calculation_binding_down.sql").read_text("utf-8"))
