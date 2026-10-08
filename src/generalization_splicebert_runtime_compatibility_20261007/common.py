"""Standard-library-only identities; importing performs no numerical/model work."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NS = "generalization_splicebert_runtime_compatibility_20261007"
SRC, OUT, REP, ART = [ROOT / name / NS for name in ("src", "results", "reports", "artifacts")]
PREFIX = ROOT / "data/interim/mechanism_v2/runtime"
ORIGINAL_SOURCE = ROOT / "src/generalization_splicebert_20261007/backend_probe.py"
ORIGINAL_MANIFEST = ROOT / "results/generalization_splicebert_20261007/backend_preparation_manifest.json"
ORIGINAL_RECEIPT = ROOT / "results/generalization_splicebert_20261007/backend_synthetic_receipt.json"
IR = ROOT / "artifacts/generalization_splicebert_20261007/backend/splicebert_1024_fp32.xml"
PLAN = REP / "plan.md"
RUNTIME_RECEIPT = ART / "scientific_runtime_receipt.json"
MANIFEST = OUT / "preparation_manifest.json"
NUMPY_VERSION = "1.26.4"
NUMPY_WHEEL = "numpy-1.26.4-cp312-cp312-win_amd64.whl"
PYPI = "https://pypi.org/pypi/numpy/1.26.4/json"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(home) for home in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, "Preserve existing artifact: " + str(path)
    else:
        with path.open("xb") as handle:
            handle.write(payload)


def jsave(path, data):
    save(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def committed(path):
    path = Path(path)
    blob = subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert blob == path.read_bytes(), "Commit exact preparation bytes before root start: " + str(path)


def no_completed_outputs():
    assert not IR.exists() and not IR.with_suffix(".bin").exists(), "Preserve candidate IR"
    assert not ORIGINAL_RECEIPT.exists(), "Preserve original completed backend probe"


def check_runtime(receipt):
    assert receipt["status"] == "PASS" and receipt["numpy_version"] == NUMPY_VERSION
    assert Path(receipt["runtime_path"]).resolve() == PREFIX.resolve()
    actual = {path.relative_to(PREFIX).as_posix() for path in PREFIX.rglob("*") if path.is_file()}
    assert actual == set(receipt["files"]), "Scientific prefix acquired unexpected/missing files"
    for name, expected in receipt["files"].items():
        path = (PREFIX / name).resolve()
        assert path.is_relative_to(PREFIX.resolve()) and not (PREFIX / name).is_symlink()
        assert sha256(path) == expected, "Scientific prefix changed: " + name
    assert sys.version_info[:2] == (3, 12) and sys.implementation.cache_tag == "cpython-312"
    for name, expected in receipt["python_native_files"].items():
        assert sha256(Path(name)) == expected
    assert Path(sys.executable).resolve() == Path(receipt["python_executable"]).resolve()


def check_preparation():
    committed(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "FROZEN_ADDITIVE_NUMPY_COMPATIBILITY_PREPARATION"
    for name, expected in manifest["files"].items():
        assert sha256(ROOT / name) == expected, "Repair preparation changed: " + name
    committed(ORIGINAL_MANIFEST)
    runtime = json.loads(RUNTIME_RECEIPT.read_text(encoding="utf-8"))
    check_runtime(runtime)
    no_completed_outputs()
    return manifest, runtime
