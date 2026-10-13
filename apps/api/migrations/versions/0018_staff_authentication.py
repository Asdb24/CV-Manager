"""One-time instance bootstrap and private staff authentication persistence."""

from pathlib import Path

from alembic import op

revision = "0018_staff_authentication"
down_revision = "0017_used_definition_seals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0018_staff_authentication_down.sql").read_text("utf-8"))
