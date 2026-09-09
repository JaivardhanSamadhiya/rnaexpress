"""Frozen held-biological-fold nuisance probes; never select localization models."""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import f1_score, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from src.analysis.run_finalshot_direct_models import sha256
from src.modeling.v4_decision_models import geometry_features, source_set_weights

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'


def main() -> None:
    rows_path = ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz'
    rows = pd.read_csv(rows_path)
    manifest = json.loads((OUT / 'rbp_feature_matrix_manifest.json').read_text())
    matrix_path = ROOT / manifest['matrix_path']
    assert sha256(matrix_path) == manifest['matrix_sha256']
    dictionary = pd.read_csv(OUT / 'rbp_feature_dictionary.csv')
    matrix = np.load(matrix_path, mmap_mode='r')
    columns = dictionary.loc[dictionary.role.eq('delta'), 'column_index'].to_numpy(int)
    assert len(columns) == 103 * 7
    feature_rows = rows.feature_row.to_numpy(int)
    # The frozen geometry includes the nuisance targets themselves. Its high
    # probe scores are positive controls, not independent scientific evidence.
    designs = {'delta_rbp': np.asarray(matrix[feature_rows][:, columns]),
               'geometry': geometry_features(rows, categories=True)}
    y_size = np.log1p(rows.edit_cost.to_numpy(float))
    y_class = rows.intervention_class.to_numpy(str)
    labels = sorted(set(y_class))
    folds = rows.biological_fold.to_numpy(int)
    records, audits = [], []
    for representation, features in designs.items():
        size_pred = np.full(len(rows), np.nan)
        class_pred = np.full(len(rows), '', dtype=object)
        for fold in range(5):
            train, test = folds != fold, folds == fold
            assert not (set(rows.loc[train, 'biological_unit']) & set(rows.loc[test, 'biological_unit']))
            scaler = StandardScaler().fit(features[train])
            x_train, x_test = scaler.transform(features[train]), scaler.transform(features[test])
            weights = source_set_weights(rows.loc[train])
            ridge = Ridge(alpha=100., solver='lsqr', tol=1e-6)
            ridge.fit(x_train, y_size[train], sample_weight=weights)
            size_pred[test] = ridge.predict(x_test)
            # Numerical cap is fixed before probe results; no C/model search.
            logistic = LogisticRegression(C=0.1, class_weight='balanced', solver='lbfgs',
                                          max_iter=2000, tol=1e-4, random_state=42017)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always', ConvergenceWarning)
                logistic.fit(x_train, y_class[train], sample_weight=weights)
            class_pred[test] = logistic.predict(x_test)
            audits.append({'representation': representation, 'fold': fold,
                           'train_rows': int(train.sum()), 'test_rows': int(test.sum()),
                           'unit_overlap': 0, 'logistic_iterations': int(logistic.n_iter_.max()),
                           'converged': not any(issubclass(w.category, ConvergenceWarning) for w in caught),
                           'unseen_test_classes': sorted(set(y_class[test]) - set(y_class[train]))})
            print(json.dumps(audits[-1]), flush=True)
        assert np.isfinite(size_pred).all() and np.all(class_pred != '')
        for source in sorted(rows.dataset.unique()):
            mask = rows.dataset.eq(source).to_numpy()
            weights = source_set_weights(rows.loc[mask])
            records.append({'representation': representation, 'dataset': source,
                            'weighted_size_r2': float(r2_score(y_size[mask], size_pred[mask], sample_weight=weights)),
                            'class_macro_f1': float(f1_score(y_class[mask], class_pred[mask],
                                labels=labels, average='macro', sample_weight=weights, zero_division=0)),
                            'class_labels': labels})
        pd.DataFrame({'row_index': np.arange(len(rows)), 'biological_fold': folds,
                      'predicted_log1p_edit_cost': size_pred, 'predicted_class': class_pred}).to_csv(
            OUT / f'shortcut_predictions_{representation}.csv.gz', index=False,
            compression={'method': 'gzip', 'mtime': 0})
    summary = {'phase': 'Frozen nuisance probes', 'rows_sha256': sha256(rows_path),
               'matrix_sha256': manifest['matrix_sha256'], 'delta_feature_count': len(columns),
               'ridge_alpha': 100., 'logistic_C': 0.1, 'class_weight': 'balanced',
               'all_probes_converged': all(a['converged'] for a in audits),
               'geometry_contains_probe_targets': True,
               'macro_f1_label_universe': labels, 'source_metrics': records,
               'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    (OUT / 'shortcut_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    pd.DataFrame(audits).to_csv(OUT / 'shortcut_fold_audit.csv', index=False)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
