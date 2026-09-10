"""Fail-closed paths, immutable records and content-addressed cache identities.

No holdout loader exists in this package during development. A future loader
requires a separately reviewed, committed pre-holdout authorization protocol.
These guards protect this pipeline, not arbitrary external Python code.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOTS = tuple(ROOT / p for p in (
    'reports/mechanism_v2', 'results/mechanism_v2', 'models/mechanism_v2',
    'configs/mechanism_v2', 'data/interim/mechanism_v2', 'data/external/mechanism_v2',
))
DEVELOPMENT_INPUTS = {
    'results/v4_phaseB/model_candidate_rows.csv.gz':
        '4e2339e1845147a14076bd8db9105a60ac91c59607c718212b59199f3ec0fd4c',
    'results/v4_phaseB/model_interventions.csv.gz':
        'a7e651e4a2a1ccf6d16ea43c6da8de384901df9a15cdf82208c2235315989835',
}
SOURCES = {'mikl_gse173098', 'tdp43_gse288185', 'moffatt_gse334718'}


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
        raise PermissionError(f'Writes outside Mechanism-v2 are prohibited: {relative}')
    return path


def write_once(relative, payload: bytes) -> Path:
    """Identical replay allowed; a different record may never overwrite evidence."""
    path = output_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f'Immutable record differs: {path}')
        return path
    # O_EXCL prevents duplicate workers silently replacing an existing record.
    with path.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def write_json(relative, value) -> Path:
    return write_once(relative, canonical_json(value))


def git(*args) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def load_development(relative='results/v4_phaseB/model_candidate_rows.csv.gz'):
    """Resolve and authorize BEFORE pandas can open any data file."""
    path = (ROOT / relative).resolve()
    allowed = { (ROOT / p).resolve(): digest for p, digest in DEVELOPMENT_INPUTS.items() }
    if path not in allowed:
        raise PermissionError('Only hash-pinned certified development tables may be loaded')
    if sha256(path) != allowed[path]:
        raise ValueError(f'Development table hash mismatch: {path}')
    import pandas as pd
    rows = pd.read_csv(path)
    if not set(rows.dataset.unique()) <= SOURCES:
        raise PermissionError('Unexpected source in certified development table')
    return rows


def cache_key(sequence: str, model_sha256: str, config: dict) -> str:
    if len(model_sha256) != 64 or any(c not in '0123456789abcdef' for c in model_sha256):
        raise ValueError('Model must be identified by a SHA-256 digest')
    sequence = sequence.upper().replace('U', 'T')
    if not sequence or set(sequence) - set('ACGT'):
        raise ValueError('Only nonempty ACGT/U sequences are supported')
    return hashlib.sha256(canonical_json({
        'sequence_sha256': hashlib.sha256(sequence.encode('ascii')).hexdigest(),
        'model_sha256': model_sha256, 'configuration': config,
    })).hexdigest()


def open_holdout(*args, **kwargs):
    raise PermissionError('HOLDOUT SEALED: no committed, verified pre-holdout authorization exists')
