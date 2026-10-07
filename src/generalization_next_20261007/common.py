"""Additive namespace, row identity and immutable input checks."""
from src.generalization_20261007.common import (
    ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret,
)
from pathlib import Path
import gzip, hashlib, io, json, subprocess

NS = 'generalization_next_20261007'
SRC, OUT, REP, ART = [ROOT / name / NS for name in ('src', 'results', 'reports', 'artifacts')]
STUDIES = ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle']
TRACKS = ['base', 'raw', 'structure', 'lookup', 'bert', 'combined']
SEED = 20261007

def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(root) for root in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve existing artifact: '+str(path)
    else:
        path.write_bytes(payload)

def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False)+'\n').encode())

def csvsave(path, frame, compressed=False):
    data = frame.to_csv(index=False, lineterminator='\n').encode()
    save(path, gzip.compress(data, mtime=0) if compressed else data)

def matrixsave(path, matrix):
    assert np.isfinite(matrix).all()
    buffer = io.BytesIO()
    np.savez_compressed(buffer, features=np.asarray(matrix))
    save(path, buffer.getvalue())

def load():
    from src.generalization_20261007.common import load as previous_load
    frame, base = previous_load()
    assert len(frame) == 26258 and base.shape == (26258, 246)
    return frame, base

def encoded_frame(frame):
    from .route_structure import encoded_pair
    result = frame.copy()
    pairs = [encoded_pair(p, m, d) for p, m, d in zip(
        frame.parent_sequence, frame.mutant_sequence, frame.dataset)]
    result['parent_sequence'] = [pair[0] for pair in pairs]
    result['mutant_sequence'] = [pair[1] for pair in pairs]
    return result

def corrected_base(frame, historical):
    """Only certified SRLE contexts change; other feature bytes are retained."""
    from src.cross_assay_20260927.features import build
    srle = frame.dataset.eq('srle').to_numpy()
    corrected = np.asarray(historical, dtype=float).copy()
    local = encoded_frame(frame.loc[srle].reset_index(drop=True))
    features, names = build(local)
    corrected[srle] = features['interaction_3']
    np.testing.assert_array_equal(corrected[~srle], np.asarray(historical)[~srle])
    assert len(local) == 1744 and set(local.parent_sequence.str.len()) == {46}
    return corrected, names['interaction_3']

def check_manifest(filename, committed=True):
    from src.generalization_20261007.verify import preservation
    preservation()
    path = OUT / filename
    manifest = readj(path)
    for name, checksum in manifest['files'].items():
        assert sha256(ROOT / name) == checksum, name
    if committed:
        content = subprocess.check_output(['git', 'show', 'HEAD:'+path.relative_to(ROOT).as_posix()], cwd=ROOT)
        assert content == path.read_bytes(), 'Manifest must be committed before execution'
    return manifest

def freeze_check():
    return check_manifest('prefit_manifest.json')

def production_check():
    return check_manifest('feature_production_manifest.json')
