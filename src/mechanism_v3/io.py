"""Fail-closed I/O for Mechanism-v3 namespaces only."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOTS = tuple(ROOT / p for p in (
    'reports/mechanism_v3', 'results/mechanism_v3', 'models/mechanism_v3',
    'configs/mechanism_v3', 'data/interim/mechanism_v3', 'data/external/mechanism_v3',
))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def output_path(relative: str | Path) -> Path:
    path = (ROOT / relative).resolve()
    if not any(path.is_relative_to(base.resolve()) and path != base.resolve()
               for base in OUTPUT_ROOTS):
        raise PermissionError(f'Writes outside Mechanism-v3 are prohibited: {relative}')
    return path


def write_once(relative, payload: bytes) -> Path:
    path = output_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f'Immutable record differs: {path}')
        return path
    with path.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def write_json(relative, value) -> Path:
    return write_once(relative, canonical_json(value))


def git(*args) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def open_holdout():
    raise PermissionError('Astrocyte holdout remains sealed under Mechanism-v3 until a separate '
                          'pre-holdout freeze expressly authorizes a one-time opening')
