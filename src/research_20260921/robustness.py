"""Fixed post-pilot baselines and composition-preserving swap diagnostic."""
from .pilots import (BASES, OUT, DATA, read_sixmers, fit_order,
                     position_features, regret, verify)
from .common import ROOT, sha256, write_json, write_new
from datetime import datetime, timezone
import itertools
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


def count_features(sequences):
    vocabulary = [''.join(p) for k in (1, 2, 3) for p in itertools.product(BASES, repeat=k)]
    return np.array([[sum(s[j:j+len(w)] == w for j in range(len(s)-len(w)+1))
                      for w in vocabulary] for s in sequences], float)


def swaps(sequence):
    result = set()
    for i in range(len(sequence)):
        for j in range(i+1, len(sequence)):
            if sequence[i] != sequence[j]:
                s = list(sequence)
                s[i], s[j] = s[j], s[i]
                result.add(''.join(s))
    return sorted(result)


def run():
    verify()
    paths = [ROOT / 'src/research_20260921/robustness.py',
             ROOT / 'reports/research_20260921/followup_spec.md']
    write_json(OUT / 'robustness_freeze.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths},
        'status': 'post-pilot specification; all following metrics not yet generated'})
    frame = read_sixmers()
    seq, y = frame.kmer.to_numpy(), frame.score.to_numpy(float)
    test, keys, base, pair, indices = fit_order(seq, y)
    positional = position_features(seq)
    predictions = {'composition': base, 'position_pair': pair}
    for name, x in [('position_additive', positional[:, :24]), ('kmer123', count_features(seq))]:
        scaler = StandardScaler().fit(x[~test])
        model = Ridge(alpha=10).fit(scaler.transform(x[~test]), (y-base)[~test])
        predictions[name] = base + model.predict(scaler.transform(x))
    rng = np.random.default_rng(20260921)
    draws = rng.integers(0, len(indices), (2000, len(indices)))
    sse = {name: np.array([np.sum((y[ix]-pred[ix])**2) for ix in indices])
           for name, pred in predictions.items()}
    result = {'scope': 'post-pilot within-assay robustness, not independent validation', 'models': {}}
    for name, pred in predictions.items():
        gains = np.array([regret(y[ix], base[ix], seq[ix]) - regret(y[ix], pred[ix], seq[ix]) for ix in indices])
        result['models'][name] = {
            'error_reduction_vs_composition': float(1-sse[name].sum()/sse['composition'].sum()),
            'error_reduction_ci': np.quantile(1-sse[name][draws].sum(1)/sse['composition'][draws].sum(1), [.025,.975]).tolist(),
            'regret_gain': float(gains.mean())}
    result['pair_vs_baselines'] = {}
    for name in ('position_additive', 'kmer123'):
        result['pair_vs_baselines'][name] = {
            'relative_error_reduction': float(1-sse['position_pair'].sum()/sse[name].sum()),
            'ci': np.quantile(1-sse['position_pair'][draws].sum(1)/sse[name][draws].sum(1), [.025,.975]).tolist()}
    eligible = set(np.concatenate(indices).tolist())
    lookup = {s: i for i, s in enumerate(seq)}
    rows = []
    for i in sorted(eligible):
        candidates = np.array([lookup[s] for s in swaps(seq[i]) if lookup[s] in eligible], dtype=int)
        if len(candidates) < 2 or np.ptp(y[candidates]) == 0:
            continue
        for sign in (1, -1):
            truth = sign*y[candidates]
            uniform_regret = (truth.max()-truth.mean())/np.ptp(truth)
            for name, pred in predictions.items():
                chosen = candidates[np.lexsort((seq[candidates], -sign*pred[candidates]))[0]]
                model_regret = (truth.max()-sign*y[chosen])/np.ptp(truth)
                rows.append({'parent': seq[i], 'composition': str(keys[i]), 'direction': sign,
                             'model': name, 'selected': seq[chosen], 'candidates': len(candidates),
                             'oriented_effect': float(sign*(y[chosen]-y[i])),
                             'gain_over_uniform': float(uniform_regret-model_regret)})
    edits = pd.DataFrame(rows)
    result['swap_task'] = {'parents': int(edits.parent.nunique()), 'models': {}}
    for name, group in edits.groupby('model'):
        means = group.groupby('composition')[['gain_over_uniform','oriented_effect']].mean()
        boot = rng.integers(0, len(means), (2000, len(means)))
        result['swap_task']['models'][name] = {
            'composition_classes': len(means), 'regret_gain_over_uniform': float(means.gain_over_uniform.mean()),
            'gain_ci': np.quantile(means.gain_over_uniform.to_numpy()[boot].mean(1), [.025,.975]).tolist(),
            'mean_oriented_nrs_change': float(means.oriented_effect.mean())}
    write_new(OUT / 'robustness_swap_predictions.csv', edits.to_csv(index=False, lineterminator='\n').encode())
    frame = pd.DataFrame({'kmer': seq, 'test': test, 'nrs': y, **predictions})
    write_new(OUT / 'robustness_predictions.csv', frame.to_csv(index=False, lineterminator='\n').encode())
    write_json(OUT / 'robustness_result.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    run()
