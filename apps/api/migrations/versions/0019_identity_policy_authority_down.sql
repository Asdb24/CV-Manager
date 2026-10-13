DROP FUNCTION cv.auth_policy_list(uuid),cv.auth_policy_write(text,uuid,cv.digest,jsonb);
DROP TABLE cv.auth_grant_revision;
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.final_authority_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; s uuid; BEGIN
 IF session_user<>'cv_runtime' THEN RETURN NULL; END IF;
 t := (to_jsonb(NEW)->>'tenant_id')::uuid;
 s := (to_jsonb(NEW)->>'scope_id')::uuid;
 IF NOT cv.tenant_allowed(t) OR (s IS NOT NULL AND NOT cv.scope_allowed(t,s)) THEN
  RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 RETURN NULL;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
