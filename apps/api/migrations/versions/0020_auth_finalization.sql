GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
ALTER FUNCTION cv.auth_policy_write(text,uuid,cv.digest,jsonb) RENAME TO auth_policy_write_0019;
REVOKE ALL ON FUNCTION cv.auth_policy_write_0019(text,uuid,cv.digest,jsonb) FROM cv_runtime;
CREATE FUNCTION cv.auth_policy_obligations() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
BEGIN
 IF to_regclass('pg_temp.cv_auth_policy_obligations') IS NULL THEN
  CREATE TEMPORARY TABLE cv_auth_policy_obligations (
   tenant_id uuid NOT NULL, policy_id uuid NOT NULL,
   transaction_id xid8 NOT NULL DEFAULT pg_current_xact_id(),
   PRIMARY KEY(tenant_id,policy_id)
  ) ON COMMIT DROP;
  ALTER TABLE pg_temp.cv_auth_policy_obligations ENABLE ROW LEVEL SECURITY;
  ALTER TABLE pg_temp.cv_auth_policy_obligations FORCE ROW LEVEL SECURITY;
  CREATE POLICY guard ON pg_temp.cv_auth_policy_obligations TO cv_guard USING(true) WITH CHECK(true);
  REVOKE ALL ON pg_temp.cv_auth_policy_obligations FROM PUBLIC;
 ELSIF (SELECT pg_get_userbyid(relowner) FROM pg_class
 WHERE oid=to_regclass('pg_temp.cv_auth_policy_obligations'))<>'cv_guard' THEN
  RAISE EXCEPTION 'AUTH_CONTEXT_INVALID' USING ERRCODE='42501';
 END IF;
END $$;
CREATE FUNCTION cv.auth_policy_write(op text,key uuid,payload cv.digest,body jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE result jsonb; a jsonb; p uuid; BEGIN
 result:=cv.auth_policy_write_0019(op,key,payload,body);
 IF op IN ('policy-activate','purpose-grant') THEN
  a:=cv.auth_current();
  p:=CASE WHEN op='policy-activate' THEN (result->>'policy_id')::uuid ELSE (result->>'purpose_id')::uuid END;
  PERFORM cv.auth_policy_obligations();
  INSERT INTO pg_temp.cv_auth_policy_obligations(tenant_id,policy_id)
  VALUES((a->>'tenant_id')::uuid,p) ON CONFLICT DO NOTHING;
 END IF;
 RETURN result;
END $$;
CREATE FUNCTION cv.auth_validate_transaction() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE p record; a jsonb; instant timestamptz; BEGIN
 PERFORM cv.auth_policy_obligations();
 FOR p IN SELECT * FROM pg_temp.cv_auth_policy_obligations ORDER BY tenant_id,policy_id LOOP
  IF p.transaction_id<>pg_current_xact_id() THEN
   RAISE EXCEPTION 'AUTH_CONTEXT_INVALID' USING ERRCODE='42501'; END IF;
  PERFORM 1 FROM cv.policy_version WHERE (tenant_id,id)=(p.tenant_id,p.policy_id) FOR SHARE;
 END LOOP;
 -- The base finalizer now takes any remaining business locks and validates those obligations.
 PERFORM cv.validate_transaction();
 a:=cv.auth_current(); instant:=clock_timestamp();
 IF (a->>'expires_at')::timestamptz<=instant THEN
  RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 FOR p IN SELECT * FROM pg_temp.cv_auth_policy_obligations LOOP
  IF a->>'role'<>'admin' OR (a->>'tenant_id')::uuid<>p.tenant_id
  OR NOT EXISTS(SELECT 1 FROM cv.policy_version v WHERE (v.tenant_id,v.id)=(p.tenant_id,p.policy_id)
   AND v.activated_at<=instant AND v.expires_at>instant
   AND NOT EXISTS(SELECT 1 FROM cv.policy_revocation r WHERE (r.tenant_id,r.policy_id)=(v.tenant_id,v.id)))
  THEN RAISE EXCEPTION 'POLICY_AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 END LOOP;
END $$;

ALTER FUNCTION cv.auth_bootstrap(uuid,text,text,text,text) RENAME TO auth_bootstrap_0018;
REVOKE ALL ON FUNCTION cv.auth_bootstrap_0018(uuid,text,text,text,text) FROM cv_runtime,cv_migrator;
CREATE FUNCTION cv.auth_bootstrap(i uuid,proof text,agency_name text,login text,credential text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE deadline timestamptz; result uuid; BEGIN
 SELECT startup_expires_at INTO deadline FROM cv.auth_installation WHERE singleton FOR UPDATE;
 result:=cv.auth_bootstrap_0018(i,proof,agency_name,login,credential);
 IF deadline IS NULL OR deadline<=clock_timestamp() THEN
  RAISE EXCEPTION 'BOOTSTRAP_EXPIRED' USING ERRCODE='42501'; END IF;
 RETURN result;
END $$;
REVOKE ALL ON FUNCTION cv.auth_policy_obligations(),cv.auth_policy_write(text,uuid,cv.digest,jsonb),
 cv.auth_validate_transaction(),cv.auth_bootstrap(uuid,text,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.auth_policy_write(text,uuid,cv.digest,jsonb),cv.auth_validate_transaction(),
 cv.auth_bootstrap(uuid,text,text,text,text) TO cv_runtime;
GRANT EXECUTE ON FUNCTION cv.auth_bootstrap(uuid,text,text,text,text) TO cv_migrator;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
