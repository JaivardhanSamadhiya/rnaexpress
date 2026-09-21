"""Small, namespace-restricted research utilities."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'data/interim/mechanism_v2/runtime'
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))
ALLOWED = tuple(ROOT / p / 'research_20260921' for p in
                ('results', 'reports', 'data/external', 'data/interim'))

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_new(path, payload):
    path = Path(path).resolve()
    if not any(path.is_relative_to(root.resolve()) and path != root.resolve()
               for root in ALLOWED):
        raise PermissionError(f'Output outside new research namespace: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f'Preserving differing existing record: {path}')
        return path
    with path.open('xb') as stream:
        stream.write(payload)
    return path

def write_json(path, data):
    return write_new(path, (json.dumps(data, indent=2, sort_keys=True,
                                      allow_nan=False) + '\n').encode())

def load_certified():
    import pandas as pd
    path = ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz'
    expected = '4e2339e1845147a14076bd8db9105a60ac91c59607c718212b59199f3ec0fd4c'
    if sha256(path) != expected:
        raise ValueError('Certified table changed')
    rows = pd.read_csv(path)
    if not set(rows.dataset.unique()) <= {
        'mikl_gse173098', 'moffatt_gse334718', 'tdp43_gse288185'}:
        raise PermissionError('Non-admitted source')
    return rows
