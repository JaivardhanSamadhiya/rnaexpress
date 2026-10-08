"""Invented-sequence tests only; no project data/model reader or estimator fit."""
import json
import math
from pathlib import Path
import time
import unittest
from . import backend as b


class BackendTests(unittest.TestCase):
    def test_01_normalization_and_invalid_input(self):
        self.assertEqual(b.normalize('atgc'), 'AUGC')
        for value in ('', 'NNN', 'AC-G'):
            with self.assertRaises(ValueError):
                b.normalize(value)

    def test_02_exact_model_controls(self):
        a, c = b.model_details(0), b.model_details(1)
        for name in ('temperature', 'dangles', 'min_loop_size', 'noGU', 'noGUclosure',
                     'circ', 'salt', 'max_bp_span', 'betaScale', 'pf_smooth', 'noLP', 'special_hp'):
            self.assertEqual(getattr(a, name), getattr(c, name))
        self.assertEqual((a.gquad, c.gquad), (0, 1))
        self.assertEqual((a.temperature, a.dangles, a.min_loop_size, a.salt, a.max_bp_span), (37., 2, 3, 1.021, -1))
        with self.assertRaises(ValueError):
            b.model_details(2)

    def test_03_native_RECORD_identity(self):
        identity = b.runtime_identity()
        self.assertTrue(identity['installed_RECORD_matches_selected_files'])
        self.assertFalse(identity['binary_recompiled_from_inspected_source'])

    def test_04_official_source_integrity(self):
        self.assertEqual(len(b.source_guard()), 30)

    def test_05_exact_two_layer_pattern_and_disruption(self):
        self.assertEqual(list(b.gq_patterns('GGAGGAGGAGG')), [(0, 11, 2, (1, 1, 1))])
        self.assertEqual(list(b.gq_patterns('GAAGGAGGAGG')), [])

    def test_06_positive_and_negative_native_cases(self):
        self.assertGreater(b.measure('GGAGGAGGAGG')['modeled_at_least_one_GQ_probability'], .99)
        self.assertEqual(b.measure('A' * 32)['modeled_at_least_one_GQ_probability'], 0.)
        self.assertEqual(b.measure('GAAGGAGGAGG')['modeled_at_least_one_GQ_probability'], 0.)

    def test_07_GQ_only_independent_state_partition(self):
        for sequence in ('GGAGGAGGAGG', 'GGGAGGGAGGGAGGG', 'G' * 32,
                         'GG' + ('A' * 15 + 'GG') * 3):
            reference, actual = b.gq_only_partition(sequence), b.measure(sequence)
            self.assertTrue(math.isclose(reference['G_kcal_mol'], actual['on']['G_kcal_mol'],
                abs_tol=b.EVENT_ABS_TOL, rel_tol=b.EVENT_REL_TOL))
            self.assertTrue(math.isclose(reference['probability_at_least_one'], actual['modeled_at_least_one_GQ_probability'],
                abs_tol=b.EVENT_ABS_TOL, rel_tol=b.EVENT_REL_TOL))

    def test_08_probability_is_not_expected_event_count(self):
        reference = b.gq_only_partition('GGAGGAGGAGG' + 'A' + 'GGAGGAGGAGG')
        self.assertGreater(reference['expected_GQ_count'], 1.)
        self.assertLessEqual(reference['probability_at_least_one'], 1.)

    def test_09_ordinary_energy_weight_equality(self):
        for sequence in ('GGGAAACCC', 'GGAGGAGGAGGCCCCC'):
            a = b.RNA.fold_compound(sequence, b.model_details(0))
            c = b.RNA.fold_compound(sequence, b.model_details(1))
            for structure in b.ordinary_structures(sequence):
                self.assertAlmostEqual(a.eval_structure(structure), c.eval_structure(structure), delta=b.ENERGY_ABS_TOL)

    def test_10_native_thermodynamic_temperature(self):
        _, result = b.fold('GGAGGAGGAGG', 1)
        self.assertAlmostEqual(result['kT_kcal_mol'], 310.15 * .00198717, places=12)

    def test_11_compute_bpp_energy_parity(self):
        for switch in (0, 1):
            _, a = b.fold('GGAGGAGGAGGCCCCC', switch, 0)
            _, c = b.fold('GGAGGAGGAGGCCCCC', switch, 1)
            self.assertAlmostEqual(a['G_kcal_mol'], c['G_kcal_mol'], delta=b.ENERGY_ABS_TOL)

    def test_12_all_four_input_lengths_and_original_API(self):
        for length in b.LENGTHS:
            sequence = 'A' * (length - 11) + 'GGAGGAGGAGG'
            result = b.measure(sequence)
            _, original = b.next_partition(sequence)
            self.assertAlmostEqual(result['off']['G_kcal_mol'], original, delta=b.ENERGY_ABS_TOL)
            self.assertTrue(0 <= result['modeled_at_least_one_GQ_probability'] <= 1)

    def test_13_no_edit_exact_zero(self):
        self.assertEqual(b.delta('GGAGGAGGAGG', 'GGAGGAGGAGG'), [0., 0.])

    def test_14_reversal_exact_antisymmetry(self):
        forward = b.delta('GGAGGAGGAGG', 'GAAGGAGGAGG')
        reverse = b.delta('GAAGGAGGAGG', 'GGAGGAGGAGG')
        self.assertEqual(forward, [-value for value in reverse])
        with self.assertRaises(ValueError):
            b.delta('AAA', 'AAAA')

    def test_15_event_numeric_stability(self):
        value = b.event_probability(-1e-12, 0., 1.)
        self.assertGreater(value, 0.)
        self.assertAlmostEqual(value, 1e-12, delta=1e-23)

    def test_16_invalid_non_nested_and_nonfinite_inputs(self):
        for values in ((1., 0., 1.), (math.nan, 0., 1.), (0., 0., 0.)):
            with self.assertRaises((ValueError, ArithmeticError)):
                b.event_probability(*values)
        with self.assertRaises(ValueError):
            b.gq_only_partition('GGC')

    def test_17_synthetic_inventory_fixed_and_complete(self):
        items = b.synthetic_inputs()
        self.assertEqual(items, b.synthetic_inputs())
        self.assertEqual(len(items), 12)
        self.assertEqual({len(sequence) for _, sequence in items}, set(b.LENGTHS))
        self.assertEqual(len({name for name, _ in items}), len(items))

    def test_18_opaque_parameter_addresses_not_compared(self):
        a = b.RNA.fold_compound('GGAGGAGGAGGCCCCC', b.model_details(0))
        c = b.RNA.fold_compound('GGAGGAGGAGGCCCCC', b.model_details(1))
        av, ao = b.ordinary_parameter_snapshot(a.params)
        cv, co = b.ordinary_parameter_snapshot(c.params)
        self.assertEqual(av, cv)
        self.assertEqual(ao, co)
        self.assertEqual(len(av), 21)
        self.assertEqual(len(ao), 9)


def run():
    b.environment()
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BackendTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'status': 'PASS' if result.wasSuccessful() else 'FAIL',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'elapsed_seconds': time.perf_counter() - start,
        'synthetic_only': True, 'models_fit': 0, 'project_alleles_folded': 0,
        'labels_read': False, 'models_read': False, 'project_feature_arrays_read': False,
        'files': {path.relative_to(b.ROOT).as_posix(): b.sha256(path)
            for path in list(b.SRC.glob('*.py')) + [b.REP / 'feasibility_protocol.md', b.REP / 'implementation_incident.md']
            + [folder / '.gitattributes' for folder in (b.SRC, b.OUT, b.REP, b.ART)]}}
    b.save_json(b.OUT / 'synthetic_tests_receipt_reviewed.json', receipt)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    run()
