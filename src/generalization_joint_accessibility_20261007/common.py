"""Additive joint-accessibility identities, guards and immutable writes."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import subprocess
from src.generalization_20261007.common import ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret

NS = 'generalization_joint_accessibility_20261007'
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ('src', 'results', 'reports', 'artifacts')]
RBP_ART, RBP_OUT = ROOT / 'artifacts/generalization_rbp_20261007', ROOT / 'results/generalization_rbp_20261007'
NEXT_ART, NEXT_OUT = ROOT / 'artifacts/generalization_next_20261007', ROOT / 'results/generalization_next_20261007'
IDENTITY = ['intervention_id', 'dataset', 'biological_component', 'parent_context_id', 'parent_sequence', 'mutant_sequence']
STUDIES = ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle']
CONTROLS = ['base', 'raw', 'access']
TRACKS = ['duplicate_marginal', 'joint']
SHAPES = {'base': 246, 'raw': 502, 'access': 758, 'duplicate_marginal': 1014, 'joint': 1014}
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'
SEED = 20261007

def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(root.resolve()) for root in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve existing artifact: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(payload)

def jsave(path, obj):
    save(path, (json.dumps(clean(obj), indent=2, sort_keys=True, allow_nan=False) + '\n').encode())

def csvsave(path, frame, compressed=False):
    payload = frame.to_csv(index=False, lineterminator='\n').encode()
    save(path, gzip.compress(payload, mtime=0) if compressed else payload)

def matrixsave(path, matrix):
    assert np.isfinite(matrix).all()
    data = io.BytesIO(); np.savez_compressed(data, features=np.asarray(matrix))
    save(path, data.getvalue())

def metadata_identity(frame):
    return hashlib.sha256(frame[IDENTITY].to_csv(index=False, lineterminator='\n').encode()).hexdigest()

def rowhash(frame):
    return hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()

def label_hash(values):
    return hashlib.sha256(np.asarray(values, dtype='<f8').tobytes()).hexdigest()

def matrix_hash(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype='<f8').tobytes()).hexdigest()

def committed(path):
    path = Path(path)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), 'Root must commit exact freeze before execution'

def manifest_check(filename, status):
    from src.generalization_20261007.verify import preservation
    preservation()
    path = OUT / filename; committed(path); manifest = readj(path)
    assert manifest['status'] == status
    for name, expected in manifest['files'].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve()) and sha256(target) == expected, name
    return manifest

def production_check():
    return manifest_check('feature_production_manifest.json', 'FROZEN_JOINT_ACCESSIBILITY_PRODUCTION')

def freeze_check():
    return manifest_check('prefit_manifest.json', 'FROZEN_JOINT_ACCESSIBILITY_PREFIT')

def sequence_frames():
    from src.generalization_splicebert_downstream_20261007.common import sequence_frames as original
    return original()

def certified_core():
    foundation = ROOT / 'results/generalization_20261007/prefit_manifest.json'
    admission = ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json'
    committed(foundation); committed(admission)
    assert sha256(admission) == readj(foundation)['files'][admission.relative_to(ROOT).as_posix()]
    assert sha256(CORE) == readj(admission)['files'][CORE.relative_to(ROOT).as_posix()]
    return CORE

def load():
    """Only admitted mean effects; no replicate/auxiliary historical readers."""
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
    assert receipt['joint_production_receipt_sha256'] == sha256(OUT / 'joint_production_receipt.json')
    assert receipt['source_control_prefit_sha256'] == sha256(RBP_OUT / 'prefit_manifest.json')
    for name, expected in receipt['files'].items():
        assert sha256(ROOT / name) == expected, name
    assert set(receipt['feature_paths']) == set(CONTROLS + TRACKS)
    return receipt
