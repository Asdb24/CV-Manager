"""Versioned staff identity contracts. Public client never imports this graph."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, Field, SecretStr, field_validator, model_validator

from cv_foundation.settings import ClosedModel


def valid_unicode(value: str) -> str:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("TEXT_INVALID") from None
    return value


UTF8Text = Annotated[str, AfterValidator(valid_unicode)]


class AuthenticationPolicy(ClosedModel):
    version: str = Field(min_length=1, max_length=100)
    owner: Literal["workspace-admin", "server-operator"]
    startup_ttl_seconds: int = Field(gt=0, le=900, strict=True)
    session_ttl_seconds: int = Field(gt=0, le=86400, strict=True)
    attempt_window_seconds: int = Field(gt=0, le=3600, strict=True)
    account_attempt_limit: int = Field(gt=0, le=100, strict=True)
    global_attempt_limit: int = Field(gt=0, le=10000, strict=True)
    session_limit: int = Field(gt=0, le=20, strict=True)
    staff_limit: int = Field(gt=0, le=1000, strict=True)
    page_size: int = Field(gt=0, le=100, strict=True)
    password_min_characters: int = Field(ge=15, le=64, strict=True)
    password_max_characters: int = Field(ge=64, le=1024, strict=True)
    argon_memory_kib: int = Field(ge=19456, le=262144, strict=True)
    argon_time_cost: int = Field(ge=2, le=10, strict=True)
    argon_parallelism: int = Field(ge=1, le=8, strict=True)
    hash_concurrency: int = Field(ge=1, le=8, strict=True)
    hash_wait_seconds: int = Field(gt=0, le=30, strict=True)
    request_max_bytes: int = Field(ge=4096, le=1048576, strict=True)

    @model_validator(mode="after")
    def coherent(self) -> "AuthenticationPolicy":
        if self.account_attempt_limit > self.global_attempt_limit:
            raise ValueError("AUTH_LIMIT_INVALID")
        if self.password_min_characters > self.password_max_characters:
            raise ValueError("PASSWORD_LIMIT_INVALID")
        return self


class PasswordInput(ClosedModel):
    password: SecretStr

    @field_validator("password")
    @classmethod
    def bounded_secret(cls, value: SecretStr) -> SecretStr:
        # Absolute parser ceiling; active policy applies the narrower password range.
        secret = value.get_secret_value()
        if not 1 <= len(secret) <= 1024:
            raise ValueError("PASSWORD_INVALID")
        try:
            secret.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("PASSWORD_INVALID") from None
        return value


class LoginRequest(PasswordInput):
    instance_id: UUID
    login_name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")


class BootstrapCreate(LoginRequest):
    agency_name: UTF8Text = Field(min_length=1, max_length=200)


class InstanceStatus(ClosedModel):
    version: Literal["auth-v1"] = "auth-v1"
    instance_id: UUID
    realm: Literal["local", "server"]
    realm_key: str
    state: Literal["new", "initialized", "closed"]


class StaffIdentity(ClosedModel):
    instance_id: UUID
    tenant_id: UUID
    user_id: UUID
    session_id: UUID
    login_name: str
    role: Literal["admin", "recruiter"]
    expires_at: datetime


class LoginResult(ClosedModel):
    # The wire response necessarily carries a token; never log this model.
    token: str = Field(repr=False)
    identity: StaffIdentity


class StaffRecord(ClosedModel):
    user_id: UUID
    login_name: str
    role: Literal["admin", "recruiter"]
    active: bool
    revision: int


class StaffCreate(PasswordInput):
    login_name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    role: Literal["admin", "recruiter"]


class StaffUpdate(ClosedModel):
    expected_revision: int = Field(gt=0, strict=True)
    role: Literal["admin", "recruiter"]
    active: bool = Field(strict=True)


class SessionRevoke(ClosedModel):
    session_id: UUID


class Confirmed(ClosedModel):
    committed: Literal[True] = True


class PolicyDefinition(ClosedModel):
    synthetic_only: Literal[True]
    production_approval: Literal[False]
    clock: Literal["database-utc"]
    description: UTF8Text = Field(min_length=1, max_length=2000)
    retention_seconds: int | None = Field(default=None, gt=0, le=604800, strict=True)
    public_submission_quota: int | None = Field(default=None, gt=0, le=10000, strict=True)
    max_pdf_bytes: int | None = Field(default=None, gt=0, le=1073741824, strict=True)
    contact_max_characters: int | None = Field(default=None, gt=0, le=2000, strict=True)


class PolicyActivate(ClosedModel):
    kind: Literal["source", "purpose", "consent", "retention", "erasure", "resource"]
    version: UTF8Text = Field(min_length=1, max_length=100)
    expires_at: datetime
    definition: PolicyDefinition

    @model_validator(mode="after")
    def complete_definition(self) -> "PolicyActivate":
        if self.expires_at.tzinfo is None:
            raise ValueError("POLICY_TIMEZONE_REQUIRED")
        if self.kind == "retention" and self.definition.retention_seconds is None:
            raise ValueError("RETENTION_REQUIRED")
        if self.kind == "resource" and any(
            value is None
            for value in (
                self.definition.public_submission_quota,
                self.definition.max_pdf_bytes,
                self.definition.contact_max_characters,
            )
        ):
            raise ValueError("RESOURCE_LIMITS_REQUIRED")
        return self


class PolicyRevoke(ClosedModel):
    reason: UTF8Text = Field(min_length=1, max_length=1000)


class PurposeGrant(ClosedModel):
    user_id: UUID
    purpose_id: UUID
    active: bool = Field(strict=True)
    expected_revision: int = Field(ge=0, strict=True)


class PolicyRecord(ClosedModel):
    policy_id: UUID
    kind: str
    version: str
    owner_user_id: UUID
    owner_role: str
    expires_at: datetime
    revoked: bool
    definition: PolicyDefinition


class GrantRecord(ClosedModel):
    user_id: UUID
    purpose_id: UUID
    active: bool
    revision: int
