"""Standard-library-only path identity and original-byte guard."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_joint_freeze_compatibility_20261007'
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ('src', 'results', 'reports', 'artifacts')]
OLD_NS = 'generalization_joint_accessibility_20261007'
OLD_SRC, OLD_OUT, OLD_REP, OLD_ART = [ROOT / folder / OLD_NS for folder in ('src', 'results', 'reports', 'artifacts')]
OLD_FEAS = OLD_OUT / 'synthetic_feasibility_receipt.json'
OLD_TESTS = OLD_OUT / 'synthetic_tests_receipt_final.json'
OLD_MANIFEST = OLD_OUT / 'feature_production_manifest.json'
FAILURE_LOG = ROOT / 'logs/generalization_campaign_20261007/joint_production_freeze_01.log'
PLAN = REP / 'plan.md'
NORMALIZATION = ART / 'normalization_plan.json'
MANIFEST = OUT / 'preparation_manifest.json'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def readj(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve earlier additive compatibility bytes'
    else:
        with path.open('xb') as stream:
            stream.write(payload)


def jsave(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())


def committed(path):
    path = Path(path)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), 'Root must commit exact preparation bytes'


def normalize_path_keys(mapping):
    """Only separator replacement. Reject every alias/collision or unsafe path."""
    assert isinstance(mapping, dict) and mapping
    normalized, aliases = {}, set()
    for key, value in mapping.items():
        assert isinstance(key, str) and key and '\x00' not in key
        name = key.replace('\\', '/')
        parts = name.split('/')
        assert not PurePosixPath(name).is_absolute() and all(part not in ('', '.', '..') and ':' not in part for part in parts), 'Relative literal path required'
        assert name not in normalized and name.casefold() not in aliases, 'Reject path separator/case alias collision'
        aliases.add(name.casefold())
        normalized[name] = value
    return normalized


def normalized_receipt(receipt):
    assert isinstance(receipt, dict) and receipt['status'] == 'PASS'
    assert receipt['project_feature_production'] is False and receipt['project_outcomes_read'] is False and receipt['supervised_fit'] is False
    assert receipt['spec']['absolute_tolerance'] == 1e-6 and receipt['spec']['relative_tolerance'] == 1e-5
    result = dict(receipt)
    result['source_sha256'] = normalize_path_keys(receipt['source_sha256'])
    assert all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) for value in result['source_sha256'].values())
    return result


def no_original_outputs():
    assert not OLD_MANIFEST.exists(), 'Preserve original production manifest'
    assert not (OLD_OUT / 'joint_production_receipt.json').exists() and not (OLD_ART / 'joint_cache').exists()
    assert not any((OLD_OUT / track / 'fits').exists() for track in ('duplicate_marginal', 'joint'))


def original_byte_check():
    tests = readj(OLD_TESTS)
    assert tests['status'] == 'PASS' and tests['tests'] == 22 and tests['models_fit'] == 0
    assert tests['project_alleles_folded'] is False and tests['project_outcomes_read'] is False
    assert set(tests['source_hashes']) == {path.name for path in OLD_SRC.glob('*.py')}
    assert len(tests['source_hashes']) == 17
    paths = [OLD_TESTS, OLD_FEAS, FAILURE_LOG]
    for name, expected in tests['source_hashes'].items():
        path = OLD_SRC / name
        assert sha256(path) == expected, name
        paths.append(path)
    for name, expected in tests['report_hashes'].items():
        path = OLD_REP / name
        assert sha256(path) == expected, name
        paths.append(path)
    for name, expected in tests['receipts'].items():
        path = OLD_OUT / name
        assert sha256(path) == expected, name
        paths.append(path)
    runtime = OLD_OUT / 'runtime_binding_receipt.json'
    assert sha256(runtime) == tests['runtime_binding_sha256']
    paths.append(runtime)
    original = readj(OLD_FEAS)
    normalized = normalized_receipt(original)
    # Match exactly the two historical source assertions in original production().
    # Other initial feasibility-source hashes may describe earlier test revisions;
    # the final22-test receipt above binds all current17 modules and both reports.
    for name in ('src/generalization_joint_accessibility_20261007/feasibility.py',
                 'src/generalization_next_20261007/route_structure.py'):
        assert normalized['source_sha256'][name] == sha256(ROOT / name), name
        paths.append(ROOT / name)
    long_check = readj(OLD_OUT / 'synthetic_long_interval_validation.json')
    assert long_check['status'] == 'PASS' and long_check['source_sha256'] == sha256(OLD_SRC / 'validation.py')
    assert long_check['absolute_tolerance'] == 1e-6 and long_check['relative_tolerance'] == 1e-5 and len(long_check['interval_checks']) == 48
    assert long_check['short_validation_sha256'] == sha256(OLD_FEAS)
    for name, expected in readj(runtime)['files'].items():
        assert sha256(ROOT / name) == expected, name
        paths.append(ROOT / name)
    assert 'KeyError:' in FAILURE_LOG.read_text(encoding='utf8') and 'source_sha256' in FAILURE_LOG.read_text(encoding='utf8')
    return sorted(set(paths)), normalized


def check_preparation():
    committed(MANIFEST)
    manifest = readj(MANIFEST)
    assert manifest['status'] == 'FROZEN_ADDITIVE_JOINT_SEPARATOR_COMPATIBILITY'
    for name, expected in manifest['files'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha256(path) == expected, name
    original_byte_check()
    plan = readj(NORMALIZATION)
    normalized = normalized_receipt(readj(OLD_FEAS))
    assert sha256(OLD_FEAS) == plan['original_receipt_sha256']
    assert normalized['source_sha256'] == plan['normalized_source_sha256']
    assert list(readj(OLD_FEAS)['source_sha256']) == plan['original_keys_in_order']
    return manifest


def environment():
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1'
    assert os.environ.get('MKL_NUM_THREADS') == '1'
