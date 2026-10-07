"""Four fixed source-only label-permutation diagnostics, never a biological null."""
from .common import *
from .engine import features
from .routes import module
from src.cross_assay_20260927.models import purge

def permute_training(frame):
    frame = frame.copy().reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    groups = ['dataset', 'biological_component', 'parent_context_id']
    for _, group in frame.groupby(groups, sort=True):
        group = group.sort_values('intervention_id')
        values = group.measured_delta.to_numpy(float)
        frame.loc[group.index, 'measured_delta'] = rng.permutation(values)
    return frame

def run():
    freeze_check()
    frame, _ = load(); matrix = features('combined'); mod = module('combined')
    choices = []
    for held in STUDIES:
        path = OUT / 'permutation' / (held+'.json')
        test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
        training = permute_training(frame.loc[train].reset_index(drop=True))
        config = {'id':'fixed_permuted_05', 'penalty':.05, 'scaling':'pair'}
        if path.exists():
            fitted = readj(path)
        else:
            fitted = mod.fit_model(training, matrix[train], config)
            fitted['permuted_labels_sha256'] = hashlib.sha256(training.measured_delta.to_numpy().tobytes()).hexdigest()
            fitted['training_ids_sha256'] = hashlib.sha256('|'.join(training.intervention_id).encode()).hexdigest()
            jsave(path, fitted)
        score = mod.predict_model(fitted, matrix[test])
        choices.append(decisions(frame.loc[test].reset_index(drop=True), score, 'permuted_combined'))
    selected = pd.concat(choices, ignore_index=True)
    csvsave(OUT/'permutation'/'decisions.csv', selected)
    csvsave(OUT/'permutation'/'comparison.csv', summary(selected))
    jsave(OUT/'permutation'/'receipt.json', {'status':'COMPLETE', 'fits':4, 'seed':SEED,
        'scope':'source-context-stratified training-label permutation; no biological-null claim',
        'held_truths_permuted':False, 'config_changes_allowed_from_result':False})

if __name__ == '__main__': run()
