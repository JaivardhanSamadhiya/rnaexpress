"""Invented resource boundaries and restoration tests; no native numerical import."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from . import worker


class ResourceTests(unittest.TestCase):
    def good(self):
        return {'physical_available': 512 * 2**20,
                'commit_headroom': 896 * 2**20 + 2**30, 'disk_available': 2**30}

    def test_exact_boundary_admitted(self):
        self.assertEqual(worker.resource_guard(self.good()), 512 * 2**20)

    def test_each_reserve_one_byte_short_rejected(self):
        for name in self.good():
            state = self.good()
            state[name] -= 1
            with self.subTest(name=name), self.assertRaises(AssertionError):
                worker.resource_guard(state)

    def test_restores_callbacks_after_exception(self):
        original = [lambda: 3, lambda: None, lambda *args: None]
        gate = SimpleNamespace(fresh=original[0], numpy_runtime=original[1], save=original[2])
        with self.assertRaisesRegex(RuntimeError, 'invented'):
            with worker.scoped_callbacks(gate, 'prefit', 'invented', guard=lambda: 4) as counts:
                self.assertEqual(gate.fresh(), 4)
                self.assertEqual(counts['fresh_guard_calls'], 1)
                raise RuntimeError('invented')
        self.assertEqual([gate.fresh, gate.numpy_runtime, gate.save], original)

    def test_only_completion_metadata_augmented(self):
        written = []
        gate = SimpleNamespace(fresh=lambda: 3, numpy_runtime=lambda: None,
                               save=lambda *args: written.append(args))
        payload = {'invented_values': [1, 2, 3]}
        with worker.scoped_callbacks(gate, 'features', 'invented', guard=lambda: 4):
            gate.save(Path('anonymous_checkpoint.json'), payload, True)
            gate.save(worker.BIO / worker.COMPLETION['features'], payload)
        self.assertIs(written[0][1], payload)
        self.assertTrue(written[0][2])
        self.assertNotIn('operational_admission', payload)
        self.assertEqual(written[1][1]['invented_values'], [1, 2, 3])
        self.assertEqual(written[1][1]['operational_admission']['stage'], 'features')

    def test_no_authorization_placeholder_exists(self):
        # Tests must never manufacture a human approval token.
        self.assertFalse(worker.AUTH.exists())

    def test_predecessor_rejects_every_wrong_binding(self):
        good = {'status': 'PASS_BOUNDED_ORIGINAL_PRELIB_STAGE', 'phase': 'features',
                'execution_manifest_sha256': 'manifest', 'scientific_completion_sha256': 'completion',
                'worker_receipt_sha256': 'worker', 'frozen_sources_unchanged': True, 'exit_code': 0}
        worker.check_predecessor_binding(good, 'features', 'manifest', 'completion', 'worker')
        for key in good:
            bad = dict(good)
            bad[key] = 'STALE_OR_MUTATED'
            with self.subTest(key=key), self.assertRaises(AssertionError):
                worker.check_predecessor_binding(bad, 'features', 'manifest', 'completion', 'worker')

    def test_worker_rejects_wrong_phase_manifest_completion_or_guard_count(self):
        good = {'status': 'ORIGINAL_PRELIB_STAGE_COMPLETE_CALLBACKS_RESTORED', 'phase': 'features',
                'execution_manifest_sha256': 'manifest', 'completion_sha256': 'completion',
                'scientific_sources_unchanged': True, 'callbacks_restored': True,
                'fresh_guard_calls': 10, 'current_python_numpy_bootstraps': 1}
        worker.check_worker_binding(good, 'features', 'manifest', 'completion')
        for key in good:
            bad = dict(good)
            bad[key] = 'WRONG'
            with self.subTest(key=key), self.assertRaises(AssertionError):
                worker.check_worker_binding(bad, 'features', 'manifest', 'completion')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ResourceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    blocked = ('numpy', 'torch', 'scipy', 'sklearn', 'pandas', 'openvino', 'transformers')
    assert not any(name == prefix or name.startswith(prefix + '.') for name in sys.modules for prefix in blocked)
    worker.OUT.mkdir(parents=True, exist_ok=True)
    (worker.OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    worker.save(worker.OUT / 'synthetic_tests_reviewed_receipt.json', {
        'status': 'PASS_INVENTED_RESOURCE_BOUNDARIES_AND_SCOPED_CALLBACK_RESTORATION',
        'test_cases': result.testsRun, 'reserve_rejection_subcases': 3,
        'test_source_sha256': worker.sha(__file__), 'numpy_imported': False,
        'source_files': {p.relative_to(worker.ROOT).as_posix(): worker.sha(p)
                         for p in Path(__file__).resolve().parent.glob('*.py')},
        'biological_inputs_read': False, 'biological_models_fit': 0,
        'authorization_created': False,
    })
