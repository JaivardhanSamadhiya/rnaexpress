"""Same invented arrays as v1; current Python attested independently."""
import importlib
import json
import math
import os
import sys
import time

from src.generalization_prelib_numpy_profile_20261022.invented import ROOT, sha
from src.generalization_current_python_20261022 import attest
from src.generalization_splicebert_runtime_compatibility_20261007 import launcher

OUT = ROOT / 'results/generalization_prelib_numpy_profile_v2_20261022'


def current_numpy_payload():
    """Fresh NumPy-byte check; old full-prefix inventory is separate metadata."""
    attest.committed(attest.ATTESTATION)
    receipt = json.loads(attest.ATTESTATION.read_bytes())
    assert receipt['status'] == 'PASS_CURRENT_PYTHON_INVENTORY_UNCHANGED_PREFIX_COMPATIBILITY_PENDING'
    assert receipt['source_sha256'] == sha(attest.__file__)
    assert receipt['python_version'] == sys.version
    assert receipt['old_runtime_receipt_sha256'] == sha(launcher.RUNTIME_RECEIPT)
    attest.committed(launcher.RUNTIME_RECEIPT)
    runtime = json.loads(launcher.RUNTIME_RECEIPT.read_bytes())
    assert runtime['numpy_version'] == '1.26.4' and runtime['status'] == 'PASS'
    components = ('numpy', 'numpy.libs', 'numpy-1.26.4.dist-info')
    prefix = launcher.PREFIX.resolve()
    expected = {rel: want for rel, want in runtime['files'].items()
                if rel.split('/')[0] in components}
    assert expected
    actual = {path.relative_to(prefix).as_posix()
              for component in components for path in (prefix / component).rglob('*') if path.is_file()}
    assert actual == set(expected), 'NumPy acquired unexpected or missing files'
    for rel, want in expected.items():
        path = prefix / rel
        assert not path.is_symlink() and path.resolve().is_relative_to(prefix)
        assert sha(path) == want, rel
    assert set(runtime['numpy_native_files']) <= set(expected)
    loaded = attest.native_python(receipt['python_native_files'])
    return runtime, {
        'current_python_inventory_sha256': sha(attest.ATTESTATION),
        'python_version': sys.version, 'actually_loaded_python_DLLs': loaded,
        'current_python_native_files': receipt['python_native_files'],
        'old_python_hash_contract_passes': False,
        'fresh_unchanged_NumPy_payload_file_count': len(expected),
        'fresh_payload_scope': list(components),
        'full_prefix_inventory_is_preparation_metadata_not_freshly_rehashed_in_worker': True,
    }


def run():
    started = time.monotonic()
    assert os.environ.get('PYTHONUTF8') == '1'
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == '2'
    launcher.clean_import_state()
    runtime, python_proof = current_numpy_payload()
    launcher.select_prefix()
    np = importlib.import_module('numpy')
    native_proof = launcher.numpy_proof(np, runtime)
    loaded_python_after = attest.native_python(python_proof['current_python_native_files'])

    # Definitions and pure kernels only. No biological-stage admission is called
    # and neither original fresh() nor numpy_runtime() is replaced.
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
        # Independent scalar summation does not trust the producer's scale.
        rms = np.asarray([math.sqrt(math.fsum(float(weight) * float(value)**2
                            for weight, value in zip(w, matrix[:, column])))
                          for column in range(matrix.shape[1])])
        active = rms > 0
        scale = np.where(active, rms, 1.0)
        for penalty in (0.005, 0.05, 0.5):
            fit = pipeline.ridge(np, matrix, y, w, penalty)
            prediction = pipeline.predict(np, matrix, fit)
            assert np.isfinite(prediction).all()
            assert fit['scaled_coefficients'][83] == 0.0 and not fit['active_columns'][83]
            assert np.array_equal(active, np.asarray(fit['active_columns']))
            scale_difference = float(np.max(np.abs(scale - np.asarray(fit['scale']))))
            assert scale_difference < 1e-12
            beta = np.linalg.solve(
                matrix.T @ (w[:, None] * matrix) + penalty * np.diag(scale * scale),
                matrix.T @ (w * y),
            )
            assert np.max(np.abs(beta[~active])) == 0.0
            difference = float(np.max(np.abs(prediction - matrix @ beta)))
            assert difference < 1e-10
            checks.append({'arm': arm, 'penalty': penalty,
                           'normal_equation_residual': fit['normal_equation_max_abs_residual'],
                           'independent_scale_max_abs_difference': scale_difference,
                           'independent_prediction_max_abs_difference': difference})
    rootw = np.sqrt(w)
    coefficient, _, rank, _ = np.linalg.lstsq(x * rootw[:, None], synthetic_scalar[:, 0] * rootw, rcond=1e-12)
    assert rank == 83 and np.isfinite(coefficient).all()
    # Verify imports that may occur lazily in solve/lstsq, not just initial import.
    final_native_proof = launcher.numpy_proof(np, runtime)
    final_python = attest.native_python(python_proof['current_python_native_files'])
    receipt = {
        'status': 'PASS_INVENTED_NUMPY_RIDGE_AND_SPAN_ONLY_CURRENT_PYTHON',
        'seed': 20261022, 'rows': 4054, 'columns': [84, 85, 85],
        'retained_matrix_bytes': sum(a.nbytes for a in matrices.values()),
        'invented_large_matrix_fits': 9, 'invented_analytic_fits': 2,
        'biological_models_fit': 0, 'project_sequence_feature_outcome_or_checkpoint_read': False,
        'original_3GiB_guards_changed_or_called': False,
        'analytic_contract': analytic, 'checks': checks, 'invented_span_rank': int(rank),
        'current_python_proof': python_proof, 'loaded_python_after_import': loaded_python_after,
        'loaded_python_after_calculations': final_python,
        'old_NumPy_payload_proof_at_import': native_proof,
        'old_NumPy_payload_proof_after_calculations': final_native_proof,
        'old_full_runtime_identity_passes_for_current_Python': False,
        'compatibility_scope': 'Only tested NumPy1.26.4 ridge, solve and lstsq operations under attested current Python; no other model runtime renewed.',
        'kernel_source_sha256': sha(ROOT / 'src/generalization_prelib_pooled_lineage_20261009/pipeline.py'),
        'elapsed_seconds': time.monotonic() - started,
        'limitations': 'Invented arithmetic does not measure real JSON/roster/label loading, serialization or all399 biological fits.',
    }
    with (OUT / 'invented_numpy_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print('INVENTED_NUMPY_ONLY_CURRENT_PYTHON_PASS', flush=True)


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
