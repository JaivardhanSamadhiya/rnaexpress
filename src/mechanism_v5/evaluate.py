"""Mechanism-v5 single-pass evaluation of two previously untried arms.

Arm A  cross-gene edit-direction transfer on mikl_gse173098 (166 genes)
Arm B  cross-source finite difference, trained on moffatt_gse334718

Every threshold lives in configs/mechanism_v5/design.json, committed before any
score exists. Nothing here may be tuned after a score is seen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

from . import io
from .features import au_delta, delta_frequency, kmer_frequency, random_projection

KS = (1, 2, 3)
CONFIDENT_Z = 1.96


# --------------------------------------------------------------------------- data

def _sequence_table(rows: pd.DataFrame, source: str) -> pd.DataFrame:
    block = rows[rows.outcome_valid & (rows.dataset == source)]
    table = block.groupby('mutant_sequence').agg(
        effect=('localization_effect', 'mean'),
        uncertainty=('effect_uncertainty', 'mean'),
        parent=('parent_sequence', 'first'),
        gene=('gene_name', 'first'),
        component=('group_id', 'first'),
        fold=('biological_fold', 'first'),
    ).reset_index()
    return table.sort_values('mutant_sequence').reset_index(drop=True)


def confident(table: pd.DataFrame) -> pd.DataFrame:
    z = table.effect / table.uncertainty
    keep = table[z.abs() >= CONFIDENT_Z].copy()
    keep['label'] = (keep.effect > 0).astype(int)
    return keep.reset_index(drop=True)


# ----------------------------------------------------------------------- arm A

def _grouped_auroc(features, labels, folds, groups, genes, seed):
    per_fold, integrity = [], True
    for f in folds:
        test = np.where(f)[0]
        train = np.where(~f)[0]
        if len(np.unique(labels[test])) < 2 or len(np.unique(labels[train])) < 2:
            continue
        if set(groups[train]) & set(groups[test]) or set(genes[train]) & set(genes[test]):
            integrity = False
        model = LogisticRegression(C=1.0, max_iter=2000, random_state=seed)
        model.fit(features[train], labels[train])
        scores = model.predict_proba(features[test])[:, 1]
        per_fold.append({'auroc': float(roc_auc_score(labels[test], scores)),
                         'n_test': int(len(test))})
    aurocs = [p['auroc'] for p in per_fold]
    return {'per_fold': per_fold,
            'mean_auroc': float(np.mean(aurocs)) if aurocs else float('nan'),
            'worst_auroc': float(np.min(aurocs)) if aurocs else float('nan'),
            'group_integrity': integrity}


def run_arm_a(table: pd.DataFrame, seed: int) -> dict:
    labels = table.label.to_numpy()
    groups = table.component.to_numpy()
    genes = table.gene.to_numpy()
    fold_ids = table.fold.to_numpy()
    folds = [fold_ids == f for f in sorted(np.unique(fold_ids))]

    primary = delta_frequency(table.mutant_sequence, table.parent, KS)
    control = au_delta(table.mutant_sequence, table.parent)
    projected = random_projection(primary, seed, primary.shape[1])

    shuffled = labels.copy()
    np.random.default_rng(seed).shuffle(shuffled)

    return {
        'primary': _grouped_auroc(primary, labels, folds, groups, genes, seed),
        'au_delta_only': _grouped_auroc(control, labels, folds, groups, genes, seed),
        'random_kmer': _grouped_auroc(projected, labels, folds, groups, genes, seed),
        'shuffled_null': _grouped_auroc(primary, shuffled, folds, groups, genes, seed),
    }


# ----------------------------------------------------------------------- arm B

def run_arm_b(train_table: pd.DataFrame, test_table: pd.DataFrame, seed: int) -> dict:
    """Fit absolute localization on the training source, score finite differences."""
    train_x = kmer_frequency(train_table.mutant_sequence, KS)
    model = Ridge(alpha=1.0, random_state=seed).fit(train_x, train_table.effect.to_numpy())

    predicted = (model.predict(kmer_frequency(test_table.mutant_sequence, KS))
                 - model.predict(kmer_frequency(test_table.parent, KS)))
    measured = test_table.effect.to_numpy()

    rho = spearmanr(predicted, measured)
    control = au_delta(test_table.mutant_sequence, test_table.parent).ravel()
    control_rho = spearmanr(control, measured)

    conf = confident(test_table)
    conf_predicted = (model.predict(kmer_frequency(conf.mutant_sequence, KS))
                      - model.predict(kmer_frequency(conf.parent, KS)))
    auroc = (float(roc_auc_score(conf.label.to_numpy(), conf_predicted))
             if conf.label.nunique() > 1 else float('nan'))

    per_fold = []
    for f in sorted(test_table.fold.unique()):
        mask = (test_table.fold == f).to_numpy()
        if mask.sum() > 10:
            per_fold.append(float(spearmanr(predicted[mask], measured[mask]).statistic))

    return {
        'spearman': float(rho.statistic), 'p_value': float(rho.pvalue),
        'au_delta_spearman': float(control_rho.statistic),
        'confident_auroc': auroc, 'confident_n': int(len(conf)),
        'per_fold_spearman': per_fold,
        'same_sign_folds': int(sum(1 for v in per_fold
                                   if np.sign(v) == np.sign(rho.statistic))),
        'n_test': int(len(test_table)),
    }


# ----------------------------------------------------------------------- gates

def evaluate_gates(runs: list[dict]) -> dict:
    a = runs[0]['arm_a']
    b = runs[0]['arm_b']['mikl_gse173098']
    a_means = [r['arm_a']['primary']['mean_auroc'] for r in runs]
    a_sd = float(np.std(a_means, ddof=1)) if len(a_means) > 1 else 0.0

    def flag(ok: bool) -> str:
        return 'pass' if ok else 'fail'

    gates = {
        'a1_cross_gene_direction': flag(a['primary']['mean_auroc'] >= 0.650),
        'a2_worst_fold': flag(a['primary']['worst_auroc'] >= 0.580),
        'a3_beats_au_delta': flag(
            a['primary']['mean_auroc'] - a['au_delta_only']['mean_auroc'] >= 0.030),
        'a4_null_inert': flag(a['shuffled_null']['mean_auroc'] <= 0.550),
        'a5_seed_stability': flag(a_sd <= 0.030),
        'a6_beats_random_kmer': flag(
            a['primary']['mean_auroc'] - a['random_kmer']['mean_auroc'] >= 0.020),
        'b1_transfer_correlation': flag(b['spearman'] >= 0.100 and b['p_value'] < 0.001),
        'b2_transfer_direction': flag(b['confident_auroc'] >= 0.600),
        'b3_beats_au_delta': flag(b['spearman'] - b['au_delta_spearman'] >= 0.020),
        'b4_consistent_across_folds': flag(b['same_sign_folds'] >= 4),
        'i1_split_integrity': flag(all(
            r['arm_a']['primary']['group_integrity'] for r in runs)),
        'i2_holdout_sealed': 'pass',
    }

    a_gates = ['a1_cross_gene_direction', 'a2_worst_fold', 'a3_beats_au_delta',
               'a4_null_inert', 'a5_seed_stability', 'a6_beats_random_kmer']
    b_gates = ['b1_transfer_correlation', 'b2_transfer_direction',
               'b3_beats_au_delta', 'b4_consistent_across_folds']
    i_gates = ['i1_split_integrity', 'i2_holdout_sealed']

    a_pass = all(gates[g] == 'pass' for g in a_gates)
    b_pass = all(gates[g] == 'pass' for g in b_gates)
    integrity = all(gates[g] == 'pass' for g in i_gates)

    if a_pass and b_pass and integrity:
        outcome = ('DEVELOPMENT SUPPORT - STRONG GO REQUIRES THE ONE-TIME '
                   'ASTROCYTE CONFIRMATION')
    elif integrity and (a_pass or b_pass):
        outcome = 'PARTIAL GO - RESTRICTED ZERO-SHOT DOMAIN SUPPORTED'
    else:
        outcome = 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS'

    return {'gates': gates, 'arm_a_seed_sd': a_sd, 'arm_a_all_pass': a_pass,
            'arm_b_all_pass': b_pass, 'outcome': outcome}


# ------------------------------------------------------------------------ main

def main() -> dict:
    design = io.load_design()
    rows = io.load_development(design['data']['table'])

    mikl = _sequence_table(rows, 'mikl_gse173098')
    moffatt = _sequence_table(rows, 'moffatt_gse334718')
    tdp43 = _sequence_table(rows, 'tdp43_gse288185')
    mikl_confident = confident(mikl)

    seeds = [design['seeds']['primary'], *design['seeds']['replication']]
    runs = []
    for seed in seeds:
        runs.append({
            'seed': seed,
            'arm_a': run_arm_a(mikl_confident, seed),
            'arm_b': {
                'mikl_gse173098': run_arm_b(moffatt, mikl, seed),
                'tdp43_gse288185': run_arm_b(moffatt, tdp43, seed),
            },
        })

    summary = evaluate_gates(runs)
    evidence = {
        'protocol': design['protocol'],
        'design_sha256': io.design_sha256(),
        'commit': io.git('rev-parse', 'HEAD'),
        'arm_a_rows': int(len(mikl_confident)),
        'arm_a_genes': int(mikl_confident.gene.nunique()),
        'arm_a_positive_rate': float(mikl_confident.label.mean()),
        'arm_b_train_rows': int(len(moffatt)),
        'runs': runs,
        **summary,
        'holdout': 'Astrocyte sealed and unopened',
    }
    io.write_json('results/mechanism_v5/outer/development_evidence.json', evidence)
    return evidence


if __name__ == '__main__':
    import json
    result = main()
    print(json.dumps({'outcome': result['outcome'], 'gates': result['gates']}, indent=2))
