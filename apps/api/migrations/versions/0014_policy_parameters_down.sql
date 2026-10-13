GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.lock_authority_policies(t uuid,definition jsonb) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 PERFORM 1 FROM cv.policy_version WHERE tenant_id=t AND id IN
 ((definition->>'purpose_id')::uuid,(definition->>'source_policy_id')::uuid,
 (definition->>'consent_policy_id')::uuid,(definition->>'retention_policy_id')::uuid,
 (definition->>'erasure_policy_id')::uuid,(definition->>'resource_policy_id')::uuid)
 ORDER BY id FOR SHARE;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
