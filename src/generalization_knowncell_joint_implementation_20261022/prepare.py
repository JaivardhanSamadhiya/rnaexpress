"""Source/summary-only readiness manifest, never metadata or FIT admission."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from .spec import (NS, DESIGN_NS, DESIGN_MANIFEST, ARMS, CONFIGS, COUNTS, GATE,
                   ALIASES, CANONICAL_MEAN, fixed_contract)
from .contracts import checkpoint_roster

ROOT = Path(__file__).resolve().parents[2]
SRC, REP, OUT = [ROOT / name / NS for name in ('src', 'reports', 'results')]


def sha_bytes(raw): return hashlib.sha256(raw).hexdigest()


def readj(path):
    path = Path(path); assert path.stat().st_size <= 2 * 2**20
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate JSON key'
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def normalize_map(files):
    result = {}
    for name, digest in files.items():
        key = name.replace('\\', '/')
        assert key not in result, 'Path-separator alias collision'
        assert not key.startswith('/') and '..' not in key.split('/') and ':' not in key
        assert isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
        result[key] = digest
    return result


def design_source_contract(design, read_source):
    """Read only exact design sources/report/summary; NEVER its declared data."""
    fixed_contract()
    assert design['status'] == 'FROZEN_STATIC_JOINT_KNOWNCELL_DESIGN_NOT_PROJECT_ADMISSION'
    assert design['arms'] == list(ARMS) and design['configs'] == list(CONFIGS)
    assert design['counts'] == COUNTS and design['gate'] == GATE
    assert design['project_dataset_reads'] == design['project_feature_reads'] == design['project_outcome_reads'] == design['models_fitted'] == 0
    assert design['scientific_runtimes_imported'] is False
    assert design['requires_separate_root_committed_metadata_and_FIT_admissions'] is True
    files = normalize_map(design['files'])
    selected = {name: digest for name, digest in files.items()
                if name.startswith('src/' + DESIGN_NS + '/')
                or name.startswith('reports/' + DESIGN_NS + '/')
                or name == 'results/' + DESIGN_NS + '/synthetic_tests_receipt.json'
                or name == 'results/' + DESIGN_NS + '/.gitattributes'}
    required = {'src/' + DESIGN_NS + '/' + name for name in
                ('__init__.py', 'spec.py', 'kernels.py', 'contracts.py', 'tests.py', 'freeze.py')}
    assert required <= set(selected)
    assert 'reports/' + DESIGN_NS + '/protocol.md' in selected
    for name, digest in selected.items(): assert sha_bytes(read_source(name)) == digest, name
    declared = design['declared_future_inputs_not_opened']
    assert set(declared) == {ALIASES['core'], ALIASES['feature']}
    for item in declared.values():
        assert item['actual_bytes_rehashed'] is False
        assert len(item['declared_sha256']) == 64
    return selected


def run():
    fixed_contract(); design_path = ROOT / DESIGN_MANIFEST
    design = readj(design_path)
    source_pins = design_source_contract(design, lambda rel: (ROOT / rel).read_bytes())
    receipt_path = OUT / 'synthetic_tests_receipt.json'; receipt = readj(receipt_path)
    assert receipt['status'] == 'PASS_INVENTED_STDLIB_IMPLEMENTATION_CHECKS'
    assert receipt['scientific_runtimes_imported'] is False
    assert receipt['project_dataset_reads'] == receipt['project_feature_reads'] == receipt['project_outcome_reads'] == receipt['models_fitted'] == 0
    sources = sorted(SRC.glob('*.py'))
    assert receipt['source_files'] == {p.relative_to(ROOT).as_posix(): sha_bytes(p.read_bytes()) for p in sources}
    for path in sources: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    own = sources + [SRC / '.gitattributes', REP / '.gitattributes', REP / 'protocol.md',
                     OUT / '.gitattributes', receipt_path]
    pins = {p.relative_to(ROOT).as_posix(): sha_bytes(p.read_bytes()) for p in own}
    payload = {'status': 'TESTED_REFERENCE_IMPLEMENTATION_NOT_METADATA_OR_FIT_ADMISSION',
               'generated_utc': datetime.now(timezone.utc).isoformat(),
               'files': {**source_pins, **pins, DESIGN_MANIFEST: sha_bytes(design_path.read_bytes())},
               'arms': ARMS, 'configs': CONFIGS, 'counts': COUNTS, 'gate': GATE,
               'canonical_mean': CANONICAL_MEAN, 'checkpoint_roster': checkpoint_roster(),
               'declared_future_inputs_not_opened': design['declared_future_inputs_not_opened'],
               'project_dataset_reads': 0, 'project_feature_reads': 0, 'project_outcome_reads': 0,
               'models_fitted': 0, 'scientific_runtimes_imported': False,
               'old_design_bytes_verified': True, 'commit_verification_required_by_root': True,
               'full_trainer_implemented': False, 'runtime_bridge_and_actual_origin_binding_required': True,
               'separate_metadata_array_label_and_FIT_admissions_required': True,
               'PUM_resource_exception_applies': False,
               'remaining': ['guarded selective project loader and actual metadata/array admission',
                             'source-only vectorized solver and full-shape canonical predictor',
                             'creation-SHA writer plus complete independent inner/outer replay',
                             'shared original NumPy-bootstrap gate and secondary reports']}
    target = OUT / 'implementation_readiness.json'
    with target.open('xb') as handle:
        handle.write((json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())
    print('REFERENCE_IMPLEMENTATION_READY', len(payload['files']), sha_bytes(target.read_bytes()), flush=True)


if __name__ == '__main__': run()
