import asyncio
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from cv_foundation.ai_harness import OwnedInputStore, startup_context
from cv_foundation.contracts import ApprovedInputManifest
from cv_foundation.settings import Component, Profile, load_settings
from cv_worker.interfaces import BoundedWorker

ROOT = Path(__file__).resolve().parents[2]


def manifest() -> ApprovedInputManifest:
    return ApprovedInputManifest(
        manifest_id=uuid4(),
        realm_key="synthetic-test-workspace",
        person_id=uuid4(),
        privacy_epoch=uuid4(),
        purpose_version="synthetic-recruitment-v1",
        consent_version="synthetic-consent-v1",
        application_revision=uuid4(),
        profile_revision=uuid4(),
        jd_version=uuid4(),
        evidence=[],
        opaque_input_handle="synthetic-authorized-handle",
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
        manifest_digest="a" * 64,
    )


def test_actual_owned_file_cleanup_and_revocation() -> None:
    settings = load_settings(ROOT / "infra/config/test.json", Profile.TEST, Component.LOCAL_AI)
    directory = ROOT / ".local" / "synthetic-owned-input-test"
    store = OwnedInputStore(
        directory,
        settings.resources.temp_capacity_bytes,
        settings.resources.temp_expiry_seconds,
        settings.realm_key,
    )
    store.recover()
    handle = store.accept(manifest(), b"synthetic authorized snapshot")
    assert store.resolve(handle, lambda _: True).read_bytes() == b"synthetic authorized snapshot"
    with pytest.raises(ValueError, match="REVOKED_OR_EXPIRED"):
        store.resolve(handle, lambda _: False)
    assert not (directory / handle).exists()
    handle = store.accept(manifest(), b"synthetic restart snapshot")
    store.recover()
    assert not (directory / handle).exists()
    with pytest.raises(ValueError, match="HANDLE_INVALID"):
        store.resolve("../outside", lambda _: True)


def test_startup_authority_is_fresh_and_no_fake_worker() -> None:
    settings = load_settings(ROOT / "infra/config/test.json", Profile.TEST, Component.LOCAL_AI)
    store = OwnedInputStore(
        ROOT / ".local/ai-inputs",
        settings.resources.temp_capacity_bytes,
        settings.resources.temp_expiry_seconds,
        settings.realm_key,
    )
    first = startup_context(settings, store, ROOT / "artifacts/models")
    second = startup_context(settings, store, ROOT / "artifacts/models")
    assert first.startup_authority != second.startup_authority

    async def lifecycle() -> None:
        worker = BoundedWorker(
            settings.resources.worker_queue_size,
            settings.resources.worker_concurrency,
            settings.resources.worker_task_timeout_ms,
        )
        await worker.start()
        assert worker.runner is None
        assert worker.queue.maxsize == settings.resources.worker_queue_size
        await worker.stop()
        assert all(task.done() for task in worker.tasks)

    asyncio.run(lifecycle())


def test_actual_expiry_and_total_storage_bound(tmp_path: Path) -> None:
    store = OwnedInputStore(tmp_path / "inputs", 10000, 1, "synthetic-test-workspace")
    expired = manifest().model_copy(update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    with pytest.raises(ValueError, match="EXPIRED"):
        store.accept(expired, b"synthetic expired input")
    assert list(store.root.iterdir()) == []
    expiring = manifest().model_copy(
        update={"expires_at": datetime.now(UTC) + timedelta(milliseconds=250)}
    )
    handle = store.accept(expiring, b"synthetic expiring input")
    time.sleep(0.3)
    with pytest.raises(ValueError, match="REVOKED_OR_EXPIRED"):
        store.resolve(handle, lambda _: True)
    assert list(store.root.iterdir()) == []
    tiny = OwnedInputStore(tmp_path / "bounded", 1, 1, "synthetic-test-workspace")
    with pytest.raises(ValueError, match="TEMP_CAPACITY_EXCEEDED"):
        tiny.accept(manifest(), b"x")
    assert list(tiny.root.iterdir()) == []


def test_actual_configured_retention_cap(tmp_path: Path) -> None:
    store = OwnedInputStore(tmp_path / "inputs", 10000, 1, "synthetic-test-workspace")
    approved = manifest()
    handle = store.accept(approved, b"synthetic locally capped lifetime")
    time.sleep(1.1)
    assert approved.expires_at > datetime.now(UTC)
    with pytest.raises(ValueError, match="REVOKED_OR_EXPIRED"):
        store.resolve(handle, lambda _: True)
    assert list(store.root.iterdir()) == []


def test_foreign_realm_is_rejected_before_storage(tmp_path: Path) -> None:
    store = OwnedInputStore(tmp_path / "inputs", 10000, 1, "synthetic-test-workspace")
    foreign = manifest().model_copy(update={"realm_key": "synthetic-other-workspace"})
    with pytest.raises(ValueError, match="INPUT_REALM_MISMATCH"):
        store.accept(foreign, b"synthetic foreign input")
    assert list(store.root.iterdir()) == []
