"""Fail-closed synthetic tests; no research data or scientific imports."""
import tempfile
import unittest
from pathlib import Path
from .admit import summaries, check_files, digest, CONTROLS


def invented():
    pins = {'results/generalization_rbp_20261007/canonical_source_only_replay.json': 'canonical'}
    replay = {'status': 'PASS', 'models_fit': 0, 'files': {}}
    for track in CONTROLS:
        for filename in ('decisions.csv', 'comparison.csv', 'run_complete.json'):
            name = 'results/generalization_rbp_20261007/' + track + '/' + filename
            pins[name] = track + filename
            if filename != 'comparison.csv': replay['files'][name] = pins[name]
    audit = {'status': 'PASS_INDEPENDENT_RBP_POINT_METRICS_AND_GATE_ARITHMETIC', 'new_models_fitted': 0,
        'canonical_checkpoint_replay_receipt_bound': True, 'all_three_complete_decision_rosters_equal': True,
        'criteria_or_old_files_changed': False, 'protected_outcomes_read': False,
        'maximum_absolute_numeric_error': 1e-16, 'numeric_values_checked': 32922, 'boolean_checks_checked': 45,
        'observed_input_sha256_postfit_not_creation_binding': pins}
    return replay, audit, pins


class GuardTests(unittest.TestCase):
    def test_separate_binding_allows_honest_absent_canonical_comparisons(self):
        r, a, pins = invented()
        self.assertEqual(len(summaries(r, a, pins.__getitem__)), 9)

    def test_missing_comparison_rejected(self):
        r, a, pins = invented(); actual = dict(pins); key = 'results/generalization_rbp_20261007/raw/comparison.csv'
        del a['observed_input_sha256_postfit_not_creation_binding'][key]
        with self.assertRaises(KeyError): summaries(r, a, actual.__getitem__)

    def test_changed_comparison_rejected(self):
        r, a, pins = invented()
        with self.assertRaises(AssertionError): summaries(r, a, lambda name: 'wrong' if name.endswith('comparison.csv') else pins[name])

    def test_changed_canonical_decisions_rejected(self):
        r, a, pins = invented(); r['files']['results/generalization_rbp_20261007/base/decisions.csv'] = 'wrong'
        with self.assertRaises(AssertionError): summaries(r, a, pins.__getitem__)

    def test_failed_audit_rejected(self):
        r, a, pins = invented(); a['status'] = 'FAILED'
        with self.assertRaises(AssertionError): summaries(r, a, pins.__getitem__)

    def test_threshold_changes_rejected(self):
        r, a, pins = invented(); a['criteria_or_old_files_changed'] = True
        with self.assertRaises(AssertionError): summaries(r, a, pins.__getitem__)

    def test_workspace_escape_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(AssertionError): check_files({'../escape': 'x'}, Path(folder))

    def test_hash_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); p = root / 'input'; p.write_bytes(b'original'); original = digest(p)
            check_files({'input': original}, root)
            p.write_bytes(b'changed')
            with self.assertRaises(AssertionError): check_files({'input': original}, root)

    def test_alias_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); p = root / 'input'; p.write_bytes(b'original')
            with self.assertRaises(AssertionError): check_files({'input': digest(p), './input': digest(p)}, root)


if __name__ == '__main__':
    unittest.main()
