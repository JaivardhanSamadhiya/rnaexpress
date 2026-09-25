import unittest
from .srle_measurement_lineage_20260925 import fixed_nrs, exhaustive
import itertools
import pandas as pd


class LineageTests(unittest.TestCase):
    def test_balanced_depth(self):
        self.assertEqual(fixed_nrs(4, 4, 100, 100), 0)

    def test_depth_is_compartment_specific(self):
        self.assertAlmostEqual(fixed_nrs(0, 0, 2048, 0), -1)

    def test_invalid_counts(self):
        for bad in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                fixed_nrs(bad, 1, 100, 100)

    def test_identity_rejects_duplicate_missing_sequence(self):
        seqs = [''.join(s) for s in itertools.product('ACGT', repeat=6)]
        exhaustive(pd.DataFrame({'kmer': seqs}))
        seqs[-1] = seqs[0]
        with self.assertRaises(ValueError):
            exhaustive(pd.DataFrame({'kmer': seqs}))


if __name__ == '__main__':
    unittest.main()
