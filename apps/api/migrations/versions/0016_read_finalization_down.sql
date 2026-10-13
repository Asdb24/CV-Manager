GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.tenant_allowed(t uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.current_authority() a
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id)=(a.tenant_id,a.user_id)
 WHERE a.tenant_id=t AND g.active AND cv.policy_live(t,g.purpose_id,'purpose'))
$$;
CREATE OR REPLACE FUNCTION cv.scope_allowed(t uuid,s uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
 SELECT EXISTS(SELECT 1 FROM cv.privacy_scope p JOIN cv.current_authority() a ON a.tenant_id=p.tenant_id
 JOIN cv.purpose_grant g ON (g.tenant_id,g.user_id,g.purpose_id)=(p.tenant_id,a.user_id,p.purpose_id)
 WHERE (p.tenant_id,p.id)=(t,s) AND g.active AND p.revoked_at IS NULL
 AND p.consent_expires_at>statement_timestamp()
 AND cv.policy_live(t,p.purpose_id,'purpose') AND cv.policy_live(t,p.source_policy_id,'source')
 AND cv.policy_live(t,p.consent_policy_id,'consent') AND cv.policy_live(t,p.retention_policy_id,'retention')
 AND cv.policy_live(t,p.erasure_policy_id,'erasure') AND cv.policy_live(t,p.resource_policy_id,'resource'))
$$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
