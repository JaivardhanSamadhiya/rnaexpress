"""Meaningful invented threshold and unequal-fold tests; no scientific import."""
import copy
import json
import unittest
from pathlib import Path

from . import gate


def passing():
    primary = {'macro_regret': .48, 'per_cell_regret': {'CAD': .48, 'Neuro-2a': .48}}
    value = {'mean_gain': .01, 'per_cell_gain': {'CAD': .005, 'Neuro-2a': .015},
             'remaining_gain': .001, 'macro_wrong_direction_harm': .02,
             'wrong_direction_harm': {'CAD': .05, 'Neuro-2a': -.01}}
    comparisons = {control: copy.deepcopy(value) for control in ('pooled', 'independent')}
    intervals = {control: [.0001, .02] for control in comparisons}
    return primary, comparisons, intervals


class Tests(unittest.TestCase):
    def test_exact_inclusive_thresholds_pass(self):
        result = gate.thresholds(*passing())
        self.assertEqual(result['status'], 'JOINT_KNOWN_CELL_DEVELOPMENT_GO')
        self.assertFalse(result['unknown_cell_generalization'])
        self.assertFalse(result['localization_generalization_pass'])

    def test_each_cell_uniform_boundary_is_strict(self):
        primary, comparisons, intervals = passing()
        primary['per_cell_regret']['CAD'] = .5
        self.assertEqual(gate.thresholds(primary, comparisons, intervals)['status'], 'NO-GO')

    def test_each_control_must_pass_and_zero_lower_bound_fails(self):
        for control in ('pooled', 'independent'):
            primary, comparisons, intervals = passing()
            intervals[control][0] = 0.
            with self.subTest(control=control):
                self.assertEqual(gate.thresholds(primary, comparisons, intervals)['status'], 'NO-GO')

    def test_other_comparison_conditions_cannot_rescue(self):
        for field in ('mean_gain', 'remaining_gain', 'macro_wrong_direction_harm'):
            primary, comparisons, intervals = passing()
            comparisons['independent'][field] = {'mean_gain': .0099, 'remaining_gain': 0., 'macro_wrong_direction_harm': .0201}[field]
            with self.subTest(field=field):
                self.assertEqual(gate.thresholds(primary, comparisons, intervals)['status'], 'NO-GO')

    def test_nonfinite_interval_rejected(self):
        primary, comparisons, intervals = passing()
        intervals['pooled'][0] = float('nan')
        with self.assertRaises(AssertionError):
            gate.thresholds(primary, comparisons, intervals)

    def test_nonfinite_primary_is_integrity_failure(self):
        primary, comparisons, intervals = passing()
        primary['macro_regret'] = float('nan')
        with self.assertRaises(AssertionError):
            gate.thresholds(primary, comparisons, intervals)

    def test_unequal_fold_removal_reweights_retained_components(self):
        genes = ['a', 'b', 'c', 'd', 'e', 'f']
        folds = dict(zip(genes, [0, 1, 1, 1, 1, 2]))
        gains = dict(zip(genes, [.3, .1, .1, .1, .1, -.1]))
        candidate = {key: {cell: {gene: .2 if key == 'regret' else 0. for gene in genes} for cell in gate.CELLS}
                     for key in ('regret', 'wrong_direction')}
        control = copy.deepcopy(candidate)
        for cell in gate.CELLS:
            for gene in genes:
                control['regret'][cell][gene] += gains[gene]
        result = gate.compare_components(candidate, control, folds)
        self.assertEqual(result['removed_best_gene_fold'], 0)
        self.assertAlmostEqual(result['remaining_gain'], .06)
        self.assertNotAlmostEqual(result['remaining_gain'], 0.)  # unequal-fold mean would be0

    def test_best_fold_tie_uses_smallest_fold(self):
        candidate = {key: {cell: {gene: 0. for gene in ('a', 'b', 'c')} for cell in gate.CELLS}
                     for key in ('regret', 'wrong_direction')}
        result = gate.compare_components(candidate, copy.deepcopy(candidate), {'a': 0, 'b': 1, 'c': 2})
        self.assertEqual(result['removed_best_gene_fold'], 0)

    def test_changed_component_roster_rejected(self):
        candidate = {key: {cell: {gene: 0. for gene in ('a', 'b', 'c')} for cell in gate.CELLS}
                     for key in ('regret', 'wrong_direction')}
        control = copy.deepcopy(candidate)
        del control['regret']['CAD']['c']
        with self.assertRaises(AssertionError):
            gate.compare_components(candidate, control, {'a': 0, 'b': 1, 'c': 2})


if __name__ == '__main__':
    import sys
    from src.generalization_prelib_numpy_profile_20261022.invented import ROOT, sha
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    assert not any(name == prefix or name.startswith(prefix + '.')
                   for name in sys.modules for prefix in ('numpy', 'pandas', 'scipy', 'torch'))
    out = ROOT / 'results/generalization_knowncell_joint_gate_20261023'
    out.mkdir(parents=True, exist_ok=True)
    (out / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    receipt = {'status': 'PASS_INVENTED_GATE_THRESHOLD_AND_COMPONENT_WEIGHT_CHECKS',
               'tests': result.testsRun, 'source_files': {p.relative_to(ROOT).as_posix(): sha(p)
                   for p in Path(__file__).resolve().parent.glob('*.py')},
               'scientific_runtime_imported': False, 'native_bootstrap_run': False,
               'project_payloads_read': False, 'project_gate_run': False}
    with (out / 'synthetic_tests_reviewed_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
