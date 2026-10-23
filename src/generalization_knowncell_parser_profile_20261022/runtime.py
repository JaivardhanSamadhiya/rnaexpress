"""Deferred scientific imports and actual current-process origins only."""
import importlib
import importlib.machinery
import json
import os
from pathlib import Path
import sys
from .common import *


def select_closed_scientific_path():
    """Current stdlib + repository + observed prefix; no outside site-packages."""
    home = Path(sys.executable).resolve().parent
    sys.path[:] = [str(PREFIX.resolve()), str(ROOT.resolve()), str(home/'python312.zip'),
                   str(home/'DLLs'), str(home/'Lib'), str(home)]
    finder = importlib.machinery.PathFinder.find_spec
    for name in ('numpy', 'pandas', 'scipy'):
        spec = finder(name, sys.path)
        assert spec and Path(spec.origin).resolve() == PREFIX.resolve()/name/'__init__.py'


def current_payload():
    # Reuse ONLY the v2 payload checker; never run its two-thread experiment.
    from src.generalization_prelib_numpy_profile_v2_20261022.invented import current_numpy_payload
    runtime, python_proof = current_numpy_payload()
    inventory = json.loads(INVENTORY.read_bytes())
    assert inventory['status'] == 'INVENTORIED_EXISTING_PAYLOAD_ONLY_NATIVE_COMPATIBILITY_PENDING'
    assert inventory['old_runtime_receipt_sha256'] == sha(RUNTIME)
    assert inventory['current_python_inventory_sha256'] == sha(PYTHON)
    assert inventory['python_version'] == sys.version
    assert inventory['files'] == payload_members(runtime['files'])
    # Full pandas/SciPy/dependency membership and bytes were checked at
    # preparation. Refresh only the NumPy payload helper plus every actually
    # imported source/native file below, preserving the fixed120s worker cap.
    for path, want in inventory['current_python_native_files'].items(): assert sha(path) == want
    return runtime, inventory, python_proof


def actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory):
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    from src.generalization_current_python_20261022 import attest
    numpy_proof = launcher.numpy_proof(np, runtime)
    prefix = PREFIX.resolve()
    for module, version in ((np, '1.26.4'), (pd, '2.2.3'), (scipy, '1.14.1')):
        assert module.__version__ == version
        assert Path(module.__file__).resolve() == prefix/module.__name__/'__init__.py'
    loaded = {}; stdlib_native = {}; observed_native = {}
    for name, module in tuple(sys.modules.items()):
        location = getattr(module, '__file__', None)
        if not location: continue
        path = Path(location).resolve()
        if path.is_relative_to(prefix):
            rel = path.relative_to(prefix).as_posix()
            assert rel in inventory['files'] and sha(path) == inventory['files'][rel], name
            loaded[rel] = inventory['files'][rel]
        elif path.suffix.lower() == '.pyd':
            assert str(path) in inventory['current_python_native_files'], name
            assert sha(path) == inventory['current_python_native_files'][str(path)]
            stdlib_native[str(path)] = sha(path)
        else:
            assert not any(x.lower() in ('site-packages', '.python_packages') for x in path.parts), str(path)
    native = inventory['native_files']
    known_basenames = {Path(key).name.lower() for key in native}
    expected_dlls = {key for key in native if key.lower().endswith('.dll')}
    loaded_prefix_dlls = set()
    for path in launcher.process_native_paths():
        if path.is_relative_to(prefix):
            rel = path.relative_to(prefix).as_posix()
            assert rel in native and sha(path) == native[rel], str(path)
            observed_native[str(path)] = native[rel]
            if rel.lower().endswith('.dll'): loaded_prefix_dlls.add(rel)
        elif path.name.lower() in known_basenames:
            raise AssertionError('Pinned scientific native basename loaded elsewhere: ' + str(path))
        elif str(path) in inventory['current_python_native_files']:
            assert sha(path) == inventory['current_python_native_files'][str(path)]
            stdlib_native[str(path)] = sha(path)
        else:
            assert path.suffix.lower() != '.pyd', 'Foreign native extension ' + str(path)
    pools = threadpoolctl.threadpool_info()
    assert pools and {pool['user_api'] for pool in pools} <= {'blas', 'openmp'}
    for pool in pools:
        path = Path(pool['filepath']).resolve(); rel = path.relative_to(prefix).as_posix()
        assert rel in native and sha(path) == native[rel]
        assert pool['num_threads'] == 1, 'Actual loaded numerical library is not one thread'
    assert any('numpy.libs/' in key for key in loaded_prefix_dlls)
    assert any('scipy.libs/' in key for key in loaded_prefix_dlls)
    python = json.loads(PYTHON.read_bytes())
    current_python = attest.native_python(python['python_native_files'])
    return {'current_python_inventory_sha256': sha(PYTHON), 'python_version': sys.version,
            'actually_loaded_Python_DLLs': current_python,
            'actually_loaded_current_python_native_files': stdlib_native,
            'actually_loaded_scientific_modules': loaded,
            'actually_loaded_scientific_native_files': observed_native,
            'actually_loaded_threadpools': pools, 'numpy_original_payload_proof': numpy_proof,
            'old_interpreter_bitwise_parity_established': False,
            'old_exact_runtime_identity_passes': False,
            'fresh_full_NumPy_payload_check': True,
            'full_pandas_SciPy_dependency_payload_scope': 'preparation inventory only; all actually loaded files freshly hashed before/after invented cases',
            'unused_pandas_SciPy_files_freshly_rehashed_in_worker': False,
            'expected_unused_scientific_dlls_not_claimed_loaded': sorted(expected_dlls-loaded_prefix_dlls)}


def bootstrap():
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    check_thread_environment(os.environ)
    launcher.clean_import_state()
    runtime, inventory, python_proof = current_payload()
    select_closed_scientific_path()
    np = importlib.import_module('numpy')
    pd = importlib.import_module('pandas')
    scipy = importlib.import_module('scipy')
    minimize = importlib.import_module('scipy.optimize').minimize
    expit = importlib.import_module('scipy.special').expit
    threadpoolctl = importlib.import_module('threadpoolctl')
    return np, pd, scipy, minimize, expit, threadpoolctl, runtime, inventory, python_proof
