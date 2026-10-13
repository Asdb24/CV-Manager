"""Transport DTOs. No CV payload, tenant assertion or path is execution authority."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from cv_foundation.settings import ClosedModel


class SafeError(ClosedModel):
    code: str
    message: str


class Liveness(ClosedModel):
    component: Literal["api", "worker"]
    alive: bool


class Capability(ClosedModel):
    state: Literal["ready", "unavailable"]
    required_dependencies: list[str]
    code: str
    owner_phase: str


class Readiness(ClosedModel):
    component: Literal["api", "worker"]
    ready: bool
    implemented_dependencies: list[str]
    capabilities: dict[str, Capability]


class PublicCapabilities(ClosedModel):
    jobs: Literal["unavailable"]
    applications: Literal["unavailable"]
    code: Literal["PUBLIC_FEATURES_NOT_IMPLEMENTED"]


class StaffCapabilities(ClosedModel):
    authentication: Literal["ready"]
    code: Literal["AUTHENTICATED"]


class JobProjection(ClosedModel):
    publication_id: UUID
    agency_display_name: str
    company_display_name: str | None
    title: str
    location: str
    work_arrangement: str
    employment_type: str
    description: str
    application_instructions: str
    application_open: bool
    expires_at: datetime | None


class PurposeConsent(ClosedModel):
    policy_version: str
    purpose_version: str
    accepted: Literal[True]


class ApplicationContact(ClosedModel):
    name: str = Field(min_length=1)
    email: str | None
    phone: str | None


class PublicSubmissionContract(ClosedModel):
    publication_id: UUID
    contact: ApplicationContact
    consent: PurposeConsent
    upload_intent_handle: str


class SubmissionReceipt(ClosedModel):
    receipt: str
    status: Literal["accepted_for_review"]


class EvidenceReference(ClosedModel):
    document_version: UUID
    page: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ApprovedInputManifest(ClosedModel):
    manifest_id: UUID
    realm_key: str
    person_id: UUID
    privacy_epoch: UUID
    purpose_version: str
    consent_version: str
    application_revision: UUID
    profile_revision: UUID
    jd_version: UUID
    evidence: list[EvidenceReference]
    opaque_input_handle: str
    expires_at: AwareDatetime
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class AITaskRequest(ClosedModel):
    input_manifest: ApprovedInputManifest
    owned_input_handle: str = Field(pattern=r"^[a-f0-9]{64}$")
    model_manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    rule_version: str
    template_version: str
    operation_key: UUID


class AdvisoryProvenance(ClosedModel):
    input_manifest_digest: str
    model_manifest_digest: str
    tokenizer_digest: str
    runtime_version: str
    rule_version: str
    template_version: str
    ranking_version: str
    execution_mode: Literal["standalone", "connected"]
    device_session_reference: str


class SemanticSuggestion(ClosedModel):
    criterion_key: str
    evidence: EvidenceReference
    advisory_similarity: float = Field(allow_inf_nan=False, ge=-1, le=1)
    rank: int = Field(gt=0)


class VerificationFinding(ClosedModel):
    rule_key: str
    message_vi: str
    evidence: list[EvidenceReference]
    status: Literal["to_verify"]


class InterviewQuestion(ClosedModel):
    template_key: str
    question_vi: str
    evidence: list[EvidenceReference]


class AdvisoryAttachment(ClosedModel):
    task_id: UUID
    provenance: AdvisoryProvenance
    input_manifest: ApprovedInputManifest
    semantic_evidence: list[SemanticSuggestion]
    findings: list[VerificationFinding]
    questions: list[InterviewQuestion]


class AITaskStatus(ClosedModel):
    task_id: UUID
    state: Literal["queued", "running", "completed", "cancelled", "failed"]
    processed_chunks: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    code: str | None


def unavailable_capabilities() -> dict[str, Capability]:
    return {
        "shell": Capability(
            state="ready", required_dependencies=[], code="SHELL_ONLY", owner_phase="02"
        ),
        "company": Capability(
            state="unavailable",
            required_dependencies=["database"],
            code="DATABASE_ADAPTER_NOT_IMPLEMENTED",
            owner_phase="03",
        ),
        "authentication": Capability(
            state="unavailable",
            required_dependencies=["database"],
            code="AUTH_NOT_IMPLEMENTED",
            owner_phase="04",
        ),
        "document": Capability(
            state="unavailable",
            required_dependencies=["database", "document_storage", "document_runner"],
            code="DOCUMENT_NOT_IMPLEMENTED",
            owner_phase="08",
        ),
        "local_ai": Capability(
            state="unavailable",
            required_dependencies=["windows_model_runner"],
            code="AI_SCHEMA_ONLY",
            owner_phase="10",
        ),
    }
