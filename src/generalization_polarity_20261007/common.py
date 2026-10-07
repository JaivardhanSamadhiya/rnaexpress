"""Immutable additive namespace and original-row preservation guards."""
from src.generalization_20261007.common import (
    ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret,
)
from pathlib import Path
import gzip, hashlib, io, json, subprocess

NS = 'generalization_polarity_20261007'
SRC, OUT, REP, ART = [ROOT / name / NS for name in ('src', 'results', 'reports', 'artifacts')]
STUDIES = ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle']
TRACKS = ['unflipped', 'polarity']
SEED = 20261007
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'
BASE = ROOT / 'artifacts/generalization_next_20261007/base_features.npz'


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
    """Read only the previously admitted core; keep original alleles for purge."""
    frame = pd.read_csv(CORE, low_memory=False)
    assert len(frame) == 26258 and set(frame.dataset) == set(STUDIES)
    assert frame.intervention_id.is_unique and frame.primary_eligible.all()
    assert np.isfinite(frame.measured_delta.to_numpy(float)).all()
    return frame, None


def freeze_check():
    from src.generalization_20261007.verify import preservation
    preservation()
    path = OUT / 'prefit_manifest.json'
    manifest = readj(path)
    for name, checksum in manifest['files'].items():
        assert sha256(ROOT / name) == checksum, name
    content = subprocess.check_output(['git', 'show', 'HEAD:'+path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert content == path.read_bytes(), 'Commit the prefit manifest before execution'
    return manifest
