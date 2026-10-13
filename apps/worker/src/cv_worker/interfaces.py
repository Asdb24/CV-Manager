import asyncio
from typing import Protocol
from uuid import UUID

from cv_foundation.contracts import ApprovedInputManifest


class DocumentRunner(Protocol):
    async def execute(self, manifest: ApprovedInputManifest, cancelled: asyncio.Event) -> None: ...


class WorkItem(Protocol):
    task_id: UUID
    manifest: ApprovedInputManifest
    cancelled: asyncio.Event


class BoundedWorker:
    def __init__(self, queue_size: int, concurrency: int, timeout_ms: int) -> None:
        self.queue: asyncio.Queue[WorkItem] = asyncio.Queue(maxsize=queue_size)
        self.concurrency = concurrency
        self.timeout_seconds = timeout_ms / 1000
        self.tasks: list[asyncio.Task[None]] = []
        self.runner: DocumentRunner | None = None
        self.stopping = False

    async def start(self) -> None:
        self.tasks = [asyncio.create_task(self.consume()) for _ in range(self.concurrency)]

    def admit(self, item: WorkItem) -> None:
        if self.stopping or self.runner is None:
            raise RuntimeError("DOCUMENT_RUNNER_UNAVAILABLE")
        self.queue.put_nowait(item)

    async def consume(self) -> None:
        while not self.stopping:
            item = await self.queue.get()
            try:
                if self.runner is None:
                    raise RuntimeError("DOCUMENT_RUNNER_UNAVAILABLE")
                async with asyncio.timeout(self.timeout_seconds):
                    await self.runner.execute(item.manifest, item.cancelled)
            except (asyncio.CancelledError, TimeoutError):
                item.cancelled.set()
                raise
            finally:
                self.queue.task_done()

    async def stop(self) -> None:
        self.stopping = True
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        while not self.queue.empty():
            item = self.queue.get_nowait()
            item.cancelled.set()
            self.queue.task_done()
