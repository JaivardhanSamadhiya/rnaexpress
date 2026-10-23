"""Small source/receipt operations, without project payload readers."""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_metadata_execution_20261023'
OUT = ROOT / 'results' / NS
MANIFEST = OUT / 'execution_manifest.json'
READY = 'results/generalization_knowncell_joint_loader_20261022/readiness_manifest_reviewed.json'
READY_SHA = 'fe6c3c420110870c75217bba667d17bd805d02221ea80bf92314a3a9a509f5d5'
ADMISSION = 'results/generalization_knowncell_joint_loader_20261022/metadata_admission_manifest.json'
BUNDLE = 'results/generalization_knowncell_joint_loader_20261022/admitted_metadata.json'
STATUS = 'FROZEN_ORIGINAL_FLOOR_METADATA_ONLY_EXECUTION'
THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def save_new(path, value):
    raw = canonical(value)
    with Path(path).open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return sha(raw)


def resource_failure(state, elapsed, active=0):
    # This is the ORIGINAL scientific floor, including during the owned job.
    if state['physical_available'] < 3 * 2**30:
        return 'Original three-GiB available physical-memory floor'
    if state['disk_available'] < 2**30:
        return 'Original one-GiB workspace disk floor'
    if state['commit_headroom'] < 2**30:
        return 'One-GiB system commit reserve'
    if elapsed > 300:
        return 'Five-minute metadata-stage lifetime'
    if active > 2:
        return 'One metadata worker plus its pinned Git helper only'
    return None


def verify_sources(manifest):
    assert manifest['status'] == STATUS
    for name, expected in manifest['files'].items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    return manifest
