"""Recheck all previously measured pairwise known-cell controls; zero fits."""
from .common import *
from src.generalization_knowncell_20261007.evaluate import source_model as linear_source_model
from src.generalization_crosscell_20261007.routes import module as linear_module
from src.generalization_rbp_20261007.canonical_inner_replay import canonical_scores, decision_table, decisions_equal
from .predict import score_match

def run(frame):
    maximum, count = 0., 0
    for feature in FEATURE_TRACKS:
        path = FEATURE_ART / (feature + '_model_features.npz')
        with np.load(path, allow_pickle=False) as data:
            assert data.files == ['features']; matrix = data['features'].astype(np.float64)
        assert matrix.shape == (13781, FEATURE_WIDTHS[feature]) and np.isfinite(matrix).all()
        pred = pd.read_csv(KNOWN_OUT / feature / 'predictions.csv.gz', float_precision='round_trip')
        d = pd.read_csv(KNOWN_OUT / feature / 'decisions.csv', float_precision='round_trip')
        assert len(pred) == len(frame) and pred.intervention_id.is_unique and set(pred.intervention_id) == set(frame.intervention_id) and set(pred.track) == {feature}
        from .verify import exact_decision_roster
        exact_decision_roster(d, frame, feature)
        for task in TASKS:
            for fold in FOLDS:
                model, config, target_mask, model_path = linear_source_model(feature, task, fold, frame, matrix)
                target = frame.loc[target_mask].reset_index(drop=True)
                score, error = canonical_scores(model, matrix, np.flatnonzero(target_mask), linear_module(feature).predict_model)
                saved = pred[pred.task.eq(task) & pred.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
                assert set(saved.configuration) == {config['id']}
                maximum = max(maximum, error, score_match(score, saved.score.to_numpy(float)))
                decisions_equal(decision_table(target, score), d[d.task.eq(task) & d.gene_fold.eq(fold)])
                count += 1
        del matrix
    assert count == 42
    result = {'status': 'PASS', 'predictors': count, 'maximum_error': maximum, 'models_fit': 0,
        'original_labels_sha256': label_hash(frame.measured_delta), 'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json'),
        'known_control_manifest_sha256': sha256(KNOWN_OUT / 'evaluation_manifest.json'),
        'known_canonical_paired_receipt_sha256': sha256(KNOWN_OUT / 'canonical_paired_state_contrast.json'),
        'scope': 'All seven original pairwise same-cell held-gene controls reproduced using unchanged source models and original labels; reused evidence'}
    jsave(OUT / 'pairwise_known_control_replay.json', result)
    return result
