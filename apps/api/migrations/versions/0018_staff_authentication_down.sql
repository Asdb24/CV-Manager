DROP FUNCTION cv.auth_configure(text,text,jsonb,cv.digest,text),cv.auth_descriptor(text,text),
 cv.auth_private_configuration(text,text),cv.auth_bootstrap(uuid,text,text,text,text),
 cv.auth_login_begin(uuid,text),cv.auth_login_finish(uuid,uuid,text,cv.digest),
 cv.auth_bind(uuid,text),cv.auth_current(),cv.auth_staff_record(uuid),cv.auth_staff_list(uuid),
 cv.auth_staff_write(text,uuid,cv.digest,jsonb),cv.auth_revoke(uuid),cv.auth_logout();
DROP TABLE cv.auth_command,cv.auth_audit,cv.auth_session,cv.auth_attempt,cv.auth_installation;
