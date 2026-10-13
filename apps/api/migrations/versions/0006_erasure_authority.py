"""Use private purge authority across PostgreSQL referential-action triggers."""

from alembic import op

revision = "0006_erasure_authority"
down_revision = "0005_public_advisory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
GRANT CREATE ON SCHEMA cv TO cv_guard;
ALTER FUNCTION cv.immutable_row() SECURITY DEFINER;
ALTER FUNCTION cv.immutable_row() OWNER TO cv_guard;
SET ROLE cv_guard;
REVOKE ALL ON FUNCTION cv.immutable_row() FROM PUBLIC;
CREATE OR REPLACE FUNCTION cv.tenant_allowed(t uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.current_authority() a
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id)=(a.tenant_id,a.user_id)
 WHERE a.tenant_id=t AND g.active AND cv.policy_live(t,g.purpose_id,'purpose'))
$$;
RESET ROLE;
DROP POLICY staff ON cv.candidate;
CREATE POLICY staff ON cv.candidate TO cv_runtime USING(
 cv.tenant_allowed(tenant_id) AND EXISTS(SELECT 1 FROM cv.privacy_scope s
 WHERE (s.tenant_id,s.candidate_id)=(candidate.tenant_id,candidate.id)
 AND cv.scope_allowed(s.tenant_id,s.id)));
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
""")


def downgrade() -> None:
    op.execute("""
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM cv.agency) THEN RAISE EXCEPTION 'POPULATED_DOWNGRADE_FORBIDDEN'; END IF;
END $$;
""")
