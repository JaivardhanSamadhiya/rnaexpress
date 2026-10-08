"""Native import deferred until exact committed preparation + fresh resources."""
import ctypes
from ctypes import wintypes
import importlib
import math
import os
from pathlib import Path
import shutil
import sys
from . import common as c, spec as s

def resources():
    assert sys.platform == 'win32'
    class Memory(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [(n, ctypes.c_ulonglong) for n in ('total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended')]
    state = Memory(); state.length = ctypes.sizeof(state)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state))
    return {'available_RAM_bytes': state.available, 'workspace_disk_free_bytes': shutil.disk_usage(c.ROOT).free}

def resource_contract(value):
    assert value['available_RAM_bytes'] >= s.MIN_RAM and value['workspace_disk_free_bytes'] >= s.MIN_DISK, 'Fresh >=1GiB RAM/disk required'
    return value

def time_contract(elapsed):
    assert math.isfinite(elapsed) and 0. <= elapsed <= s.MAX_PROBE_SECONDS, 'Fixed numerical time cap reached; preserve completed calls, no PASS'
    return elapsed

def memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in ('peak', 'working', 'paged_peak', 'paged', 'nonpaged_peak', 'nonpaged', 'pagefile', 'pagefile_peak')]
    state = Counters(); state.cb = ctypes.sizeof(state)
    kernel = ctypes.WinDLL('kernel32'); api = ctypes.WinDLL('psapi')
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    api.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    api.GetProcessMemoryInfo.restype = wintypes.BOOL
    assert api.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(state), ctypes.sizeof(state))
    return {'working_set_bytes': state.working, 'peak_working_set_bytes': state.peak, 'pagefile_bytes': state.pagefile, 'peak_pagefile_bytes': state.pagefile_peak}

def actual_origins(runtime, paths, modules=None):
    """Observed imported NumPy/SciPy source/native paths must match pinned bytes."""
    modules = sys.modules if modules is None else modules; prefix = c.PREFIX.resolve()
    expected = {(prefix / n).resolve(): h for n, h in runtime['files'].items()}
    names = {p.name.lower() for p in expected if p.suffix.lower() in ('.dll', '.pyd')}
    imported = {}; native = {}
    for name, module in tuple(modules.items()):
        if name.split('.')[0] not in ('numpy', 'scipy'): continue
        location = getattr(module, '__file__', None)
        if location:
            path = Path(location).resolve()
            assert path.is_relative_to(prefix) and path in expected and c.sha(path) == expected[path], name
            imported[str(path)] = expected[path]
    for value in paths:
        path = Path(value).resolve()
        if path.name.lower() in names or path.is_relative_to(prefix):
            assert path in expected and c.sha(path) == expected[path], 'Unexpected numerical native origin: ' + str(path)
            native[str(path)] = expected[path]
    assert imported and native
    return {'actually_imported_numerical_files': imported, 'actually_loaded_native_files': native}

def admit(root_start=False):
    assert root_start, 'Root review, exact commit and explicit native start required'
    c.clean_imports(); c.freshness(); first = resource_contract(resources())
    assert os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == s.THREADS
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == os.environ.get('PYTHONUTF8') == '1'
    c.committed(c.MANIFEST); manifest = c.readj(c.MANIFEST); c.manifest_checks(manifest)
    for name in manifest['own_committed_files']: c.committed(c.ROOT / name)
    from src.generalization_splicebert_runtime_compatibility_20261007 import common as old, launcher
    runtime = c.readj(c.SCIENTIFIC); old.check_runtime(runtime)
    assert Path(sys.executable).resolve() == Path(runtime['python_executable']).resolve()
    second = resource_contract(resources()); c.clean_imports(); launcher.select_prefix()
    # FIRST numerical import occurs only here, after two resource checks.
    np = importlib.import_module('numpy'); numpy_proof = launcher.numpy_proof(np, runtime)
    scipy = importlib.import_module('scipy'); optimizer = importlib.import_module('scipy.optimize')
    proof = {'status': 'PASS', 'numpy': numpy_proof, 'scipy_version': scipy.__version__, 'scipy_origin': str(Path(scipy.__file__).resolve()),
             'origins': actual_origins(runtime, launcher.process_native_paths()), 'first_resources': first, 'before_import_resources': second,
             'after_import_resources': resource_contract(resources()), 'threads': 1, 'scientific_runtime_sha256': c.sha(c.SCIENTIFIC)}
    assert memory()['peak_working_set_bytes'] <= s.MAX_WORKING_SET, 'Native baseline >400MiB; stop'
    c.jsave(c.OUT / 'current_runtime_import_receipt.json', proof)
    return np, optimizer, runtime, manifest
