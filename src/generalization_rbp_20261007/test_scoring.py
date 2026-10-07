"""Independent tiny motif/evidence checks; no localization data or fits."""

import itertools
import unittest

from .catalog import direct_human, matrix_digest, parse_pfm
from .scoring import np, PSEUDOCOUNT, smooth_log_odds, scan, summaries, allele_delta


class MotifTests(unittest.TestCase):
    def test_direct_status_does_not_admit_inferred_motif(self):
        row = {"RBP_Species": "Homo_sapiens", "RBP_Status": "D", "Motif_Type": "JPLE"}
        self.assertFalse(direct_human(row))
        row["Motif_Type"] = "RNAcompete"
        self.assertTrue(direct_human(row))
        row["RBP_Status"] = "I"
        self.assertFalse(direct_human(row))
        row.update(RBP_Status="D", RBP_Species="Mus_musculus")
        self.assertFalse(direct_human(row))

    def test_duplicate_matrix_hash_and_explicit_base_order(self):
        first = parse_pfm(b"Pos\tA\tC\tG\tU\n1\t1\t0\t0\t0\n2\t0\t0.5\t0.5\t0\n")
        second = parse_pfm(b"Pos\tA\tC\tG\tU\n1\t1.0\t0.0\t0.0\t0.0\n2\t0.0\t.5\t.5\t0.0\n")
        self.assertEqual(matrix_digest(first), matrix_digest(second))
        self.assertNotEqual(matrix_digest(first), matrix_digest(first[::-1]))
        with self.assertRaises(ValueError):
            parse_pfm(b"")
        with self.assertRaises(AssertionError):
            parse_pfm(b"Pos\tA\tG\tC\tU\n1\t1\t0\t0\t0\n")

    def test_scan_matches_independent_window_enumeration(self):
        pfm = np.array([[.7, .1, .1, .1], [.05, .05, .85, .05]])
        group = [(2, np.array([0]), smooth_log_odds(pfm)[None])]
        for bases in itertools.product("ACGU", repeat=3):
            sequence = "".join(bases)
            expected = []
            for start in range(2):
                likelihood = 1.
                for position in range(2):
                    p = pfm[position, "ACGU".index(sequence[start + position])]
                    likelihood *= ((p + PSEUDOCOUNT) / (1 + 4 * PSEUDOCOUNT)) / .25
                expected.append(likelihood ** .5)
            np.testing.assert_allclose(scan(sequence, group)[0][2][0], expected, rtol=1e-14, atol=1e-14)

    def test_accessibility_off_null_reversal_and_affected_pool(self):
        pfm = np.array([[1., 0., 0., 0.], [0., 0., 1., 0.]])
        group = [(2, np.array([0]), smooth_log_odds(pfm)[None])]
        parent, mutant = "AGCA", "AACA"
        raw = summaries(parent, [1], groups=group)
        np.testing.assert_array_equal(raw, summaries(parent, [1], np.ones(4), group))
        np.testing.assert_allclose(summaries(parent, [1], np.full(4, .5), group), raw * .5)
        np.testing.assert_array_equal(summaries(parent, [1], np.zeros(4), group), np.zeros(4))
        np.testing.assert_array_equal(allele_delta(parent, parent, groups=group), np.zeros(4))
        np.testing.assert_array_equal(allele_delta(parent, mutant, groups=group), -allele_delta(mutant, parent, groups=group))
        scores = scan(parent, group)[0][2][0]
        self.assertAlmostEqual(raw[2], float(scores[:2].mean()))
        self.assertAlmostEqual(raw[3], float(scores[:2].max()))


if __name__ == "__main__":
    unittest.main()
