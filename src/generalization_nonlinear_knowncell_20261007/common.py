"""Immutable evaluation writes and exact inherited metadata/parser identities."""
from src.generalization_nonlinear_crosscell_20261007.common import ROOT, np, pd, sha256, clean, readj, decisions, TRACKS, WIDTHS, FEATURE_TRACKS, FEATURE_WIDTHS, META, CORE, FOLDS
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

NS = 'generalization_nonlinear_knowncell_20261007'
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ('src', 'results', 'reports', 'artifacts')]
SOURCE_OUT = ROOT / 'results/generalization_nonlinear_crosscell_20261007'
SOURCE_SRC = ROOT / 'src/generalization_nonlinear_crosscell_20261007'
FEATURE_ART = ROOT / 'artifacts/generalization_crosscell_20261007'
KNOWN_OUT = ROOT / 'results/generalization_knowncell_20261007'
KNOWN_SRC = ROOT / 'src/generalization_knowncell_20261007'
TASKS = {'CAD_known': ('CAD', 'CAD_to_N2A'), 'N2A_known': ('Neuro-2a', 'N2A_to_CAD')}
INFORMED = ['hgb/structure', 'hgb/bert', 'hgb/combined']
SEED = 20261007

def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(root.resolve()) for root in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve completed artifact ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(payload)

def jsave(path, value):
    save(path, (json.dumps(clean(value), indent=2, sort_keys=True, allow_nan=False) + '\n').encode())

def csvsave(path, frame, compressed=False):
    payload = frame.to_csv(index=False, lineterminator='\n').encode()
    save(path, gzip.compress(payload, mtime=0) if compressed else payload)

def rowhash(frame):
    return hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()

def metadata_hash(frame):
    return hashlib.sha256(frame[META].to_csv(index=False, lineterminator='\n').encode()).hexdigest()

def label_hash(values):
    return hashlib.sha256(np.asarray(values, dtype='<f8').tobytes()).hexdigest()

def matrix_hash(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype='<f8').tobytes()).hexdigest()

def committed(path):
    path = Path(path)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), 'Commit exact evaluation freeze before execution'

def load(outcomes=False):
    # Original known-cell loader reads explicit metadata, and only the Mikl
    # original-row labels when explicitly requested after evaluation freeze.
    from src.generalization_knowncell_20261007.common import load as admitted
    frame = admitted(outcomes)
    assert set(frame.held_parent_fold) == set(FOLDS)
    if (OUT / 'row_index.csv.gz').exists():
        saved = pd.read_csv(OUT / 'row_index.csv.gz', usecols=META, low_memory=False)[META]
        pd.testing.assert_frame_equal(frame[META], saved)
    return frame

def checked_files(files):
    for name, expected in files.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha256(path) == expected, name

def validate_source_reference(reference, actual):
    # The original Windows prefit serializes str(relativePath), using backslashes.
    # Normalize separators only; reject alias collisions rather than silently
    # reading or rewriting its frozen JSON with a different convention.
    assert reference['status'] == 'FROZEN_PREFIT'
    pinned = {name.replace('\\', '/'): expected for name, expected in reference['files'].items()}
    assert len(pinned) == len(reference['files'])
    for name, expected in actual.items():
        assert pinned[name] == expected, 'Source input not bound by original nonlinear prefit: ' + name

def source_inputs():
    from src.generalization_nonlinear_crosscell_20261007.common import freeze_check as original
    manifest = original()
    prepared = readj(OUT / 'metadata_receipt.json')
    assert prepared['status'] == 'PASS' and prepared['source_prefit_sha256'] == sha256(SOURCE_OUT / 'prefit_manifest.json')
    checked_files(prepared['source_input_files'])
    validate_source_reference(manifest, prepared['source_input_files'])
    assert prepared['core_sha256'] == sha256(CORE)
    return manifest

def freeze_check():
    source_inputs()
    path = OUT / 'evaluation_manifest.json'; committed(path); manifest = readj(path)
    assert manifest['status'] == 'FROZEN_NONLINEAR_KNOWN_CELL_EVALUATION'
    checked_files(manifest['files'])
    return manifest
