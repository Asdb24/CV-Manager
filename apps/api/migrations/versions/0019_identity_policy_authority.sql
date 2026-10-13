CREATE TABLE cv.auth_grant_revision (
 tenant_id uuid NOT NULL, user_id uuid NOT NULL, purpose_id uuid NOT NULL,
 revision integer NOT NULL CHECK(revision>0), PRIMARY KEY(tenant_id,user_id,purpose_id),
 FOREIGN KEY(tenant_id,user_id,purpose_id) REFERENCES cv.purpose_grant(tenant_id,user_id,purpose_id)
);
ALTER TABLE cv.auth_grant_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv.auth_grant_revision FORCE ROW LEVEL SECURITY;
CREATE POLICY guard ON cv.auth_grant_revision TO cv_guard USING(true) WITH CHECK(true);
GRANT SELECT,INSERT,UPDATE,DELETE ON cv.auth_grant_revision TO cv_guard;
GRANT CREATE ON SCHEMA cv TO cv_guard;
SET ROLE cv_guard;
INSERT INTO cv.auth_grant_revision SELECT tenant_id,user_id,purpose_id,1 FROM cv.purpose_grant;

-- Privacy-policy administration is an explicit admin purpose. It must remain
-- possible before first recruitment-purpose activation and after its revocation.
CREATE OR REPLACE FUNCTION cv.final_authority_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE t uuid; s uuid; BEGIN
 IF session_user<>'cv_runtime' THEN RETURN NULL; END IF;
 t := (to_jsonb(NEW)->>'tenant_id')::uuid;
 IF TG_TABLE_NAME IN ('policy_version','policy_revocation') THEN
  PERFORM cv.require_authority(t,true);
 ELSE
  s := (to_jsonb(NEW)->>'scope_id')::uuid;
  IF NOT cv.tenant_allowed(t) OR (s IS NOT NULL AND NOT cv.scope_allowed(t,s)) THEN
   RAISE EXCEPTION 'AUTH_REVOKED' USING ERRCODE='42501'; END IF;
 END IF;
 RETURN NULL;
END $$;

