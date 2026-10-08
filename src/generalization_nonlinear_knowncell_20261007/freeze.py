"""Root reviews/commits a separate zero-fit evaluation freeze after prerequisites."""
from .common import *

def run():
    source_inputs()
    assert not (OUT / 'evaluation_manifest.json').exists() and not (OUT / 'evaluation_complete.json').exists()
    assert not any((OUT / track / 'fits').exists() for track in TRACKS), 'No new fitting directory is allowed'
    tests = readj(OUT / 'synthetic_tests_receipt_final.json')
    assert tests['status'] == 'PASS' and tests['models_fit'] == 0 and tests['project_models_opened'] is False
    assert set(tests['source_hashes']) == {path.name for path in SRC.glob('*.py')}
    for name, expected in tests['source_hashes'].items():
        assert sha256(SRC / name) == expected, name
    for name, expected in tests['report_hashes'].items():
        assert sha256(REP / name) == expected, name
    metadata = readj(OUT / 'metadata_receipt.json'); checked_files(metadata['files'])
    original = readj(SOURCE_OUT / 'verification_receipt.json')
    assert original['status'] == 'PASS' and original['inner_models_replayed'] == 504 and original['outer_models_replayed'] == 84
    assert original['source_only_selection_checked'] and original['gene_and_exact_allele_exclusions_checked']
    assert original['canonical_full_validation_scores_anchor_exact_ties'] and original['independent_predictor_bounds_checked']
    assert original['maximum_score_error'] < 1e-9; checked_files(original['result_files'])
    known = readj(KNOWN_OUT / 'verification_receipt.json')
    assert known['status'] == 'PASS' and known['predictors_checked'] == known['crossed_state_predictors_rechecked'] == 42
    assert known['same_checkpoint_both_states_verified'] and known['maximum_score_error'] <= 1e-9
    assert known['evaluation_manifest_sha256'] == sha256(KNOWN_OUT / 'evaluation_manifest.json'); checked_files(known['result_files'])
    paired = readj(KNOWN_OUT / 'canonical_paired_state_contrast.json')
    assert paired['status'] == 'DESCRIPTIVE' and paired['predictor_calls'] == 42 and paired['new_fits'] == 0
    assert paired['all_paired_feature_bytes_equal'] and paired['maximum_independent_score_error'] <= 1e-9
    assert paired['evaluation_manifest_sha256'] == sha256(KNOWN_OUT / 'evaluation_manifest.json')
    committed(SOURCE_OUT / 'prefit_manifest.json'); committed(KNOWN_OUT / 'evaluation_manifest.json')
    paths = [path for folder in (SRC, REP, OUT, ART) for path in folder.glob('*') if path.is_file()]
    paths += [CORE, SOURCE_OUT / 'prefit_manifest.json', SOURCE_OUT / 'runtime_binding.json', SOURCE_OUT / 'verification_receipt.json',
        KNOWN_OUT / 'evaluation_manifest.json', KNOWN_OUT / 'verification_receipt.json', KNOWN_OUT / 'canonical_paired_state_contrast.json',
        ROOT / 'results/generalization_20261007/prefit_manifest.json', ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json',
        ROOT / 'src/generalization_rbp_20261007/canonical_inner_replay.py', ROOT / 'src/generalization_rbp_20261007/inner_replay.py',
        ROOT / 'src/generalization_crosscell_20261007/common.py', ROOT / 'src/generalization_crosscell_20261007/routes.py',
        ROOT / 'src/generalization_crosscell_20261007/splits.py', ROOT / 'src/generalization_crosscell_20261007/verify.py',
        ROOT / 'src/generalization_crosscell_20261007/bootstrap.py', ROOT / 'src/generalization_20261007/common.py',
        ROOT / 'src/generalization_20261007/route_scaling.py', ROOT / 'src/cross_assay_20260927/models.py',
        ROOT / 'src/research_20260921/common.py']
    paths += [ROOT / name for name in metadata['source_input_files']]
    paths += list(KNOWN_SRC.glob('*.py'))
    for track in TRACKS:
        complete = readj(SOURCE_OUT / track / 'run_complete.json')
        assert complete['status'] == 'PASS' and complete['track'] == track and complete['fit_files'] == 42 and complete['prediction_rows'] == 13781
        assert complete['prefit_manifest_sha256'] == sha256(SOURCE_OUT / 'prefit_manifest.json')
        paths += [path for path in (SOURCE_OUT / track).rglob('*') if path.is_file()]
    paths += [ROOT / name for name in readj(KNOWN_OUT / 'evaluation_manifest.json')['files']]
    paths += [ROOT / name for name in known['result_files']]
    for feature in FEATURE_TRACKS:
        paths += [KNOWN_OUT / feature / 'canonical_paired_state_contrast.csv', KNOWN_OUT / feature / 'canonical_paired_state_roster.json']
    jsave(OUT / 'evaluation_manifest.json', {'status': 'FROZEN_NONLINEAR_KNOWN_CELL_EVALUATION',
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        'new_fits': 0, 'original_campaign_checkpoints': 588, 'outer_predictors_reused': 84, 'tracks': TRACKS,
        'metadata_sha256': metadata['metadata_sha256'], 'row_ids_sha256': metadata['row_ids_sha256'],
        'source_configurations_unchanged': True, 'source_models_have_immutable_creation_SHA': True,
        'numerical_threads': 1, 'source_nonlinear_complete_verify_required': True, 'known_canonical_paired_complete_required': True,
        'target_evaluation_started': False, 'independent_confirmation': False, 'root_commits_and_explicit_start_before_evaluation': True})
    print('Nonlinear known-cell evaluation freeze written; root commits and explicitly starts after review', flush=True)

if __name__ == '__main__':
    run()
