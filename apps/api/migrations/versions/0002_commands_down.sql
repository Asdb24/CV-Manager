DO $$ DECLARE r record; BEGIN
 FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='cv' LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS final_auth ON cv.%I',r.tablename);
 END LOOP;
 FOR r IN SELECT indexname FROM pg_indexes WHERE schemaname='cv' AND indexname LIKE 'fk_%' LOOP
  EXECUTE format('DROP INDEX cv.%I',r.indexname);
 END LOOP;
END $$;
DROP TRIGGER revoke_policy_lock ON cv.policy_revocation;
DROP FUNCTION cv.rename_company(uuid,integer,text,uuid,uuid),cv.move_stage(uuid,uuid,integer,cv.stage,text,uuid),
 cv.claim_extraction(uuid,cv.digest,cv.digest,cv.digest,jsonb),cv.claim_evaluation(uuid,uuid,uuid,uuid,uuid,cv.digest,cv.digest,jsonb),
 cv.erase_scope(uuid,uuid),cv.database_ready(),cv.command_begin(uuid,uuid,text,uuid,cv.digest),
 cv.command_finish(uuid,uuid,text,uuid,cv.digest,uuid,uuid),cv.lock_scope(uuid,uuid),cv.require_authority(uuid,boolean),cv.revocation_lock();
DROP TABLE cv.erasure_context;
CREATE OR REPLACE FUNCTION cv.immutable_row() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='DELETE' AND current_user='cv_guard' AND
 EXISTS(SELECT 1 FROM cv.erasure_request r WHERE r.tenant_id=(to_jsonb(OLD)->>'tenant_id')::uuid
 AND r.scope_id=(to_jsonb(OLD)->>'scope_id')::uuid AND r.status='requested') THEN RETURN OLD; END IF;
 RAISE EXCEPTION 'IMMUTABLE_HISTORY' USING ERRCODE='23514';
END $$;
