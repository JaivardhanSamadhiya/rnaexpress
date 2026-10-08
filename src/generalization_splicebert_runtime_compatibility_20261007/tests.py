"""Scoped standard-library mock tests: no numerical/model import or inference."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import common, launcher, prepare


class Tests(unittest.TestCase):
    def test_original_guard_before_bootstrap_and_exact_once(self):
        events = []
        def original(root_start=False):
            events.append(("original", root_start))
            return {"resource_admission_now": True, "unchanged": 7}
        def bootstrap(state):
            events.append(("bootstrap", state["unchanged"]))
            return {"verified": True}
        guard = launcher.make_guard(original, bootstrap)
        self.assertEqual(guard(root_start=True), {"resource_admission_now": True, "unchanged": 7,
            "additive_NumPy_runtime_compatibility": {"verified": True}})
        self.assertEqual(events, [("original", True), ("bootstrap", 7)])
        with self.assertRaises(AssertionError):
            guard(root_start=True)
        self.assertEqual(len(events), 2)

    def test_rejected_original_guard_never_bootstraps(self):
        events = []
        def original(root_start=False):
            events.append(root_start)
            assert root_start, "Original explicit authorization"
            raise AssertionError("Original resource/hash failure")
        guard = launcher.make_guard(original, lambda _: events.append("forbidden"))
        with self.assertRaises(AssertionError):
            guard(root_start=False)
        self.assertEqual(events, [False])
        guard = launcher.make_guard(original, lambda _: events.append("forbidden"))
        with self.assertRaises(AssertionError):
            guard(root_start=True)
        self.assertEqual(events, [False, True])

    def test_original_resource_failure_never_bootstraps(self):
        events = []
        guard = launcher.make_guard(lambda root_start: {"resource_admission_now": False},
                                    lambda _: events.append("forbidden"))
        with self.assertRaises(AssertionError):
            guard(root_start=True)
        self.assertEqual(events, [])

    def test_temporary_guard_restores_exact_object_success_and_failure(self):
        original = lambda root_start: {"resource_admission_now": True}
        module = SimpleNamespace(guard=original)
        with launcher.temporary_guard(module, lambda _: {"verified": True}):
            self.assertIsNot(module.guard, original)
            self.assertTrue(module.guard(True)["additive_NumPy_runtime_compatibility"]["verified"])
        self.assertIs(module.guard, original)
        with self.assertRaisesRegex(RuntimeError, "synthetic exception"):
            with launcher.temporary_guard(module, lambda _: {"verified": True}):
                raise RuntimeError("synthetic exception")
        self.assertIs(module.guard, original)

    def test_fresh_process_rejects_preloaded_numerical_and_model_names(self):
        launcher.clean_import_state({"json": object(), "notnumpy": object()})
        for prefix in launcher.BLOCKED_PRELOADED:
            for name in (prefix, prefix + ".child"):
                with self.assertRaises(AssertionError):
                    launcher.clean_import_state({name: object()})

    def test_import_free_origin_resolution_and_wrong_origin(self):
        prefix = Path("synthetic_runtime").resolve()
        with patch.object(sys, "path", list(sys.path)):
            origin = prefix / "numpy/__init__.py"
            seen = []
            def finder(name, paths):
                seen.append((name, paths[0]))
                return SimpleNamespace(origin=str(origin))
            self.assertEqual(launcher.select_prefix(prefix, finder), str(origin))
            self.assertEqual(seen, [("numpy", str(prefix))])
        with patch.object(sys, "path", list(sys.path)):
            with self.assertRaises(AssertionError):
                launcher.select_prefix(prefix, lambda *_: SimpleNamespace(origin=str(Path("wrong/numpy/__init__.py").resolve())))
        with patch.object(sys, "path", list(sys.path)):
            with self.assertRaises(AssertionError):
                launcher.select_prefix(prefix, lambda *_: None)

    def test_native_paths_bind_origin_bytes_and_required_blas(self):
        prefix = Path("synthetic_runtime").resolve()
        files = {"numpy/core/example.cp312-win_amd64.pyd": "pyd", "numpy.libs/openblas.dll": "dll"}
        good = [prefix / name for name in files]
        hasher = lambda path: files[Path(path).relative_to(prefix).as_posix()]
        self.assertEqual(launcher.validate_native_paths(good, files, prefix, hasher), files)
        with self.assertRaises(AssertionError):
            launcher.validate_native_paths([Path("wrong/openblas.dll").resolve()], files, prefix, hasher)
        with self.assertRaises(AssertionError):
            launcher.validate_native_paths(good, files, prefix, lambda _: "changed")
        with self.assertRaises(AssertionError):
            launcher.validate_native_paths(good[:1], files, prefix, hasher)
        with self.assertRaises(AssertionError):
            launcher.validate_native_paths(good, {"numpy/x.dll": "x", "numpy.libs/x.dll": "x"}, prefix, hasher)
        with self.assertRaises(AssertionError):
            launcher.validate_native_paths(good, {"../outside.dll": "x"}, prefix, hasher)

    def test_archive_member_scope_rejects_unsafe_names(self):
        self.assertTrue(prepare.package_member("numpy/__init__.py"))
        self.assertTrue(prepare.package_member("numpy.libs/blas.dll"))
        self.assertFalse(prepare.package_member("numpy/core/"))
        self.assertFalse(prepare.package_member("numpy-1.26.4.dist-info/RECORD"))
        self.assertFalse(prepare.package_member(common.NUMPY_WHEEL))
        for unsafe in ("", "/numpy/x", "numpy/../x", "C:/numpy/x", "numpy\\..\\x"):
            with self.assertRaises(AssertionError):
                prepare.package_member(unsafe)

    def test_current_windows_module_inventory_without_numerical_import(self):
        self.assertEqual(sys.platform, "win32")
        paths = launcher.process_native_paths()
        self.assertIn(Path(sys.executable).resolve(), paths)
        self.assertTrue(any(path.name.lower() == "python312.dll" for path in paths))
        launcher.clean_import_state()

    def test_actual_import_proof_mock_binds_core_and_all_loaded_package_files(self):
        prefix = Path("synthetic_runtime").resolve()
        init = prefix / "numpy/__init__.py"
        core = prefix / "numpy/core/_multiarray_umath.cp312-win_amd64.pyd"
        dll = prefix / "numpy.libs/openblas.dll"
        checksum = "synthetic-byte-hash"
        module = SimpleNamespace(__version__="1.26.4", __file__=str(init))
        native = SimpleNamespace(__file__=str(core))
        files = {path.relative_to(prefix).as_posix(): checksum for path in (init, core, dll)}
        runtime = {"files": files, "numpy_native_files": {core.relative_to(prefix).as_posix(): checksum,
                   dll.relative_to(prefix).as_posix(): checksum}}
        with patch.object(launcher, "PREFIX", prefix), patch.object(launcher, "sha256", lambda _: checksum), \
             patch.object(launcher, "process_native_paths", lambda: [core, dll]), \
             patch.object(launcher, "validate_native_paths", lambda paths, natives: dict(natives)), \
             patch.dict(sys.modules, {"numpy": module, "numpy.core._multiarray_umath": native}):
            proof = launcher.numpy_proof(module, runtime)
            self.assertEqual(proof["numpy_origin"], str(init))
            self.assertEqual(proof["native_core_origin"], str(core))
            self.assertEqual(proof["loaded_NumPy_files"], {init.relative_to(prefix).as_posix(): checksum,
                             core.relative_to(prefix).as_posix(): checksum})
            module.__version__ = "2.4.6"
            with self.assertRaises(AssertionError):
                launcher.numpy_proof(module, runtime)
            module.__version__ = "1.26.4"
            native.__file__ = str(prefix / "numpy/core/_multiarray_umath.cp311-win_amd64.pyd")
            with self.assertRaises(AssertionError):
                launcher.numpy_proof(module, runtime)

    def test_original_source_and_guard_contract_remain_frozen(self):
        frozen = json.loads(common.ORIGINAL_MANIFEST.read_text(encoding="utf-8"))
        key = common.ORIGINAL_SOURCE.relative_to(common.ROOT).as_posix()
        self.assertEqual(common.sha256(common.ORIGINAL_SOURCE), frozen["files"][key])
        tree = ast.parse(common.ORIGINAL_SOURCE.read_text(encoding="utf-8"))
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        # Its first statement still calls the unchanged global guard before imports.
        self.assertIsInstance(run.body[0], ast.Assign)
        self.assertEqual(run.body[0].value.func.id, "guard")
        self.assertIsInstance(run.body[1], ast.Import)
        self.assertEqual(run.body[1].names[0].name, "numpy")
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "guard")
        checks = [node for node in ast.walk(guard) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name) and node.func.id == "resource_state"]
        self.assertEqual(len(checks), 2)


def run():
    launcher.clean_import_state()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    launcher.clean_import_state()
    assert result.wasSuccessful()
    sources = {path.relative_to(common.ROOT).as_posix(): common.sha256(path) for path in sorted(common.SRC.glob("*.py"))}
    for path in common.SRC.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    common.jsave(common.OUT / "synthetic_tests_receipt.json", {"status": "PASS", "test_count": result.testsRun,
        "source_hashes": sources, "scope": "Standard-library-only synthetic/mock tests and unchanged original AST/hash contract",
        "actual_NumPy_imports": 0, "actual_model_package_imports": 0, "actual_backend_calls": 0,
        "project_alleles": 0, "outcomes": False, "supervised_fits": 0})
    print("Additive compatibility scoped tests PASS", result.testsRun, "numerical imports0; backend calls0", flush=True)


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
