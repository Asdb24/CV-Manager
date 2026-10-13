"""Phase 10 launcher interface, protected handles and expiring local input ownership."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import stat
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI
from pydantic import AwareDatetime

from cv_foundation.contracts import ApprovedInputManifest
from cv_foundation.settings import ClosedModel, Settings
from cv_foundation.windows_privacy import protect_directory


@dataclass(frozen=True)
class StartupContext:
    settings: Settings
    startup_authority: str
    input_store: OwnedInputStore
    model_asset_root: Path

    @property
    def owned_input_root(self) -> Path:
        return self.input_store.root


class WindowsModelModule(Protocol):
    def create_app(self, context: StartupContext) -> FastAPI: ...


class StoredInputMetadata(ClosedModel):
    manifest: ApprovedInputManifest
    owned_expires_at: AwareDatetime


def startup_context(
    settings: Settings, store: OwnedInputStore, model_asset_root: Path
) -> StartupContext:
    return StartupContext(
        settings=settings,
        startup_authority=secrets.token_urlsafe(32),
        input_store=store,
        model_asset_root=model_asset_root,
    )


def validate_manifest(manifest: Path, asset_root: Path) -> None:
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    for asset in raw["assets"]:
        path = (asset_root / asset["path"]).resolve()
        if not path.is_relative_to(asset_root.resolve()) or not path.is_file():
            raise ValueError("MODEL_ASSET_MISSING")
        if path.stat().st_size != asset["bytes"]:
            raise ValueError("MODEL_ASSET_CORRUPT")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != asset["sha256"]:
            raise ValueError("MODEL_ASSET_CORRUPT")


class OwnedInputStore:
    """Local dev harness inputs only; no arbitrary caller filesystem paths accepted."""

    def __init__(
        self, root: Path, capacity_bytes: int, expiry_seconds: int, realm_key: str
    ) -> None:
        if root.is_symlink() or root.is_junction():
            raise ValueError("OWNED_INPUT_ROOT_REPARSE_FORBIDDEN")
        if capacity_bytes <= 0 or expiry_seconds <= 0:
            raise ValueError("TEMP_CAPACITY_INVALID")
        self.root = root.resolve()
        self.capacity_bytes = capacity_bytes
        self.expiry_seconds = expiry_seconds
        self.realm_key = realm_key
        self.lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            protect_directory(self.root)
        else:
            self.root.chmod(stat.S_IRWXU)

    def accept(self, manifest: ApprovedInputManifest, data: bytes) -> str:
        if manifest.realm_key != self.realm_key:
            raise ValueError("INPUT_REALM_MISMATCH")
        if manifest.expires_at <= datetime.now(UTC):
            raise ValueError("INPUT_AUTHORITY_EXPIRED")
        metadata = (
            StoredInputMetadata(
                manifest=manifest,
                owned_expires_at=min(
                    manifest.expires_at, datetime.now(UTC) + timedelta(seconds=self.expiry_seconds)
                ),
            )
            .model_dump_json()
            .encode("utf-8")
        )
        with self.lock:
            size = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
            if len(data) + len(metadata) + size > self.capacity_bytes:
                raise ValueError("TEMP_CAPACITY_EXCEEDED")
            handle = secrets.token_hex(32)
            directory = self.root / handle
            directory.mkdir()
            try:
                (directory / "input.bin").write_bytes(data)
                (directory / "manifest.json").write_bytes(metadata)
            except OSError:
                self.remove(handle)
                raise
            return handle

    def resolve(
        self, handle: str, current_authority: Callable[[ApprovedInputManifest], bool]
    ) -> Path:
        if len(handle) != 64 or any(c not in "0123456789abcdef" for c in handle):
            raise ValueError("INPUT_HANDLE_INVALID")
        directory = self.root / handle
        if directory.is_symlink() or directory.is_junction():
            raise ValueError("INPUT_HANDLE_REPARSE_FORBIDDEN")
        for file_name in ["manifest.json", "input.bin"]:
            file_path = directory / file_name
            if file_path.is_symlink() or file_path.is_junction():
                raise ValueError("INPUT_FILE_REPARSE_FORBIDDEN")
        metadata = StoredInputMetadata.model_validate_json(
            (directory / "manifest.json").read_text(encoding="utf-8")
        )
        if metadata.manifest.realm_key != self.realm_key:
            self.remove(handle)
            raise ValueError("INPUT_REALM_MISMATCH")
        if (
            metadata.owned_expires_at <= datetime.now(UTC)
            or metadata.manifest.expires_at <= datetime.now(UTC)
            or not current_authority(metadata.manifest)
        ):
            self.remove(handle)
            raise ValueError("INPUT_AUTHORITY_REVOKED_OR_EXPIRED")
        return directory / "input.bin"

    def remove(self, handle: str) -> None:
        if len(handle) != 64 or any(c not in "0123456789abcdef" for c in handle):
            raise ValueError("INPUT_HANDLE_INVALID")
        directory = self.root / handle
        if directory.is_symlink() or directory.is_junction():
            raise ValueError("INPUT_HANDLE_REPARSE_FORBIDDEN")
        if directory.exists():
            shutil.rmtree(directory)

    def recover(self) -> None:
        # No authority survives restart. The owning dev harness discards all prior inputs.
        for path in self.root.iterdir():
            if path.is_dir() and len(path.name) == 64:
                self.remove(path.name)
