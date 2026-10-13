from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from cv_foundation.contracts import Liveness, Readiness
from cv_foundation.database import configured_database, database_readiness
from cv_foundation.settings import Settings
from fastapi import FastAPI
from starlette.responses import JSONResponse

from cv_worker.interfaces import BoundedWorker


def create_app(settings: Settings) -> FastAPI:
    database = configured_database(settings)
    worker = BoundedWorker(
        settings.resources.worker_queue_size,
        settings.resources.worker_concurrency,
        settings.resources.worker_task_timeout_ms,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()

    app = FastAPI(title="Owned document worker", version="0.1.0", lifespan=lifespan)

    @app.get("/live", response_model=Liveness, operation_id="workerLiveness")
    def live() -> Liveness:
        return Liveness(component="worker", alive=True)

    @app.get("/ready", response_model=Readiness, responses={503: {"model": Readiness}})
    def ready() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=database_readiness("worker", database).model_dump(),
        )

    return app
