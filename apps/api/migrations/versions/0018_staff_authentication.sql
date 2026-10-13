-- Auth tables are inaccessible to runtime/public except the exact functions below.
CREATE TABLE cv.auth_installation (
 singleton boolean PRIMARY KEY CHECK(singleton), instance_id uuid NOT NULL UNIQUE,
 state text NOT NULL CHECK(state IN ('new','initialized','closed')),
 realm text CHECK(realm IN ('local','server')), realm_key text,
 tenant_id uuid REFERENCES cv.agency(id), policy jsonb,
 startup_digest cv.digest, startup_expires_at timestamptz,
 command_secret text, window_started timestamptz NOT NULL DEFAULT clock_timestamp(),
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
 CHECK((realm IS NULL)=(realm_key IS NULL)),
 CHECK(state<>'initialized' OR tenant_id IS NOT NULL)
);
CREATE TABLE cv.auth_attempt (
 login_digest cv.digest PRIMARY KEY, window_started timestamptz NOT NULL,
 attempts integer NOT NULL CHECK(attempts>0)
);
CREATE TABLE cv.auth_session (
 tenant_id uuid NOT NULL, session_id uuid NOT NULL, instance_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,session_id),
 FOREIGN KEY(tenant_id,session_id) REFERENCES cv.staff_session(tenant_id,id),
 FOREIGN KEY(instance_id) REFERENCES cv.auth_installation(instance_id)
);
CREATE TABLE cv.auth_audit (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), instance_id uuid NOT NULL,
 actor_id uuid, action text NOT NULL, record_id uuid,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(instance_id) REFERENCES cv.auth_installation(instance_id)
);
CREATE TABLE cv.auth_command (
 instance_id uuid NOT NULL, actor_id uuid NOT NULL, operation text NOT NULL,
 operation_key uuid NOT NULL, payload_digest cv.digest NOT NULL,
 result jsonb NOT NULL, PRIMARY KEY(instance_id,actor_id,operation,operation_key),
 FOREIGN KEY(instance_id) REFERENCES cv.auth_installation(instance_id)
);
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['auth_installation','auth_attempt','auth_session','auth_audit','auth_command'] LOOP
  EXECUTE format('ALTER TABLE cv.%I ENABLE ROW LEVEL SECURITY',n);
  EXECUTE format('ALTER TABLE cv.%I FORCE ROW LEVEL SECURITY',n);
  EXECUTE format('CREATE POLICY guard ON cv.%I TO cv_guard USING(true) WITH CHECK(true)',n);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON cv.%I TO cv_guard',n);
 END LOOP;
END $$;
CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON cv.auth_audit
 FOR EACH ROW EXECUTE FUNCTION cv.immutable_row();
CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON cv.auth_command
 FOR EACH ROW EXECUTE FUNCTION cv.immutable_row();
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;

-- Inspect every pre-existing table; an existing/damaged workspace never becomes new.
DO $$ DECLARE r record; populated boolean; fresh boolean:=true; BEGIN
 FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='cv' AND tablename NOT LIKE 'auth_%' LOOP
  EXECUTE format('SELECT EXISTS(SELECT 1 FROM cv.%I)',r.tablename) INTO populated;
  IF populated THEN fresh:=false; EXIT; END IF;
 END LOOP;
 INSERT INTO cv.auth_installation(singleton,instance_id,state)
 VALUES(true,gen_random_uuid(),CASE WHEN fresh THEN 'new' ELSE 'closed' END);
END $$;

