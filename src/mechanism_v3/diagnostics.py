"""Diagnostics that decide whether ANY selector can pass the RNAddress gates.

These are explicitly labelled diagnostics. None of them is a zero-shot result and
none of them can produce a GO verdict. They answer three questions the earlier
experiments never asked directly:

1. **Assay reproducibility ceiling.** Given the reported per-candidate measurement
   uncertainty, how well would a *perfect* predictor of the true effect score if it
   were re-measured once? If that ceiling is close to the geometry baseline, the
   pre-registered gate thresholds are unreachable by any model, and every failure
   so far is a property of the benchmark rather than of the representation.

2. **Leaky within-parent ceiling.** If a model is allowed to train on sibling
   mutants of the very same parent in the very same assay (explicitly NOT
   zero-shot), is there any learnable mutation-level signal at all?

3. **Grammar informativeness.** Mechanism-v3's grammar delta is zero for most
   candidates, so most decision sets are decided by lexical tie-breaking rather
   than by the grammar. That is an implementation defect in the v3 comparison,
   and its size is quantified here.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.mechanism_v2.evaluation import decision_metrics
from src.mechanism_v2.ranking import PairedRanker, RankConfig

from .grammar import load_grammar, score_rows, size_baseline
from .io import ROOT, write_json

DIAGNOSTICS = 'results/mechanism_v3/diagnostics/ceiling_analysis.json'

# Published Mechanism-v2 outer numbers, quoted for comparison only.
V2_SELECTOR = {'rank': 0.6270668284700763, 'regret': 0.4073787434663261}
V2_BASELINE_M0 = {'rank': 0.6020600089358199, 'regret': 0.4325822025549311}


def context_mean(metrics):
    """Average within source/component/direction, then equal source x direction."""
    per_unit = metrics.groupby(['dataset', 'component', 'direction'], sort=True)[
        ['rank', 'regret']].mean().reset_index()
    per_context = per_unit.groupby(['dataset', 'direction'], sort=True)[
        ['rank', 'regret']].mean()
    return {'rank': float(per_context['rank'].mean()),
            'regret': float(per_context.regret.mean())}


def assay_reliability(rows, seed=20260912, replicates=200):
    """Test-retest ceiling implied by the reported measurement uncertainty."""
    effect = rows.localization_effect.to_numpy(float)
    uncertainty = rows.effect_uncertainty.to_numpy(float)
    finite = np.isfinite(uncertainty)
    work = rows.assign(_effect=effect, _unc=np.where(finite, uncertainty, np.nan))

    # Variance decomposition within each decision set.
    records = []
    for decision, group in work.groupby('decision_set_id', sort=True):
        values = group._effect.to_numpy(float)
        noise = group._unc.to_numpy(float)
        if len(values) < 2 or not np.isfinite(values).all():
            continue
        between = float(np.var(values, ddof=1))
        mean_noise_var = float(np.nanmean(noise ** 2)) if np.isfinite(noise).any() else np.nan
        records.append({'decision_set_id': decision, 'candidates': int(len(values)),
                        'between_variance': between, 'mean_noise_variance': mean_noise_var})
    frame = pd.DataFrame(records)
    usable = frame.dropna(subset=['mean_noise_variance'])
    reliability = np.nan
    if not usable.empty:
        signal = np.maximum(usable.between_variance - usable.mean_noise_variance, 0.0)
        reliability = float(np.mean(signal / usable.between_variance.replace(0, np.nan)))

    # Noisy-oracle: a perfect predictor of the true effect, re-measured once.
    rng = np.random.default_rng(seed)
    scale = np.where(np.isfinite(uncertainty), uncertainty, 0.0)
    ceiling = []
    for _ in range(replicates):
        noisy = effect + rng.normal(0.0, scale)
        metrics, _ = decision_metrics(rows, noisy)
        ceiling.append(context_mean(metrics))
    ceiling_rank = float(np.mean([c['rank'] for c in ceiling]))
    ceiling_regret = float(np.mean([c['regret'] for c in ceiling]))

    exact, _ = decision_metrics(rows, effect)
    perfect = context_mean(exact)

    return {
        'uncertainty_semantics': sorted(set(rows.uncertainty_semantics.astype(str))),
        'outcome_semantics': sorted(set(rows.outcome_semantics.astype(str))),
        'candidates_with_finite_uncertainty': float(finite.mean()),
        'median_replicate_count': float(np.nanmedian(rows.replicate_count.to_numpy(float))),
        'mean_within_decision_reliability': reliability,
        'decisions_analysed': int(len(frame)),
        'perfect_oracle': perfect,
        'noisy_oracle_ceiling': {'rank': ceiling_rank, 'regret': ceiling_regret,
                                 'replicates': replicates, 'seed': seed},
        'mechanism_v2_selector': V2_SELECTOR,
        'mechanism_v2_geometry_baseline': V2_BASELINE_M0,
        'headroom_rank_ceiling_minus_baseline': ceiling_rank - V2_BASELINE_M0['rank'],
        'headroom_regret_baseline_minus_ceiling': V2_BASELINE_M0['regret'] - ceiling_regret,
        'interpretation': (
            'The noisy oracle is the best any predictor could do if it knew the true effect '
            'exactly and the benchmark were re-measured once with its own reported uncertainty. '
            'It is an upper bound on achievable rank and a lower bound on achievable regret.'),
    }


def grammar_informativeness(rows):
    """How often the frozen grammar actually distinguishes candidates."""
    design = load_grammar()
    grammar = score_rows(rows, design['elements'])
    baseline = size_baseline(rows)
    work = rows.assign(_g=grammar)
    distinct = work.groupby('decision_set_id', sort=True)._g.nunique()
    informative_sets = set(distinct[distinct >= 2].index)
    mask = rows.decision_set_id.isin(informative_sets).to_numpy()

    record = {
        'nonzero_grammar_delta_fraction': float((grammar != 0).mean()),
        'decisions_total': int(rows.decision_set_id.nunique()),
        'decisions_with_at_least_two_distinct_grammar_values': int(len(informative_sets)),
        'candidate_rows_in_informative_decisions': int(mask.sum()),
        'components_in_informative_decisions': int(rows.loc[mask].component.nunique())
        if mask.any() else 0,
        'defect': ('In the first Mechanism-v3 run the grammar was compared on every decision set, '
                   'including the majority in which every candidate scores exactly zero and the '
                   'winner is therefore chosen by lexical candidate_id. That comparison measures '
                   'tie-breaking, not grammar.'),
    }
    if mask.any():
        g_metrics, _ = decision_metrics(rows.loc[mask], grammar[mask])
        b_metrics, _ = decision_metrics(rows.loc[mask], baseline[mask])
        record['informative_subset'] = {
            'grammar': context_mean(g_metrics),
            'size_baseline': context_mean(b_metrics),
        }
        record['informative_subset']['rank_gain'] = (
            record['informative_subset']['grammar']['rank']
            - record['informative_subset']['size_baseline']['rank'])
        record['informative_subset']['regret_gain'] = (
            record['informative_subset']['size_baseline']['regret']
            - record['informative_subset']['grammar']['regret'])
    return record


def leaky_within_parent_ceiling(rows, seed=20260912):
    """Train on sibling mutants of the SAME parent; explicitly not zero-shot.

    If this leaky setting cannot rank held-out mutants either, the mutation-level
    signal is at the measurement noise floor and no zero-shot method can succeed.
    """
    from src.mechanism_v2.feature_store import FeatureStore
    store = FeatureStore()
    aligned = store.rows
    rng = np.random.default_rng(seed)
    held = np.zeros(len(aligned), bool)
    for _, index in aligned.groupby('decision_set_id', sort=True).indices.items():
        index = np.asarray(index, int)
        if len(index) < 4:
            continue
        pick = rng.permutation(index)[: len(index) // 2]
        held[pick] = True
    train_idx = np.flatnonzero(~held)
    held_idx = np.flatnonzero(held)

    out = {'train_rows': int(len(train_idx)), 'held_rows': int(len(held_idx)),
           'design': ('half the candidates of each decision set are held out; the other half of '
                      'the SAME parent and SAME assay is used for training. This is deliberately '
                      'leaky and is a ceiling diagnostic only.')}
    for family in ('M0', 'M4'):
        x, columns = store.matrix(family)
        frame = store.train_frame(train_idx)
        model = PairedRanker(RankConfig(ridge=0.01, nuisance='none', pairs_per_set=128,
                                        seed=int(seed), max_iterations=400, tolerance=1e-8))
        model.fit(x[train_idx], frame, columns)
        score = model.predict(x[held_idx])
        metrics, _ = decision_metrics(aligned.iloc[held_idx], score)
        out[family] = context_mean(metrics)
    out['rank_gain_M4_vs_M0'] = out['M4']['rank'] - out['M0']['rank']
    out['regret_gain_M4_vs_M0'] = out['M0']['regret'] - out['M4']['regret']
    return out


def _all_feature_matrix(store):
    """Every available block at once, plus the frozen random-kmer control block."""
    blocks, columns = [], []
    for name in ('geometry', 'rbp_delta', 'bert_pooled_delta', 'structure_delta',
                 'processing_delta', 'motif_delta', 'trans_aligned'):
        value = store.blocks[name]
        array = np.asarray(value if name in {'geometry', 'trans_aligned'}
                           else value[store.feature_rows], float)
        blocks.append(array)
        columns += [f'{name}:{j:04d}' for j in range(array.shape[1])]
    manifest = json.loads((ROOT / 'results/mechanism_v2/features'
                           / 'random_kmer_delta_manifest.json').read_text())
    kmer = np.load(ROOT / manifest['path'], allow_pickle=False)
    kmer = np.asarray(kmer)[store.feature_rows]
    blocks.append(kmer)
    columns += [f'random_kmer:{j:04d}' for j in range(kmer.shape[1])]
    return np.column_stack(blocks).astype(np.float64), columns


def capacity_ceiling(seed=20260912):
    """Most generous possible leaky fit: all blocks, linear ranker and a nonlinear model.

    This bounds what ANY selector built on these representations can add over
    geometry on this benchmark, because it is allowed to train on sibling mutants
    of the same parent in the same assay.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor

    from src.mechanism_v2.feature_store import FeatureStore
    store = FeatureStore()
    aligned = store.rows
    rng = np.random.default_rng(seed)
    held = np.zeros(len(aligned), bool)
    for _, index in aligned.groupby('decision_set_id', sort=True).indices.items():
        index = np.asarray(index, int)
        if len(index) < 4:
            continue
        held[rng.permutation(index)[: len(index) // 2]] = True
    train_idx = np.flatnonzero(~held)
    held_idx = np.flatnonzero(held)

    x_all, columns = _all_feature_matrix(store)
    geometry, geometry_columns = store.matrix('M0')
    out = {'features': len(columns), 'train_rows': int(len(train_idx)),
           'held_rows': int(len(held_idx))}

    linear = PairedRanker(RankConfig(ridge=0.01, nuisance='none', pairs_per_set=128,
                                      seed=int(seed), max_iterations=400, tolerance=1e-8))
    linear.fit(x_all[train_idx], store.train_frame(train_idx), columns)
    metrics, _ = decision_metrics(aligned.iloc[held_idx], linear.predict(x_all[held_idx]))
    out['linear_all_features'] = context_mean(metrics)

    target = aligned.localization_effect.to_numpy(float)
    forest = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06,
                                           max_depth=6, random_state=int(seed))
    forest.fit(x_all[train_idx], target[train_idx])
    metrics, _ = decision_metrics(aligned.iloc[held_idx], forest.predict(x_all[held_idx]))
    out['nonlinear_all_features'] = context_mean(metrics)

    base = PairedRanker(RankConfig(ridge=0.01, nuisance='none', pairs_per_set=128,
                                    seed=int(seed), max_iterations=400, tolerance=1e-8))
    base.fit(geometry[train_idx], store.train_frame(train_idx), geometry_columns)
    metrics, _ = decision_metrics(aligned.iloc[held_idx], base.predict(geometry[held_idx]))
    out['geometry_baseline'] = context_mean(metrics)

    for key in ('linear_all_features', 'nonlinear_all_features'):
        out[f'{key}_rank_gain'] = out[key]['rank'] - out['geometry_baseline']['rank']
        out[f'{key}_regret_gain'] = out['geometry_baseline']['regret'] - out[key]['regret']
    out['gate_g1_requires'] = {'rank_gain_minimum': 0.020, 'regret_gain_minimum': 0.010}
    out['interpretation'] = (
        'These are leaky upper bounds, not zero-shot results. A zero-shot selector cannot '
        'reasonably be expected to exceed the leaky ceiling on the same benchmark.')
    return out


def run_diagnostics():
    from .evaluate import load_rows
    rows, _ = load_rows()
    record = {
        'format': 'mechanism_v3_ceiling_diagnostics_v1',
        'status': 'diagnostic only; cannot produce any verdict',
        'mechanism_v2_verdict_preserved': 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS',
        'assay_reliability': assay_reliability(rows),
        'grammar_informativeness': grammar_informativeness(rows),
        'leaky_within_parent_ceiling': leaky_within_parent_ceiling(rows),
        'capacity_ceiling_all_features': capacity_ceiling(),
    }
    write_json(DIAGNOSTICS, record)
    print(json.dumps({k: v for k, v in record.items()
                      if k not in {'format', 'status', 'mechanism_v2_verdict_preserved'}},
                     indent=2, default=float), flush=True)
    return record


if __name__ == '__main__':
    run_diagnostics()
