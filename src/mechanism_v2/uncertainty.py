"""Connected-group bootstrap refits, rank uncertainty and the coverage policy.

The pre-registered design asks for three connected-group bootstrap refits of the
selected recipe plus a within-decision percentile-rank standard deviation, with
the coverage choice (100%, 90%, 75%) made inside training folds only. The full
coverage result always remains the gate; selective coverage is secondary and can
never replace it.

A bootstrap replicate resamples whole connected components with replacement. A
component drawn twice is relabelled, so a repeated draw genuinely duplicates an
independent unit instead of colliding with itself inside a decision set.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .development_training import verify_freeze
from .feature_store import FeatureStore
from .fitting import fit_identity, inner_partition, outer_partition, provider_digest, row_identity, run_fit
from .gates import metric_frame
from .io import ROOT, canonical_json, sha256, write_json
from .outer_evaluation import selected_recipes, verify_outer_freeze
from .providers import FamilyProvider

UNCERTAINTY = 'results/mechanism_v2/outer/uncertainty.json'
REPLICATES = 3


def bootstrap_draw(store, train_idx, seed):
    """Resample whole connected components with replacement; relabel repeats."""
    rows = store.rows.iloc[np.asarray(train_idx, int)]
    components = np.array(sorted(rows.component.astype(str).unique()))
    if len(components) < 2:
        raise ValueError('At least two components required for a group bootstrap')
    rng = np.random.default_rng(seed)
    draw = rng.choice(components, size=len(components), replace=True)
    grouped = {str(name): group for name, group in rows.groupby(rows.component.astype(str))}
    frames = []
    for replicate, component in enumerate(draw):
        group = grouped[str(component)].copy()
        tag = f'#b{replicate}'
        group['component'] = group.component.astype(str) + tag
        group['biological_unit'] = group.component
        group['decision_set_id'] = group.decision_set_id.astype(str) + tag
        frames.append(group.reset_index(drop=True))
    frame = pd.concat(frames, ignore_index=True)
    order = np.concatenate([np.asarray(grouped[str(c)].index, int) for c in draw])
    digest = hashlib.sha256(canonical_json(sorted(draw.tolist()))).hexdigest()
    return order, frame, {'components_drawn': int(len(draw)),
                          'distinct_components': int(len(set(draw.tolist()))),
                          'rows': int(len(frame)), 'seed': int(seed), 'draw_sha256': digest}


def percentile_rank(rows, score):
    """Within-decision percentile rank in [0, 1]; 1 is the top-ranked candidate."""
    values = np.asarray(score, float)
    out = np.full(len(values), np.nan)
    frame = pd.DataFrame({'decision': rows.decision_set_id.astype(str).to_numpy()})
    for _, index in frame.groupby('decision', sort=False).indices.items():
        index = np.asarray(index, int)
        if len(index) < 2:
            out[index] = 1.0
            continue
        out[index] = (rankdata(values[index], method='average') - 1) / (len(index) - 1)
    return out


def replicate_scores(store, provider, recipe, train_idx, eval_idx, label, *, freeze_sha256,
                     namespace='uncertainty', seeds=None):
    """Three bootstrap refits scoring the same held rows; nothing else is changed."""
    seeds = seeds or [store.design['seed'] + 1000 + k for k in range(REPLICATES)]
    x, columns, provenance = provider.build(store, train_idx, eval_idx, label)
    held = np.asarray(eval_idx, int)
    values = []
    audits = []
    for replicate, seed in enumerate(seeds):
        order, frame, audit = bootstrap_draw(store, train_idx, seed)
        identity = fit_identity(
            freeze_sha256=freeze_sha256,
            recipe={'provider': provider.name, 'recipe_id': recipe.get('recipe_id'),
                    'config': recipe['config']},
            provider={'name': provider.name, 'partition_digest': provider_digest(provenance),
                      'columns': len(columns)},
            partition={'train': {'count': audit['rows'], 'sha256': audit['draw_sha256']},
                       'evaluation': row_identity(held)},
            extra={'stage': 'group_bootstrap', 'replicate': int(replicate), 'draw': audit})
        _, prediction = run_fit(f'{namespace}/{provider.name}/{label}_b{replicate}', identity,
                                x, columns, recipe['config'], frame, order, held)
        values.append(prediction)
        audits.append(audit)
    return np.vstack(values), audits


def decision_uncertainty(rows, replicates):
    """Standard deviation of the within-decision percentile rank across refits."""
    ranks = np.vstack([percentile_rank(rows, row) for row in replicates])
    spread = ranks.std(axis=0, ddof=1)
    frame = pd.DataFrame({'decision_set_id': rows.decision_set_id.astype(str).to_numpy(),
                          'spread': spread})
    return frame.groupby('decision_set_id', sort=True).spread.max()


def covered_regret(rows, score, decision_spread, coverage):
    """Regret restricted to the least uncertain decisions at the requested coverage."""
    metrics, _ = metric_frame(rows, score)
    if metrics.empty:
        return None
    spread = decision_spread.reindex(metrics.decision_set_id.astype(str)).to_numpy()
    if np.isnan(spread).any():
        raise ValueError('Missing uncertainty for an eligible decision')
    keep = spread <= np.quantile(spread, coverage) if coverage < 1 else np.ones(len(spread), bool)
    subset = metrics.loc[keep]
    if subset.empty:
        return None
    cells = subset.groupby(['dataset', 'component', 'direction'])[['regret', 'rank']].mean()
    contexts = cells.groupby(['dataset', 'direction']).mean()
    return {'coverage_requested': float(coverage),
            'coverage_achieved': float(keep.mean()),
            'regret': float(contexts.regret.mean()), 'rank': float(contexts['rank'].mean()),
            'decisions': int(len(subset))}


def run_uncertainty():
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    selections = selected_recipes(store, frozen)
    candidates = store.design['uncertainty']['coverage_candidates']
    tolerance = store.design['selection']['regret_tolerance']
    inner_policy, outer_records = {}, {}
    for outer in range(store.design['outer_folds']):
        recipe = selections['primary'][outer]
        provider = FamilyProvider(recipe['family'])
        inner_scores = np.full(len(store.rows), np.nan)
        inner_replicates = np.full((REPLICATES, len(store.rows)), np.nan)
        for inner in range(store.design['inner_folds']):
            train, valid = inner_partition(store, outer, inner)
            checkpoint = ROOT / (f'results/mechanism_v2/training/outer_{outer}/'
                                 f'{recipe["recipe_id"]}/inner_{inner}.json')
            record = json.loads(checkpoint.read_text())
            if sha256(ROOT / record['predictions']['path']) != record['predictions']['sha256']:
                raise ValueError('Committed inner prediction cache hash mismatch')
            cached = np.load(ROOT / record['predictions']['path'], allow_pickle=False)
            if not np.array_equal(cached[:, 0].astype(int), valid):
                raise ValueError('Committed inner prediction row identity mismatch')
            inner_scores[valid] = cached[:, 1]
            replicates, _ = replicate_scores(store, provider, recipe, train, valid,
                                             f'inner_{outer}_{inner}', freeze_sha256=digest)
            inner_replicates[:, valid] = replicates
        pool = np.flatnonzero(np.isfinite(inner_scores))
        spread = decision_uncertainty(store.rows.iloc[pool], inner_replicates[:, pool])
        options = []
        for coverage in candidates:
            value = covered_regret(store.rows.iloc[pool], inner_scores[pool], spread, coverage)
            if value:
                options.append(value)
        best = min(v['regret'] for v in options)
        tied = [v for v in options if v['regret'] <= best + tolerance]
        chosen = max(tied, key=lambda v: v['coverage_requested'])
        inner_policy[str(outer)] = {'options': options, 'selected_coverage': chosen['coverage_requested'],
                                    'selection_rule': 'inner-only minimum covered regret within the '
                                                      '0.002 tolerance, then greater coverage',
                                    'recipe_id': recipe['recipe_id']}
        train, held = outer_partition(store, outer)
        replicates, audits = replicate_scores(store, provider, recipe, train, held,
                                              f'outer_{outer}', freeze_sha256=digest)
        outer_spread = decision_uncertainty(store.rows.iloc[held], replicates)
        outer_records[str(outer)] = {
            'recipe_id': recipe['recipe_id'], 'replicate_draws': audits,
            'decision_rank_spread': {'mean': float(outer_spread.mean()),
                                     'median': float(outer_spread.median()),
                                     'maximum': float(outer_spread.max()),
                                     'decisions': int(len(outer_spread))},
            'selected_coverage': chosen['coverage_requested']}
        print(f'Uncertainty complete for outer fold {outer}: coverage policy '
              f'{chosen["coverage_requested"]}', flush=True)
        provider.release()
    record = {'format': 'mechanism_v2_uncertainty_v1',
              'outer_freeze_git_commit': freeze['git_commit'],
              'replicates_per_partition': REPLICATES,
              'coverage_candidates': candidates,
              'inner_coverage_policy': inner_policy,
              'outer_uncertainty': outer_records,
              'primary_gate_coverage': 'full coverage always remains the pre-registered gate',
              'note': ('three group-bootstrap refits give a coarse rank-stability summary, not a '
                       'calibrated predictive interval')}
    write_json(UNCERTAINTY, record)
    print('Uncertainty and coverage policy recorded', flush=True)
    return record
