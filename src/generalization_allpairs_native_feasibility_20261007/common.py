"""Standard-library-only identities and immutable namespace writes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from . import spec as s

ROOT = Path(__file__).resolve().parents[2]
SRC, ART, OUT, REP = [ROOT / p / s.NS for p in ('src', 'artifacts', 'results', 'reports')]
MANIFEST = OUT / 'preparation_manifest_v2.json'
TESTS = OUT / 'synthetic_tests_receipt_v2.json'
SCIENTIFIC = ROOT / 'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
PREREQUISITES = [SCIENTIFIC,
    ROOT / 'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
    ROOT / 'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',
    ROOT / 'results/generalization_splicebert_runtime_compatibility_20261007/preparation_manifest.json',
    ROOT / 'src/generalization_splicebert_20261007/backend_probe.py',
    ROOT / 'artifacts/generalization_splicebert_runtime_compatibility_20261007/numpy_official_member_parity.json',
    ROOT / 'src/generalization_allpairs_feasibility_20261007/math_mock.py',
    ROOT / 'src/generalization_allpairs_feasibility_20261007/tests.py',
    ROOT / 'reports/generalization_allpairs_feasibility_20261007/feasibility.md',
    ROOT / 'results/generalization_allpairs_feasibility_20261007/synthetic_receipt_v2.json',
    ROOT / 'results/generalization_allpairs_feasibility_20261007/receipt_writer_incident_01.json',
    ROOT / 'src/cross_assay_20260927/models.py',
    ROOT / 'src/generalization_20261007/route_scaling.py']

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 ** 2), b''): h.update(b)
    return h.hexdigest()

def readj(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    path = Path(path).resolve()
    assert any(path.is_relative_to(p.resolve()) for p in (SRC, ART, OUT, REP))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f: f.write(data)

def jsave(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())

def committed(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), str(path)

def clean_imports():
    blocked = {'numpy', 'pandas', 'scipy', 'sklearn', 'torch', 'transformers', 'openvino', 'RNA'}
    assert not any(n.split('.')[0] in blocked for n in sys.modules), 'Fresh numerical-import-free process required'

def freshness():
    for name in ('native_receipt.json', 'native_attempt_incident.json', 'current_runtime_import_receipt.json'):
        assert not (OUT / name).exists(), 'Preserve prior native attempt: ' + name
    assert not list(OUT.glob('case_n*_p*.json')), 'Preserve orphan case receipts; no automatic retry'

def manifest_checks(manifest, hasher=sha):
    assert manifest['status'] == 'FROZEN_INVENTED_ALLPAIRS_NATIVE_PREPARATION'
    assert manifest['project_data_or_fitting_authorized'] is False
    assert manifest['native_executed'] is False
    for name, expected in manifest['files'].items():
        p = (ROOT / name).resolve()
        assert p.is_relative_to(ROOT) and hasher(p) == expected, name
