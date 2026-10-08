"""Independently traverse coefficients/trees and canonical choices in both states."""
from .common import *
from .evaluate import features, source_model, task_summary
from .predict import canonical_scores, score_match
import os
from src.generalization_nonlinear_crosscell_20261007.routes import module
from src.generalization_rbp_20261007.canonical_inner_replay import decision_table, decisions_equal

def exact_decision_roster(saved, frame, track, crossed=False):
    assert set(saved.model) == {track}
    fields = ['task', 'gene_fold', 'parent_context_id', 'direction']
    assert not saved.duplicated(fields).any() and set(saved.dataset) == {'mikl_gse173098'}
    expected = set()
    for task, (cell, source_task) in TASKS.items():
        selected_cell = ('Neuro-2a' if cell == 'CAD' else 'CAD') if crossed else cell
        name = source_task if crossed else task
        contexts = frame[frame.cell_type.eq(selected_cell)][['held_parent_fold', 'parent_context_id']].drop_duplicates()
        expected.update((name, int(fold), context, direction) for fold, context in contexts.itertuples(index=False, name=None) for direction in (-1, 1))
    assert len(saved) == len(expected) and set(saved[fields].itertuples(index=False, name=None)) == expected

def run():
    assert all(os.environ.get(name) == '1' for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    manifest = freeze_check(); complete = readj(OUT / 'evaluation_complete.json')
    assert complete['status'] == 'PASS' and complete['evaluation_manifest_sha256'] == sha256(OUT / 'evaluation_manifest.json')
    frame = load(True); assert label_hash(frame.measured_delta) == complete['original_labels_sha256']
    maximum, same_count, crossed_count, decisions_count = 0., 0, 0, 0
    for track in TRACKS:
        matrix = features(track); mod = module(track)
        pred = pd.read_csv(OUT / track / 'predictions.csv.gz', float_precision='round_trip')
        d = pd.read_csv(OUT / track / 'decisions.csv', float_precision='round_trip')
        old_pred = pd.read_csv(SOURCE_OUT / track / 'predictions.csv.gz', float_precision='round_trip')
        old_d = pd.read_csv(SOURCE_OUT / track / 'decisions.csv', float_precision='round_trip')
        for p in (pred, old_pred):
            assert len(p) == len(frame) and p.intervention_id.is_unique and set(p.intervention_id) == set(frame.intervention_id) and set(p.track) == {track}
        exact_decision_roster(d, frame, track); exact_decision_roster(old_d, frame, track, crossed=True)
        roster = readj(OUT / track / 'roster.json'); assert len(roster) == 6
        assert {(entry['task'], entry['fold']) for entry in roster} == {(task, fold) for task in TASKS for fold in FOLDS}
        track_complete = readj(OUT / track / 'complete.json')
        assert track_complete['status'] == 'PASS' and track_complete['track'] == track and track_complete['rows'] == len(frame) and track_complete['new_fits'] == 0
        assert track_complete['evaluation_manifest_sha256'] == sha256(OUT / 'evaluation_manifest.json')
        assert track_complete['original_labels_sha256'] == label_hash(frame.measured_delta)
        for task in TASKS:
            for fold in FOLDS:
                model, config, target_mask, opposite_mask, path = source_model(track, task, fold, frame, matrix)
                entry = next(value for value in roster if value['task'] == task and value['fold'] == fold)
                assert entry['configuration'] == config and entry['source_task'] == TASKS[task][1]
                assert entry['source_checkpoint'] == path.relative_to(ROOT).as_posix() and entry['source_checkpoint_sha256'] == sha256(path)
                assert entry['source_creation_sidecar_sha256'] == sha256(path.with_suffix('.sha256.json'))
                for crossed, mask in ((False, target_mask), (True, opposite_mask)):
                    target = frame.loc[mask].reset_index(drop=True)
                    score, bound = canonical_scores(track, model, matrix[mask], mod.predict_model)
                    prediction, decision = (old_pred, old_d) if crossed else (pred, d)
                    name = TASKS[task][1] if crossed else task
                    saved = prediction[prediction.task.eq(name) & prediction.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
                    assert len(saved) == len(target) and set(saved.configuration) == {config['id']}
                    maximum = max(maximum, bound, score_match(score, saved.score.to_numpy(float)))
                    expected = decision_table(target, score)
                    decisions_equal(expected, decision[decision.task.eq(name) & decision.gene_fold.eq(fold)])
                    decisions_count += len(expected)
                    if crossed:
                        crossed_count += 1
                    else:
                        same_count += 1
                        assert entry['target_ids_sha256'] == rowhash(target) and entry['target_metadata_sha256'] == metadata_hash(target)
                        assert entry['target_labels_sha256'] == label_hash(target.measured_delta) and entry['target_rows'] == len(target)
        actual = task_summary(d).sort_values('task').reset_index(drop=True)
        saved = pd.read_csv(OUT / track / 'comparison.csv', float_precision='round_trip').sort_values('task').reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, saved, check_exact=False, atol=1e-12, rtol=0)
        print('Nonlinear known-cell independent both-state replay', track, 'PASS', flush=True)
        del matrix
    assert same_count == crossed_count == 84
    from .control_replay import run as replay_pairwise
    controls = replay_pairwise(frame)
    jsave(OUT / 'verification_receipt.json', {'status': 'PASS', 'predictors_checked': same_count, 'crossed_state_predictors_rechecked': crossed_count,
        'maximum_score_error': maximum, 'decisions_checked': decisions_count, 'same_checkpoint_both_states_verified': True,
        'source_configuration_unchanged': True, 'canonical_full_target_ties_preserved': True,
        'independent_hgb_partition_traversal_and_ridge_coefficients': True,
        'pairwise_known_controls_predictors_replayed': controls['predictors'],
        'pairwise_known_control_maximum_error': controls['maximum_error'],
        'pairwise_known_control_replay_receipt_sha256': sha256(OUT / 'pairwise_known_control_replay.json'),
        'new_fits': 0, 'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json'),
        'result_files': {path.relative_to(ROOT).as_posix(): sha256(path) for track in TRACKS for path in (OUT / track).rglob('*') if path.is_file()},
        'independent_confirmation': False})

if __name__ == '__main__':
    run()
