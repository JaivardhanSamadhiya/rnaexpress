"""Fail-closed I/O for Mechanism-v5 namespaces only."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOTS = tuple(ROOT / p for p in (
    'reports/mechanism_v5', 'results/mechanism_v5', 'models/mechanism_v5',
    'configs/mechanism_v5', 'data/interim/mechanism_v5', 'data/external/mechanism_v5',
))

DEVELOPMENT_INPUTS = {
    'results/v4_phaseB/model_candidate_rows.csv.gz':
        '4e2339e1845147a14076bd8db9105a60ac91c59607c718212b59199f3ec0fd4c',
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
        raise PermissionError(f'Writes outside Mechanism-v5 are prohibited: {relative}')
    return path


def write_once(relative, payload: bytes) -> Path:
    """Identical replay allowed; a differing record may never overwrite evidence."""
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


def load_design() -> dict:
    return json.loads((ROOT / 'configs/mechanism_v5/design.json').read_text(encoding='utf-8'))


def design_sha256() -> str:
    return sha256(ROOT / 'configs/mechanism_v5/design.json')


def load_development(relative='results/v4_phaseB/model_candidate_rows.csv.gz'):
    """Resolve and authorize before any data file can be opened."""
    path = (ROOT / relative).resolve()
    allowed = {(ROOT / p).resolve(): digest for p, digest in DEVELOPMENT_INPUTS.items()}
    if path not in allowed:
        raise PermissionError('Only hash-pinned certified development tables may be loaded')
    if sha256(path) != allowed[path]:
        raise ValueError(f'Development table hash mismatch: {path}')
    import pandas as pd
    rows = pd.read_csv(path)
    if not set(rows.dataset.unique()) <= SOURCES:
        raise PermissionError('Unexpected source in certified development table')
    return rows


def open_holdout(*args, **kwargs):
    raise PermissionError(
        'ASTROCYTE SEALED: Mechanism-v5 development may not open the holdout. A one-time '
        'opening requires a separate committed pre-holdout freeze that expressly authorizes it.')