CREATE FUNCTION cv.auth_policy_list(after_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; cap integer; result jsonb; BEGIN
 a:=cv.auth_current(); PERFORM cv.require_authority((a->>'tenant_id')::uuid,true);
 SELECT (policy->>'page_size')::integer INTO cap FROM cv.auth_installation WHERE singleton;
 SELECT coalesce(jsonb_agg(value ORDER BY id),'[]'::jsonb) INTO result FROM (
  SELECT p.id,jsonb_build_object('policy_id',p.id,'kind',p.kind,'version',p.version,
  'owner_user_id',p.owner_user_id,'owner_role',p.owner_role,'expires_at',p.expires_at,
  'revoked',EXISTS(SELECT 1 FROM cv.policy_revocation r WHERE (r.tenant_id,r.policy_id)=(p.tenant_id,p.id)),
  'definition',p.definition) value FROM cv.policy_version p WHERE p.tenant_id=(a->>'tenant_id')::uuid
  AND (after_id IS NULL OR p.id>after_id) ORDER BY p.id LIMIT cap
 ) bounded;
 RETURN result;
END $$;

CREATE FUNCTION cv.auth_policy_write(op text,key uuid,payload cv.digest,body jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,cv AS $$
DECLARE a jsonb; w cv.auth_installation; prior cv.auth_command; result jsonb;
 p uuid; u uuid; v cv.policy_version; old_revision integer; active_value boolean; owner text;
BEGIN
 a:=cv.auth_current(); PERFORM cv.require_authority((a->>'tenant_id')::uuid,true);
 SELECT * INTO w FROM cv.auth_installation WHERE singleton FOR UPDATE;
 IF key IS NULL OR payload IS NULL OR op NOT IN ('policy-activate','policy-revoke','purpose-grant') THEN
  RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
 SELECT * INTO prior FROM cv.auth_command WHERE (instance_id,actor_id,operation,operation_key)=
 (w.instance_id,(a->>'user_id')::uuid,op,key);
 IF FOUND THEN
  IF prior.payload_digest<>payload THEN RAISE EXCEPTION 'IDEMPOTENCY_CONFLICT' USING ERRCODE='23514'; END IF;
  RETURN prior.result;
 END IF;
 IF op='policy-activate' THEN
  IF body->>'kind' NOT IN ('source','purpose','consent','retention','erasure','resource')
  OR body->>'kind' IS NULL OR coalesce(btrim(body->>'version'),'')=''
  OR (body->>'expires_at')::timestamptz<=clock_timestamp() OR body->>'expires_at' IS NULL
  OR (body->'definition'->>'synthetic_only') IS DISTINCT FROM 'true'
  OR (body->'definition'->>'production_approval') IS DISTINCT FROM 'false'
  OR (body->'definition'->>'clock') IS DISTINCT FROM 'database-utc' THEN
   RAISE EXCEPTION 'POLICY_INVALID' USING ERRCODE='23514'; END IF;
  p:=gen_random_uuid(); owner:=CASE WHEN w.realm='local' THEN 'workspace-admin' ELSE 'agency-admin' END;
  INSERT INTO cv.policy_version VALUES(w.tenant_id,p,body->>'kind',body->>'version',
   (a->>'user_id')::uuid,owner,true,clock_timestamp(),(body->>'expires_at')::timestamptz,body->'definition');
  result:=jsonb_build_object('policy_id',p,'kind',body->>'kind','version',body->>'version',
   'owner_user_id',a->>'user_id','owner_role',owner,'expires_at',body->>'expires_at',
   'revoked',false,'definition',body->'definition');
 ELSIF op='policy-revoke' THEN
  p:=(body->>'policy_id')::uuid;
  SELECT * INTO v FROM cv.policy_version WHERE (tenant_id,id)=(w.tenant_id,p) FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'ACCESS_DENIED' USING ERRCODE='42501'; END IF;
  IF coalesce(btrim(body->>'reason'),'')='' THEN RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
  INSERT INTO cv.policy_revocation VALUES(w.tenant_id,p,clock_timestamp(),(a->>'user_id')::uuid,body->>'reason')
  ON CONFLICT DO NOTHING;
  result:=jsonb_build_object('committed',true);
 ELSE
  p:=(body->>'purpose_id')::uuid; u:=(body->>'user_id')::uuid;
  PERFORM cv.auth_staff_record(u);
  SELECT * INTO v FROM cv.policy_version WHERE (tenant_id,id,kind)=(w.tenant_id,p,'purpose') FOR SHARE;
  IF NOT FOUND OR NOT cv.policy_live_at(w.tenant_id,p,'purpose',clock_timestamp()) THEN
   RAISE EXCEPTION 'ACCESS_DENIED' USING ERRCODE='42501'; END IF;
  SELECT revision INTO old_revision FROM cv.auth_grant_revision
   WHERE (tenant_id,user_id,purpose_id)=(w.tenant_id,u,p) FOR UPDATE;
  old_revision:=coalesce(old_revision,0);
  IF old_revision IS DISTINCT FROM (body->>'expected_revision')::integer THEN
   RAISE EXCEPTION 'REVISION_CONFLICT' USING ERRCODE='40001'; END IF;
  active_value:=(body->>'active')::boolean;
  IF active_value IS NULL THEN RAISE EXCEPTION 'INPUT_INVALID' USING ERRCODE='23514'; END IF;
  INSERT INTO cv.purpose_grant VALUES(w.tenant_id,u,p,active_value)
  ON CONFLICT(tenant_id,user_id,purpose_id) DO UPDATE SET active=excluded.active;
  INSERT INTO cv.auth_grant_revision VALUES(w.tenant_id,u,p,old_revision+1)
  ON CONFLICT(tenant_id,user_id,purpose_id) DO UPDATE SET revision=excluded.revision;
  result:=jsonb_build_object('user_id',u,'purpose_id',p,'active',active_value,'revision',old_revision+1);
 END IF;
 INSERT INTO cv.auth_command VALUES(w.instance_id,(a->>'user_id')::uuid,op,key,payload,result);
 INSERT INTO cv.auth_audit(instance_id,actor_id,action,record_id)
 VALUES(w.instance_id,(a->>'user_id')::uuid,op,p);
 RETURN result;
END $$;
REVOKE ALL ON FUNCTION cv.auth_policy_list(uuid),cv.auth_policy_write(text,uuid,cv.digest,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cv.auth_policy_list(uuid),cv.auth_policy_write(text,uuid,cv.digest,jsonb) TO cv_runtime;
RESET ROLE;
REVOKE CREATE ON SCHEMA cv FROM cv_guard;
