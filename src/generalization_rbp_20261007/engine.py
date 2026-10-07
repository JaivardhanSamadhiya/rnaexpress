"""Nested whole-assay selection with immutable checkpoints."""
from .common import *
from .routes import module
from src.cross_assay_20260927.models import purge
import sys

def features(track):
    assert track in TRACKS
    with np.load(ART / (track+'_model_features.npz')) as archive:
        matrix = archive['features'].astype(float)
    assert matrix.shape == (26258, {"base":246,"raw":502,"access":758}[track]) and np.isfinite(matrix).all()
    return matrix

def checkpoint(track, name, frame, matrix, config):
    path = OUT / track / 'fits' / (name+'_'+config['id']+'.json')
    ids = hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    if path.exists():
        result = readj(path)
        assert result['_training_ids_sha256'] == ids and result['_config'] == config
        return result
    result = module(track).fit_model(frame, matrix, config)
    result['_training_ids_sha256'] = ids
    result['_training_studies'] = sorted(frame.dataset.unique())
    result['_training_components'] = sorted(frame.biological_component.unique())
    result['_config'] = config
    jsave(path, result)
    return result

def run(track):
    freeze_check()
    assert not (OUT / track / 'run_complete.json').exists(), 'Preserve completed track'
    frame = load()
    matrix = features(track); mod = module(track)
    predictions, choices, folds, selections = [], [], [], []
    for held in STUDIES:
        test = frame.dataset.eq(held).to_numpy()
        train = purge(frame, ~test, test)
        source, source_x = frame.loc[train].reset_index(drop=True), matrix[train]
        values = []
        for config in mod.CONFIGS:
            source_regrets = []
            for inner in sorted(source.dataset.unique()):
                validation = source.dataset.eq(inner).to_numpy()
                inner_train = purge(source, ~validation, validation)
                tr, va = source.loc[inner_train].reset_index(drop=True), source.loc[validation].reset_index(drop=True)
                assert held not in set(tr.dataset) and inner not in set(tr.dataset)
                fitted = checkpoint(track, held+'__inner__'+inner, tr, source_x[inner_train], config)
                score = mod.predict_model(fitted, source_x[validation])
                regret = inner_regret(va, score); source_regrets.append(regret)
                selections.append({'outer_held':held, 'inner_held':inner, 'configuration':config['id'],
                    'regret':regret, 'training_rows':len(tr), 'validation_rows':len(va),
                    'training_ids_sha256':fitted['_training_ids_sha256']})
            values.append(float(np.mean(source_regrets)))
            print(track, held, config['id'], 'inner complete', flush=True)
        best = min(values)
        index = next(i for i, v in enumerate(values) if v <= best+1e-12)
        config = mod.CONFIGS[index]
        fitted = checkpoint(track, held+'__outer', source, source_x, config)
        target = frame.loc[test].reset_index(drop=True)
        score = mod.predict_model(fitted, matrix[test])
        choices.append(decisions(target, score, track))
        predictions.extend({'track':track, 'dataset':held, 'intervention_id':row.intervention_id,
                            'score':float(score[i]), 'configuration':config['id']}
                           for i, row in enumerate(target.itertuples()))
        folds.append({'held':held, 'selected_configuration':config, 'inner_macro_regret':values[index],
            'all_inner_scores':dict(zip([c['id'] for c in mod.CONFIGS], values)),
            'training_studies':fitted['_training_studies'], 'training_components':fitted['_training_components'],
            'training_ids_sha256':fitted['_training_ids_sha256'],
            'test_ids_sha256':hashlib.sha256('|'.join(target.intervention_id).encode()).hexdigest(),
            'test_rows':len(target)})
        print(track, held, 'outer complete', flush=True)
    selected = pd.concat(choices, ignore_index=True)
    csvsave(OUT/track/'decisions.csv', selected)
    csvsave(OUT/track/'predictions.csv.gz', pd.DataFrame(predictions), True)
    csvsave(OUT/track/'inner_selection.csv', pd.DataFrame(selections))
    csvsave(OUT/track/'comparison.csv', summary(selected))
    jsave(OUT/track/'folds.json', folds)
    jsave(OUT/track/'run_complete.json', {'status':'PASS', 'track':track,
        'prefit_manifest_sha256':sha256(OUT/'prefit_manifest.json'),
        'fit_files':len(list((OUT/track/'fits').glob('*.json'))),
        'prediction_rows':len(predictions), 'decision_rows':len(selected),
        'outer_target_selection':False, 'independent_confirmation':False})

if __name__ == '__main__': run(sys.argv[1])
