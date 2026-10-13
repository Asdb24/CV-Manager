"""Repair heterogeneous trigger records without rewriting applied migrations."""

from alembic import op

revision = "0003_constraint_repair"
down_revision = "0002_commands"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
CREATE OR REPLACE FUNCTION cv.rubric_total_check() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; r uuid; BEGIN
 t:=NEW.tenant_id;
 IF TG_TABLE_NAME='rubric_version' THEN r:=NEW.id; ELSE r:=NEW.rubric_id; END IF;
 IF (SELECT coalesce(sum(weight),0) FROM cv.rubric_criterion WHERE tenant_id=t AND rubric_id=r)<>100
 THEN RAISE EXCEPTION 'RUBRIC_WEIGHT_SUM' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
GRANT USAGE ON SCHEMA public TO cv_guard;
""")


def downgrade() -> None:
    op.execute("""
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM cv.agency) THEN RAISE EXCEPTION 'POPULATED_DOWNGRADE_FORBIDDEN'; END IF;
END $$;
CREATE OR REPLACE FUNCTION cv.rubric_total_check() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; r uuid; BEGIN
 t:=NEW.tenant_id; r:=CASE WHEN TG_TABLE_NAME='rubric_version' THEN NEW.id ELSE NEW.rubric_id END;
 IF (SELECT coalesce(sum(weight),0) FROM cv.rubric_criterion WHERE tenant_id=t AND rubric_id=r)<>100
 THEN RAISE EXCEPTION 'RUBRIC_WEIGHT_SUM' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
REVOKE USAGE ON SCHEMA public FROM cv_guard;
""")
