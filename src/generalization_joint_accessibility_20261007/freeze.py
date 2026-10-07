"""Separate production and prefit freezes; never extract or fit by importing."""
import sys
from .common import *
from .runtime import check as runtime_check
from .assemble import source_controls

def tests_check():
    receipt = readj(OUT / 'synthetic_tests_receipt_final.json')
    assert receipt['status'] == 'PASS' and receipt['models_fit'] == 0 and receipt['project_alleles_folded'] is False
    assert set(receipt['source_hashes']) == {path.name for path in SRC.glob('*.py')}
    for name, expected in receipt['source_hashes'].items():
        assert sha256(SRC / name) == expected, name

def base_paths():
    paths = [path for folder in (SRC, REP) for path in folder.glob('*') if path.is_file()]
    paths += [OUT / 'synthetic_tests_receipt_final.json', OUT / 'synthetic_feasibility_receipt.json', OUT / 'synthetic_long_interval_validation.json',
        OUT / 'synthetic_pool_benchmark_receipt.json', OUT / 'runtime_binding_receipt.json',
        OUT / 'preparation_receipt.json', OUT / 'row_index.csv.gz', ART / 'sequence_request_manifest.json',
        NEXT_ART / 'sequence_inventory.csv.gz', NEXT_ART / 'encoded_sequence_inventory.csv.gz',
        NEXT_OUT / 'feature_production_manifest.json', NEXT_OUT / 'short_feature_receipt.json',
        RBP_OUT / 'prefit_manifest.json', RBP_OUT / 'feature_production_manifest.json', RBP_OUT / 'prepare_receipt.json',
        RBP_ART / 'model_row_index.csv.gz', RBP_OUT / 'projection_receipt.json',
        ROOT / 'src/generalization_splicebert_downstream_20261007/common.py',
        ROOT / 'src/generalization_rbp_20261007/production.py',
        ROOT / 'src/generalization_20261007/common.py', ROOT / 'src/cross_assay_20260927/common.py',
        ROOT / 'src/research_20260921/common.py']
    paths += [ROOT / name for name in runtime_check()['files']]
    paths += [RBP_ART / (track + '_model_features.npz') for track in CONTROLS]
    return paths

def production():
    assert not (OUT / 'feature_production_manifest.json').exists()
    assert not (OUT / 'joint_production_receipt.json').exists() and not (ART / 'joint_cache').exists()
    assert not any((OUT / track / 'fits').exists() for track in TRACKS)
    tests_check(); runtime_check(); source_controls()
    assert readj(OUT / 'preparation_receipt.json')['status'] == 'PASS'
    feasibility = readj(OUT / 'synthetic_feasibility_receipt.json'); assert feasibility['status'] == 'PASS'
    kernel_name = (SRC / 'feasibility.py').relative_to(ROOT).as_posix()
    assert feasibility['source_sha256'][kernel_name] == sha256(SRC / 'feasibility.py'), 'Preserve tested algorithm or require a new separately named validation generation'
    reference_name = 'src/generalization_next_20261007/route_structure.py'
    assert feasibility['source_sha256'][reference_name] == sha256(ROOT / reference_name)
    long_check = readj(OUT / 'synthetic_long_interval_validation.json'); assert long_check['status'] == 'PASS'
    assert long_check['source_sha256'] == sha256(SRC / 'validation.py')
    assert long_check['absolute_tolerance'] == 1e-6 and long_check['relative_tolerance'] == 1e-5
    assert len(long_check['interval_checks']) == 48 and readj(OUT / 'synthetic_pool_benchmark_receipt.json')['status'] == 'PASS'
    paths = base_paths()
    jsave(OUT / 'feature_production_manifest.json', {'status': 'FROZEN_JOINT_ACCESSIBILITY_PRODUCTION',
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        'alleles': 18220, 'rows': 26258, 'tracks': TRACKS, 'shapes': SHAPES, 'production_threads': 1,
        'immutable_creation_digests_required': True, 'synthetic_equivalence_atol': 1e-6, 'synthetic_equivalence_rtol': 1e-5,
        'project_features_exist': False, 'fits_exist': False, 'project_outcomes_read': False,
        'production_does_not_wait_for_control_fits': True, 'root_commit_and_start_signal_required': True})

def prefit():
    from .control_reuse import prepare_reference, check as controls_check
    production_check(); runtime_check(); source_controls(); receipt = input_check(); tests_check()
    assert not (OUT / 'prefit_manifest.json').exists() and not any((OUT / track / 'fits').exists() for track in TRACKS)
    if not (OUT / 'control_reuse_receipt.json').exists():
        prepare_reference()
    control = controls_check(); frame = load()
    assert metadata_identity(frame) == receipt['original_metadata_sha256']
    assert label_hash(frame.measured_delta) == control['original_labels_sha256']
    paths = base_paths() + [OUT / 'feature_production_manifest.json', OUT / 'joint_production_receipt.json',
        OUT / 'input_receipt.json', OUT / 'control_reuse_receipt.json', ART / 'joint_cache_index.json', CORE,
        ROOT / 'results/generalization_20261007/prefit_manifest.json', ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json',
        ROOT / 'src/generalization_20261007/route_scaling.py', ROOT / 'src/cross_assay_20260927/models.py',
        ROOT / 'src/generalization_next_20261007/bootstrap.py', ROOT / 'src/generalization_splicebert_downstream_20261007/gate.py',
        ROOT / 'artifacts/cross_assay_20260927/model_comparison.csv', ROOT / 'results/cross_assay_20260927/decision_metrics.csv']
    paths += [ROOT / name for name in receipt['files']] + [ROOT / name for name in control['files']]
    for entry in readj(ART / 'joint_cache_index.json')['alleles']:
        paths += [ROOT / entry['path'], ROOT / entry['creation_path']]
    jsave(OUT / 'prefit_manifest.json', {'status': 'FROZEN_JOINT_ACCESSIBILITY_PREFIT',
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        'tracks': TRACKS, 'shapes': SHAPES, 'fits_per_track': 40, 'primary_fit_checkpoints': 80,
        'control_fitting_policy': 'REUSE_THREE_RBP_FIT_TWO_NEW_TRACKS', 'reused_controls': CONTROLS,
        'reused_controls_are_new_evidence': False, 'original_labels_sha256': label_hash(frame.measured_delta),
        'original_metadata_identity_sha256': metadata_identity(frame), 'source_only_three_penalties': [.005, .05, .5],
        'numerical_threads': 1, 'no_fits_exist': True, 'checkpoint_creation_SHA_sidecars_required': True,
        'all_inner_and_outer_replay_required': True, 'independent_confirmation': False, 'observed_data_followup': True,
        'joint_incremental_controls': ['access', 'duplicate_marginal'], 'mean_incremental_gain_min': .01,
        'incremental_leave_best_assay_out_positive': True, 'root_commits_before_fitting': True})

if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('production', 'prefit')
    production() if sys.argv[1] == 'production' else prefit()
