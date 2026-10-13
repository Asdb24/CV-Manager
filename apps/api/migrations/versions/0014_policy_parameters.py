"""Qualify policy snapshot parameters in transaction finalization."""

from pathlib import Path

from alembic import op

revision = "0014_policy_parameters"
down_revision = "0013_transaction_finalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0014_policy_parameters_down.sql").read_text("utf-8"))
