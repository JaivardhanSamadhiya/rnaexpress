"""Pre-registered Mechanism-v3 arm N: nonlinear estimator, zero-shot outer folds.

The contract is in `configs/mechanism_v3/arm_nonlinear.json`, committed before
this module produced any zero-shot score. Whole connected components are held
out by the committed split, so no evaluation parent appears in training. The
baseline uses the identical estimator family on geometry alone, which isolates
the feature contribution from the model class.
"""
from __future__ import annotations

import json

import numpy as np

from src.mechanism_v2.evaluation import decision_metrics

from .diagnostics import _all_feature_matrix, context_mean
from .io import ROOT, sha256, write_json

ARM_CONFIG = 'configs/mechanism_v3/arm_nonlinear.json'
ARM_EVIDENCE = 'results/mechanism_v3/outer/arm_nonlinear_evidence.json'


def load_arm_config():
    record = json.loads((ROOT / ARM_CONFIG).read_text())
    if record['version'] != 'mechanism_v3_arm_nonlinear_v1':
        raise ValueError('Unknown arm config')
    if not record['committed_before_scoring']:
        raise PermissionError('Arm config must be committed before scoring')
    return record


def _fit_score(x, target, store, seed, config):
    """Zero-shot: train on outer_fold != k, score fold k exactly once."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    folds = store.rows.outer_fold.to_numpy(int)
    score = np.full(len(store.rows), np.nan)
    spec = config['estimator']
    for fold in sorted(set(folds.tolist())):
        train = np.flatnonzero(folds != fold)
        held = np.flatnonzero(folds == fold)
        model = HistGradientBoostingRegressor(
            max_iter=spec['max_iter'], learning_rate=spec['learning_rate'],
            max_depth=spec['max_depth'], random_state=int(seed))
        model.fit(x[train], target[train])
        score[held] = model.predict(x[held])
    if not np.isfinite(score).all():
        raise ValueError('Arm N did not score every candidate exactly once')
    return score


def _distributed(metrics, base_metrics):
    keys = ['dataset', 'component', 'direction']
    merged = metrics.merge(base_metrics, on=keys + ['decision_set_id'],
                           suffixes=('', '_base'), validate='one_to_one')
    merged['regret_gain'] = merged.regret_base - merged.regret
    per_component = merged.groupby('component', sort=True).regret_gain.mean()
    decile = per_component.quantile(0.10)
    worst = per_component[per_component <= decile]
    return {
        'components': int(len(per_component)),
        'median_component_regret_gain': float(per_component.median()),
        'fraction_components_improved': float((per_component > 0).mean()),
        'worst_decile_component_mean_regret_gain': float(worst.mean()) if len(worst) else float('nan'),
    }


def run_arm():
    from src.mechanism_v2.feature_store import FeatureStore
    config = load_arm_config()
    store = FeatureStore()
    rows = store.rows
    target = rows.localization_effect.to_numpy(float)
    x_all, columns = _all_feature_matrix(store)
    geometry, _ = store.matrix('M0')

    per_seed, points = {}, []
    for seed in config['replication_seeds']:
        full = _fit_score(x_all, target, store, seed, config)
        base = _fit_score(geometry, target, store, seed, config)
        metrics, _ = decision_metrics(rows, full)
        base_metrics, _ = decision_metrics(rows, base)
        full_ctx = context_mean(metrics)
        base_ctx = context_mean(base_metrics)
        point = {'rank_gain': full_ctx['rank'] - base_ctx['rank'],
                 'regret_gain': base_ctx['regret'] - full_ctx['regret']}
        g1 = config['gates']['g1_useful_selection']
        distributed = _distributed(metrics, base_metrics)
        g2 = config['gates']['g2_distributed_benefit']
        g10 = config['gates']['g10_hard_harm']
        per_seed[str(seed)] = {
            'absolute_full': full_ctx, 'absolute_geometry_baseline': base_ctx,
            'point': point, 'distributed': distributed,
            'g1_status': 'pass' if (point['rank_gain'] >= g1['rank_gain_minimum']
                                     and point['regret_gain'] >= g1['regret_gain_minimum']) else 'fail',
            'g2_status': 'pass' if (
                distributed['median_component_regret_gain']
                > g2['median_component_regret_gain_minimum_exclusive']
                and distributed['fraction_components_improved']
                >= g2['fraction_components_improved_minimum']) else 'fail',
            'g10_status': 'pass' if (
                distributed['worst_decile_component_mean_regret_gain']
                >= g10['worst_decile_component_mean_regret_gain_minimum']) else 'fail',
        }
        points.append(point)
        print(f'seed {seed}: rank_gain {point["rank_gain"]:+.4f} '
              f'regret_gain {point["regret_gain"]:+.4f} '
              f'g1 {per_seed[str(seed)]["g1_status"]} '
              f'g2 {per_seed[str(seed)]["g2_status"]} '
              f'g10 {per_seed[str(seed)]["g10_status"]}', flush=True)

    rank_sd = float(np.std([p['rank_gain'] for p in points], ddof=1))
    regret_sd = float(np.std([p['regret_gain'] for p in points], ddof=1))
    g9 = config['gates']['g9_seed_stability']
    categories = {name: {per_seed[s][name] for s in per_seed}
                  for name in ('g1_status', 'g2_status', 'g10_status')}
    g9_status = 'pass' if (max(rank_sd, regret_sd) <= g9['primary_gain_standard_deviation_maximum']
                           and all(len(v) == 1 for v in categories.values())) else 'fail'

    gate_status = {
        'g1_useful_selection': 'pass' if all(
            per_seed[s]['g1_status'] == 'pass' for s in per_seed) else 'fail',
        'g2_distributed_benefit': 'pass' if all(
            per_seed[s]['g2_status'] == 'pass' for s in per_seed) else 'fail',
        'g9_seed_stability': g9_status,
        'g10_hard_harm': 'pass' if all(
            per_seed[s]['g10_status'] == 'pass' for s in per_seed) else 'fail',
    }
    record = {
        'format': 'mechanism_v3_arm_nonlinear_evidence_v1',
        'arm_config_sha256': sha256(ROOT / ARM_CONFIG),
        'arm_id': config['arm_id'],
        'features': len(columns),
        'zero_shot_contract': config['zero_shot_contract'],
        'per_seed': per_seed,
        'seed_standard_deviation': {'rank_gain': rank_sd, 'regret_gain': regret_sd},
        'gate_status': gate_status,
        'gates_failed': sorted(k for k, v in gate_status.items() if v == 'fail'),
        'all_gates_passed': all(v == 'pass' for v in gate_status.values()),
        'stopping_rule': config['stopping_rule'],
        'mechanism_v2_verdict_preserved': 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS',
        'holdout_opened': False,
    }
    write_json(ARM_EVIDENCE, record)
    print(json.dumps(gate_status, indent=2), flush=True)
    return record


if __name__ == '__main__':
    run_arm()
