"""Reuse every original selected outer checkpoint; never refit or select targets."""
import os
import sys
from .common import *
from .splits import masks
from src.generalization_nonlinear_crosscell_20261007.routes import module
from src.generalization_nonlinear_crosscell_20261007.verify import load_checkpoint, check_model

def features(track):
    assert track in TRACKS
    path = FEATURE_ART / (track.split('/')[1] + '_model_features.npz')
    with np.load(path, allow_pickle=False) as archive:
        assert archive.files == ['features']; matrix = archive['features'].astype(np.float64)
    assert matrix.shape == (13781, WIDTHS[track]) and np.isfinite(matrix).all()
    return matrix

def select_source(configs, values):
    assert len(configs) == len(values) == 3 and np.isfinite(values).all()
    minimum = min(values)
    return next(config for config, value in zip(configs, values) if value <= minimum + 1e-12)

def source_model(track, task, fold, frame, matrix):
    assert track in TRACKS
    source_task = TASKS[task][1]
    roster = readj(SOURCE_OUT / track / 'folds.json')
    assert len(roster) == 6 and {(row['task'], row['fold']) for row in roster} == {(name, f) for _, name in TASKS.values() for f in FOLDS}
    info = next(row for row in roster if row['task'] == source_task and row['fold'] == fold)
    mod = module(track); choices = pd.read_csv(SOURCE_OUT / track / 'source_selection.csv', float_precision='round_trip')
    values = []
    assert set(info['all_source_oof_scores']) == {config['id'] for config in mod.CONFIGS}
    for config in mod.CONFIGS:
        recorded = choices[choices.task.eq(source_task) & choices.outer_fold.eq(fold) & choices.configuration.eq(config['id'])]
        assert len(recorded) == 1
        value = float(recorded.iloc[0].combined_source_oof_macro_regret)
        assert abs(value - info['all_source_oof_scores'][config['id']]) < 1e-12
        values.append(value)
    config = select_source(mod.CONFIGS, values); assert config == info['selected_configuration']
    train, target, opposite = masks(frame, task, fold)
    source = frame.loc[train].reset_index(drop=True)
    assert rowhash(source) == info['training_ids_sha256'] and rowhash(frame.loc[opposite]) == info['test_ids_sha256']
    assert info['test_rows'] == int(opposite.sum()) and info['training_cell'] == TASKS[task][0]
    assert info['training_components'] == sorted(source.biological_component.unique())
    path = SOURCE_OUT / track / 'fits' / (source_task + '__fold' + str(fold) + '__outer_' + config['id'] + '.json')
    model = load_checkpoint(path)
    check_model(model, source, config, track, matrix[train])
    return model, config, target, opposite, path

def task_summary(frame):
    columns = ['regret', 'wrong_direction', 'avoidable_wrong', 'pairwise_accuracy']
    return frame.groupby(['model', 'task', 'biological_component'])[columns].mean().groupby(['model', 'task']).mean().reset_index()

def run(root_start=False):
    assert root_start, 'Root explicitly starts evaluation after exact evaluation freeze commit'
    manifest = freeze_check()
    for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ.get(variable) == '1', variable
    assert not (OUT / 'evaluation_complete.json').exists()
    frame = load(True); original_labels = label_hash(frame.measured_delta)
    assert rowhash(frame) == manifest['row_ids_sha256'] and metadata_hash(frame) == manifest['metadata_sha256']
    for track in TRACKS:
        assert not (OUT / track / 'complete.json').exists()
        matrix = features(track); predictions, all_decisions, rosters = [], [], []
        for task in TASKS:
            for fold in FOLDS:
                model, config, target_mask, _, path = source_model(track, task, fold, frame, matrix)
                target = frame.loc[target_mask].reset_index(drop=True)
                score = module(track).predict_model(model, matrix[target_mask])
                d = decisions(target, score, track); d['task'] = task; d['gene_fold'] = fold; all_decisions.append(d)
                predictions.extend({'track': track, 'task': task, 'gene_fold': fold, 'intervention_id': row.intervention_id,
                    'score': float(score[index]), 'configuration': config['id']} for index, row in enumerate(target.itertuples()))
                rosters.append({'task': task, 'source_task': TASKS[task][1], 'fold': fold, 'configuration': config,
                    'source_checkpoint': path.relative_to(ROOT).as_posix(), 'source_checkpoint_sha256': sha256(path),
                    'source_creation_sidecar_sha256': sha256(path.with_suffix('.sha256.json')),
                    'target_ids_sha256': rowhash(target), 'target_metadata_sha256': metadata_hash(target),
                    'target_labels_sha256': label_hash(target.measured_delta), 'target_rows': len(target)})
        assert len(predictions) == 13781 and len({row['intervention_id'] for row in predictions}) == 13781
        d = pd.concat(all_decisions, ignore_index=True)
        csvsave(OUT / track / 'predictions.csv.gz', pd.DataFrame(predictions), True)
        csvsave(OUT / track / 'decisions.csv', d); csvsave(OUT / track / 'comparison.csv', task_summary(d))
        jsave(OUT / track / 'roster.json', rosters)
        jsave(OUT / track / 'complete.json', {'status': 'PASS', 'track': track, 'rows': 13781, 'new_fits': 0,
            'original_labels_sha256': original_labels, 'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json')})
        print('Nonlinear known-cell', track, 'six unchanged checkpoints evaluated; zero fits', flush=True)
        del matrix
    jsave(OUT / 'evaluation_complete.json', {'status': 'PASS', 'tracks': TRACKS, 'new_fits': 0,
        'reused_outer_predictors': 84, 'original_labels_sha256': original_labels,
        'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json'), 'independent_confirmation': False})

if __name__ == '__main__':
    run('--root-start' in sys.argv[1:])
