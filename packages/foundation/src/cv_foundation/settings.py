"""The sole operational-settings validator. Browser projections are allowlists."""

from __future__ import annotations

import argparse
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InfrastructureSettings(ClosedModel):
    profile: Literal["development", "test"]
    project: str = Field(pattern=r"^cv-synthetic-[a-z]+$")
    bind_host: Literal["127.0.0.1"]
    port: int = Field(ge=1, le=65535, strict=True)
    database: str = Field(pattern=r"^cv_synthetic_[a-z]+$")
    role: str = Field(pattern=r"^cv_synthetic_[a-z]+$")
    password_environment: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    health_interval_seconds: int = Field(gt=0, le=120, strict=True)
    health_timeout_seconds: int = Field(gt=0, le=120, strict=True)
    health_retries: int = Field(gt=0, le=100, strict=True)
    memory_bytes: int = Field(gt=0, le=10737418240, strict=True)


class DatabaseTestSettings(ClosedModel):
    """Isolated synthetic cluster settings; never a recipient runtime manifest."""

    profile: Literal["test"]
    cluster_directory: str = Field(min_length=1)
    credential_file: str = Field(min_length=1)
    host: Literal["127.0.0.1"]
    port: int = Field(ge=1, le=65535, strict=True)
    database: str = Field(pattern=r"^cv_phase03_[a-z_]+$")
    connect_timeout_seconds: int = Field(gt=0, le=60, strict=True)
    statement_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    lock_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    startup_timeout_seconds: int = Field(gt=0, le=120, strict=True)
    seed_validity_seconds: int = Field(gt=0, le=604800, strict=True)
    synthetic_company_count: int = Field(gt=0, le=100000, strict=True)
    synthetic_person_count: int = Field(gt=0, le=100000, strict=True)
    query_page_size: int = Field(gt=0, le=1000, strict=True)

    @model_validator(mode="after")
    def owned_paths(self) -> DatabaseTestSettings:
        root = Path.cwd().resolve()
        for value in [self.cluster_directory, self.credential_file]:
            if not (root / value).resolve().is_relative_to(root / ".local" / "phase03"):
                raise ValueError("DATABASE_TEST_PATH_OUTSIDE_OWNED_DIRECTORY")
        return self


class DatabaseConnectionSettings(ClosedModel):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535, strict=True)
    database: str = Field(min_length=1)
    user: Literal["cv_runtime", "cv_public", "cv_probe"]
    password: SecretStr
    sslmode: Literal["disable", "verify-full"]
    sslrootcert: str | None
    connect_timeout_seconds: int = Field(gt=0, le=60, strict=True)
    statement_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    lock_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    connection_limit: int = Field(gt=0, le=64, strict=True)

    @model_validator(mode="after")
    def secure_connection(self) -> DatabaseConnectionSettings:
        if not self.password.get_secret_value():
            raise ValueError("DATABASE_PASSWORD_REQUIRED")
        if self.sslmode == "disable" and self.host not in {"127.0.0.1", "::1"}:
            raise ValueError("DATABASE_TLS_REQUIRED")
        if self.sslmode == "verify-full" and not self.sslrootcert:
            raise ValueError("DATABASE_TRUST_ROOT_REQUIRED")
        return self


