"""Installed metadata ledger, not legal or release redistribution qualification."""

import importlib.metadata
import json
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
npm = []
for location, locked in lock["packages"].items():
    if not location or locked.get("link") or not location.startswith("node_modules/"):
        continue
    package_path = root / location / "package.json"
    if not package_path.is_file():
        npm.append(
            {
                "name": location.removeprefix("node_modules/"),
                "version": locked.get("version"),
                "license": locked.get(
                    "license", "NO SPDX FIELD; optional foreign-platform dependency"
                ),
                "source": locked.get("resolved"),
                "integrity": locked.get("integrity"),
                "installation": "not installed on this Windows platform",
            }
        )
        continue
    package = json.loads(package_path.read_text(encoding="utf-8"))
    npm.append(
        {
            "name": package["name"],
            "version": package["version"],
            "license": package.get("license", "NO SPDX FIELD; inspect bundled notice"),
            "source": locked.get("resolved"),
            "integrity": locked.get("integrity"),
        }
    )
python = []
for distribution in importlib.metadata.distributions():
    meta = distribution.metadata
    if meta.get("Name") == "agency-cv-foundation":
        continue
    expression = meta.get("License-Expression") or meta.get("License")
    classifiers = [item for item in meta.get_all("Classifier", []) if item.startswith("License ::")]
    python.append(
        {
            "name": meta["Name"],
            "version": distribution.version,
            "license_expression": expression,
            "license_classifiers": classifiers,
            "source": f"https://pypi.org/project/{meta['Name']}/{distribution.version}/",
            "bundled_license_files": [
                str(item)
                for item in distribution.files or []
                if "license" in str(item).lower() or "copying" in str(item).lower()
            ],
        }
    )
cargo = shutil.which("cargo")
if not cargo:
    raise ValueError("LOCKED_RUST_TOOLCHAIN_REQUIRED")
# Official resolved Cargo, fixed read-only metadata command, no shell composition.
completed = subprocess.run(  # noqa: S603
    [
        cargo,
        "metadata",
        "--locked",
        "--format-version",
        "1",
        "--manifest-path",
        str(root / "apps/desktop/src-tauri/Cargo.toml"),
    ],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
metadata = json.loads(completed.stdout)
rust = [
    {
        "name": item["name"],
        "version": item["version"],
        "license": item["license"],
        "license_file": item["license_file"],
        "source": item["source"],
    }
    for item in metadata["packages"]
    if item["source"]
]
result = {
    "scope": "Resolved dependency metadata and locks; release redistribution review owner 16",
    "npm": sorted(npm, key=lambda x: x["name"]),
    "python": sorted(python, key=lambda x: x["name"]),
    "rust": sorted(rust, key=lambda x: x["name"]),
}
(root / "docs/architecture/DEPENDENCY_LICENSES.json").write_text(
    json.dumps(result, indent=2) + "\n", encoding="utf-8"
)
print(f"DEPENDENCY_LICENSE_METADATA_RECORDED npm={len(npm)} python={len(python)} rust={len(rust)}")
