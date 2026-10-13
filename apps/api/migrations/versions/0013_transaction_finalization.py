"""Retain private transaction obligations through early constraint validation."""

from pathlib import Path

from alembic import op

revision = "0013_transaction_finalization"
down_revision = "0012_history_bindings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0013_transaction_finalization_down.sql").read_text("utf-8"))