class Profile(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STANDALONE = "standalone"
    SERVER = "server"
    CONNECTED = "connected"


class Component(StrEnum):
    DESKTOP = "desktop"
    WEB = "web"
    API = "api"
    WORKER = "worker"
    LOCAL_AI = "local_ai"


class Binding(ClosedModel):
    host: str
    port: int = Field(ge=1, le=65535, strict=True)


class Network(ClosedModel):
    api_origin: str
    desktop_origin: str
    native_desktop_origin: Literal["http://tauri.localhost"]
    web_origin: str
    worker_origin: str
    ai_origin: str
    approved_server_origin: str | None
    cors_origins: list[str]
    api_binding: Binding
    worker_binding: Binding
    request_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    shutdown_timeout_ms: int = Field(gt=0, le=120000, multiple_of=1000, strict=True)
    keep_alive_seconds: int = Field(gt=0, le=120, strict=True)
    tls_verify: Literal[True]
    redirect_policy: Literal["deny"]
    csp_script_policy: Literal["nonce-self"]
    csp_frame_ancestors: Literal["none"]


class Resources(ClosedModel):
    policy_version: str = Field(min_length=1)
    ai_peak_working_set_bytes: int = Field(gt=0, le=1610612736, strict=True)
    ai_threads: int = Field(gt=0, le=64, strict=True)
    ai_batch_size: int = Field(gt=0, le=64, strict=True)
    ai_concurrency: int = Field(gt=0, le=8, strict=True)
    ai_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    ai_max_tokens: int = Field(gt=0, le=512, strict=True)
    ai_max_chunks: int = Field(gt=0, le=2048, strict=True)
    max_pdf_bytes: int = Field(gt=0, le=1073741824, strict=True)
    max_pdf_pages: int = Field(gt=0, le=10000, strict=True)
    max_text_characters: int = Field(gt=0, le=10000000, strict=True)
    worker_queue_size: int = Field(gt=0, le=10000, strict=True)
    worker_concurrency: int = Field(gt=0, le=64, strict=True)
    worker_task_timeout_ms: int = Field(gt=0, le=120000, strict=True)
    temp_expiry_seconds: int = Field(gt=0, le=86400, strict=True)
    temp_capacity_bytes: int = Field(gt=0, le=10737418240, strict=True)
    public_page_size: int = Field(gt=0, le=200, strict=True)
    public_submission_quota: int = Field(gt=0, le=10000, strict=True)


class Dependencies(ClosedModel):
    authentication_policy_file: str = Field(min_length=1)
    database_secret_env: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    document_root: str | None = Field(min_length=1)
    temporary_root: str = Field(min_length=1)
    model_manifest: str = Field(min_length=1)


class PrivacyPolicy(ClosedModel):
    version: str = Field(min_length=1)
    owner_role: str
    data_class: str
    real_onboarding_approved: bool
    source_policy_version: str = Field(min_length=1)
    consent_policy_version: str = Field(min_length=1)
    purpose_policy_version: str = Field(min_length=1)
    retention_policy_version: str = Field(min_length=1)
    erasure_policy_version: str = Field(min_length=1)


class ReleaseManifest(ClosedModel):
    manifest_version: str = Field(min_length=1)
    release_kind: Literal["installed", "portable"]
    owner: Literal["native-release"]

    @model_validator(mode="after")
    def valid_kind(self) -> ReleaseManifest:
        if self.release_kind not in {"installed", "portable"} or self.owner != "native-release":
            raise ValueError("RELEASE_MANIFEST_INVALID")
        return self


def origin_parts(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(value)
    if (
        value != value.strip()
        or parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or value.endswith("/")
    ):
        raise ValueError("ORIGIN_INVALID")
    # IANA default scheme ports are protocol definitions, not a dev-service fallback.
    port = parsed.port
    if port is not None and port < 1:
        raise ValueError("ORIGIN_PORT_INVALID")
    effective_port = port if port is not None else (443 if parsed.scheme == "https" else 80)
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    default_port = 443 if parsed.scheme == "https" else 80
    canonical = f"{parsed.scheme}://{host}" + (
        f":{effective_port}" if effective_port != default_port else ""
    )
    if value != canonical:
        raise ValueError("CANONICAL_ORIGIN_REQUIRED")
    return (
        parsed.scheme,
        parsed.hostname,
        effective_port,
    )


class Settings(ClosedModel):
    profile: Profile
    realm: Literal["local", "server"]
    realm_key: str = Field(min_length=1)
    execution_mode: Literal["standalone", "connected"]
    release_manifest: str | None
    network: Network
    resources: Resources
    dependencies: Dependencies
    privacy: PrivacyPolicy

    @model_validator(mode="after")
    def validate_authority(self) -> Settings:
        if self.realm not in {"local", "server"} or self.execution_mode not in {
            "standalone",
            "connected",
        }:
            raise ValueError("MODE_INVALID")
        if (self.realm == "local") != (self.execution_mode == "standalone"):
            raise ValueError("REALM_MODE_MISMATCH")
        origins = [
            self.network.api_origin,
            self.network.desktop_origin,
            self.network.web_origin,
            self.network.worker_origin,
            self.network.ai_origin,
            *self.network.cors_origins,
        ]
        for origin in origins:
            origin_parts(origin)
        for owned in [self.network.worker_origin, self.network.ai_origin]:
            scheme, host, _ = origin_parts(owned)
            if scheme != "http" or host not in {"127.0.0.1", "::1"}:
                raise ValueError("OWNED_LOOPBACK_REQUIRED")
        if self.profile in {Profile.DEVELOPMENT, Profile.TEST}:
            for origin in origins:
                # Tauri's Windows embedded origin is virtual, never a network destination.
                scheme, host, _ = origin_parts(origin)
                if origin != self.network.native_desktop_origin and (
                    scheme != "http" or host not in {"127.0.0.1", "::1"}
                ):
                    raise ValueError("DEVELOPMENT_LOOPBACK_REQUIRED")
            if self.release_manifest is not None:
                raise ValueError("DEVELOPMENT_RELEASE_MANIFEST_FORBIDDEN")
            endpoints = [
                origin_parts(value)[1:]
                for value in [
                    self.network.api_origin,
                    self.network.desktop_origin,
                    self.network.web_origin,
                    self.network.worker_origin,
                    self.network.ai_origin,
                ]
            ]
            if len(set(endpoints)) != len(endpoints):
                raise ValueError("OWNED_SERVICE_PORT_COLLISION")
        else:
            if self.profile == Profile.STANDALONE and self.realm != "local":
                raise ValueError("PROFILE_REALM_MISMATCH")
            if self.profile in {Profile.CONNECTED, Profile.SERVER} and self.realm != "server":
                raise ValueError("PROFILE_REALM_MISMATCH")
            if self.realm == "server":
                approved = self.network.approved_server_origin
                if approved is None or origin_parts(approved)[0] != "https":
                    raise ValueError("APPROVED_HTTPS_SERVER_REQUIRED")
                if self.network.api_origin != approved:
                    raise ValueError("APPROVED_SERVER_MISMATCH")
                if origin_parts(self.network.web_origin)[0] != "https":
                    raise ValueError("PUBLIC_HTTPS_REQUIRED")
            elif origin_parts(self.network.api_origin)[1] not in {"127.0.0.1", "::1"}:
                raise ValueError("LOCAL_API_LOOPBACK_REQUIRED")
        if self.profile == Profile.SERVER and (
            not self.dependencies.database_secret_env or not self.dependencies.document_root
        ):
            raise ValueError("SERVER_PERSISTENCE_SETTINGS_REQUIRED")
        if self.profile in {Profile.CONNECTED, Profile.STANDALONE} and not self.release_manifest:
            raise ValueError("NATIVE_RELEASE_MANIFEST_REQUIRED")
        if self.realm == "local" and self.network.approved_server_origin is not None:
            raise ValueError("LOCAL_SERVER_ORIGIN_FORBIDDEN")
        if set(self.network.cors_origins) != {
            self.network.desktop_origin,
            self.network.native_desktop_origin,
            self.network.web_origin,
        }:
            raise ValueError("EXACT_CORS_ALLOWLIST_REQUIRED")
        for origin, binding in [
            (self.network.api_origin, self.network.api_binding),
            (self.network.worker_origin, self.network.worker_binding),
        ]:
            if binding.host not in {"127.0.0.1", "::1"}:
                raise ValueError("SERVICE_BINDING_LOOPBACK_REQUIRED")
            if (
                self.profile in {Profile.DEVELOPMENT, Profile.TEST}
                or origin == self.network.worker_origin
                or self.realm == "local"
            ):
                _, host, port = origin_parts(origin)
                if (host, port) != (binding.host, binding.port):
                    raise ValueError("BINDING_ORIGIN_MISMATCH")
        if self.privacy.data_class != "synthetic-only" or self.privacy.real_onboarding_approved:
            raise ValueError("REAL_ONBOARDING_NOT_APPROVED_IN_FOUNDATION")
        if self.privacy.owner_role not in {"workspace-admin", "agency-admin"}:
            raise ValueError("POLICY_OWNER_INVALID")
        return self

    def for_component(self, component: Component) -> Settings:
        allowed = {
            Component.DESKTOP: {
                Profile.DEVELOPMENT,
                Profile.TEST,
                Profile.STANDALONE,
                Profile.CONNECTED,
            },
            Component.WEB: {Profile.DEVELOPMENT, Profile.TEST, Profile.SERVER},
            Component.API: {Profile.DEVELOPMENT, Profile.TEST, Profile.STANDALONE, Profile.SERVER},
            Component.WORKER: {
                Profile.DEVELOPMENT,
                Profile.TEST,
                Profile.STANDALONE,
                Profile.SERVER,
            },
            Component.LOCAL_AI: {
                Profile.DEVELOPMENT,
                Profile.TEST,
                Profile.STANDALONE,
                Profile.CONNECTED,
            },
        }
        if self.profile not in allowed[component]:
            raise ValueError("COMPONENT_PROFILE_INCOMPATIBLE")
        return self


class ClientConfiguration(ClosedModel):
    profile: Profile
    execution_mode: Literal["standalone", "connected"]
    realm_key: str
    api_origin: str
    desktop_origin: str
    web_origin: str
    desktop_host: str
    desktop_port: int
    web_host: str
    web_port: int
    request_timeout_ms: int
    release_kind: Literal["installed", "portable"] | None


def load_settings(path: Path, profile: Profile, component: Component) -> Settings:
    settings = Settings.model_validate_json(path.read_text(encoding="utf-8"))
    if settings.profile != profile:
        raise ValueError("EXPLICIT_PROFILE_MISMATCH")
    settings.for_component(component)
    if settings.release_manifest:
        ReleaseManifest.model_validate_json(
            Path(settings.release_manifest).read_text(encoding="utf-8")
        )
    return settings


def client_projection(settings: Settings) -> ClientConfiguration:
    release = None
    if settings.release_manifest:
        release = ReleaseManifest.model_validate_json(
            Path(settings.release_manifest).read_text(encoding="utf-8")
        ).release_kind
    return ClientConfiguration(
        profile=settings.profile,
        execution_mode=settings.execution_mode,
        realm_key=settings.realm_key,
        api_origin=settings.network.api_origin,
        desktop_origin=settings.network.desktop_origin,
        web_origin=settings.network.web_origin,
        desktop_host=origin_parts(settings.network.desktop_origin)[1],
        desktop_port=origin_parts(settings.network.desktop_origin)[2],
        web_host=origin_parts(settings.network.web_origin)[1],
        web_port=origin_parts(settings.network.web_origin)[2],
        request_timeout_ms=settings.network.request_timeout_ms,
        release_kind=release,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", type=Profile, required=True)
    parser.add_argument("--component", type=Component, required=True)
    parser.add_argument("--client", action="store_true")
    args = parser.parse_args()
    try:
        settings = load_settings(args.config, args.profile, args.component)
    except (ValueError, OSError, ValidationError):
        parser.exit(2, "CONFIGURATION_INVALID: inspect required settings and component/profile.\n")
    if args.client:
        print(client_projection(settings).model_dump_json())
    else:
        print(json.dumps({"valid": True, "component": args.component, "profile": args.profile}))


if __name__ == "__main__":
    main()
