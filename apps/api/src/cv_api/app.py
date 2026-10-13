from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from cv_foundation.contracts import (
    AdvisoryAttachment,
    JobProjection,
    Liveness,
    PublicCapabilities,
    PublicSubmissionContract,
    Readiness,
    SafeError,
    StaffCapabilities,
    SubmissionReceipt,
)
from cv_foundation.database import PersistenceError, configured_database, database_readiness
from cv_foundation.settings import ClientConfiguration, Settings
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.requests import Request
from starlette.responses import JSONResponse

from cv_api.auth_boundary import AuthenticationBoundary
from cv_api.auth_routes import proof, router
from cv_api.authentication import Authentication, AuthenticationError

bearer = HTTPBearer(auto_error=False)


def create_app(settings: Settings) -> FastAPI:
    database = configured_database(settings)
    authentication = Authentication(database, settings)

    def staff_authority(token: Annotated[str, Depends(proof)]) -> None:
        authentication.current(token)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(title="Agency CV API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.network.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Bootstrap-Authority"],
    )
    app.add_middleware(
        AuthenticationBoundary, settings=settings, max_bytes=authentication.policy.request_max_bytes
    )
    app.include_router(router(authentication))

    @app.exception_handler(AuthenticationError)
    @app.exception_handler(PersistenceError)
    async def authentication_error(_: Request, exc: Exception) -> JSONResponse:
        code = str(exc)
        unavailable = {
            "AUTH_UNAVAILABLE",
            "AUTH_POLICY_MISMATCH",
            "DATABASE_UNAVAILABLE",
            "AUTH_BUSY",
            "DATABASE_BUSY",
            "DATABASE_TIMEOUT",
        }
        conflict = {"CONFLICT", "CONSTRAINT_REJECTED", "REVISION_CONFLICT", "RETRY_TRANSACTION"}
        status = (
            503
            if code in unavailable
            else 409
            if code in conflict
            else 422
            if code == "PASSWORD_POLICY"
            else 401
        )
        return JSONResponse(
            status_code=status,
            content={
                "code": code,
                "message": "Kiểm tra thông tin đăng nhập, quyền hoặc trạng thái kết nối.",
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.exception_handler(HTTPException)
    async def safe_exception(_: Request, exc: HTTPException) -> JSONResponse:
        code = str(exc.detail) if isinstance(exc.detail, str) else "REQUEST_REJECTED"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": code,
                "message": "Chức năng chưa khả dụng hoặc quyền truy cập không hợp lệ.",
            },
        )

    @app.exception_handler(RequestValidationError)
    async def safe_validation(_: Request, __: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "INPUT_INVALID",
                "message": "Kiểm tra các trường bắt buộc và định dạng dữ liệu.",
            },
        )

    @app.get("/live", response_model=Liveness, tags=["system"], operation_id="apiLiveness")
    def live() -> Liveness:
        return Liveness(component="api", alive=True)

    @app.get(
        "/ready",
        response_model=Readiness,
        tags=["system"],
        operation_id="apiReadiness",
        responses={503: {"model": Readiness}},
    )
    def ready() -> JSONResponse:
        state = database_readiness("api", database)
        return JSONResponse(status_code=503, content=state.model_dump())

    @app.get(
        "/public/capabilities",
        response_model=PublicCapabilities,
        tags=["public"],
        operation_id="publicCapabilities",
    )
    def public_capabilities() -> PublicCapabilities:
        return PublicCapabilities(
            jobs="unavailable", applications="unavailable", code="PUBLIC_FEATURES_NOT_IMPLEMENTED"
        )

    @app.get(
        "/public/jobs",
        response_model=list[JobProjection],
        tags=["public"],
        operation_id="publicJobs",
        responses={503: {"model": SafeError}},
    )
    def public_jobs() -> None:
        raise HTTPException(status_code=503, detail="JOBS_NOT_IMPLEMENTED")

    @app.post(
        "/public/applications",
        response_model=SubmissionReceipt,
        tags=["public"],
        operation_id="publicApplication",
        responses={503: {"model": SafeError}},
    )
    def public_application(_: PublicSubmissionContract) -> None:
        # No accepted receipt or file/candidate creation exists in this phase.
        raise HTTPException(status_code=503, detail="PUBLIC_INTAKE_NOT_IMPLEMENTED")

    @app.get(
        "/staff/capabilities",
        response_model=StaffCapabilities,
        tags=["staff"],
        operation_id="staffCapabilities",
        dependencies=[Depends(staff_authority)],
        responses={401: {"model": SafeError}},
    )
    def staff_capabilities() -> StaffCapabilities:
        return StaffCapabilities(authentication="ready", code="AUTHENTICATED")

    @app.post(
        "/staff/advisory-attachments",
        tags=["staff"],
        operation_id="attachAdvisory",
        dependencies=[Depends(staff_authority)],
        responses={401: {"model": SafeError}, 503: {"model": SafeError}},
    )
    def attach_advisory(_: AdvisoryAttachment) -> None:
        raise HTTPException(status_code=503, detail="ADVISORY_ATTACHMENT_NOT_IMPLEMENTED")

    # Projection schema is generated from the same authoritative model, not a second validator.
    @app.get(
        "/contracts/client-configuration",
        response_model=ClientConfiguration,
        tags=["contract"],
        operation_id="clientConfigurationContract",
        include_in_schema=True,
    )
    def config_contract() -> None:
        raise HTTPException(status_code=503, detail="SCHEMA_ONLY")

    return app
