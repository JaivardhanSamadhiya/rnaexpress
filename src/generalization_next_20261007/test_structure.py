"""Synthetic ensemble/motif checks; no research outcome fitting."""

import unittest
from .route_structure import np, RNA, TEMPERATURE, ensemble, partition, summaries, structure_delta, encoded_pair, certified_arms, raw_delta, build_features, unit_unpaired_summary


class StructureTests(unittest.TestCase):
    def test_unpaired_marginal_matches_independent_partition_constraint(self):
        sequence = "GGGGAAAACCCC"
        unpaired, entropy, distance, energy = ensemble(sequence)
        rt = RNA.GASCONST * (273.15 + TEMPERATURE) / 1000.
        for index in (0, 5, 11):
            _, constrained_energy = partition(sequence, (index,))
            expected = np.exp(-(constrained_energy - energy) / rt)
            self.assertAlmostEqual(unpaired[index], expected, delta=2e-6)
        self.assertTrue(np.all((unpaired >= 0) & (unpaired <= 1)))
        self.assertTrue(np.all(entropy >= -1e-12))
        self.assertTrue(np.all((distance >= 0) & (distance <= 1)))

    def test_accessible_complete_motif_on_unstructured_sequence(self):
        result = summaries("CCTCCC", [2])
        np.testing.assert_allclose(result[:4], 1., atol=1e-12)
        np.testing.assert_allclose(result[-2:], 1., atol=1e-12)
        self.assertEqual(result[6], 0.)
        self.assertEqual(result[7], 0.)
        self.assertEqual(result[8], 0.)

    def test_exact_null_reversal_and_certified_coordinate_shift(self):
        parent, mutant = "GGGGAAAACCCC", "GGGGACAACCCC"
        np.testing.assert_array_equal(structure_delta(parent, parent, "mikl_gse173098"), np.zeros(11))
        np.testing.assert_array_equal(structure_delta(parent, mutant, "mikl_gse173098"), -structure_delta(mutant, parent, "mikl_gse173098"))
        encoded_parent, encoded_mutant, positions = encoded_pair("AACCCC", "AATCCC", "srle")
        left, right = certified_arms()
        self.assertEqual(encoded_parent, left + "AACCCC" + right)
        self.assertEqual(len(encoded_parent), 46)
        np.testing.assert_array_equal(positions, [22])

    def test_invalid_context_or_sequences_rejected(self):
        for parent, mutant, dataset in (("AAAA", "AAAT", "srle"), ("AACN", "AACT", "mikl_gse173098"),
                                        ("AAA", "AAAA", "mikl_gse173098"), ("AAAA", "AAAT", "unknown")):
            with self.assertRaises(ValueError):
                encoded_pair(parent, mutant, dataset)

    def test_raw_control_exact_arithmetic_and_no_folding(self):
        from unittest.mock import patch
        with patch("src.generalization_next_20261007.route_structure.ensemble", side_effect=AssertionError("Raw control must not fold")):
            np.testing.assert_allclose(raw_delta("AAAG", "AAAC", "mikl_gse173098"), [-.25, -1 / 3, 0., 0., 0.], atol=1e-15)
            expected = raw_delta("CCTCCG", "CCTCCC", "mikl_gse173098")
            np.testing.assert_array_equal(expected[-2:], [1., 1.])
            np.testing.assert_array_equal(expected, -raw_delta("CCTCCC", "CCTCCG", "mikl_gse173098"))
            np.testing.assert_array_equal(raw_delta("CCTCCC", "CCTCCC", "mikl_gse173098"), np.zeros(5))

    def test_raw_and_ensemble_column_order_with_injected_summaries(self):
        import pandas as pd
        frame = pd.DataFrame({"parent_sequence": ["AAAG"], "mutant_sequence": ["AAAC"], "dataset": ["mikl_gse173098"]})
        result = build_features(frame, np.zeros((1, 246)), summary_provider=unit_unpaired_summary)
        self.assertEqual(result.shape, (1, 262))
        expected = raw_delta("AAAG", "AAAC", "mikl_gse173098")
        np.testing.assert_array_equal(result[0, 246:251], expected)
        np.testing.assert_array_equal(result[0, 251:257], np.zeros(6))
        np.testing.assert_array_equal(result[0, 257:], expected)


if __name__ == "__main__":
    unittest.main()
