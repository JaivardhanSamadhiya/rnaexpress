"""Bounded exploratory maximin fragment selection on original source rows only."""
from .common import ROOT, sha256, write_json, write_new
from .context_calibration import OUT, DATA, CONTEXTS, key, features, fit_predict, read_outcomes
import json, sys, subprocess
import numpy as np
import pandas as pd
from scipy.stats import rankdata

NAME = 'context_robust_selection'
POLICIES = ['maximin', 'average', *CONTEXTS, 'composition_maximin', 'uniform']


def percentiles(values):
    values = np.asarray(values, float)
    if values.ndim != 2 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError('Invalid rank input')
    return (rankdata(values, method='average', axis=0)-1)/(len(values)-1)


def decisions(truth, kmer_prediction, composition_prediction, sign):
    measured = percentiles(sign*truth)
    utility = measured.min(axis=1)
    predicted = percentiles(sign*kmer_prediction)
    composition = percentiles(sign*composition_prediction)
    scores = {'maximin': predicted.min(axis=1), 'average': predicted.mean(axis=1),
              'composition_maximin': composition.min(axis=1), 'uniform': np.zeros(len(truth))}
    scores.update({c: predicted[:, i] for i, c in enumerate(CONTEXTS)})
    result = {}
    for policy, score in scores.items():
        selected = score == score.max()
        result[policy] = {'regret': float(utility.max()-utility[selected].mean()),
                          'top_quartile_all_contexts': float((utility[selected] >= .75).mean()),
                          'tied_choices': int(selected.sum())}
    return result, bool(utility.max() >= .75)


def source_rows():
    f = pd.read_csv(OUT/'context_calibration_partition.csv')
    f = f[f.partition == 'source'].reset_index(drop=True)
    if len(f) != 3235 or f.component.nunique() != 61: raise ValueError('Source scope changed')
    return f


def freeze():
    source_rows()
    paths = [ROOT/'src/research_20260921'/n for n in ['context_robust_selection.py', 'test_context_robust_selection.py', 'context_calibration.py', 'common.py']]
    paths += [ROOT/'reports/research_20260921/context_robust_selection_spec.md', OUT/'context_calibration_partition.csv', DATA/'context2022_data3.xlsx']
    write_json(OUT/(NAME+'_freeze.json'), {'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths},
        'scope': 'Exploratory reused-source diagnostic; no confirmation or other new label access.'})


def run():
    fp = OUT/(NAME+'_freeze.json')
    for p, h in json.loads(fp.read_text())['files'].items():
        if sha256(ROOT/p) != h: raise ValueError('Frozen file changed '+p)
    if subprocess.check_output(['git', 'show', 'HEAD:'+fp.relative_to(ROOT).as_posix()], cwd=ROOT) != fp.read_bytes():
        raise ValueError('Commit freeze first')
    f = source_rows(); values, accessed = read_outcomes(DATA/'context2022_data3.xlsx', f.excel_row)
    y = np.asarray([values[r] for r in f.excel_row]); x = features(f.sequence)
    components = sorted(f.component.unique(), key=lambda c: key('curve-fold|'+c))
    folds = {c: i%5 for i, c in enumerate(components)}
    p = np.full_like(y, np.nan); comp = p.copy()
    for fold in range(5):
        test = f.component.map(folds).eq(fold).to_numpy(); train = ~test
        for context in range(4):
            p[test, context] = fit_predict(x, y[:, context], train, test, 100)
            comp[test, context] = fit_predict(x[:, :4], y[:, context], train, test, 100)
        print(f'Completed source-only fold {fold+1}/5', flush=True)
    pred = f[['id', 'excel_row', 'component', 'gene', 'library']].copy()
    for j, c in enumerate(CONTEXTS):
        pred['kmer_'+c] = p[:, j]; pred['composition_'+c] = comp[:, j]
    pred['fold'] = f.component.map(folds)
    write_new(OUT/(NAME+'_predictions.csv'), pred.to_csv(index=False, lineterminator='\n').encode())
    rows, excluded = [], []
    for (component, gene, library), g in f.groupby(['component', 'gene', 'library']):
        original = g.index.to_numpy(); ix = original[np.isfinite(y[original]).all(axis=1)]
        info = {'component': component, 'gene': gene, 'library': library, 'metadata_candidates': len(g), 'complete_candidates': len(ix)}
        reason = 'fewer_than_ten_complete' if len(ix) < 10 else ('constant_context' if np.any(np.ptp(y[ix], axis=0) <= 0) else None)
        if reason:
            excluded.append({**info, 'reason': reason}); continue
        for sign, direction in [(1, 'nuclear'), (-1, 'cytoplasmic')]:
            result, feasible = decisions(y[ix], p[ix], comp[ix], sign)
            for policy, metrics in result.items():
                rows.append({**info, 'direction': direction, 'policy': policy,
                             'top_quartile_feasible': feasible, **metrics})
    d = pd.DataFrame(rows)
    if d.empty: raise ValueError('No eligible decisions')
    means = d.groupby(['component', 'policy']).regret.mean().unstack('policy')
    draws = np.random.default_rng(20260924).integers(0, len(means), (5000, len(means)))
    comparisons = {}; promising = len(means) >= 20
    for policy in POLICIES[1:]:
        gain = (means[policy]-means.maximin).to_numpy(); ci = np.quantile(gain[draws].mean(axis=1), [.025, .975])
        comparisons[policy] = {'gain': float(gain.mean()), 'descriptive_component_ci95': ci.tolist()}
        promising = promising and gain.mean() >= .03 and ci[0] > 0
    directional = d.groupby(['component', 'direction', 'policy'])[['regret', 'top_quartile_all_contexts', 'top_quartile_feasible']].mean().groupby(['direction', 'policy']).mean()
    result = {'scope': 'Exploratory source-only cross-validation; existing source outcomes reused. No independent validation or promotion.',
              'source_rows': len(f), 'source_components': len(components), 'numeric_cells_read': len(accessed),
              'complete_case_rows': int(np.isfinite(y).all(axis=1).sum()), 'eligible_components': len(means),
              'eligible_gene_library_sets': len(d)//(2*len(POLICIES)), 'excluded_sets': excluded,
              'mean_robust_regret': means.mean().to_dict(), 'comparisons': comparisons,
              'directional_summary': {direction: {policy: directional.loc[(direction, policy)].to_dict() for policy in POLICIES} for direction in ['nuclear', 'cytoplasmic']},
              'promising_source_only_criterion': bool(promising), 'any_new_outcomes_opened': False}
    write_new(OUT/(NAME+'_decisions.csv'), d.to_csv(index=False, lineterminator='\n').encode())
    write_json(OUT/(NAME+'_result.json'), result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['excluded_sets', 'directional_summary']}, indent=2), flush=True)


if __name__ == '__main__': {'freeze': freeze, 'run': run}[sys.argv[1]]()
