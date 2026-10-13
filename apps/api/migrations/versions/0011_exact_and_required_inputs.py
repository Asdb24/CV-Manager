"""Preserve decimal precision and reject absent revision/public version inputs."""

from pathlib import Path

from alembic import op

revision = "0011_exact_and_required_inputs"
down_revision = "0010_final_command_authority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(
        Path(__file__).with_name("0011_exact_and_required_inputs_down.sql").read_text("utf-8")
    )
