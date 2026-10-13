DROP FUNCTION cv.auth_login_begin(uuid,text),cv.auth_bootstrap_admit(uuid,text);
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
ALTER FUNCTION cv.auth_login_begin_0018(uuid,text) RENAME TO auth_login_begin;
GRANT EXECUTE ON FUNCTION cv.auth_login_begin(uuid,text) TO cv_runtime;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
