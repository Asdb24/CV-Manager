GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
ALTER FUNCTION cv.auth_login_begin(uuid,text) RENAME TO auth_login_begin_0018;
REVOKE ALL ON FUNCTION cv.auth_login_begin_0018(uuid,text) FROM cv_runtime;

CREATE FUNCTION cv.auth_login_begin(i uuid,login text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; a cv.auth_attempt; h cv.digest; u cv.staff_user;
 instant timestamptz; window_seconds integer; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR w.instance_id IS DISTINCT FROM i OR w.state<>'initialized' THEN
  RETURN jsonb_build_object('admitted',false); END IF;
 instant:=clock_timestamp(); window_seconds:=(w.policy->>'attempt_window_seconds')::integer;
 IF w.window_started+make_interval(secs=>window_seconds)<=instant THEN
  UPDATE cv.auth_installation SET window_started=instant,attempts=0 WHERE singleton;
  w.attempts:=0;
  DELETE FROM cv.auth_attempt WHERE window_started+make_interval(secs=>window_seconds)<=instant;
 END IF;
 IF w.attempts>=(w.policy->>'global_attempt_limit')::integer THEN
  RETURN jsonb_build_object('admitted',false); END IF;
 UPDATE cv.auth_installation SET attempts=attempts+1 WHERE singleton;
 h:=encode(sha256(convert_to(login,'UTF8')),'hex');
 SELECT * INTO a FROM cv.auth_attempt WHERE login_digest=h;
 IF FOUND AND a.window_started+make_interval(secs=>window_seconds)>instant THEN
  IF a.attempts>=(w.policy->>'account_attempt_limit')::integer THEN
   RETURN jsonb_build_object('admitted',false); END IF;
  UPDATE cv.auth_attempt SET attempts=attempts+1 WHERE login_digest=h;
 ELSE
  INSERT INTO cv.auth_attempt VALUES(h,instant,1) ON CONFLICT(login_digest)
  DO UPDATE SET window_started=excluded.window_started,attempts=1;
 END IF;
 SELECT s.* INTO u FROM cv.staff_user s JOIN cv.membership m ON (m.tenant_id,m.user_id)=(s.tenant_id,s.id)
 WHERE s.tenant_id=w.tenant_id AND s.login_name=login AND s.active AND m.active FOR SHARE OF s,m;
 IF NOT FOUND THEN RETURN jsonb_build_object('admitted',true,'credential',NULL); END IF;
 RETURN jsonb_build_object('admitted',true,'credential',
  jsonb_build_object('user_id',u.id,'credential_hash',u.credential_hash));
END $$;

CREATE FUNCTION cv.auth_bootstrap_admit(i uuid,proof text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR session_user<>'cv_runtime' OR w.realm IS DISTINCT FROM 'local'
 OR w.instance_id IS DISTINCT FROM i OR w.state<>'new' OR proof IS NULL
 OR w.startup_digest IS DISTINCT FROM encode(sha256(convert_to(proof,'UTF8')),'hex')
 OR w.startup_expires_at IS NULL OR w.startup_expires_at<=clock_timestamp()
 OR EXISTS(SELECT 1 FROM cv.agency) THEN
  RAISE EXCEPTION 'BOOTSTRAP_DENIED' USING ERRCODE='42501'; END IF;
 -- Retain this lock in the service's hash/create transaction. The final create
 -- repeats proof, realm/state/empty-workspace and fresh expiry checks.
END $$;

REVOKE ALL ON FUNCTION cv.auth_login_begin(uuid,text),cv.auth_bootstrap_admit(uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.auth_login_begin(uuid,text),cv.auth_bootstrap_admit(uuid,text) TO cv_runtime;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
