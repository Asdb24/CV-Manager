DROP FUNCTION cv.auth_policy_write(text,uuid,cv.digest,jsonb),cv.auth_validate_transaction(),
 cv.auth_policy_obligations(),cv.auth_bootstrap(uuid,text,text,text,text);
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
ALTER FUNCTION cv.auth_policy_write_0019(text,uuid,cv.digest,jsonb) RENAME TO auth_policy_write;
ALTER FUNCTION cv.auth_bootstrap_0018(uuid,text,text,text,text) RENAME TO auth_bootstrap;
GRANT EXECUTE ON FUNCTION cv.auth_policy_write(text,uuid,cv.digest,jsonb),
 cv.auth_bootstrap(uuid,text,text,text,text) TO cv_runtime;
GRANT EXECUTE ON FUNCTION cv.auth_bootstrap(uuid,text,text,text,text) TO cv_migrator;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
