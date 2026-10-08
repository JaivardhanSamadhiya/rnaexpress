"""Descriptive identical-allele/shape/state contrast; does not alter any gate."""
from .common import *
from .evaluate import features, source_model
from .predict import canonical_scores
from src.generalization_nonlinear_crosscell_20261007.routes import module
from src.generalization_knowncell_20261007.canonical_paired_contrast import shared_matrix, common_choices
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
import os

def run():
    freeze_check()
    assert all(os.environ.get(name) == '1' for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    verification = readj(OUT / 'verification_receipt.json')
    assert verification['status'] == 'PASS' and verification['predictors_checked'] == verification['crossed_state_predictors_rechecked'] == 84
    assert verification['same_checkpoint_both_states_verified'] and verification['evaluation_manifest_sha256'] == sha256(OUT / 'evaluation_manifest.json')
    checked_files(verification['result_files'])
    frame, pairs = load(True), pd.read_csv(OUT / 'exact_menu_pairs.csv')
    assert len(pairs) == 2408 and pairs.biological_component.nunique() == 187
    results, calls, maximum = [], 0, 0.
    for track in TRACKS:
        matrix = features(track); pieces, roster = [], []
        for fold in FOLDS:
            rows, shared = shared_matrix(frame, matrix, pairs, fold)
            for task in TASKS:
                model, config, _, _, path = source_model(track, task, fold, frame, matrix)
                score, bound = canonical_scores(track, model, shared, module(track).predict_model)
                maximum = max(maximum, bound); calls += 1
                pieces.append(common_choices(rows, score, task))
                roster.append({'task': task, 'fold': fold, 'configuration': config,
                    'source_checkpoint': path.relative_to(ROOT).as_posix(), 'source_checkpoint_sha256': sha256(path),
                    'shared_matrix_sha256': matrix_hash(shared),
                    'paired_row_metadata_sha256': hashlib.sha256(rows.to_csv(index=False, lineterminator='\n').encode()).hexdigest(),
                    'paired_feature_bytes_equal': True, 'native_predictor_calls': 1, 'rows': len(rows)})
        d = pd.concat(pieces, ignore_index=True)
        assert len(d) == 2408 * 4 and not d.duplicated(['task', 'pair_context', 'direction']).any()
        gains = {task: d[d.task.eq(task)].groupby('biological_component').known_advantage.mean() for task in TASKS}
        assert all(len(value) == 187 for value in gains.values())
        bootstrap = shared_bootstrap(gains, 5000, SEED)
        results.append({'track': track, 'mean_known_advantage': float(np.mean([value.mean() for value in gains.values()])),
            'per_known_cell': {task: float(value.mean()) for task, value in gains.items()},
            'descriptive_ci': [float(np.quantile(bootstrap, .025)), float(np.quantile(bootstrap, .975))], 'components': 187, 'menus': 2408})
        csvsave(OUT / track / 'canonical_paired_state_contrast.csv', d)
        jsave(OUT / track / 'canonical_paired_state_roster.json', roster)
        del matrix
    assert calls == 84
    jsave(OUT / 'canonical_paired_state_contrast.json', {'status': 'DESCRIPTIVE', 'tracks': results, 'native_predictor_calls': calls,
        'maximum_independent_score_error': maximum, 'paired_feature_bytes_equal': True, 'new_fits': 0,
        'main_gate_and_intervention_ID_ties_unchanged': True, 'diagnostic_ties': 'Exact score tie uses shared lexical mutant sequence',
        'matrix_shape': 'One common full-menu ordered matrix per frozen source checkpoint/fold for both truths',
        'selects_nothing': True, 'causal_cell_state_claim': False, 'independent_confirmation': False,
        'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json')})

if __name__ == '__main__':
    run()
