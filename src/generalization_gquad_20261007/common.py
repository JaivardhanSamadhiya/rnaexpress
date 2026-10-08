"""Numerical bootstrap for later assembly/fits; metadata preparation avoids it."""
import gzip
import hashlib
import io
import json
from src.generalization_20261007.common import np, pd, clean, decisions, summary, inner_regret
from .guards import ROOT, SRC, OUT, REP, ART, NEXT_ART, NEXT_OUT, FEAS_OUT, IDENTITY, STUDIES, CORE
from .guards import sha256, readj, save, committed, production_check, freeze_check, canonical_map
from .spec import TRACKS, SHAPES
SEED = 20261007

def jsave(path, value):
    save(path, (json.dumps(clean(value), indent=2, sort_keys=True, allow_nan=False) + '\n').encode())

def csvsave(path, frame, compressed=False):
    data = frame.to_csv(index=False, lineterminator='\n').encode()
    save(path, gzip.compress(data, mtime=0) if compressed else data)

def matrixsave(path, matrix):
    assert np.isfinite(matrix).all()
    buffer = io.BytesIO(); np.savez_compressed(buffer, features=np.asarray(matrix, dtype=np.float64))
    save(path, buffer.getvalue())

def metadata_identity(frame):
    return hashlib.sha256(frame[IDENTITY].to_csv(index=False, lineterminator='\n').encode()).hexdigest()

def rowhash(frame):
    return hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()

def label_hash(values):
    return hashlib.sha256(np.asarray(values, dtype='<f8').tobytes()).hexdigest()

def matrix_hash(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype='<f8').tobytes()).hexdigest()

def certified_core():
    foundation = ROOT / 'results/generalization_20261007/prefit_manifest.json'
    admission = ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json'
    committed(foundation); committed(admission)
    assert sha256(admission) == canonical_map(readj(foundation)['files'])[admission.relative_to(ROOT).as_posix()]
    assert sha256(CORE) == canonical_map(readj(admission)['files'])[CORE.relative_to(ROOT).as_posix()]
    return CORE

def load():
    fields = IDENTITY + ['endpoint_class', 'measured_delta', 'primary_eligible']
    frame = pd.read_csv(certified_core(), usecols=fields, low_memory=False)[fields]
    assert len(frame) == 26258 and frame.intervention_id.is_unique and frame.primary_eligible.all()
    assert set(frame.dataset) == set(STUDIES) and np.isfinite(frame.measured_delta.to_numpy(float)).all()
    rows = pd.read_csv(OUT / 'row_index.csv.gz', usecols=IDENTITY, low_memory=False)[IDENTITY]
    pd.testing.assert_frame_equal(frame[IDENTITY], rows)
    return frame

def input_check():
    receipt = readj(OUT / 'input_receipt.json')
    assert receipt['status'] == 'PASS' and receipt['rows'] == 26258 and receipt['shapes'] == SHAPES
    assert receipt['production_manifest_sha256'] == sha256(OUT / 'feature_production_manifest.json')
    assert receipt['features_receipt_sha256'] == sha256(OUT / 'features_receipt.json')
    assert receipt['source_control_prefit_manifest_sha256'] == sha256(NEXT_OUT / 'prefit_manifest.json')
    assert set(receipt['feature_paths']) == set(TRACKS)
    for name, expected in receipt['files'].items():
        assert sha256(ROOT / name) == expected, name
    assert receipt['row_index_sha256'] == sha256(OUT / 'row_index.csv.gz')
    return receipt
