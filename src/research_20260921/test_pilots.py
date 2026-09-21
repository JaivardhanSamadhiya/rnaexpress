"""Synthetic tests only. Run with unittest; never discover legacy pytest tests."""
from .common import ROOT, write_new
from .pilots import comp_key, count_member_allowed, fit_order, regret, test_bucket
import itertools
import unittest
import numpy as np

class PilotTests(unittest.TestCase):
    def test_partition_deterministic_and_nontrivial(self):
        seq = [''.join(v) for v in itertools.product('ACGT', repeat=6)]
        mask = np.array([test_bucket(s) for s in seq])
        self.assertTrue(700 < mask.sum() < 950)
        self.assertEqual([test_bucket(s) for s in seq], [test_bucket(s) for s in seq])

    def test_known_order_effect(self):
        seq = np.array([''.join(v) for v in itertools.product('ACGT', repeat=6)])
        y = np.array([2 * (s[0] == 'A') - (s[5] == 'C') + 2 * (s[1:3] == 'GT') for s in seq])
        _, _, base, pred, groups = fit_order(seq, y)
        ix = np.concatenate(groups)
        reduction = 1 - np.sum((y[ix] - pred[ix])**2) / np.sum((y[ix] - base[ix])**2)
        self.assertGreater(reduction, .85)

    def test_composition_only_no_residual_signal(self):
        seq = np.array([''.join(v) for v in itertools.product('ACGT', repeat=6)])
        y = np.array([s.count('A') + .5 * s.count('C')**2 for s in seq])
        _, _, base, pred, groups = fit_order(seq, y)
        ix = np.concatenate(groups)
        np.testing.assert_allclose(y[ix], base[ix], atol=1e-10)
        np.testing.assert_allclose(y[ix], pred[ix], atol=1e-10)

    def test_holdout_members_refused(self):
        for rep in (3, 4):
            self.assertFalse(count_member_allowed(f'GSM5552976_CAD_Neurite_GFP_Rep{rep}.umis.txt.gz'))
        self.assertTrue(count_member_allowed('GSM5552964_CAD_Soma_FF_Rep1.umis.txt.gz'))
        self.assertFalse(count_member_allowed('../GSM5552964_CAD_Soma_FF_Rep1.umis.txt.gz'))

    def test_regret_direction_and_tie(self):
        self.assertEqual(regret([0, 1, 2], [0, 1, 2], ['a', 'b', 'c']), 0)
        self.assertEqual(regret([0, 1, 2], [2, 1, 0], ['a', 'b', 'c']), 1)
        self.assertEqual(regret([0, 1, 2], [1, 1, 1], ['a', 'b', 'c']), .5)

    def test_preserved_namespace_write_refused(self):
        with self.assertRaises(PermissionError):
            write_new(ROOT / 'results/mechanism_v2/do_not_create.txt', b'no')
        with self.assertRaises(PermissionError):
            write_new(ROOT / 'reports/research_20260921/../mechanism_v2/do_not_create.txt', b'no')

if __name__ == '__main__':
    unittest.main()
