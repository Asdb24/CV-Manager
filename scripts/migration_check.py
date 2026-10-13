"""Check the linear revision graph and every frozen migration byte."""

import hashlib
import json
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "contracts/migration-state.json").read_text(encoding="utf-8"))
directory = ScriptDirectory.from_config(Config(str(root / "apps/api/alembic.ini")))
revisions = list(directory.walk_revisions())
if manifest["state"] != "implemented" or manifest["owner_phase"] != "03":
    raise SystemExit("MIGRATION_MANIFEST_INVALID")
if [r.revision for r in reversed(revisions)] != manifest["expected_revisions"]:
    raise SystemExit("MIGRATION_REVISION_DRIFT")
if directory.get_heads() != [manifest["head"]]:
    raise SystemExit("MIGRATION_HEAD_DRIFT")
actual_files = {
    p.relative_to(root).as_posix()
    for p in (root / "apps/api/migrations/versions").iterdir()
    if p.suffix in {".py", ".sql"}
}
if actual_files != set(manifest["files_sha256"]):
    raise SystemExit("MIGRATION_FILE_INVENTORY_DRIFT")
for name, expected in manifest["files_sha256"].items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise SystemExit("APPLIED_MIGRATION_CHANGED: " + name)
print("MIGRATION_GRAPH_AND_FROZEN_BYTES_VERIFIED: real lifecycle is a separate required check")
