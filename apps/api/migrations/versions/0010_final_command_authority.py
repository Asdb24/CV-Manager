"""Recheck exact command purpose and erasure authority at commit."""

from pathlib import Path

from alembic import op

revision = "0010_final_command_authority"
down_revision = "0009_extraction_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0010_final_command_authority_down.sql").read_text("utf-8"))
