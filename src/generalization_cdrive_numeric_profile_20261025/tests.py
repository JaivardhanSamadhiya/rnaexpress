"""Invented stdlib-only contract tests; no software payload/native/job reads."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from . import spec, runtime
from .contracts import (canonical, compare_results, decode, digest, inventory_contract,
                        native_maps, resource_failure, validate_child)


def fixture():
    old = {'fake/component_%04d.py' % index: '0' * 64 for index in range(7996)}
    files = dict(old, **spec.ADDITIONAL_CACHES)
    home = spec.EXPECTED_PYTHON.parent
    native = {str(home / name): want for name, want in spec.ANCHORS.items()}
    native.update({str(home / 'DLLs' / ('invented%02d.pyd' % index)): '1' * 64 for index in range(39)})
    inventory = {
        'status': spec.INVENTORY_STATUS,
        'private_material_verification_sha256':spec.MATERIAL_VERIFICATION_SHA,
        'storage_relocation_explicitly_verified':True,
        'actual_selected_scientific_prefix':str(spec.PREFIX),
        'initial_preparation_manifest_sha256': spec.INVENTORY_MANIFEST_SHA,
        'scientific_packages_imported': False, 'actually_loaded_python_DLL_origins_verified': False,
        'numerical_compatibility_established': False, 'biological_inputs_read': False,
        'biological_model_fits': 0, 'stage_authority_granted': False,
        'historical_V4_acceptance_reused_for_new_Python': False,
        'native_discovery_sha256': spec.DISCOVERY_SHA,
        'current_bundled_stdlib_native_files': native, 'current_native_file_count': 42,
        'changed_native_file_count': 38, 'selected_scientific_payload_files': files,
        'selected_scientific_payload_file_count': 7998,
        'two_explicit_possible_cache_payloads': spec.ADDITIONAL_CACHES,
        'unchanged_versions_from_package_metadata': {'numpy': '1.26.4', 'pandas': '2.2.3', 'scipy': '1.14.1'},
    }
    return inventory, {'current_native_files': native}, {'files': old, 'native_files': {}}, \
        {'files': files, 'native_files': {}}, {'files': files}


def results_fixture():
    return {'parser': {'status': 'PASS_INVENTED_EXACT_DEFERRED_PARSER', 'invented': ['-0.0']},
            'optimizer': {'status': 'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER',
                          'scipy_optimizer_units': 12, 'biological_model_fits': 0, 'gradient': 1e-12},
            'extra_deferred_native_contracts': {'array_contract': {'bits': '00'}, 'shared_bootstrap': {'draws': 5000}}}


class Cases(unittest.TestCase):
    def test_fixed_full_inventory_contract_invented_maps(self):
        result = inventory_contract(*fixture())
        self.assertEqual([len(value) for value in result], [7998, 0, 42, 3])

    def test_payload_NumPy_count_is_derived_not_guessed_no_actual_payload(self):
        inventory, discovery, base, expanded, old_runtime = fixture()
        new_names = ('numpy/__init__.py', 'numpy.libs/invented.txt', 'numpy-1.26.4.dist-info/METADATA')
        for old_name, new_name in zip(list(base['files'])[:3], new_names):
            base['files'][new_name] = base['files'].pop(old_name)
        files = dict(base['files'], **spec.ADDITIONAL_CACHES)
        inventory['selected_scientific_payload_files'] = expanded['files'] = old_runtime['files'] = files
        inventory.update(python_version=sys.version, python_cache_tag='cpython-312')
        old_runtime.update(status='PASS', numpy_version='1.26.4', numpy_native_files={})
        supplied = {spec.INVENTORY: inventory, spec.DISCOVERY: discovery, spec.BASE_INVENTORY: base,
                    spec.EXPANDED_INVENTORY: expanded, spec.OLD_RUNTIME: old_runtime}
        with tempfile.TemporaryDirectory() as folder:
            prefix = Path(folder)
            for key in new_names:
                path = prefix / key; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'invented')
            def fake_sha(path):
                return inventory['current_bundled_stdlib_native_files'].get(str(path), '0' * 64)
            manifest = {'files': {spec.INVENTORY.relative_to(spec.ROOT).as_posix(): '3' * 64}}
            inventory['actual_selected_scientific_prefix']=str(prefix)
            with patch.object(spec, 'PREFIX', prefix), patch.object(runtime, 'sha', side_effect=fake_sha), \
                 patch.object(runtime, 'bound_document', side_effect=lambda _, path: supplied[path]):
                _, _, proof = runtime.current_payload(manifest)
        self.assertEqual(proof['fresh_NumPy_payload_files'], 3)
        self.assertEqual(len(proof['derived_current_python_three']), 3)

    def test_failed_inventory_never_admitted(self):
        values = list(fixture())
        for bad in ('FAILED_REFRESH_V2_ATTEMPT_PRESERVED_NO_RETRY', 'PASS'):
            values[0]['status'] = bad
            with self.assertRaisesRegex(AssertionError, 'Successful fresh'):
                inventory_contract(*values)

    def test_incomplete_or_drifted_payload_rejected(self):
        for action in ('remove', 'change', 'add'):
            values = list(fixture())
            selected = copy.deepcopy(values[0]['selected_scientific_payload_files'])
            if action == 'remove': selected.pop(next(iter(selected)))
            if action == 'change': selected[next(iter(selected))] = '9' * 64
            if action == 'add': selected['unreviewed/file.py'] = '9' * 64
            values[0]['selected_scientific_payload_files'] = selected
            with self.subTest(action=action), self.assertRaises(AssertionError):
                inventory_contract(*values)

    def test_exact_current42_and_new3_not_old3(self):
        inventory, discovery, *_ = fixture()
        current, three = native_maps(inventory, discovery)
        self.assertEqual(len(current), 42)
        self.assertEqual({Path(name).name.casefold(): want for name, want in three.items()}, spec.ANCHORS)
        changed = copy.deepcopy(inventory)
        changed['current_bundled_stdlib_native_files'][next(iter(three))] = '9' * 64
        with self.assertRaises(AssertionError): native_maps(changed, discovery)
        changed_discovery = copy.deepcopy(discovery)
        changed_discovery['current_native_files'] = changed['current_bundled_stdlib_native_files']
        with self.assertRaises(AssertionError): native_maps(changed, changed_discovery)

    def test_false_stage_authority_and_historical_reuse_rejected(self):
        for key in ('stage_authority_granted', 'historical_V4_acceptance_reused_for_new_Python', 'scientific_packages_imported'):
            values = list(fixture()); values[0][key] = True
            with self.subTest(key=key), self.assertRaises(AssertionError): inventory_contract(*values)

    def test_duplicate_and_nonfinite_json_rejected(self):
        with self.assertRaises(AssertionError): decode(b'{"x":1,"x":2}')
        for token in (b'NaN', b'Infinity', b'-Infinity'):
            with self.assertRaises(ValueError): decode(b'{"x":' + token + b'}')
        with self.assertRaises(ValueError): canonical({'x': float('nan')})

    def test_all_three_result_views_required_exactly(self):
        baseline = results_fixture()
        self.assertEqual(set(compare_results(copy.deepcopy(baseline), baseline)), set(baseline))
        for key in baseline:
            changed = copy.deepcopy(baseline); changed[key]['changed'] = 1
            with self.subTest(key=key), self.assertRaisesRegex(AssertionError, 'differs'):
                compare_results(changed, baseline)

    def test_wrong_optimizer_units_and_science_claim_rejected(self):
        for key, bad in (('scipy_optimizer_units', 11), ('biological_model_fits', 1)):
            changed = results_fixture(); changed['optimizer'][key] = bad
            with self.assertRaises(AssertionError): compare_results(changed, changed)

    def test_native_classifier_rejects_unpinned_bundled_and_redirected_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); prefix = base / 'prefix'; home = base / 'python'
            bundled = home / 'DLLs' / 'x.pyd'; scientific = prefix / 'numpy.libs' / 'blas.dll'
            current = {str(bundled.resolve()): '1' * 64}; native = {'numpy.libs/blas.dll': '2' * 64}
            hashes = {str(bundled.resolve()): '1' * 64, str(scientific.resolve()): '2' * 64}
            actual = runtime.classify_loaded_native([bundled, scientific], native, current,
                prefix=prefix, home=home, hasher=lambda path: hashes[str(path)])
            self.assertEqual([len(value) for value in actual], [1, 1])
            for wrong in (home / 'DLLs/unknown.dll', base / 'elsewhere/x.pyd', base / 'elsewhere/blas.dll'):
                with self.subTest(path=wrong), self.assertRaises(AssertionError):
                    runtime.classify_loaded_native([wrong], native, current, prefix=prefix, home=home, hasher=lambda _: '1' * 64)

    def test_native_classifier_detects_changed_loaded_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); native = base / 'python/DLLs/x.pyd'
            with self.assertRaises(AssertionError):
                runtime.classify_loaded_native([native], {}, {str(native.resolve()): '1' * 64},
                    prefix=base / 'prefix', home=base / 'python', hasher=lambda _: '2' * 64)

    def test_resources_exact_boundaries_and_final_deadline(self):
        state = {'physical_available': 512 * 2**20, 'commit_headroom': 1920 * 2**20, 'disk_available': 2**30}
        self.assertIsNone(resource_failure(state, 150, startup=True))
        self.assertIn('deadline', resource_failure(state, 150.000001))
        for key in state:
            changed = dict(state); changed[key] = {'physical_available': 256 * 2**20,
                'commit_headroom': 2**30, 'disk_available': 2**30}[key] - 1
            with self.subTest(key=key): self.assertIsNotNone(resource_failure(changed, 10))
        for value in (float('nan'), float('inf'), -1):
            with self.assertRaises(AssertionError): resource_failure(state, value)

    def test_child_completion_requires_three_full_hashes_and_all_views(self):
        results = results_fixture(); sha = '4' * 64
        child = {'status': spec.CHILD_PASS, 'parent_pid': 5, 'child_pid': 7,
            'preparation_manifest_sha256': sha, 'bytes': spec.BYTES, 'hashes': ['8' * 64] * 3,
            'invented_optimizer_units': 12, 'biological_rows_read': 0, 'biological_model_fits': 0,
            'results': results, 'canonical_result_sha256': compare_results(results, results)}
        validate_child(child, results, sha, 5, 7, '8' * 64)
        for key, bad in (('parent_pid', 6), ('bytes', 16 * 2**20), ('hashes', ['8' * 64] * 2), ('biological_rows_read', 1)):
            changed = dict(child); changed[key] = bad
            with self.subTest(key=key), self.assertRaises(AssertionError): validate_child(changed, results, sha, 5, 7, '8' * 64)

    def test_deferred_bootstrap_gates_each_six_imports_without_native_calls(self):
        from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
        observed = []
        modules = [types.SimpleNamespace() for _ in range(6)]
        modules[3].minimize = object(); modules[4].expit = object()
        def fake_import(name):
            observed.append(('import', name)); return modules[sum(item[0] == 'import' for item in observed) - 1]
        def fresh(): observed.append(('fresh', None))
        with patch.dict('os.environ', spec.THREAD_ENV), patch.object(launcher, 'clean_import_state'), \
             patch.object(runtime, 'current_payload', return_value=({}, {}, {})), \
             patch.object(runtime, 'select_closed_scientific_path'), \
             patch.object(runtime.importlib, 'import_module', side_effect=fake_import):
            value = runtime.bootstrap({}, fresh)
        self.assertEqual(len(value), 9)
        self.assertEqual(sum(item[0] == 'fresh' for item in observed), 7)
        self.assertEqual([item[1] for item in observed if item[0] == 'import'],
                         ['numpy', 'pandas', 'scipy', 'scipy.optimize', 'scipy.special', 'threadpoolctl'])
        self.assertTrue(all(observed[index - 1][0] == 'fresh' for index, item in enumerate(observed) if item[0] == 'import'))

    def test_source_delegation_and_no_old_runtime_bootstrap(self):
        tree = ast.parse((spec.SRC / 'runtime.py').read_text(encoding='utf8'))
        imported = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertNotIn('src.generalization_knowncell_parser_profile_v3_20261023.runtime', imported)
        source = (spec.SRC / 'runtime.py').read_text(encoding='utf8')
        self.assertIn('attest.native_python(three)', source)
        self.assertNotIn('attest.check(', source)
        self.assertNotIn('attest.ATTESTATION', source)
        probe = ast.parse((spec.SRC / 'probe.py').read_text(encoding='utf8'))
        expected = {'parser_profile', 'optimizer_profile', 'extras_v2'}
        actual = {node.module.rsplit('.', 1)[-1] for node in ast.walk(probe)
                  if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('src.generalization_knowncell_parser_profile_20261022.')}
        self.assertEqual(actual, expected)


def run_tests():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name == 'numpy' or name.startswith(('numpy.', 'scipy.', 'pandas.')) for name in sys.modules)
    value = {'status': 'PASS_STDLIB_INVENTED_CURRENT42_NUMERIC_SOURCE_CONTRACTS',
             'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
             'source_sha256': {path.relative_to(spec.ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(spec.SRC.glob('*.py'))},
             'scientific_imports_native_jobs_biological_reads': 0,
             'actual_fresh_inventory_read': False, 'native_compatibility_established': False}
    with (spec.OUT / 'synthetic_tests_receipt_reviewed.json').open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print('INVENTED_SOURCE_TESTS_ONLY', result.testsRun, digest((spec.OUT / 'synthetic_tests_receipt_reviewed.json').read_bytes()))


if __name__ == '__main__':
    run_tests()