CREATE FUNCTION cv.auth_configure(r text,k text,p jsonb,startup cv.digest,secret text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; BEGIN
 IF session_user<>'cv_migrator' THEN RAISE EXCEPTION 'OPERATOR_REQUIRED' USING ERRCODE='42501'; END IF;
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR w.state<>'new' OR EXISTS(SELECT 1 FROM cv.agency)
 OR r NOT IN ('local','server') OR coalesce(btrim(k),'')='' OR p IS NULL
 OR coalesce(length(secret),0)<43 OR startup IS NULL
 OR coalesce((p->>'startup_ttl_seconds')::integer,0) NOT BETWEEN 1 AND 900
 OR (w.realm IS NOT NULL AND (w.realm,w.realm_key,w.policy) IS DISTINCT FROM (r,k,p)) THEN
  RAISE EXCEPTION 'BOOTSTRAP_CLOSED' USING ERRCODE='42501'; END IF;
 UPDATE cv.auth_installation SET realm=r,realm_key=k,policy=p,startup_digest=startup,
 startup_expires_at=clock_timestamp()+make_interval(secs=>(p->>'startup_ttl_seconds')::integer),
 command_secret=coalesce(command_secret,secret) WHERE singleton;
 RETURN w.instance_id;
END $$;

CREATE FUNCTION cv.auth_descriptor(k text,r text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton;
 IF NOT FOUND OR (w.realm,w.realm_key) IS DISTINCT FROM (r,k) THEN
  RAISE EXCEPTION 'AUTH_UNAVAILABLE' USING ERRCODE='42501'; END IF;
 RETURN jsonb_build_object('instance_id',w.instance_id,'state',w.state,'realm',w.realm,'realm_key',w.realm_key);
END $$;

CREATE FUNCTION cv.auth_private_configuration(k text,r text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; BEGIN
 PERFORM cv.auth_descriptor(k,r);
 SELECT * INTO w FROM cv.auth_installation WHERE singleton;
 RETURN jsonb_build_object('policy',w.policy,'command_secret',w.command_secret);
END $$;

CREATE FUNCTION cv.auth_bootstrap(i uuid,proof text,agency_name text,login text,credential text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; t uuid; u uuid; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR w.instance_id IS DISTINCT FROM i OR w.state<>'new'
 OR w.startup_digest IS DISTINCT FROM encode(sha256(convert_to(proof,'UTF8')),'hex')
 OR w.startup_expires_at IS NULL OR w.startup_expires_at<=clock_timestamp()
 OR (w.realm='server' AND session_user<>'cv_migrator')
 OR (w.realm='local' AND session_user NOT IN ('cv_runtime','cv_migrator'))
 OR w.realm IS NULL OR EXISTS(SELECT 1 FROM cv.agency)
 THEN RAISE EXCEPTION 'BOOTSTRAP_DENIED' USING ERRCODE='42501'; END IF;
 IF credential NOT LIKE '$argon2id$v=19$%' OR credential IS NULL
 OR login !~ '^[a-z0-9][a-z0-9._-]{0,63}$' OR login IS NULL
 OR coalesce(length(btrim(agency_name)),0) NOT BETWEEN 1 AND 200 THEN
  RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
 t:=gen_random_uuid(); u:=gen_random_uuid();
 INSERT INTO cv.agency(id,realm_key,name) VALUES(t,w.realm_key,agency_name);
 INSERT INTO cv.staff_user(tenant_id,id,login_name,credential_hash,active) VALUES(t,u,login,credential,true);
 INSERT INTO cv.membership VALUES(t,u,'admin',true,1);
 UPDATE cv.auth_installation SET state='initialized',tenant_id=t,startup_digest=NULL,
 startup_expires_at=NULL WHERE singleton;
 INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id) VALUES(i,u,'bootstrap',t);
 RETURN t;
END $$;

-- Reservation and password verification share one bounded transaction/lock.
-- Rejected attempts return normally so their counters commit even on wrong passwords.
CREATE FUNCTION cv.auth_login_begin(i uuid,login text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; a cv.auth_attempt; h cv.digest; u cv.staff_user;
 instant timestamptz; window_seconds integer; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR w.instance_id IS DISTINCT FROM i OR w.state<>'initialized' THEN RETURN NULL; END IF;
 instant:=clock_timestamp(); window_seconds:=(w.policy->>'attempt_window_seconds')::integer;
 IF w.window_started+make_interval(secs=>window_seconds)<=instant THEN
  UPDATE cv.auth_installation SET window_started=instant,attempts=0 WHERE singleton;
  w.attempts:=0;
  DELETE FROM cv.auth_attempt WHERE window_started+make_interval(secs=>window_seconds)<=instant;
 END IF;
 IF w.attempts>=(w.policy->>'global_attempt_limit')::integer THEN RETURN NULL; END IF;
 UPDATE cv.auth_installation SET attempts=attempts+1 WHERE singleton;
 h:=encode(sha256(convert_to(login,'UTF8')),'hex');
 SELECT * INTO a FROM cv.auth_attempt WHERE login_digest=h;
 IF FOUND AND a.window_started+make_interval(secs=>window_seconds)>instant THEN
  IF a.attempts>=(w.policy->>'account_attempt_limit')::integer THEN RETURN NULL; END IF;
  UPDATE cv.auth_attempt SET attempts=attempts+1 WHERE login_digest=h;
 ELSE
  INSERT INTO cv.auth_attempt VALUES(h,instant,1) ON CONFLICT(login_digest)
  DO UPDATE SET window_started=excluded.window_started,attempts=1;
 END IF;
 SELECT s.* INTO u FROM cv.staff_user s JOIN cv.membership m ON (m.tenant_id,m.user_id)=(s.tenant_id,s.id)
 WHERE s.tenant_id=w.tenant_id AND s.login_name=login AND s.active AND m.active FOR SHARE OF s,m;
 IF NOT FOUND THEN RETURN NULL; END IF;
 RETURN jsonb_build_object('user_id',u.id,'credential_hash',u.credential_hash);
END $$;

CREATE FUNCTION cv.auth_login_finish(i uuid,u uuid,observed_hash text,token_hash cv.digest)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; actor cv.staff_user; member cv.membership;
 sid uuid; expiry timestamptz; BEGIN
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF w.instance_id IS DISTINCT FROM i OR w.state<>'initialized' OR token_hash IS NULL THEN
  RAISE EXCEPTION 'AUTH_DENIED' USING ERRCODE='42501'; END IF;
 SELECT * INTO actor FROM cv.staff_user WHERE (tenant_id,id)=(w.tenant_id,u) FOR SHARE;
 SELECT * INTO member FROM cv.membership WHERE (tenant_id,user_id)=(w.tenant_id,u) FOR SHARE;
 IF actor.id IS NULL OR member.user_id IS NULL OR NOT actor.active OR NOT member.active
 OR actor.credential_hash IS DISTINCT FROM observed_hash THEN
  RAISE EXCEPTION 'AUTH_DENIED' USING ERRCODE='42501'; END IF;
 -- Refuse rather than silently evicting another device's live session.
 IF (SELECT count(*) FROM cv.staff_session WHERE (tenant_id,user_id)=(w.tenant_id,u)
 AND revoked_at IS NULL AND expires_at>clock_timestamp())>=(w.policy->>'session_limit')::integer
 THEN RETURN NULL; END IF;
 sid:=gen_random_uuid(); expiry:=clock_timestamp()+make_interval(secs=>(w.policy->>'session_ttl_seconds')::integer);
 INSERT INTO cv.staff_session(tenant_id,id,user_id,token_digest,expires_at)
 VALUES(w.tenant_id,sid,u,token_hash,expiry);
 INSERT INTO cv.auth_session VALUES(w.tenant_id,sid,i);
 INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id) VALUES(i,u,'login',sid);
 RETURN jsonb_build_object('instance_id',i,'tenant_id',w.tenant_id,'user_id',u,'session_id',sid,
 'login_name',actor.login_name,'role',member.role,'expires_at',expiry);
END $$;

CREATE FUNCTION cv.auth_bind(i uuid,proof text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE w cv.auth_installation; BEGIN
 -- Serialize authentication administration in the same order as login, before identity locks.
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF NOT FOUND OR w.instance_id IS DISTINCT FROM i OR w.state<>'initialized'
 OR NOT EXISTS(SELECT 1 FROM cv.auth_session a JOIN cv.staff_session s
 ON (s.tenant_id,s.id)=(a.tenant_id,a.session_id) WHERE a.instance_id=i AND a.tenant_id=w.tenant_id
 AND s.token_digest=encode(sha256(convert_to(proof,'UTF8')),'hex')) THEN
  RAISE EXCEPTION 'AUTH_DENIED' USING ERRCODE='42501'; END IF;
 PERFORM cv.bind_session(proof);
END $$;

CREATE FUNCTION cv.auth_current() RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE result jsonb; BEGIN
 SELECT jsonb_build_object('instance_id',w.instance_id,'tenant_id',a.tenant_id,'user_id',a.user_id,
 'session_id',c.session_id,'login_name',u.login_name,'role',a.role,'expires_at',s.expires_at)
 INTO result FROM cv.current_authority() a JOIN cv.auth_installation w ON w.tenant_id=a.tenant_id
 JOIN cv.transaction_context c ON c.backend_pid=pg_backend_pid() AND c.transaction_id=pg_current_xact_id()
 JOIN cv.staff_user u ON (u.tenant_id,u.id)=(a.tenant_id,a.user_id)
 JOIN cv.staff_session s ON (s.tenant_id,s.id)=(c.tenant_id,c.session_id)
 JOIN cv.auth_session b ON (b.tenant_id,b.session_id,b.instance_id)=(s.tenant_id,s.id,w.instance_id);
 IF result IS NULL THEN RAISE EXCEPTION 'AUTH_DENIED' USING ERRCODE='42501'; END IF;
 RETURN result;
END $$;

CREATE FUNCTION cv.auth_staff_record(u uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; result jsonb; BEGIN
 a:=cv.auth_current(); PERFORM cv.require_authority((a->>'tenant_id')::uuid,true);
 SELECT jsonb_build_object('user_id',s.id,'login_name',s.login_name,'role',m.role,
 'active',s.active AND m.active,'revision',m.revision) INTO result
 FROM cv.staff_user s JOIN cv.membership m ON (m.tenant_id,m.user_id)=(s.tenant_id,s.id)
 WHERE s.tenant_id=(a->>'tenant_id')::uuid AND s.id=u;
 IF result IS NULL THEN RAISE EXCEPTION 'ACCESS_DENIED' USING ERRCODE='42501'; END IF;
 RETURN result;
END $$;

CREATE FUNCTION cv.auth_staff_list(after_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; result jsonb; cap integer; BEGIN
 a:=cv.auth_current(); PERFORM cv.require_authority((a->>'tenant_id')::uuid,true);
 SELECT (policy->>'page_size')::integer INTO cap FROM cv.auth_installation WHERE singleton;
 SELECT coalesce(jsonb_agg(cv.auth_staff_record(id) ORDER BY id),'[]'::jsonb) INTO result
 FROM (SELECT id FROM cv.staff_user WHERE tenant_id=(a->>'tenant_id')::uuid
 AND (after_id IS NULL OR id>after_id) ORDER BY id LIMIT cap) s;
 RETURN result;
END $$;

CREATE FUNCTION cv.auth_staff_write(op text,key uuid,payload cv.digest,body jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; w cv.auth_installation; prior cv.auth_command; result jsonb; u uuid;
 member cv.membership; credential text; BEGIN
 a:=cv.auth_current(); PERFORM cv.require_authority((a->>'tenant_id')::uuid,true);
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF key IS NULL OR payload IS NULL OR op NOT IN ('staff-create','staff-update') THEN
  RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
 SELECT * INTO prior FROM cv.auth_command WHERE (instance_id,actor_id,operation,operation_key)=
 (w.instance_id,(a->>'user_id')::uuid,op,key);
 IF FOUND THEN
  IF prior.payload_digest<>payload THEN RAISE EXCEPTION 'IDEMPOTENCY_CONFLICT' USING ERRCODE='23514'; END IF;
  PERFORM cv.auth_staff_record((prior.result->>'user_id')::uuid);
  RETURN prior.result;
 END IF;
 IF body->>'role' NOT IN ('admin','recruiter') OR body->>'role' IS NULL THEN
  RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
 IF op='staff-create' THEN
  IF (SELECT count(*) FROM cv.staff_user WHERE tenant_id=w.tenant_id)>=(w.policy->>'staff_limit')::integer
  THEN RAISE EXCEPTION 'STAFF_LIMIT' USING ERRCODE='23514'; END IF;
  credential:=body->>'credential_hash';
  IF credential IS NULL OR credential NOT LIKE '$argon2id$v=19$%' OR body->>'login_name' IS NULL
  OR body->>'login_name' !~ '^[a-z0-9][a-z0-9._-]{0,63}$' THEN
   RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
  u:=gen_random_uuid();
  INSERT INTO cv.staff_user(tenant_id,id,login_name,credential_hash,active)
  VALUES(w.tenant_id,u,body->>'login_name',credential,true);
  INSERT INTO cv.membership VALUES(w.tenant_id,u,body->>'role',true,1);
 ELSE
  u:=(body->>'user_id')::uuid;
  SELECT * INTO member FROM cv.membership WHERE (tenant_id,user_id)=(w.tenant_id,u) FOR UPDATE;
  IF NOT FOUND OR u=(a->>'user_id')::uuid THEN
   RAISE EXCEPTION 'ACCESS_DENIED' USING ERRCODE='42501'; END IF;
  IF member.revision IS DISTINCT FROM (body->>'expected_revision')::integer THEN
   RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
  IF body->>'active' IS NULL THEN RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
  UPDATE cv.membership SET role=body->>'role',active=(body->>'active')::boolean,revision=revision+1
  WHERE (tenant_id,user_id)=(w.tenant_id,u);
  UPDATE cv.staff_user SET active=(body->>'active')::boolean WHERE (tenant_id,id)=(w.tenant_id,u);
  UPDATE cv.staff_session SET revoked_at=clock_timestamp()
  WHERE (tenant_id,user_id)=(w.tenant_id,u) AND revoked_at IS NULL;
 END IF;
 result:=cv.auth_staff_record(u);
 INSERT INTO cv.auth_command VALUES(w.instance_id,(a->>'user_id')::uuid,op,key,payload,result);
 INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id)
 VALUES(w.instance_id,(a->>'user_id')::uuid,op,u);
 RETURN result;
END $$;

CREATE FUNCTION cv.auth_revoke(sid uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; target cv.staff_session; BEGIN
 a:=cv.auth_current();
 SELECT * INTO target FROM cv.staff_session WHERE (tenant_id,id)=((a->>'tenant_id')::uuid,sid) FOR UPDATE;
 IF NOT FOUND OR (target.user_id<>(a->>'user_id')::uuid AND a->>'role'<>'admin') THEN
  RAISE EXCEPTION 'ACCESS_DENIED' USING ERRCODE='42501'; END IF;
 IF sid=(a->>'session_id')::uuid THEN
  RAISE EXCEPTION 'USE_LOGOUT' USING ERRCODE='23514'; END IF;
 IF target.revoked_at IS NULL THEN
  UPDATE cv.staff_session SET revoked_at=clock_timestamp() WHERE (tenant_id,id)=(target.tenant_id,sid);
  INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id)
  VALUES((a->>'instance_id')::uuid,(a->>'user_id')::uuid,'session-revoke',sid);
 END IF;
END $$;

CREATE FUNCTION cv.auth_logout() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; BEGIN
 a:=cv.auth_current();
 -- This is the final command: validate all outstanding authority before consuming this session.
 PERFORM cv.validate_transaction();
 INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id)
 VALUES((a->>'instance_id')::uuid,(a->>'user_id')::uuid,'logout',(a->>'session_id')::uuid);
 UPDATE cv.staff_session SET revoked_at=clock_timestamp()
 WHERE (tenant_id,id)=((a->>'tenant_id')::uuid,(a->>'session_id')::uuid);
 DELETE FROM cv.transaction_context WHERE backend_pid=pg_backend_pid() AND transaction_id=pg_current_xact_id();
END $$;

REVOKE ALL ON FUNCTION cv.auth_configure(text,text,jsonb,cv.digest,text),
 cv.auth_descriptor(text,text),cv.auth_private_configuration(text,text),
 cv.auth_bootstrap(uuid,text,text,text,text),cv.auth_login_begin(uuid,text),
 cv.auth_login_finish(uuid,uuid,text,cv.digest),cv.auth_bind(uuid,text),cv.auth_current(),
 cv.auth_staff_record(uuid),cv.auth_staff_list(uuid),cv.auth_staff_write(text,uuid,cv.digest,jsonb),
 cv.auth_revoke(uuid),cv.auth_logout() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.auth_configure(text,text,jsonb,cv.digest,text),
 cv.auth_bootstrap(uuid,text,text,text,text) TO cv_migrator;
GRANT EXECUTE ON FUNCTION cv.auth_descriptor(text,text),cv.auth_private_configuration(text,text),
 cv.auth_bootstrap(uuid,text,text,text,text),cv.auth_login_begin(uuid,text),
 cv.auth_login_finish(uuid,uuid,text,cv.digest),cv.auth_bind(uuid,text),cv.auth_current(),
 cv.auth_staff_record(uuid),cv.auth_staff_list(uuid),cv.auth_staff_write(text,uuid,cv.digest,jsonb),
 cv.auth_revoke(uuid),cv.auth_logout() TO cv_runtime;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
