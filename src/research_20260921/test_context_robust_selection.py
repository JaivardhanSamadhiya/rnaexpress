from .common import ROOT
from .context_robust_selection import percentiles, decisions
import unittest
import numpy as np


class RobustSelectionTests(unittest.TestCase):
    def test_average_rank_ties(self):
        x = np.array([[0., 1.], [0., 2.], [2., 3.]])
        np.testing.assert_array_equal(percentiles(x), [[.25, 0.], [.25, .5], [1., 1.]])

    def test_uniform_utility_is_not_assumed_half(self):
        y = np.array([[0., 2.], [1., 1.], [2., 0.]])
        y = np.column_stack([y, y])
        d, feasible = decisions(y, y, y, 1)
        self.assertAlmostEqual(d['uniform']['regret'], 1/3)
        self.assertEqual(d['maximin']['regret'], 0.)
        self.assertFalse(feasible)

    def test_opposite_direction_changes_selection(self):
        y = np.tile(np.arange(5.)[:, None], (1, 4))
        for sign in [1, -1]:
            d, feasible = decisions(y, y, y, sign)
            self.assertEqual(d['maximin']['regret'], 0.)
            self.assertEqual(d['maximin']['top_quartile_all_contexts'], 1.)
            self.assertTrue(feasible)


if __name__ == '__main__': unittest.main()
