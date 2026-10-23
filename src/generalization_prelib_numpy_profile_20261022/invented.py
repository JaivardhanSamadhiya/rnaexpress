"""Invented matrices only; no project feature, sequence or outcome loaders."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

from src.generalization_pum_process_probe_20261021 import headless

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/generalization_prelib_numpy_profile_20261022'


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def run():
    started = time.monotonic()
    assert sys.implementation.cache_tag == 'cpython-312'
    assert os.environ.get('PYTHONUTF8') == '1'
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == '2'
    # This public runtime receipt is metadata; no project numerical array is read.
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    launcher.clean_import_state()
    runtime_path = launcher.RUNTIME_RECEIPT
    runtime_bytes = runtime_path.read_bytes()
    import subprocess
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + runtime_path.relative_to(ROOT).as_posix()], cwd=ROOT
    ) == runtime_bytes
    runtime = json.loads(runtime_bytes)
    assert Path(sys.executable).resolve() == Path(runtime['python_executable']).resolve()
    for path, want in runtime['python_native_files'].items():
        assert sha(path) == want, path
    launcher.select_prefix()
    np = importlib.import_module('numpy')
    native_proof = launcher.numpy_proof(np, runtime)

    # Import defines pure kernels/contracts. Do not call any biological stage or
    # its admission routine, and never replace its original fresh() callback.
    from src.generalization_prelib_pooled_lineage_20261009 import pipeline
    analytic = pipeline.numerical_contract(np)
    rng = np.random.RandomState(20261022)
    x = rng.normal(0.0, 0.01, size=(4054, 84))
    x[rng.random_sample(x.shape) < 0.92] = 0.0
    x[:, 83] = 0.0
    synthetic_scalar = rng.normal(size=(4054, 1))
    matrices = {
        'invented84': x,
        'invented85': np.concatenate((x, synthetic_scalar), axis=1),
        'invented_duplicate85': np.concatenate((x, x[:, 79:80]), axis=1),
    }
    y = rng.normal(size=4054)
    w = rng.uniform(0.1, 1.0, size=4054)
    w /= w.sum()
    checks = []
    for arm, matrix in matrices.items():
        for penalty in (0.005, 0.05, 0.5):
            fit = pipeline.ridge(np, matrix, y, w, penalty)
            prediction = pipeline.predict(np, matrix, fit)
            assert np.isfinite(prediction).all()
            assert fit['scaled_coefficients'][83] == 0.0
            assert not fit['active_columns'][83]
            # Independently solve the same objective in unscaled coordinates.
            scale = np.asarray(fit['scale'])
            beta = np.linalg.solve(
                matrix.T @ (w[:, None] * matrix) + penalty * np.diag(scale * scale),
                matrix.T @ (w * y),
            )
            difference = float(np.max(np.abs(prediction - matrix @ beta)))
            assert difference < 1e-10
            checks.append({'arm': arm, 'penalty': penalty,
                           'normal_equation_residual': fit['normal_equation_max_abs_residual'],
                           'independent_prediction_max_abs_difference': difference})
    rootw = np.sqrt(w)
    coefficient, _, rank, _ = np.linalg.lstsq(x * rootw[:, None], synthetic_scalar[:, 0] * rootw, rcond=1e-12)
    assert rank == 83 and np.isfinite(coefficient).all()
    receipt = {
        'status': 'PASS_INVENTED_NUMPY_RIDGE_AND_SPAN_ONLY',
        'rows': 4054, 'columns': [84, 85, 85],
        'retained_matrix_bytes': sum(a.nbytes for a in matrices.values()),
        'invented_large_matrix_fits': 9, 'invented_analytic_fits': 2,
        'biological_models_fit': 0,
        'project_sequence_feature_outcome_or_checkpoint_read': False,
        'original_3GiB_guards_changed_or_called': False,
        'analytic_contract': analytic, 'checks': checks,
        'invented_span_rank': int(rank), 'numpy_runtime_proof': native_proof,
        'runtime_receipt_sha256': sha(runtime_path),
        'kernel_source_sha256': sha(ROOT / 'src/generalization_prelib_pooled_lineage_20261009/pipeline.py'),
        'elapsed_seconds': time.monotonic() - started,
        'limitations': 'Invented dense/sparse algebra does not measure real JSON/roster/label loading, serialization or all399 biological fits.',
    }
    with (OUT / 'invented_numpy_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print('INVENTED_NUMPY_ONLY_PASS', flush=True)


if __name__ == '__main__':
    with (OUT / 'invented_worker.log').open('x', encoding='utf-8', buffering=1) as log:
        sys.stdout = log
        sys.stderr = log
        try:
            run()
        except BaseException:
            import traceback
            traceback.print_exc()
            raise
