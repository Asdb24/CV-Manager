ALTER TABLE cv.erasure_request ADD COLUMN erasure_policy_id uuid;
ALTER TABLE cv.erasure_request ADD CONSTRAINT erasure_policy_reference
 FOREIGN KEY(tenant_id,erasure_policy_id) REFERENCES cv.policy_version(tenant_id,id);
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE FUNCTION cv.erasure_policy_pin() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  SELECT erasure_policy_id INTO NEW.erasure_policy_id FROM cv.privacy_scope
  WHERE (tenant_id,id)=(NEW.tenant_id,NEW.scope_id) FOR UPDATE;
  IF NEW.erasure_policy_id IS NULL THEN
   RAISE EXCEPTION 'ERASURE_POLICY_REQUIRED' USING ERRCODE='42501'; END IF;
  PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(NEW.tenant_id,NEW.erasure_policy_id) FOR SHARE;
 ELSIF NEW.erasure_policy_id IS DISTINCT FROM OLD.erasure_policy_id THEN
  RAISE EXCEPTION 'ERASURE_POLICY_IMMUTABLE' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cv.final_erasure_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF session_user='cv_runtime' THEN
  IF NOT EXISTS(SELECT 1 FROM cv.current_authority() a
  WHERE (a.tenant_id,a.user_id,a.role)=(NEW.tenant_id,NEW.actor_id,'admin'))
  OR NOT cv.policy_live(NEW.tenant_id,NEW.erasure_policy_id,'erasure') THEN
   RAISE EXCEPTION 'ERASURE_AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 END IF;
 RETURN NULL;
END $$;
CREATE FUNCTION cv.final_command_purpose_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF session_user='cv_runtime' AND (NOT cv.policy_live(NEW.tenant_id,NEW.purpose_id,'purpose')
 OR NOT EXISTS(SELECT 1 FROM cv.current_authority() a JOIN cv.purpose_grant g
 ON (g.tenant_id,g.user_id)=(a.tenant_id,a.user_id)
 WHERE (a.tenant_id,a.user_id,g.purpose_id)=(NEW.tenant_id,NEW.actor_id,NEW.purpose_id) AND g.active)) THEN
  RAISE EXCEPTION 'COMMAND_PURPOSE_REVOKED' USING ERRCODE='42501';
 END IF;
 RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION cv.erasure_policy_pin(),cv.final_erasure_check(),cv.final_command_purpose_check() FROM PUBLIC;
RESET ROLE;
CREATE TRIGGER erasure_policy_pin BEFORE INSERT OR UPDATE ON cv.erasure_request
 FOR EACH ROW EXECUTE FUNCTION cv.erasure_policy_pin();
CREATE CONSTRAINT TRIGGER final_erasure AFTER INSERT OR UPDATE ON cv.erasure_request
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_erasure_check();
CREATE CONSTRAINT TRIGGER final_command_purpose AFTER INSERT ON cv.command_result
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION cv.final_command_purpose_check();
CREATE INDEX erasure_policy_fk ON cv.erasure_request(tenant_id,erasure_policy_id);
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
