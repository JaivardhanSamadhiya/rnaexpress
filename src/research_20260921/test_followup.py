"""Synthetic controls for post-pilot representations and edit neighborhoods."""
import unittest
import numpy as np
from .robustness import count_features, swaps
from .pilots import comp_key


class FollowupTests(unittest.TestCase):
    def test_overlapping_counts(self):
        x = count_features(['AAAAAA', 'ACGTAC'])
        self.assertEqual(x.shape, (2, 84))
        np.testing.assert_array_equal(x[:, :4].sum(1), [6, 6])
        np.testing.assert_array_equal(x[:, 4:20].sum(1), [5, 5])
        np.testing.assert_array_equal(x[:, 20:].sum(1), [4, 4])
        self.assertEqual(x[0, 4], 5)
        self.assertEqual(x[0, 20], 4)

    def test_swaps_are_exact_two_edits_and_preserve_composition(self):
        for parent in ('AAAAAA', 'AAACCC', 'ACGTAC'):
            children = swaps(parent)
            self.assertEqual(children, sorted(set(children)))
            for child in children:
                self.assertEqual(comp_key(child), comp_key(parent))
                self.assertEqual(sum(a != b for a, b in zip(parent, child)), 2)
                self.assertIn(parent, swaps(child))
        self.assertEqual(swaps('AAAAAA'), [])
        self.assertEqual(len(swaps('AAACCC')), 9)


if __name__ == '__main__':
    unittest.main()
