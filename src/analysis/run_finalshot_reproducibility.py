"""Repeat one complete frozen outer refit without changing archived models."""
from __future__ import annotations

import gc
import argparse
from contextlib import nullcontext
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits, threadpool_info

from src.analysis.run_finalshot_direct_models import latent_rank_target, sha256
from src.analysis.run_finalshot_representation_benchmark import latent_rank_target as rank_target
from src.modeling.finalshot_models import FinalShotFeatureStore, fit_sparse_group
from src.modeling.v4_decision_models import source_set_weights

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'


def main(blas_threads: int | None = 1) -> None:
    rows_path = ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz'
    rows = pd.read_csv(rows_path)
    manifest = json.loads((OUT / 'rbp_feature_matrix_manifest.json').read_text())
    matrix = ROOT / manifest['matrix_path']
    assert sha256(matrix) == manifest['matrix_sha256']
    train = np.flatnonzero(rows.biological_fold.to_numpy() != 0)
    test = np.flatnonzero(rows.biological_fold.to_numpy() == 0)
    assert not set(rows.iloc[train].biological_unit) & set(rows.iloc[test].biological_unit)
    target = latent_rank_target(rows)[train]
    geometry_target = rank_target(rows)[train]
    weights = source_set_weights(rows.iloc[train])
    store = FinalShotFeatureStore(rows, matrix, OUT / 'rbp_feature_dictionary.csv',
                                 OUT / 'rbp_expression_proxy.csv')
    records = []
    for family in ('M0', 'M1', 'M2'):
        xtrain, layout = store.materialize(train, family)
        xtest, _ = store.materialize(test, family)
        if family != 'M0':
            with np.load(OUT / f'nested_direct/{family}_outer_fold_0.npz', allow_pickle=False) as a:
                metadata = json.loads(str(a['metadata_json'].item()))
                archived = a['prediction'].copy()
                assert np.array_equal(test, a['test_indices'])
        else:
            archived = pd.read_csv(OUT / 'm0_m3_predictions.csv.gz').M0_geometry.to_numpy()[test]
        predictions, convergence, iterations = [], [], []
        for repeat in range(2):
            if family == 'M0':
                scaler = StandardScaler().fit(xtrain)
                model = Ridge(alpha=100., solver='lsqr', tol=1e-6).fit(
                    scaler.transform(xtrain), geometry_target, sample_weight=weights)
                pred = model.predict(scaler.transform(xtest))
                converged = True
                iterations.append(int(np.asarray(model.n_iter_).reshape(-1)[0]))
            else:
                model = fit_sparse_group(xtrain, target, weights, layout,
                    metadata['selected_penalty'], metadata['selected_group_fraction'])
                pred = model.predict(xtest)
                converged = bool(model.converged)
                iterations.append(int(model.iterations))
            assert np.isfinite(pred).all()
            predictions.append(pred)
            convergence.append(converged)
            print(f'{family} outer=0 repeat={repeat + 1} converged={converged}', flush=True)
        difference = float(np.max(np.abs(predictions[0].astype(float)-predictions[1].astype(float))))
        records.append({'family': family, 'outer_fold': 0, 'train_rows': len(train),
            'test_rows': len(test), 'unit_overlap': 0, 'converged': all(convergence),
            'iterations': iterations,
            'repeat_max_absolute_difference': difference,
            'archived_max_absolute_difference': float(np.max(np.abs(predictions[0]-archived))),
            'repeat_pass_1e_minus_8': all(convergence) and difference <= 1e-8})
        del xtrain, xtest, predictions, model
        gc.collect()
    result = {'rows_sha256': sha256(rows_path), 'matrix_sha256': manifest['matrix_sha256'],
              'python': platform.python_version(), 'blas_thread_limit': blas_threads,
              'threadpools': threadpool_info(),
              'scope': 'Two full refits of fixed outer fold 0 with its archived inner-selected recipe; no selection repeated or changed.',
              'records': records, 'deterministic_smoke_pass': all(r['repeat_pass_1e_minus_8'] for r in records)}
    label = 'default' if blas_threads is None else str(blas_threads)
    (OUT / f'deterministic_reproducibility_threads_{label}.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--blas-threads', type=int, default=1, help='0 preserves native runtime settings')
    args = parser.parse_args()
    threads = args.blas_threads or None
    with threadpool_limits(limits=threads) if threads is not None else nullcontext():
        main(threads)
