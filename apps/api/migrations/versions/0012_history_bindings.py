"""Seal advisory child sets and bind occurrence job and factual content."""

from pathlib import Path

from alembic import op

revision = "0012_history_bindings"
down_revision = "0011_exact_and_required_inputs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0012_history_bindings_down.sql").read_text("utf-8"))
