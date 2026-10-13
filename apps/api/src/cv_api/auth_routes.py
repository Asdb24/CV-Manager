"""Staff-only versioned routes and restricted local bootstrap interface."""

from typing import Annotated
from uuid import UUID

from cv_foundation.auth_contracts import (
    BootstrapCreate,
    Confirmed,
    GrantRecord,
    InstanceStatus,
    LoginRequest,
    LoginResult,
    PolicyActivate,
    PolicyRecord,
    PolicyRevoke,
    PurposeGrant,
    SessionRevoke,
    StaffCreate,
    StaffIdentity,
    StaffRecord,
    StaffUpdate,
)
from cv_foundation.contracts import SafeError
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cv_api.authentication import Authentication

bearer = HTTPBearer(auto_error=False)


def proof(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None or not 1 <= len(credentials.credentials) <= 256:
        raise HTTPException(status_code=401, detail="AUTH_DENIED")
    return credentials.credentials


StaffProof = Annotated[str, Depends(proof)]
OperationKey = Annotated[UUID, Header(alias="Idempotency-Key")]


def router(authentication: Authentication) -> APIRouter:
    routes = APIRouter(
        tags=["staff"],
        responses={401: {"model": SafeError}, 403: {"model": SafeError}, 409: {"model": SafeError}},
    )

    @routes.get("/auth/v1/instance", operation_id="authInstance", response_model=InstanceStatus)
    def instance() -> InstanceStatus:
        return authentication.status()

    @routes.post("/auth/v1/bootstrap", operation_id="localBootstrap", response_model=Confirmed)
    def bootstrap(
        body: BootstrapCreate,
        startup: Annotated[
            str, Header(alias="X-Bootstrap-Authority", min_length=1, max_length=256)
        ],
    ) -> Confirmed:
        authentication.bootstrap(body, startup)
        return Confirmed()

    @routes.post("/auth/v1/login", operation_id="staffLogin", response_model=LoginResult)
    def login(body: LoginRequest) -> LoginResult:
        return authentication.login(body)

    @routes.get("/auth/v1/session", operation_id="currentSession", response_model=StaffIdentity)
    def current(token: StaffProof) -> StaffIdentity:
        return authentication.current(token)

    @routes.post("/auth/v1/logout", operation_id="staffLogout", response_model=Confirmed)
    def logout(token: StaffProof) -> Confirmed:
        authentication.logout(token)
        return Confirmed()

    @routes.post("/auth/v1/revoke", operation_id="revokeSession", response_model=Confirmed)
    def revoke(body: SessionRevoke, token: StaffProof) -> Confirmed:
        authentication.revoke(token, body.session_id)
        return Confirmed()

    @routes.get("/staff/v1/users", operation_id="listStaff", response_model=list[StaffRecord])
    def users(token: StaffProof, after: UUID | None = None) -> list[StaffRecord]:
        return authentication.list_staff(token, after)

    @routes.post("/staff/v1/users", operation_id="createStaff", response_model=StaffRecord)
    def create_user(body: StaffCreate, token: StaffProof, key: OperationKey) -> StaffRecord:
        return authentication.write_staff(token, key, body)

    @routes.post(
        "/staff/v1/users/{user_id}", operation_id="updateStaff", response_model=StaffRecord
    )
    def update_user(
        user_id: UUID, body: StaffUpdate, token: StaffProof, key: OperationKey
    ) -> StaffRecord:
        return authentication.write_staff(token, key, body, user_id)

    @routes.get(
        "/staff/v1/policies", operation_id="listPolicies", response_model=list[PolicyRecord]
    )
    def policies(token: StaffProof, after: UUID | None = None) -> list[PolicyRecord]:
        return authentication.list_policies(token, after)

    @routes.post("/staff/v1/policies", operation_id="activatePolicy", response_model=PolicyRecord)
    def activate(body: PolicyActivate, token: StaffProof, key: OperationKey) -> PolicyRecord:
        return PolicyRecord.model_validate(authentication.policy_command(token, key, body))

    @routes.post(
        "/staff/v1/policies/{policy_id}/revoke",
        operation_id="revokePolicy",
        response_model=Confirmed,
    )
    def revoke_policy(
        policy_id: UUID, body: PolicyRevoke, token: StaffProof, key: OperationKey
    ) -> Confirmed:
        return Confirmed.model_validate(authentication.policy_command(token, key, body, policy_id))

    @routes.post(
        "/staff/v1/purpose-grants", operation_id="grantPurpose", response_model=GrantRecord
    )
    def grant(body: PurposeGrant, token: StaffProof, key: OperationKey) -> GrantRecord:
        return GrantRecord.model_validate(authentication.policy_command(token, key, body))

    return routes
