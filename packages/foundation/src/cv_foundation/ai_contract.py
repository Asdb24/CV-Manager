"""Actual FastAPI schema for the future employee-Windows service. No inference server."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cv_foundation.contracts import AITaskRequest, AITaskStatus, SafeError

startup_bearer = HTTPBearer(auto_error=False)


def startup_authority(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(startup_bearer)],
) -> None:
    # Schema app grants no startup/task authority, even with a caller-supplied token.
    raise HTTPException(status_code=503, detail="AI_SCHEMA_ONLY")


def create_contract_app() -> FastAPI:
    app = FastAPI(title="Windows local AI contract", version="0.1.0")

    @app.exception_handler(HTTPException)
    async def safe_contract_error(_: Request, error: HTTPException) -> JSONResponse:
        return JSONResponse(
            SafeError(
                code="AI_SCHEMA_ONLY", message="Dịch vụ AI chưa được triển khai."
            ).model_dump(),
            status_code=error.status_code,
        )

    @app.post(
        "/ai/tasks",
        tags=["local-ai"],
        operation_id="submitLocalAITask",
        response_model=AITaskStatus,
        responses={503: {"model": SafeError}},
        dependencies=[Depends(startup_authority)],
    )
    def submit(_: AITaskRequest) -> None:
        raise HTTPException(status_code=503, detail="AI_SCHEMA_ONLY")

    @app.get(
        "/ai/tasks/{task_id}",
        tags=["local-ai"],
        operation_id="localAITaskStatus",
        response_model=AITaskStatus,
        responses={503: {"model": SafeError}},
        dependencies=[Depends(startup_authority)],
    )
    def status(task_id: UUID) -> None:
        raise HTTPException(status_code=503, detail="AI_SCHEMA_ONLY")

    @app.post(
        "/ai/tasks/{task_id}/cancel",
        tags=["local-ai"],
        operation_id="cancelLocalAITask",
        response_model=AITaskStatus,
        responses={503: {"model": SafeError}},
        dependencies=[Depends(startup_authority)],
    )
    def cancel(task_id: UUID) -> None:
        raise HTTPException(status_code=503, detail="AI_SCHEMA_ONLY")

    return app
