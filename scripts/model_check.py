"""Pinned artifact integrity and real CPU kernel smoke, never product advice success."""

import ctypes
import hashlib
import json
import platform
from ctypes import wintypes
from pathlib import Path

import numpy as np
import onnxruntime as ort
from cv_foundation.ai_harness import validate_manifest
from cv_foundation.settings import Component, Profile, load_settings
from tokenizers import Tokenizer

root = Path(__file__).resolve().parent.parent
manifest_path = root / "contracts/model-manifest.json"
manifest_bytes = manifest_path.read_bytes()
digest = hashlib.sha256(manifest_bytes).hexdigest()
if digest != (root / "contracts/model-manifest.sha256").read_text(encoding="utf-8").strip():
    raise ValueError("MODEL_MANIFEST_DRIFT")
manifest = json.loads(manifest_bytes)
validate_manifest(manifest_path, root / "artifacts/models")
license_digest = hashlib.sha256(
    (root / "contracts/licenses/upstream-unilm-MIT.txt").read_bytes()
).hexdigest()
if license_digest != manifest["license"]["copied_license_sha256"]:
    raise ValueError("MODEL_LICENSE_DRIFT")
settings = load_settings(root / "infra/config/test.json", Profile.TEST, Component.LOCAL_AI)
options = ort.SessionOptions()
options.intra_op_num_threads = settings.resources.ai_threads
options.inter_op_num_threads = settings.resources.ai_concurrency
session = ort.InferenceSession(
    str(root / "artifacts/models" / manifest["assets"][0]["path"]),
    sess_options=options,
    providers=["CPUExecutionProvider"],
)
if ort.__version__ != manifest["execution"]["onnxruntime_version"]:
    raise ValueError("MODEL_RUNTIME_VERSION_DRIFT")
tokenizer = Tokenizer.from_file(str(root / "artifacts/models/tokenizer.json"))
model_config = json.loads((root / "artifacts/models/config.json").read_text(encoding="utf-8"))
special_tokens = json.loads(
    (root / "artifacts/models/special_tokens_map.json").read_text(encoding="utf-8")
)
tokenizer.enable_truncation(max_length=settings.resources.ai_max_tokens)
tokenizer.enable_padding(pad_id=model_config["pad_token_id"], pad_token=special_tokens["pad_token"])
synthetic = ["query: Vị trí thử nghiệm tổng hợp.", "passage: Văn bản thử nghiệm tổng hợp."][
    : settings.resources.ai_batch_size
]
encoded = tokenizer.encode_batch(synthetic)
inputs = {
    "input_ids": np.array([item.ids for item in encoded], dtype=np.int64),
    "attention_mask": np.array([item.attention_mask for item in encoded], dtype=np.int64),
    "token_type_ids": np.array([item.type_ids for item in encoded], dtype=np.int64),
}
output = session.run(["last_hidden_state"], inputs)[0]
if output.shape[-1] != manifest["adapter"]["embedding_dimensions"] or not np.isfinite(output).all():
    raise ValueError("CPU_ARTIFACT_COMPATIBILITY_FAILED")


class ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("page_fault_count", wintypes.DWORD),
        ("peak_working_set", ctypes.c_size_t),
        ("working_set", ctypes.c_size_t),
        ("peak_paged", ctypes.c_size_t),
        ("paged", ctypes.c_size_t),
        ("peak_nonpaged", ctypes.c_size_t),
        ("nonpaged", ctypes.c_size_t),
        ("pagefile", ctypes.c_size_t),
        ("peak_pagefile", ctypes.c_size_t),
    ]


kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
psapi = ctypes.WinDLL("psapi", use_last_error=True)
psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(ProcessMemoryCounters),
    wintypes.DWORD,
]
counters = ProcessMemoryCounters()
counters.cb = ctypes.sizeof(counters)
if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
    raise OSError("ACTUAL_WINDOWS_MEMORY_COUNTER_UNAVAILABLE")
if counters.peak_working_set > settings.resources.ai_peak_working_set_bytes:
    raise ValueError("CPU_COMPATIBILITY_PROCESS_BUDGET_EXCEEDED")
result = {
    "kind": "pinned artifact and Windows CPU kernel compatibility smoke; no product advice service",
    "platform": platform.platform(),
    "onnxruntime": ort.__version__,
    "providers": session.get_providers(),
    "inputs": [
        {"name": item.name, "type": item.type, "shape": item.shape} for item in session.get_inputs()
    ],
    "outputs": [
        {"name": item.name, "type": item.type, "shape": item.shape}
        for item in session.get_outputs()
    ],
    "model_manifest_sha256": digest,
    "assets_verified": len(manifest["assets"]),
    "license_sha256": license_digest,
    "cpu_smoke": {
        "synthetic_strings": len(synthetic),
        "raw_hidden_state_shape": list(output.shape),
        "finite": True,
        "provider": "CPUExecutionProvider",
        "peak_process_working_set_bytes": counters.peak_working_set,
        "configured_budget_bytes": settings.resources.ai_peak_working_set_bytes,
    },
    "product_inference": "UNVERIFIED owner 10",
    "working_set_and_100_cv": "UNVERIFIED owner 18",
}
(root / ".local").mkdir(exist_ok=True)
(root / ".local/model-contract-check.json").write_text(
    json.dumps(result, indent=2) + "\n", encoding="utf-8"
)
print("PINNED_MODEL_INTEGRITY_AND_WINDOWS_CPU_COMPATIBILITY: PASS; PRODUCT INFERENCE UNVERIFIED")
