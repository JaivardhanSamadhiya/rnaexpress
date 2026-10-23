"""Root-gated invented parser and optimizer operations; never biological data."""
import json
import sys
import time
from .common_v2 import *


def run():
    started = time.monotonic()
    assert sys.flags.no_site == 1, 'Scientific child must start with -S; no startup .pth processing'
    from .supervise_v2 import admitted
    manifest = admitted()
    from .runtime_v2 import bootstrap, actual_proof
    np, pd, scipy, minimize, expit, threadpoolctl, runtime, inventory, python_proof = bootstrap()
    initial = actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory)
    from .parser_profile import run as parser_checks
    parser = parser_checks(pd)
    from .optimizer_profile import run as optimizer_checks
    optimizer = optimizer_checks(np, minimize, expit)
    from .extras_v2 import run as extra_checks
    extras = extra_checks(np,pd)
    final = actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory)
    assert all(sha(ROOT/name) == want for name, want in manifest['files'].items())
    jsave(OUT/'actual_origin_receipt.json', {
        'status': 'PASS_ACTUAL_LOADED_PANDAS_NUMPY_SCIPY_ONE_THREAD_CURRENT_PYTHON_V2',
        'initial': initial, 'final': final, 'python_payload_check': python_proof,
        'payload_inventory_sha256': sha(INVENTORY), 'preparation_manifest_sha256': sha(MANIFEST),
        'pandas_version': pd.__version__, 'scipy_version': scipy.__version__,
        'pandas_module_path': str(Path(pd.__file__).resolve()), 'pandas_module_sha256': sha(pd.__file__),
        'old_interpreter_bitwise_parity_established': False,
        'biological_rows_read': 0, 'biological_model_fits': 0})
    origin_sha = sha(OUT/'actual_origin_receipt.json')
    current_python = json.loads(PYTHON.read_bytes())
    jsave(OUT/'pandas_admission_candidate.json', {
        'status': NATIVE_PASS,
        'pandas_version': '2.2.3', 'original_pandas_version': '2.2.3',
        'original_pandas_package_and_native_bytes_unchanged': True,
        'invented_original_parser_options_and_results': 'PASS_PINNED_PANDAS_DEFAULT_CSV_OPTIONS_RESULTS',
        'old_interpreter_bitwise_parity_established': False,
        'python_cache_tag': sys.implementation.cache_tag,
        'python_executable': sys.executable, 'python_native_files': certificate_python_files(current_python),
        'pandas_module_path': str(Path(pd.__file__).resolve()), 'pandas_module_sha256': sha(pd.__file__),
        'actual_origin_receipt_sha256': origin_sha,
        'unchanged_package_check_scope': 'Full payload at preparation; all actually imported sources/natives freshly hashed before/after cases; unused pandas/SciPy files not freshly rehashed in worker',
        'biological_rows_read': 0, 'model_fits': 0,
        'admission_requires_supervisor_pass': True,
        'automatic_biological_admission': False})
    jsave(OUT/'invented_profile_receipt.json', {
        'status': 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V2',
        'preparation_manifest_sha256': sha(MANIFEST), 'actual_origin_receipt_sha256': origin_sha,
        'pandas_admission_candidate_sha256': sha(OUT/'pandas_admission_candidate.json'),
        'parser': parser, 'optimizer': optimizer, 'numerical_threads': 1,
        'extra_deferred_native_contracts': extras,
        'elapsed_seconds': time.monotonic()-started,
        'biological_rows_read': 0, 'biological_model_fits': 0,
        'old_interpreter_bitwise_parity_established': False,
        'scope': 'Only invented parsing/optimizer/scoring compatibility; no biological-stage admission or full old-interpreter equivalence.'})
    print('INVENTED_PANDAS_SCIPY_ONLY_PASS', flush=True)


if __name__ == '__main__':
    with (OUT/'invented_worker.log').open('x', encoding='utf-8', buffering=1) as log:
        sys.stdout = sys.stderr = log
        try: run()
        except BaseException:
            import traceback
            traceback.print_exc()
            raise
