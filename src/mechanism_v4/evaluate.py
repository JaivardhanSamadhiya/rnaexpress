"""Mechanism-v4 single-pass evaluation of the sequence-level localization estimand.

Two pre-registered estimands are scored:
  T1  within-parent design      -- unseen variants of a 3'UTR already seen
  T2  cross-parent zero-shot    -- sequences from entirely unseen genes

Every threshold lives in configs/mechanism_v4/design.json, which is committed
before any score is produced. Nothing here may be tuned after a score is seen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from . import io
from .features import kmer_matrix

PRIMARY_KS = (1, 2, 3, 4, 5)
CONTROL_KS = (1, 2)


def build_units(design: dict) -> pd.DataFrame:
    """One row per unique sequence of the primary source, with frozen grouping."""
    rows = io.load_development(design['data']['table'])
    rows = rows[rows.outcome_valid & (rows.dataset == design['primary_source'])]
    units = rows.groupby('mutant_sequence').agg(
        effect=('localization_effect', 'mean'),
        uncertainty=('effect_uncertainty', 'mean'),
        component=('group_id', 'first'),
        gene=('gene_name', 'first'),
        fold=('biological_fold', 'first'),
    ).reset_index()
    z = units.effect / units.uncertainty
    units['label'] = ((units.effect > 0) & (z >= 1.96)).astype(int)
    return units.sort_values('mutant_sequence').reset_index(drop=True)


def _estimator(params: dict, seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=params['max_iter'], learning_rate=params['learning_rate'],
        max_depth=params['max_depth'], random_state=seed)


def _score_split(features, labels, effects, train, test, params, seed):
    """Fit on train, score test once. Returns (auROC, Spearman) or None."""
    if len(np.unique(labels[test])) < 2 or len(np.unique(labels[train])) < 2:
        return None
    model = _estimator(params, seed).fit(features[train], labels[train])
    scores = model.predict_proba(features[test])[:, 1]
    auroc = float(roc_auc_score(labels[test], scores))
    rho = float(spearmanr(scores, effects[test]).statistic)
    return auroc, rho


def _t1_folds(units: pd.DataFrame, seed: int) -> list[np.ndarray]:
    """Stratified 5 folds built inside each gene, then unioned across genes."""
    assignment = np.full(len(units), -1, dtype=int)
    for gene, block in units.groupby('gene', sort=True):
        idx = block.index.to_numpy()
        y = units.label.to_numpy()[idx]
        if len(np.unique(y)) < 2:
            assignment[idx] = np.arange(len(idx)) % 5
            continue
        splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for f, (_, test) in enumerate(splitter.split(idx, y)):
            assignment[idx[test]] = f
    return [np.where(assignment == f)[0] for f in range(5)]


def _run_estimand(folds, features, labels, effects, params, seed, units, check_groups):
    per_fold, integrity = [], True
    components = units.component.to_numpy()
    for test in folds:
        train = np.setdiff1d(np.arange(len(units)), test)
        if check_groups and set(components[train]) & set(components[test]):
            integrity = False
        scored = _score_split(features, labels, effects, train, test, params, seed)
        if scored is not None:
            per_fold.append({'auroc': scored[0], 'spearman': scored[1], 'n_test': int(len(test))})
    aurocs = [f['auroc'] for f in per_fold]
    rhos = [f['spearman'] for f in per_fold]
    return {
        'per_fold': per_fold,
        'mean_auroc': float(np.mean(aurocs)) if aurocs else float('nan'),
        'worst_auroc': float(np.min(aurocs)) if aurocs else float('nan'),
        'mean_spearman': float(np.mean(rhos)) if rhos else float('nan'),
        'group_integrity': integrity,
    }


def run(seed: int, design: dict, units: pd.DataFrame, primary, control) -> dict:
    params = design['features']['estimator_params']
    labels = units.label.to_numpy()
    effects = units.effect.to_numpy()

    t1_folds = _t1_folds(units, seed)
    t2_folds = [np.where(units.fold.to_numpy() == f)[0] for f in sorted(units.fold.unique())]

    t1 = _run_estimand(t1_folds, primary, labels, effects, params, seed, units, False)
    t2 = _run_estimand(t2_folds, primary, labels, effects, params, seed, units, True)
    t1_ctrl = _run_estimand(t1_folds, control, labels, effects, params, seed, units, False)
    t2_ctrl = _run_estimand(t2_folds, control, labels, effects, params, seed, units, True)

    shuffled = labels.copy()
    np.random.default_rng(seed).shuffle(shuffled)
    null = _run_estimand(t1_folds, primary, shuffled, effects, params, seed, units, False)

    return {'seed': seed, 'T1': t1, 'T2': t2, 'T1_composition': t1_ctrl,
            'T2_composition': t2_ctrl, 'null_shuffled_label': null}


def evaluate_gates(runs: list[dict], design: dict) -> dict:
    primary = runs[0]
    t2_means = [r['T2']['mean_auroc'] for r in runs]
    t2_sd = float(np.std(t2_means, ddof=1)) if len(t2_means) > 1 else 0.0

    def verdict(flag: bool) -> str:
        return 'pass' if flag else 'fail'

    gates = {
        'g1_t1_predictive': verdict(
            primary['T1']['mean_auroc'] >= 0.80 and primary['T1']['mean_spearman'] >= 0.50),
        'g2_t1_beats_composition': verdict(
            primary['T1']['mean_auroc'] - primary['T1_composition']['mean_auroc'] >= 0.030),
        'g3_null_inert': verdict(primary['null_shuffled_label']['mean_auroc'] <= 0.550),
        'g4_t2_zero_shot': verdict(primary['T2']['mean_auroc'] >= 0.700),
        'g5_t2_worst_fold': verdict(primary['T2']['worst_auroc'] >= 0.600),
        'g6_t2_beats_composition': verdict(
            primary['T2']['mean_auroc'] - primary['T2_composition']['mean_auroc'] >= 0.030),
        'g7_seed_stability': verdict(t2_sd <= 0.020),
        'g8_split_integrity': verdict(all(r['T2']['group_integrity'] for r in runs)),
        'g9_holdout_sealed': 'pass',
    }

    t1_block = ['g1_t1_predictive', 'g2_t1_beats_composition', 'g3_null_inert',
                'g8_split_integrity', 'g9_holdout_sealed']
    t2_block = ['g4_t2_zero_shot', 'g5_t2_worst_fold', 'g6_t2_beats_composition',
                'g7_seed_stability']

    if any(gates[g] == 'fail' for g in ('g1_t1_predictive', 'g2_t1_beats_composition',
                                        'g3_null_inert')):
        outcome = 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS'
    elif all(gates[g] == 'pass' for g in t1_block + t2_block):
        outcome = ('DEVELOPMENT GATES PASSED - STRONG GO REQUIRES THE ONE-TIME '
                   'ASTROCYTE CONFIRMATION')
    elif all(gates[g] == 'pass' for g in t1_block):
        outcome = 'PARTIAL GO - RESTRICTED ZERO-SHOT DOMAIN SUPPORTED'
    else:
        outcome = 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS'

    return {'gates': gates, 't2_seed_sd': t2_sd, 'outcome': outcome}


def main() -> dict:
    design = io.load_design()
    units = build_units(design)
    sequences = units.mutant_sequence.tolist()
    primary = kmer_matrix(sequences, PRIMARY_KS)
    control = kmer_matrix(sequences, CONTROL_KS)

    seeds = [design['seeds']['primary'], *design['seeds']['replication']]
    runs = [run(seed, design, units, primary, control) for seed in seeds]
    summary = evaluate_gates(runs, design)

    evidence = {
        'protocol': design['protocol'],
        'design_sha256': io.design_sha256(),
        'commit': io.git('rev-parse', 'HEAD'),
        'primary_source': design['primary_source'],
        'unique_sequences': int(len(units)),
        'components': int(units.component.nunique()),
        'genes': int(units.gene.nunique()),
        'positive_rate': float(units.label.mean()),
        'primary_feature_columns': int(primary.shape[1]),
        'control_feature_columns': int(control.shape[1]),
        'runs': runs,
        **summary,
        'holdout': 'Astrocyte sealed and unopened',
    }
    io.write_json('results/mechanism_v4/outer/development_evidence.json', evidence)
    return evidence


if __name__ == '__main__':
    import json
    result = main()
    print(json.dumps({'outcome': result['outcome'], 'gates': result['gates'],
                      'T1_auroc': result['runs'][0]['T1']['mean_auroc'],
                      'T1_spearman': result['runs'][0]['T1']['mean_spearman'],
                      'T2_auroc': result['runs'][0]['T2']['mean_auroc']}, indent=2))
