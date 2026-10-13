"""Admin-only synthetic policy activation, revocation and revisioned purpose grants."""

from pathlib import Path

from alembic import op

revision = "0019_identity_policy_authority"
down_revision = "0018_staff_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(
        Path(__file__).with_name("0019_identity_policy_authority_down.sql").read_text("utf-8")
    )
