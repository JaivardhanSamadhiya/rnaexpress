"""Scoped tests of feature semantics on synthetic sequences, without outcomes."""

import unittest

from .route_mechanism import (
    np, SUMMARY_NAMES, MECHANISM_NAMES, CONFIGS, motif_starts,
    affected_starts, summarize, mechanism_delta, build_features, feature_schema,
)


class MechanismTests(unittest.TestCase):
    def test_overlapping_core_and_leading_purine(self):
        sequence = "ACCTCCCACCTCCCTCCTCCC"
        self.assertEqual(motif_starts(sequence, "[AG]CCTCCC"), (0, 7))
        self.assertEqual(motif_starts("CCTCCTCC", "CCTCC"), (0, 3))
        self.assertEqual(motif_starts("TCCTCCC", "[AG]CCTCCC"), ())

    def test_affected_windows_against_brute_force(self):
        for length in (1, 8, 17, 70):
            for width in (8, 16, 32, 64):
                for positions in ((0,), (length - 1,), (0, length - 1)):
                    actual_width = min(length, width)
                    brute = tuple(start for start in range(length - actual_width + 1)
                                  if any(start <= position < start + actual_width for position in positions))
                    self.assertEqual(affected_starts(length, width, positions), brute)

    def test_exact_no_edit_null_and_reversal(self):
        parent, mutant = "ACCTCCCAGAGATTTAGGACCTCC", "ACATCCCAGAGCTTTAGGACCTCC"
        np.testing.assert_array_equal(mechanism_delta(parent, parent), np.zeros(125))
        np.testing.assert_array_equal(mechanism_delta(parent, mutant), -mechanism_delta(mutant, parent))
        np.testing.assert_array_equal(mechanism_delta("ACGU", "ACGA"), mechanism_delta("ACGT", "ACGA"))

    def test_core_counts_and_complete_window_normalization(self):
        summary = dict(zip(SUMMARY_NAMES, summarize("ACCTCCC", (3,))))
        self.assertEqual(summary["whole_RCCTCCC_density"], 1.)
        self.assertEqual(summary["whole_CCTCC_density"], 1 / 3)
        self.assertEqual(summary["max_CCTCC_start_density_42nt"], 1 / 3)
        self.assertEqual(summary["CCTCC_pair_decay_10nt_density"], 0.)

    def test_purine_run_summaries(self):
        summary = dict(zip(SUMMARY_NAMES, summarize("AGAATTGG", (0, 7))))
        self.assertEqual(summary["whole_AG_fraction"], .75)
        self.assertEqual(summary["longest_AG_run_fraction"], .5)
        self.assertEqual(summary["mass_AG_runs_ge4_fraction"], .5)
        self.assertAlmostEqual(summary["AG_adjacent_pair_fraction"], 4 / 7)

    def test_feature_only_schema_and_finite_short_sequences(self):
        self.assertEqual(len(SUMMARY_NAMES), 25)
        self.assertEqual(len(MECHANISM_NAMES), 125)
        self.assertEqual(len(set(MECHANISM_NAMES)), 125)
        self.assertEqual([config["penalty"] for config in CONFIGS], [.005, .05, .5])
        self.assertEqual(feature_schema()["total_columns"], 371)
        for parent, mutant in (("A", "C"), ("AAAA", "CCCC"), ("TTTT", "AGAG")):
            self.assertTrue(np.isfinite(mechanism_delta(parent, mutant)).all())

    def test_frame_fields_other_than_sequence_do_not_enter_features(self):
        class Frame:
            def __len__(self):
                return 2
            def __getitem__(self, key):
                allowed = {"parent_sequence": ["ACCTCCC", "GGGAGAA"],
                           "mutant_sequence": ["ACATCCC", "GGGCGAA"]}
                if key not in allowed:
                    raise AssertionError("Outcome or identifier access: " + key)
                return allowed[key]
        result = build_features(Frame(), np.zeros((2, 246)))
        self.assertEqual(result.shape, (2, 371))
        np.testing.assert_array_equal(result[:, :246], 0.)
        np.testing.assert_array_equal(result[0, 246:], mechanism_delta("ACCTCCC", "ACATCCC"))

    def test_invalid_sequences_and_baseline_rejected(self):
        for parent, mutant in (("AACN", "AACT"), ("AAC", "AACT"), ("", "")):
            with self.assertRaises(ValueError):
                mechanism_delta(parent, mutant)
        with self.assertRaises(ValueError):
            build_features({"parent_sequence": ["ACGT"], "mutant_sequence": ["ACGA"]}, np.zeros((1, 245)))


if __name__ == "__main__":
    unittest.main()
