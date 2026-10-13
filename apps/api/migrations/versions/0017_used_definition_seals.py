"""Seal construction sets as soon as a canonical or advisory record uses them."""

from pathlib import Path

from alembic import op

revision = "0017_used_definition_seals"
down_revision = "0016_read_finalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0017_used_definition_seals_down.sql").read_text("utf-8"))
