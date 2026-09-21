"""Outcome-descriptive inventory and synthetic control checks; no selector fit."""
from .common import ROOT, load_certified, sha256, write_json
import json
import subprocess
import sys
import numpy as np

def run():
    rng = np.random.default_rng(20260921)
    x = rng.normal(size=(300, 84))
    basis = np.random.default_rng(20260912).normal(size=(84, 84))
    z = x @ basis
    reconstructed = np.linalg.solve(basis.T, z.T).T
    w = rng.normal(size=84)
    projected_w = np.linalg.solve(basis, w)
    # Orthogonal reparameterization is exactly invariant for an L2 linear model.
    q, _ = np.linalg.qr(basis)
    alpha = 1.0
    y = x @ w + rng.normal(size=len(x))
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(84), x.T @ y)
    beta_q = np.linalg.solve((x @ q).T @ (x @ q) + alpha * np.eye(84),
                             (x @ q).T @ y)
    projection = {
        'width': 84, 'rank': int(np.linalg.matrix_rank(basis)),
        'condition_number': float(np.linalg.cond(basis)),
        'max_feature_reconstruction_error': float(np.max(abs(x - reconstructed))),
        'max_linear_score_reparameterization_error': float(np.max(abs(x @ w - z @ projected_w))),
        'orthogonal_ridge_prediction_max_error': float(np.max(abs(x @ beta - (x @ q) @ beta_q))),
        'interpretation': 'A square full-rank random projection retains all input information. '
            'A nonorthogonal projection changes the L2 penalty geometry; it is not '
            'a mechanism-destroying null and does not isolate AU composition.'}
    assert projection['rank'] == 84
    assert projection['max_feature_reconstruction_error'] < 1e-8
    assert projection['orthogonal_ridge_prediction_max_error'] < 1e-8

    rows = load_certified()
    inventories = []
    for (source, cell, reporter), g in rows.groupby(['dataset', 'cell_type', 'reporter'], dropna=False):
        uncertainty = g.effect_uncertainty.to_numpy(float)
        # This deliberately reports no new model/outcome correlations.
        inventories.append({
            'source': str(source), 'cell': str(cell), 'reporter': str(reporter),
            'rows': len(g), 'decisions': int(g.decision_set_id.nunique()),
            'genes': int(g.gene_name.nunique()), 'parents': int(g.parent_id.nunique()),
            'finite_uncertainty_fraction': float(np.isfinite(uncertainty).mean()),
            'nonpositive_finite_uncertainty_rows': int((np.isfinite(uncertainty) & (uncertainty <= 0)).sum()),
            'uncertainty_semantics': sorted(g.uncertainty_semantics.astype(str).unique()),
            'outcome_semantics': sorted(g.outcome_semantics.astype(str).unique()),
        })
    # Audit whether sequence-only aggregation conflates legal contexts/parents.
    aggregation = []
    for source, g in rows.groupby('dataset'):
        by_sequence = g.groupby('mutant_sequence')
        aggregation.append({'source': source, 'unique_mutants': int(by_sequence.ngroups),
            'mutants_multiple_parents': int((by_sequence.parent_sequence.nunique() > 1).sum()),
            'mutants_multiple_cells': int((by_sequence.cell_type.nunique() > 1).sum()),
            'mutants_multiple_reporters': int((by_sequence.reporter.nunique() > 1).sum()),
            'mutants_multiple_folds': int((by_sequence.biological_fold.nunique() > 1).sum())})
    old_path = ROOT / 'results/mechanism_v3/diagnostics/ceiling_analysis.json'
    old = json.loads(old_path.read_text())
    selected = {k: old['assay_reliability'][k] for k in (
        'mean_within_decision_reliability', 'noisy_oracle_ceiling',
        'headroom_rank_ceiling_minus_baseline', 'headroom_regret_baseline_minus_ceiling')}
    y_observed = rng.normal(size=100)
    missing_unc = np.full(100, np.nan)
    pseudo_prediction = y_observed + rng.normal(0, np.where(np.isfinite(missing_unc), missing_unc, 0))
    assert np.array_equal(y_observed, pseudo_prediction)
    report = {
        'status': 'interpretation audit, not biological discovery or new verdict',
        'python': sys.executable,
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'script_sha256': sha256(__file__),
        'certified_input_sha256': sha256(ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz'),
        'projection_check': projection,
        'context_inventory': inventories,
        'sequence_aggregation_inventory': aggregation,
        'existing_v3_diagnostics': selected,
        'missing_uncertainty_synthetic_prediction_equals_observed': bool(np.array_equal(y_observed, pseudo_prediction)),
        'conclusions': [
            'Finite-model performance does not upper-bound every possible model.',
            'Averaged per-decision reliability is not the fraction of all benchmark variance that is noise.',
            'Raw-ratio diagnostic SE is not necessarily the SE of WT-normalized author outcomes.',
            'Adding noise to observed outcomes and using zero noise when missing does not simulate an established latent-truth oracle.',
            'An information-preserving kmer basis change cannot show that higher-order sequence information is absent.',
            'Sequence-only aggregation may merge contexts and parents; inspect the inventory before interpreting variant-level direction.',
            'These limitations do not reverse any frozen failed gate.'
        ],
        'sealed_data_accessed': False, 'selector_fits': 0,
    }
    out = ROOT / 'results/research_20260921/interpretation_audit.json'
    write_json(out, report)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    run()
