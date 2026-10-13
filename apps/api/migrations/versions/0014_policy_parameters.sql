GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
CREATE OR REPLACE FUNCTION cv.lock_authority_policies(t uuid,definition jsonb) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 PERFORM 1 FROM cv.policy_version WHERE tenant_id=t AND id IN
 ((lock_authority_policies.definition->>'purpose_id')::uuid,(lock_authority_policies.definition->>'source_policy_id')::uuid,
 (lock_authority_policies.definition->>'consent_policy_id')::uuid,(lock_authority_policies.definition->>'retention_policy_id')::uuid,
 (lock_authority_policies.definition->>'erasure_policy_id')::uuid,(lock_authority_policies.definition->>'resource_policy_id')::uuid)
 ORDER BY id FOR SHARE;
END $$;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
