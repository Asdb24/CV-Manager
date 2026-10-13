"""Retain identity-policy finalization obligations through early checks and retries."""

from pathlib import Path

from alembic import op

revision = "0020_auth_finalization"
down_revision = "0019_identity_policy_authority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0020_auth_finalization_down.sql").read_text("utf-8"))
