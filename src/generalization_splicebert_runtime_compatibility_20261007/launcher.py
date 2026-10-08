"""Temporary guard adapter; unchanged original synthetic conversion algorithm."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import importlib
import importlib.machinery
import json
from pathlib import Path
import sys

from .common import *

BLOCKED_PRELOADED = ("numpy", "torch", "transformers", "openvino", "scipy", "sklearn", "pandas")


def clean_import_state(modules=None):
    modules = sys.modules if modules is None else modules
    assert not any(name == prefix or name.startswith(prefix + ".")
                   for name in modules for prefix in BLOCKED_PRELOADED), \
        "Fresh process required: no preloaded numerical/model packages"


def select_prefix(prefix=PREFIX, finder=None):
    """No addsitedir/.pth execution or package import; only inspected sys.path."""
    prefix = Path(prefix).resolve()
    sys.path.insert(0, str(prefix))
    finder = importlib.machinery.PathFinder.find_spec if finder is None else finder
    specification = finder("numpy", sys.path)
    assert specification is not None and specification.origin
    assert Path(specification.origin).resolve() == prefix / "numpy/__init__.py", \
        "NumPy would resolve outside the exact CP312 scientific prefix"
    return str(Path(specification.origin).resolve())


def process_native_paths():
    """Enumerate this Windows process's loaded module paths; no external process."""
    assert sys.platform == "win32"
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    process = kernel.GetCurrentProcess()
    module_type = wintypes.HMODULE
    psapi.EnumProcessModulesEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(module_type),
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
    psapi.EnumProcessModulesEx.restype = wintypes.BOOL
    psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, module_type, wintypes.LPWSTR, wintypes.DWORD]
    psapi.GetModuleFileNameExW.restype = wintypes.DWORD
    capacity = 1024
    while True:
        modules = (module_type * capacity)()
        required = wintypes.DWORD()
        assert psapi.EnumProcessModulesEx(process, modules, ctypes.sizeof(modules), ctypes.byref(required), 3)
        if required.value <= ctypes.sizeof(modules):
            break
        capacity *= 2
        assert capacity <= 16384
    result = []
    for native in modules[:required.value // ctypes.sizeof(module_type)]:
        buffer = ctypes.create_unicode_buffer(32768)
        count = psapi.GetModuleFileNameExW(process, native, buffer, len(buffer))
        assert count
        result.append(Path(buffer.value).resolve())
    return result


def validate_native_paths(paths, native_files, prefix=PREFIX, hasher=sha256):
    """Bind loaded same-name NumPy PYD/DLLs to exact pinned paths/bytes."""
    prefix = Path(prefix).resolve()
    expected = {Path(name).name.lower(): (prefix / name).resolve() for name in native_files}
    assert len(expected) == len(native_files), "Ambiguous native NumPy basenames"
    assert all(path.is_relative_to(prefix) for path in expected.values())
    selected = {}
    for item in paths:
        path = Path(item).resolve()
        if path.name.lower() not in expected:
            continue
        assert path == expected[path.name.lower()], "Native NumPy module resolved elsewhere: " + str(path)
        relative = path.relative_to(prefix).as_posix()
        assert hasher(path) == native_files[relative]
        selected[relative] = native_files[relative]
    required_dlls = {name for name in native_files if name.endswith(".dll")}
    assert required_dlls and required_dlls <= set(selected), "NumPy BLAS DLL origin not verified"
    return selected


def numpy_proof(module, runtime):
    assert module.__version__ == NUMPY_VERSION
    assert Path(module.__file__).resolve() == PREFIX.resolve() / "numpy/__init__.py"
    native = sys.modules.get("numpy.core._multiarray_umath")
    assert native is not None and native.__file__
    core_path = Path(native.__file__).resolve()
    assert core_path == PREFIX.resolve() / "numpy/core/_multiarray_umath.cp312-win_amd64.pyd"
    assert sha256(core_path) == runtime["numpy_native_files"][core_path.relative_to(PREFIX).as_posix()]
    loaded = {}
    for name, value in tuple(sys.modules.items()):
        if name == "numpy" or name.startswith("numpy."):
            location = getattr(value, "__file__", None)
            if location:
                path = Path(location).resolve()
                assert path.is_relative_to(PREFIX.resolve()), name
                relative = path.relative_to(PREFIX).as_posix()
                assert sha256(path) == runtime["files"][relative], name
                loaded[relative] = runtime["files"][relative]
    native_paths = validate_native_paths(process_native_paths(), runtime["numpy_native_files"])
    assert not any(name == prefix or name.startswith(prefix + ".")
                   for name in sys.modules for prefix in ("torch", "transformers", "openvino"))
    return {"status": "PASS", "numpy_version": module.__version__, "numpy_origin": str(Path(module.__file__).resolve()),
        "native_core_origin": str(core_path), "native_core_sha256": sha256(core_path),
        "loaded_NumPy_files": loaded, "actually_loaded_NumPy_native_modules": native_paths,
        "scientific_runtime_receipt": RUNTIME_RECEIPT.relative_to(ROOT).as_posix(),
        "scientific_runtime_receipt_sha256": sha256(RUNTIME_RECEIPT),
        "repair_preparation_manifest": MANIFEST.relative_to(ROOT).as_posix(), "repair_preparation_sha256": sha256(MANIFEST),
        "launcher_source_sha256": sha256(__file__), "original_backend_source_sha256": sha256(ORIGINAL_SOURCE),
        "official_NumPy_member_parity_sha256": sha256(ART / "numpy_official_member_parity.json"),
        "model_packages_imported_before_NumPy_verification": False, "project_alleles": 0, "outcomes": False}


def make_guard(original_guard, bootstrap):
    calls = 0

    def wrapped(root_start=False):
        nonlocal calls
        calls += 1
        assert calls == 1, "Original guard must run exactly once per fresh attempt"
        headroom = original_guard(root_start=root_start)
        assert headroom["resource_admission_now"]
        proof = bootstrap(headroom)
        return {**headroom, "additive_NumPy_runtime_compatibility": proof}

    return wrapped


@contextmanager
def temporary_guard(module, bootstrap):
    original = module.guard
    module.guard = make_guard(original, bootstrap)
    try:
        yield
    finally:
        module.guard = original


def run(root_start=False):
    assert root_start, "Root explicitly authorizes synthetic-only backend work"
    clean_import_state()
    manifest, runtime = check_preparation()
    assert not (OUT / "numpy_import_receipt.json").exists(), "Preserve completed repair attempt"
    assert not (OUT / "backend_attempt_incident.json").exists(), "Preserve failed repair attempt for review"
    original = importlib.import_module("src.generalization_splicebert_20261007.backend_probe")
    unchanged_guard = original.guard
    assert Path(original.__file__).resolve() == ORIGINAL_SOURCE.resolve()
    assert sha256(original.__file__) == manifest["files"][ORIGINAL_SOURCE.relative_to(ROOT).as_posix()]
    assert original.IR == IR and original.CHECKPOINT_SHA == "2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d"

    def bootstrap(headroom):
        clean_import_state()
        origin = select_prefix()
        # The actual unchanged guard just completed both headroom checks and
        # all original hashes. An additional fresh check preserves this floor.
        before = original.resource_state()
        assert before["resource_admission_now"], "Fresh3GiB/5GiB required before corrected NumPy import"
        numpy = importlib.import_module("numpy")
        proof = numpy_proof(numpy, runtime)
        assert proof["numpy_origin"] == origin
        after = original.resource_state()
        assert after["resource_admission_now"], "Fresh3GiB/5GiB required before Torch/model imports"
        proof.update({"resource_before_NumPy": before, "resource_before_Torch": after,
            "original_guard_resource_checks_completed": 2, "original_guard_calls": 1})
        jsave(OUT / "numpy_import_receipt.json", proof)
        print("Guarded NumPy", proof["numpy_version"], proof["numpy_origin"], "PASS; original guard1x", flush=True)
        return proof

    try:
        with temporary_guard(original, bootstrap):
            original.run(root_start=True)
    except BaseException as error:
        jsave(OUT / "backend_attempt_incident.json", {"status": "FAILED_PRESERVED_FOR_REVIEW",
            "error_class": type(error).__name__, "message": str(error), "repair_preparation_sha256": sha256(MANIFEST),
            "original_source_unchanged": sha256(ORIGINAL_SOURCE) == manifest["files"][ORIGINAL_SOURCE.relative_to(ROOT).as_posix()],
            "conversion_algorithm_unchanged": True, "unsafe_load_fallback": False,
            "project_alleles": 0, "outcomes_read": False, "models_fit": 0,
            "original_candidate_outputs_preserved": True})
        raise
    assert original.guard is unchanged_guard
    backend = json.loads(ORIGINAL_RECEIPT.read_text(encoding="utf-8"))
    assert backend["status"] == "PASS" and backend["synthetic_alleles"] == 16
    assert backend["project_alleles_inferred"] == backend["models_fit"] == 0 and not backend["outcomes_used"]
    assert backend["headroom_before_import"]["additive_NumPy_runtime_compatibility"] == json.loads((OUT / "numpy_import_receipt.json").read_text())
    check_runtime(runtime)
    jsave(OUT / "backend_compatibility_receipt.json", {"status": "PASS_SYNTHETIC_BACKEND_WITH_VERIFIED_NUMPY_ORIGIN",
        "repair_preparation_sha256": sha256(MANIFEST), "NumPy_import_receipt_sha256": sha256(OUT / "numpy_import_receipt.json"),
        "original_backend_preparation_sha256": sha256(ORIGINAL_MANIFEST), "original_backend_source_sha256": sha256(ORIGINAL_SOURCE),
        "original_backend_synthetic_receipt_sha256": sha256(ORIGINAL_RECEIPT),
        "IR_xml_sha256": sha256(IR), "IR_bin_sha256": sha256(IR.with_suffix(".bin")),
        "original_guard_binding_restored": True, "source_guard_runs": 1,
        "synthetic_alleles": 16, "conversion_algorithm_unchanged": True,
        "source_or_manifest_modified": False, "project_alleles": 0, "outcomes_read": False, "models_fit": 0,
        "full_production_authorized": False,
        "downstream_bridge": "Original IR/parity fields preserved; repair manifest/import/compatibility receipts are additional required provenance, not substituted original-runtime certification"})
    print("Additive runtime compatibility PASS; synthetic-only original backend parity complete", flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] == ["--root-start"]
    run(root_start=True)
