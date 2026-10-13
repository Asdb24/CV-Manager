"""Bind extraction definitions to their digests and permit irreversible revocation."""

from pathlib import Path

from alembic import op

revision = "0009_extraction_policy"
down_revision = "0008_calculation_binding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0009_extraction_policy_down.sql").read_text("utf-8"))
