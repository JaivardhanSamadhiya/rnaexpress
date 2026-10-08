"""Preserve the old failed builder; certify its missing comparison binding explicitly."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_joint_control_admission_20261008'
OUT = ROOT / 'results' / NS
RBP = ROOT / 'results/generalization_rbp_20261007'
JOINT = ROOT / 'results/generalization_joint_accessibility_20261007'
AUDIT = ROOT / 'results/generalization_campaign_20261007/rbp_numerical_audit_03.json'
CONTROLS = ('base', 'raw', 'access')


def digest(path):
    with Path(path).open('rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
        return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def check_files(files, root=ROOT):
    normalized = {}
    for name, expected in files.items():
        path = (root / name).resolve()
        assert path.is_relative_to(root.resolve()), 'Outside workspace'
        key = str(path).casefold()
        assert key not in normalized, 'Path alias'
        assert digest(path) == expected, 'Changed input: ' + name
        normalized[key] = expected


def summaries(replay, audit, hash_file):
    assert replay['status'] == 'PASS' and replay['models_fit'] == 0
    assert audit['status'] == 'PASS_INDEPENDENT_RBP_POINT_METRICS_AND_GATE_ARITHMETIC'
    assert audit['new_models_fitted'] == 0 and audit['canonical_checkpoint_replay_receipt_bound']
    assert audit['all_three_complete_decision_rosters_equal']
    assert not audit['criteria_or_old_files_changed'] and not audit['protected_outcomes_read']
    assert audit['maximum_absolute_numeric_error'] <= 1e-12
    assert audit['numeric_values_checked'] == 32922 and audit['boolean_checks_checked'] == 45
    pins = audit['observed_input_sha256_postfit_not_creation_binding']
    canonical = 'results/generalization_rbp_20261007/canonical_source_only_replay.json'
    assert pins[canonical] == hash_file(canonical)
    result = {}
    for track in CONTROLS:
        prefix = 'results/generalization_rbp_20261007/' + track + '/'
        for filename in ('decisions.csv', 'comparison.csv', 'run_complete.json'):
            name = prefix + filename
            assert pins[name] == hash_file(name), 'Missing or changed independent summary binding'
            result[name] = pins[name]
        # Canonical score replay certifies the actual decisions; the separate
        # aggregate audit certifies their comparison CSV. Neither is a birth SHA.
        name = prefix + 'decisions.csv'
        assert replay['files'][name] == result[name]
    return result


def committed(path):
    name = path.relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) == path.read_bytes(), 'Commit exact admission design'


def run(root_start=False):
    assert root_start, 'Root explicitly starts reviewed admission'
    design_path = OUT / 'design_manifest.json'
    committed(design_path)
    design = read(design_path)
    assert design['status'] == 'FROZEN_JOINT_CONTROL_ADMISSION'
    check_files(design['files'])
    for name in design['own_files']:
        committed(ROOT / name)
    assert all(os.environ.get(v) == '1' for v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    assert not (JOINT / 'control_reuse_receipt.json').exists()
    assert not (JOINT / 'prefit_manifest.json').exists()
    assert not any((JOINT / track / 'fits').exists() for track in ('duplicate_marginal', 'joint'))
    replay_path = RBP / 'canonical_source_only_replay.json'
    replay, audit = read(replay_path), read(AUDIT)
    files = summaries(replay, audit, lambda name: digest(ROOT / name))
    check_files(replay['files'])
    check_files(audit['observed_input_sha256_postfit_not_creation_binding'])
    # Import the original, pinned scientific bootstrap only after the stdlib guard.
    import src.research_20260921.common
    from src.generalization_joint_accessibility_20261007.common import np, pd, certified_core
    from src.generalization_joint_accessibility_20261007.assemble import source_controls
    source_controls()
    freeze_path = RBP / 'prefit_manifest.json'
    freeze = read(freeze_path)
    assert replay['namespace'] == 'generalization_rbp_20261007'
    assert replay['prefit_manifest_sha256'] == digest(freeze_path)
    assert replay['inner_checkpoints_checked'] == 108 and replay['outer_checkpoints_checked'] == 12
    assert not replay['replicate_evidence_opened'] and not replay['historical_data_npz_loaded']
    assert not replay['protected_outcomes_opened'] and replay['core_sha256'] == digest(certified_core())
    assert replay['numerical_threads'] == 1 and replay['maximum_independent_arithmetic_error'] <= 1e-9
    libraries = replay['loaded_numeric_libraries']
    for name, package in (('numpy', np), ('pandas', pd)):
        assert libraries[name + '_version'] == package.__version__
        assert libraries[name + '_init_sha256'] == digest(package.__file__)
    files.update(replay['files'])
    for track in CONTROLS:
        complete = read(RBP / track / 'run_complete.json')
        assert complete['status'] == 'PASS' and complete['fit_files'] == 40
        assert complete['prediction_rows'] == 26258 and complete['prefit_manifest_sha256'] == digest(freeze_path)
        checkpoints = list((RBP / track / 'fits').glob('*.json'))
        assert len(checkpoints) == 40
        required = checkpoints + [RBP / track / name for name in ('predictions.csv.gz', 'decisions.csv', 'inner_selection.csv', 'folds.json', 'run_complete.json')]
        for path in required:
            name = path.relative_to(ROOT).as_posix()
            assert replay['files'][name] == digest(path), name
        path = ROOT / 'artifacts/generalization_rbp_20261007' / (track + '_model_features.npz')
        name = path.relative_to(ROOT).as_posix()
        assert freeze['files'][name] == digest(path)
        files[name] = digest(path)
    for name in ('src/generalization_rbp_20261007/routes.py', 'src/generalization_20261007/route_scaling.py', 'src/cross_assay_20260927/models.py'):
        assert freeze['files'][name] == digest(ROOT / name)
        files[name] = digest(ROOT / name)
    for path in (replay_path, freeze_path, AUDIT, design_path):
        files[path.relative_to(ROOT).as_posix()] = digest(path)
    files.update(design['files'])
    receipt = {'status': 'PASS', 'policy': 'REUSE_ORIGINAL_THREE_RBP_CONTROLS_NO_REFIT',
        'control_prefit_sha256': digest(freeze_path), 'control_canonical_source_only_replay_sha256': digest(replay_path),
        'original_labels_sha256': replay['mean_effect_float64_sha256'], 'core_sha256': replay['core_sha256'],
        'standalone_new_tracks': ['duplicate_marginal', 'joint'], 'reused_control_tracks': list(CONTROLS),
        'reused_control_fits': 120, 'new_fits_required': 80, 'files': files, 'models_fit': 0,
        'comparison_binding_source': 'Independent point-metric audit 03, separate from canonical checkpoint replay',
        'comparison_binding_is_postfit_not_birth_certificate': True,
        'bootstrap_draws_independently_resimulated': False,
        'old_failed_builder_and_replay_unchanged': True,
        'scope': 'Reuse exposed development controls with complete replay and independently audited comparisons; no new evidence and no retroactive creation-time hashes'}
    payload = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with (JOINT / 'control_reuse_receipt.json').open('xb') as stream:
        stream.write(payload)
    print('PASS: 120 unchanged controls admitted using canonical replay plus independently bound aggregate summaries; zero fits', flush=True)


if __name__ == '__main__':
    run('--root-start' in sys.argv[1:])
