"""Namespace guards and independent candidate decision metrics."""
from src.cross_assay_20260927.common import ROOT, np, pd, sha256, clean, readj
from pathlib import Path
import json, hashlib, gzip, subprocess
from scipy.stats import kendalltau

NS = 'generalization_20261007'
SRC, OUT, REP, ART = [ROOT / x / NS for x in ('src', 'results', 'reports', 'artifacts')]
STUDIES = ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle']
TRACKS = ['scaling', 'representation', 'mechanism', 'coverage', 'endpoint']
SEED = 20261007

def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(x) for x in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, f'Preserve {path}'
    else:
        path.write_bytes(payload)

def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False)+'\n').encode())

def csvsave(path, frame, compressed=False):
    payload = frame.to_csv(index=False, lineterminator='\n').encode()
    save(path, gzip.compress(payload, mtime=0) if compressed else payload)

def load():
    from src.probabilistic_ranking_20260928.common import load as original_load
    frame, x, _, _ = original_load()
    assert len(frame) == 26258 and set(frame.dataset) == set(STUDIES)
    return frame, x

def freeze_check():
    from src.probabilistic_ranking_20260928.common import frozen
    frozen()
    manifest = readj(OUT/'prefit_manifest.json')
    for name, checksum in manifest['files'].items():
        assert sha256(ROOT/name) == checksum, name
    committed = subprocess.check_output(['git', 'show', 'HEAD:results/'+NS+'/prefit_manifest.json'], cwd=ROOT)
    assert committed == (OUT/'prefit_manifest.json').read_bytes()
    return manifest

def decisions(frame, score, model, stage='held_assay'):
    """Independent extremes/choice/regret; numeric effect is an assay contrast."""
    assert len(score) == len(frame) and np.isfinite(score).all()
    rows = []
    for context, g in frame.groupby('parent_context_id', sort=True):
        g = g.sort_values('intervention_id')
        indexes = g.index.to_numpy()
        y, s = g.measured_delta.to_numpy(float), np.asarray(score)[indexes]
        spread = float(np.ptp(y))
        assert len(g) >= 2 and spread > 0
        n = len(g)
        # Kendall's tau-b correction gives half credit for predicted ties.
        if np.ptp(s) == 0:
            pair = .5
        else:
            total = n*(n-1)/2
            tied_y = sum(c*(c-1)/2 for c in pd.Series(y).value_counts())
            tied_s = sum(c*(c-1)/2 for c in pd.Series(s).value_counts())
            pair = .5+.5*kendalltau(y,s).statistic*np.sqrt((total-tied_y)*(total-tied_s))/(total-tied_y)
        for direction in (-1, 1):
            truth, prediction = direction*y, direction*s
            order = np.argsort(-prediction, kind='stable')
            j = int(order[0])
            wrong = truth[j] < -1e-12
            feasible = bool((truth > 1e-12).any())
            rows.append({'stage':stage, 'model':model, 'dataset':g.dataset.iloc[0],
                'biological_component':g.biological_component.iloc[0], 'parent_context_id':context,
                'direction':direction, 'candidates':n, 'selected_id':g.intervention_id.iloc[j],
                'regret':float((truth.max()-truth[j])/spread), 'wrong_direction':float(wrong),
                'avoidable_wrong':float(wrong and feasible), 'no_feasible_candidate':float(not feasible),
                'unavoidable_wrong':float(wrong and bool((truth < -1e-12).all())),
                'neutral_only_alternative_wrong':float(wrong and not feasible and not (truth < -1e-12).all()),
                'best_recovery':float(truth[j] == truth.max()), 'top5_best_recovery':float(truth[order[:5]].max() == truth.max()),
                'pairwise_accuracy':float(pair), 'selected_effect':float(y[j]), 'selected_score':float(s[j])})
    return pd.DataFrame(rows)

def summary(frame):
    cols = ['regret','wrong_direction','avoidable_wrong','no_feasible_candidate',
            'unavoidable_wrong','neutral_only_alternative_wrong','best_recovery','top5_best_recovery','pairwise_accuracy']
    return frame.groupby(['model','dataset','biological_component'])[cols].mean().groupby(['model','dataset']).mean().reset_index()

def inner_regret(frame, score):
    d=decisions(frame.reset_index(drop=True), score, 'inner', 'inner')
    return float(summary(d).regret.mean())
