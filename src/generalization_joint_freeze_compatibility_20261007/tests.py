"""Scoped stdlib/mock adapter tests, never invoke an actual project freeze."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c
from . import production_freeze_compatibility as a

H = 'a' * 64


def feasibility():
    return {'status': 'PASS', 'project_feature_production': False,
        'project_outcomes_read': False, 'supervised_fit': False,
        'spec': {'absolute_tolerance': 1e-6, 'relative_tolerance': 1e-5, 'unchanged': 'literal'},
        'source_sha256': {'src\\synthetic\\kernel.py': H},
        'unchanged_nested_data': {'x': [1, 2, 3]}}


def payload():
    return {'status': 'FROZEN_JOINT_ACCESSIBILITY_PRODUCTION', 'alleles': 18220,
        'rows': 26258, 'tracks': ['duplicate_marginal', 'joint'],
        'shapes': {'base': 246, 'raw': 502, 'access': 758, 'duplicate_marginal': 1014, 'joint': 1014},
        'production_threads': 1, 'immutable_creation_digests_required': True,
        'synthetic_equivalence_atol': 1e-6, 'synthetic_equivalence_rtol': 1e-5,
        'project_features_exist': False, 'fits_exist': False, 'project_outcomes_read': False,
        'files': {'src/original.py': H}, 'other_preserved': {'a': [1, 2]}}


def saver(writes=None, extra=None, existing=False, hasher=None):
    writes = [] if writes is None else writes
    return a.make_saver(lambda path, value: writes.append((path, value)),
        {'src/additive.py': H} if extra is None else extra,
        {'literal_provenance': 'only_separators'}, target=Path('synthetic_manifest.json'),
        exists=lambda _: existing, hasher=(lambda _: H) if hasher is None else hasher)


class Tests(unittest.TestCase):
    def test_01_only_separator_keys_change(self):
        original = feasibility(); before = copy.deepcopy(original)
        result = c.normalized_receipt(original)
        self.assertEqual(original, before)
        self.assertEqual(result['source_sha256'], {'src/synthetic/kernel.py': H})
        for key in original:
            if key != 'source_sha256':
                self.assertEqual(result[key], original[key])
        self.assertEqual(list(result['source_sha256'].values()), list(original['source_sha256'].values()))

    def test_02_separator_and_case_collisions_rejected(self):
        for values in (
            {'src\\a.py': H, 'src/a.py': H},
            {'src\\a.py': H, 'src/a.py': 'b' * 64},
            {'src/A.py': H, 'src/a.py': H}):
            with self.assertRaises(AssertionError):
                c.normalize_path_keys(values)

    def test_03_absolute_traversal_and_ambiguous_literals_rejected(self):
        for name in ('/src/a', 'C:\\src\\a', '../a', 'src/../a', 'src//a', 'src/./a', '', 'src\x00a'):
            with self.assertRaises(AssertionError):
                c.normalize_path_keys({name: H})

    def test_04_nonhash_or_wrong_validation_receipt_rejected(self):
        for field, value in (('status', 'FAIL'), ('supervised_fit', True), ('project_outcomes_read', True)):
            record = feasibility(); record[field] = value
            with self.assertRaises(AssertionError):
                c.normalized_receipt(record)
        record = feasibility(); record['source_sha256']['src\\synthetic\\kernel.py'] = 'bad'
        with self.assertRaises(AssertionError):
            c.normalized_receipt(record)

    def test_05_tolerances_cannot_change(self):
        record = feasibility(); record['spec']['absolute_tolerance'] = 2e-6
        with self.assertRaises(AssertionError):
            c.normalized_receipt(record)

    def test_06_read_adapter_targets_one_exact_receipt_only(self):
        target = Path('synthetic_feasibility.json').resolve(); calls = []; other = object()
        def original(path):
            calls.append(Path(path).resolve())
            return feasibility() if Path(path).resolve() == target else other
        reader = a.make_reader(original, H, target=target, hasher=lambda _: H)
        self.assertEqual(reader(target)['source_sha256'], {'src/synthetic/kernel.py': H})
        self.assertIs(reader('different.json'), other)
        self.assertEqual(len(calls), 2)

    def test_07_changed_original_receipt_fails_before_read(self):
        reader = a.make_reader(lambda _: self.fail('must not read changed bytes'), H,
            target='synthetic.json', hasher=lambda _: 'b' * 64)
        with self.assertRaises(AssertionError):
            reader('synthetic.json')

    def test_08_save_keeps_every_original_field_entry_and_object(self):
        original = payload(); before = copy.deepcopy(original); writes = []
        save = saver(writes)
        save('synthetic_manifest.json', original)
        self.assertEqual(original, before)
        result = writes[0][1]
        for key in before:
            if key != 'files':
                self.assertEqual(result[key], before[key])
        self.assertEqual(result['files']['src/original.py'], H)
        self.assertEqual(result['files']['src/additive.py'], H)
        self.assertEqual(result['path_compatibility'], {'literal_provenance': 'only_separators'})

    def test_09_repeated_or_unexpected_writes_fail(self):
        save = saver()
        with self.assertRaises(AssertionError):
            save('wrong.json', payload())
        save('synthetic_manifest.json', payload())
        with self.assertRaises(AssertionError):
            save('synthetic_manifest.json', payload())

    def test_10_existing_original_manifest_is_never_overwritten(self):
        with self.assertRaises(AssertionError):
            saver(existing=True)('synthetic_manifest.json', payload())

    def test_11_hash_mismatch_and_changed_original_entry_fail(self):
        with self.assertRaises(AssertionError):
            saver(hasher=lambda _: 'b' * 64)('synthetic_manifest.json', payload())
        extra = {'src/original.py': 'b' * 64}
        with self.assertRaises(AssertionError):
            saver(extra=extra, hasher=lambda _: 'b' * 64)('synthetic_manifest.json', payload())

    def test_12_status_shapes_and_tolerances_cannot_be_widened(self):
        for key, value in (('status', 'OTHER'), ('rows', 1), ('synthetic_equivalence_rtol', 1e-4), ('production_threads', 2)):
            record = payload(); record[key] = value
            with self.assertRaises(AssertionError):
                saver()('synthetic_manifest.json', record)

    def test_13_delegates_original_once_and_restores_exact_bindings(self):
        writes, calls = [], []
        original_read = lambda _: feasibility()
        original_save = lambda path, value: writes.append((path, value))
        module = SimpleNamespace(readj=original_read, jsave=original_save)
        def production():
            calls.append('original-admission-and-freeze')
            self.assertEqual(module.readj('synthetic.json')['source_sha256'], {'src/synthetic/kernel.py': H})
            module.jsave('synthetic_manifest.json', payload())
        module.production = production
        reader = a.make_reader(original_read, H, target='synthetic.json', hasher=lambda _: H)
        save = a.make_saver(original_save, {'src/additive.py': H}, {}, target='synthetic_manifest.json',
            exists=lambda _: False, hasher=lambda _: H)
        a.delegate_once(module, reader, save)
        self.assertEqual(calls, ['original-admission-and-freeze'])
        self.assertIs(module.readj, original_read); self.assertIs(module.jsave, original_save)
        self.assertEqual(len(writes), 1)

    def test_14_failed_original_check_restores_bindings_and_never_saves(self):
        original_read, original_save = object(), object()
        def production():
            raise ValueError('original-admission-failure')
        module = SimpleNamespace(readj=original_read, jsave=original_save, production=production)
        with self.assertRaisesRegex(ValueError, 'original-admission-failure'):
            a.delegate_once(module, lambda _: None, saver())
        self.assertIs(module.readj, original_read); self.assertIs(module.jsave, original_save)

    def test_15_explicit_start_rejected_before_preparation_or_import(self):
        with patch.object(c, 'check_preparation', lambda: self.fail('must not guard/import')):
            with self.assertRaises(AssertionError):
                a.run(root_start=False)

    def test_16_old_final_source_roster_remains_exact17(self):
        receipt = c.readj(c.OLD_TESTS)
        self.assertEqual(receipt['tests'], 22)
        self.assertEqual(set(receipt['source_hashes']), {path.name for path in c.OLD_SRC.glob('*.py')})
        self.assertEqual(len(receipt['source_hashes']), 17)
        for name, expected in receipt['source_hashes'].items():
            self.assertEqual(c.sha256(c.OLD_SRC / name), expected)

    def test_17_original_production_and_prefit_keep_manifest_file_rechecks(self):
        tree = ast.parse((c.OLD_SRC / 'common.py').read_text())
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'manifest_check')
        self.assertTrue(any(isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
            and node.value.id == 'manifest' and isinstance(node.slice, ast.Constant)
            and node.slice.value == 'files' for node in ast.walk(guard)))
        tree = ast.parse((c.OLD_SRC / 'freeze.py').read_text())
        prefit = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'prefit')
        self.assertTrue(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'production_check' for node in ast.walk(prefit)))

    def test_18_stdlib_source_parses_and_four_byte_attributes(self):
        for path in c.SRC.glob('*.py'):
            ast.parse(path.read_text())
        for folder in (c.SRC, c.OUT, c.REP, c.ART):
            self.assertEqual((folder / '.gitattributes').read_bytes(), b'* -text\n')


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful()
    c.jsave(c.OUT / 'synthetic_tests_receipt.json', {'status': 'PASS', 'tests': result.testsRun,
        'source_hashes': {path.relative_to(c.ROOT).as_posix(): c.sha256(path) for path in sorted(c.SRC.glob('*.py'))},
        'plan_sha256': c.sha256(c.PLAN), 'actual_original_freeze_calls': 0,
        'mock_original_freeze_delegations_only': True, 'numeric_or_model_imports': 0,
        'project_outcomes_read': False, 'project_feature_values_read': False,
        'project_production_run': False, 'models_fit': 0})
    print('Additive joint path compatibility synthetic tests PASS', result.testsRun, 'actual original freeze calls0', flush=True)


if __name__ == '__main__':
    run()
