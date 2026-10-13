"""Preserve publication pins and recheck anonymous acceptance at commit."""

from pathlib import Path

from alembic import op

revision = "0007_intake_commit"
down_revision = "0006_erasure_authority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("""
DROP TRIGGER immutable_delete ON cv.extraction;
DROP TRIGGER immutable_delete ON cv.evaluation;
DROP TRIGGER publication_identity ON cv.publication;
DROP TRIGGER grant_binding ON cv.public_upload_grant;
DROP TRIGGER intake_binding ON cv.intake;
DROP TRIGGER final_public_acceptance ON cv.intake;
DROP FUNCTION cv.publication_identity_check();
DROP FUNCTION cv.upload_grant_binding_check();
DROP FUNCTION cv.intake_binding_check();
DROP FUNCTION cv.final_public_acceptance_check();
""")
