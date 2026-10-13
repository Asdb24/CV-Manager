GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
-- These predicates record only successful reads and are deliberately VOLATILE.
-- Guard-owned authority queries bypass neither authentication nor private RLS;
-- their fixed guard policy avoids recursive invocation of the staff predicate.
CREATE OR REPLACE FUNCTION cv.tenant_allowed(t uuid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a record;
BEGIN
 SELECT authority.user_id,g.purpose_id INTO a FROM cv.current_authority() authority
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id)=(authority.tenant_id,authority.user_id)
 WHERE authority.tenant_id=t AND g.active AND cv.policy_live(t,g.purpose_id,'purpose')
 ORDER BY g.purpose_id LIMIT 1;
 IF NOT FOUND THEN RETURN false; END IF;
 PERFORM cv.register_obligation('purpose',t,a.user_id,a.purpose_id);
 RETURN true;
END $$;

CREATE OR REPLACE FUNCTION cv.scope_allowed(t uuid,s uuid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE actor uuid;
BEGIN
 SELECT a.user_id INTO actor FROM cv.privacy_scope p
 JOIN cv.current_authority() a ON a.tenant_id=p.tenant_id
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id,g.purpose_id)=(p.tenant_id,a.user_id,p.purpose_id)
 WHERE (p.tenant_id,p.id)=(t,s) AND g.active AND p.revoked_at IS NULL
 AND p.consent_expires_at>statement_timestamp()
 AND cv.policy_live(t,p.purpose_id,'purpose') AND cv.policy_live(t,p.source_policy_id,'source')
 AND cv.policy_live(t,p.consent_policy_id,'consent') AND cv.policy_live(t,p.retention_policy_id,'retention')
 AND cv.policy_live(t,p.erasure_policy_id,'erasure') AND cv.policy_live(t,p.resource_policy_id,'resource');
 IF NOT FOUND THEN RETURN false; END IF;
 PERFORM cv.register_obligation('scope',t,actor,s);
 RETURN true;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
