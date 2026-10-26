"""Own current42 bootstrap/proof. Numerical imports happen only when called."""
import importlib
import importlib.machinery
import os
from pathlib import Path
import sys
from . import spec
from .contracts import decode, digest, inventory_contract


def sha(path):
    import hashlib
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def bound_document(manifest, path):
    key = path.relative_to(spec.ROOT).as_posix()
    assert not path.is_symlink()
    raw = path.read_bytes()
    assert digest(raw) == manifest['files'][key], 'Bound metadata changed: ' + key
    return decode(raw)


def current_payload(manifest):
    """Refresh exact current42 and NumPy bytes; unused7998 scope is inventory."""
    inventory = bound_document(manifest, spec.INVENTORY)
    discovery = bound_document(manifest, spec.DISCOVERY)
    base = bound_document(manifest, spec.BASE_INVENTORY)
    expanded = bound_document(manifest, spec.EXPANDED_INVENTORY)
    runtime = bound_document(manifest, spec.OLD_RUNTIME)
    files, native, current, three = inventory_contract(inventory, discovery, base, expanded, runtime)
    assert Path(sys.executable).resolve() == spec.EXPECTED_PYTHON.resolve()
    assert inventory['python_version'] == sys.version
    assert sys.implementation.cache_tag == inventory['python_cache_tag'] == 'cpython-312'
    for name, want in current.items():
        assert sha(name) == want, 'Refreshed current native drift: ' + name
    expected = {name: want for name, want in files.items()
                if name.split('/')[0] in ('numpy', 'numpy.libs', 'numpy-1.26.4.dist-info')}
    assert len(expected) == 1231
    actual = set()
    for component in ('numpy', 'numpy.libs', 'numpy-1.26.4.dist-info'):
        for path in (spec.PREFIX / component).rglob('*'):
            if path.is_file():
                assert not path.is_symlink() and path.resolve().is_relative_to(spec.PREFIX.resolve())
                actual.add(path.relative_to(spec.PREFIX).as_posix())
    assert actual == set(expected), 'NumPy package membership changed'
    for name, want in expected.items():
        assert sha(spec.PREFIX / name) == want, name
    return runtime, inventory, {
        'fresh_inventory_sha256': manifest['files'][spec.INVENTORY.relative_to(spec.ROOT).as_posix()],
        'current42_native_files_freshly_checked': current,
        'derived_current_python_three': three,
        'fresh_NumPy_payload_files': len(expected),
        'unused_pandas_SciPy_payload_rehashed_in_worker': False,
        'old_exact_runtime_identity_passes': False,
    }


def select_closed_scientific_path():
    home = Path(sys.executable).resolve().parent
    sys.path[:] = [str(spec.PREFIX.resolve()), str(spec.ROOT.resolve()),
                   str(home / 'python312.zip'), str(home / 'DLLs'), str(home / 'Lib'), str(home)]
    for name in ('numpy', 'pandas', 'scipy'):
        found = importlib.machinery.PathFinder.find_spec(name, sys.path)
        assert found and Path(found.origin).resolve() == spec.PREFIX.resolve() / name / '__init__.py'


def classify_loaded_native(paths, scientific, current, prefix=spec.PREFIX, home=None, hasher=sha):
    """Freshly bind all loaded current42 paths; reject unknown bundled natives."""
    prefix = Path(prefix).resolve()
    home = spec.EXPECTED_PYTHON.resolve().parent if home is None else Path(home).resolve()
    current = {str(Path(name).resolve()): want for name, want in current.items()}
    scientific_names = {Path(name).name.casefold() for name in scientific}
    current_names = {Path(name).name.casefold() for name in current}
    loaded_scientific, loaded_current = {}, {}
    for item in paths:
        path = Path(item).resolve()
        if path.is_relative_to(prefix):
            key = path.relative_to(prefix).as_posix()
            assert key in scientific and hasher(path) == scientific[key], str(path)
            loaded_scientific[str(path)] = scientific[key]
        elif path.name.casefold() in scientific_names:
            raise AssertionError('Scientific native basename loaded outside prefix: ' + str(path))
        elif str(path) in current:
            assert hasher(path) == current[str(path)], str(path)
            loaded_current[str(path)] = current[str(path)]
        elif path.is_relative_to(home) or path.name.casefold() in current_names:
            raise AssertionError('Unpinned/redirected bundled native: ' + str(path))
        else:
            assert path.suffix.lower() != '.pyd', 'Foreign native extension: ' + str(path)
    return loaded_scientific, loaded_current


def actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory, manifest):
    """Current metadata only; no calls to any old Python attestation checker."""
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    from src.generalization_current_python_20261022 import attest
    from src.generalization_knowncell_parser_profile_v3_20261023.cache_integrity import possible_cache_proof
    files = inventory['selected_scientific_payload_files']
    current = inventory['current_bundled_stdlib_native_files']
    three = {name: want for name, want in current.items() if Path(name).name.casefold() in spec.ANCHORS}
    assert len(three) == 3
    numpy_proof = launcher.numpy_proof(np, runtime)  # Unchanged NumPy-only package proof.
    prefix = spec.PREFIX.resolve()
    for module, version in ((np, '1.26.4'), (pd, '2.2.3'), (scipy, '1.14.1')):
        assert module.__version__ == version
        assert Path(module.__file__).resolve() == prefix / module.__name__ / '__init__.py'
    loaded, stdlib_extensions = {}, {}
    for name, module in tuple(sys.modules.items()):
        location = getattr(module, '__file__', None)
        if not location:
            continue
        path = Path(location).resolve()
        if path.is_relative_to(prefix):
            key = path.relative_to(prefix).as_posix()
            assert key in files and sha(path) == files[key], name
            loaded[key] = files[key]
        elif path.suffix.lower() == '.pyd':
            assert str(path) in current and sha(path) == current[str(path)], name
            stdlib_extensions[str(path)] = current[str(path)]
        else:
            assert not any(x.casefold() in ('site-packages', '.python_packages') for x in path.parts), str(path)
    native = {name: want for name, want in files.items() if Path(name).suffix.lower() in ('.dll', '.pyd')}
    observed, native_current = classify_loaded_native(launcher.process_native_paths(), native, current)
    assert set(stdlib_extensions) <= set(native_current)
    loaded_dlls = {Path(name).relative_to(prefix).as_posix() for name in observed if name.lower().endswith('.dll')}
    pools = threadpoolctl.threadpool_info()
    assert pools and {pool['user_api'] for pool in pools} <= {'blas', 'openmp'}
    for pool in pools:
        path = Path(pool['filepath']).resolve()
        key = path.relative_to(prefix).as_posix()
        assert key in native and sha(path) == native[key]
        assert pool['num_threads'] == 1
    assert any('numpy.libs/' in key for key in loaded_dlls)
    assert any('scipy.libs/' in key for key in loaded_dlls)
    # This exact parameterized helper does not load/check its old ATTESTATION.
    current_python = attest.native_python(three)
    caches = possible_cache_proof(sys.modules, spec.PREFIX, files)
    return {
        'status': 'PASS_ACTUAL_CURRENT42_NATIVE_AND_UNCHANGED_LOADED_SCIENTIFIC_ORIGINS',
        'fresh_inventory_sha256': manifest['files'][spec.INVENTORY.relative_to(spec.ROOT).as_posix()],
        'native_discovery_sha256': spec.DISCOVERY_SHA,
        'python_version': sys.version, 'actually_loaded_Python_DLLs': current_python,
        'actually_loaded_current_bundled_native_files': native_current,
        'actually_loaded_scientific_modules': loaded,
        'actually_loaded_scientific_native_files': observed,
        'actually_loaded_threadpools': pools, 'numpy_original_payload_proof': numpy_proof,
        'possible_bytecode_payload_proof': caches, 'two_explicit_root_cache_admissions': spec.ADDITIONAL_CACHES,
        'old_exact_runtime_identity_passes': False, 'old_interpreter_bitwise_parity_established': False,
        'full7998_scope': 'fresh prior inventory; actually loaded bytes checked before/after invented cases',
        'all_stdlib_source_bytes_inventoried': False, 'biological_admission_granted': False,
    }


def bootstrap(manifest, fresh):
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    assert all(os.environ.get(key) == value for key, value in spec.THREAD_ENV.items())
    launcher.clean_import_state()
    fresh()
    runtime, inventory, python_proof = current_payload(manifest)
    select_closed_scientific_path()
    values = []
    for name in ('numpy', 'pandas', 'scipy', 'scipy.optimize', 'scipy.special', 'threadpoolctl'):
        fresh()
        values.append(importlib.import_module(name))
    np, pd, scipy, optimize, special, threadpoolctl = values
    return np, pd, scipy, optimize.minimize, special.expit, threadpoolctl, runtime, inventory, python_proof
