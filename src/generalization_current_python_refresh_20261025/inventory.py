"""Deferred byte inventory only. Root review/commit required before invocation.

No scientific imports, DLL-origin API, ctypes, package execution, data or models.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from . import spec
from .contracts import accepted_v4, compare_inventory, decode, digest, native_contract, payload_contract, relative_key, valid_sha


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def stable_file_hash(path):
    """Detect ordinary metadata changes during a single opaque-byte hash read."""
    path = Path(path)
    before = path.stat()
    value = sha(path)
    after = path.stat()
    assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns) == (
        after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'Software file changed while hashing: '+str(path)
    return value, {'size_bytes':after.st_size,'mtime_ns':after.st_mtime_ns,
        'ctime_ns':after.st_ctime_ns,'ctime_semantics':'Platform file metadata only; not proof of byte-change time'}


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def safe_file(path, parent):
    path, parent = Path(path), Path(parent).resolve()
    assert path.is_file() and not path.is_symlink(), 'Missing/symlink file: '+str(path)
    assert path.resolve().is_relative_to(parent), 'Resolved path escapes fixed root: '+str(path)
    return path


def enumerate_payload(prefix, components, caches):
    prefix = Path(prefix).resolve()
    paths = {}
    for component in components:
        relative_key(component)
        path = prefix/component
        assert path.exists() and not path.is_symlink(), 'Missing/symlink component: '+component
        entries = [path] if path.is_file() else path.rglob('*')
        for entry in entries:
            assert not entry.is_symlink(), 'Symlink inside selected component: '+str(entry)
            if entry.is_file():
                safe_file(entry, prefix)
                paths[entry.relative_to(prefix).as_posix()] = entry
    # Root __pycache__ is deliberately not broadly admitted or executed.
    for name in caches:
        relative_key(name)
        paths[name] = safe_file(prefix/name, prefix)
    return paths


def enumerate_native(home):
    home = Path(home).resolve()
    paths = [home/'python.exe'] + list(home.glob('*.dll'))
    paths += list((home/'DLLs').glob('*.dll')) + list((home/'DLLs').glob('*.pyd'))
    return {str(path.resolve()):safe_file(path,home) for path in paths}


def initial_manifest(expected):
    assert valid_sha(expected)
    raw = spec.MANIFEST.read_bytes()
    assert digest(raw) == expected, 'Initial preparation bytes differ from explicit root argument'
    # Detached direct Git is the existing Windows headless behavior; no shell.
    git = subprocess.check_output(['git','show','HEAD:'+spec.MANIFEST.relative_to(spec.ROOT).as_posix()],
        cwd=spec.ROOT, creationflags=0x8 if os.name == 'nt' else 0)
    assert git == raw, 'Preparation manifest not exactly committed to HEAD'
    document = decode(raw)
    assert document['status'] == spec.PREPARATION_STATUS
    for name, want in document['files'].items():
        relative_key(name)
        assert sha(safe_file(spec.ROOT/name,spec.ROOT)) == want, name
    return document, raw


def prior_documents():
    result = {}
    for name, want in spec.PRIOR_PINS.items():
        raw = (spec.ROOT/name).read_bytes()
        assert digest(raw) == want, 'Prior metadata changed: '+name
        result[name] = decode(raw)
    v4 = spec.V4_DIR
    hashes = {name[len(v4):]:want for name,want in spec.PRIOR_PINS.items() if name.startswith(v4)}
    accepted_v4(result[spec.V4_STATUS],result[v4+'supervisor_receipt.json'],
        result[v4+'invented_profile_receipt.json'],result[v4+'pandas_admission_candidate.json'],
        hashes,spec.PRIOR_PINS[spec.V4_MANIFEST])
    return result


def runtime_preconditions():
    assert Path(sys.executable).resolve() == spec.EXPECTED_PYTHON.resolve()
    assert sys.version_info[:3] == (3,12,14) and sys.implementation.cache_tag == 'cpython-312'
    assert sys.flags.no_site and sys.dont_write_bytecode and os.environ.get('PYTHONUTF8') == '1'
    assert sys.pycache_prefix and Path(sys.pycache_prefix).resolve() == spec.SOURCE_CACHE.resolve()
    assert not spec.SOURCE_CACHE.exists(), 'Fresh absent cache prefix required; never execute old source caches'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for name in sys.modules)


def run(expected):
    started = time.monotonic()
    runtime_preconditions()
    manifest, initial = initial_manifest(expected)
    birth = {'status':'STARTED_EXPLICIT_BYTE_INVENTORY_NO_NATIVE_ORIGIN_OR_NUMERICAL_PROBE',
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid':os.getpid(),
        'initial_preparation_manifest_sha256':digest(initial)}
    save(spec.OUT/'inventory_attempt_birth.json',birth)
    try:
        prior = prior_documents()
        base, expanded, old = (prior[name] for name in (spec.BASE_PAYLOAD,spec.PAYLOAD,spec.OLD_RUNTIME))
        payload = payload_contract(base,expanded,old,spec.ADDITIONAL_CACHES,base['components'])
        assert Path(base['prefix']).resolve() == spec.PREFIX.resolve()
        assert Path(old['runtime_path']).resolve() == spec.PREFIX.resolve()
        old_python = prior[spec.PRIOR_PYTHON]
        assert old_python['python_version'] == base['python_version'] == sys.version
        assert Path(old_python['python_executable']).resolve() == spec.EXPECTED_PYTHON.resolve()
        assert old_python['python_native_files'].items() <= base['current_python_native_files'].items()
        selected = enumerate_payload(spec.PREFIX,base['components'],spec.ADDITIONAL_CACHES)
        observed = {name:stable_file_hash(path)[0] for name,path in selected.items()}
        compare_inventory(payload,observed,'Selected scientific payload')
        native_paths = enumerate_native(spec.EXPECTED_PYTHON.parent)
        native_records = {name:stable_file_hash(path) for name,path in native_paths.items()}
        native = {name:item[0] for name,item in native_records.items()}
        changes = native_contract(base['current_python_native_files'],native,
            spec.NEW_NATIVE_BY_BASENAME,str(spec.EXPECTED_PYTHON.parent))
        assert len(native) == 42, 'Prior bundled native inventory has exactly42 entries'
        current_three = {name:want for name,want in native.items() if Path(name).name in spec.NEW_NATIVE_BY_BASENAME}
        assert len(current_three) == 3
        # Detect source/metadata drift over the complete scan before success.
        assert spec.MANIFEST.read_bytes() == initial, 'Preparation manifest changed during inventory'
        for name,want in manifest['files'].items():
            assert sha(spec.ROOT/name) == want, name
        runtime_preconditions()
        result = {'status':spec.INVENTORY_STATUS,
            'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'initial_preparation_manifest_sha256':digest(initial),
            'prior_pins':spec.PRIOR_PINS,'historical_V4_acceptance_reused_for_new_Python':False,
            'python_executable':str(Path(sys.executable).resolve()),'python_version':sys.version,
            'python_cache_tag':sys.implementation.cache_tag,'python_native_files':current_three,
            'current_bundled_stdlib_native_files':native,'current_native_file_count':len(native),
            'current_bundled_stdlib_native_file_metadata':{name:item[1] for name,item in native_records.items()},
            'changes_from_22October_native_inventory':changes,
            'selected_scientific_payload_files':observed,'selected_scientific_payload_file_count':len(observed),
            'unchanged_versions_from_package_metadata':base['versions'],
            'two_explicit_possible_cache_payloads':spec.ADDITIONAL_CACHES,
            'cache_execution_claimed':False,'actually_loaded_python_DLL_origins_verified':False,
            'source_cache_prefix':str(spec.SOURCE_CACHE),'source_cache_prefix_exists':False,
            'all_stdlib_source_bytes_inventoried':False,'scientific_packages_imported':False,
            'numerical_compatibility_established':False,'old_interpreter_bitwise_parity_established':False,
            'cause_or_exact_time_of_binary_change_established':False,
            'biological_inputs_read':False,'biological_model_fits':0,'stage_authority_granted':False,
            'old_sources_certificates_prefix_and_guards_changed':False,
            'inventory_elapsed_seconds':time.monotonic()-started}
        save(spec.OUT/'current_python_inventory_refresh.json',result)
        print('INVENTORY_ONLY_COMPATIBILITY_PENDING',len(observed),len(native),flush=True)
        return result
    except BaseException as error:
        save(spec.OUT/'inventory_failure.json',{'status':'FAILED_REFRESH_ATTEMPT_PRESERVED_NO_RETRY',
            'initial_preparation_manifest_sha256':digest(initial),
            'exception_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),
            'elapsed_seconds':time.monotonic()-started,'scientific_packages_imported':False,
            'biological_inputs_read':False,'compatibility_established':False})
        raise


if __name__ == '__main__':
    assert len(sys.argv) == 3 and sys.argv[1] == '--expected-preparation-sha'
    run(sys.argv[2])
