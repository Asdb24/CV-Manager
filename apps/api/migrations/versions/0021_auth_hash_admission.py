"""Separate denied reservations from admitted dummy checks; admit bootstrap before hashing."""

from pathlib import Path

from alembic import op

revision = "0021_auth_hash_admission"
down_revision = "0020_auth_finalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text("utf-8"))


def downgrade() -> None:
    op.execute(Path(__file__).with_name("0021_auth_hash_admission_down.sql").read_text("utf-8"))
