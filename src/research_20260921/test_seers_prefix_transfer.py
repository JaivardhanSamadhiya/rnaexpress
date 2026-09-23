import unittest
import numpy as np
from .seers_prefix_transfer import regret,count_run


class ScreenTests(unittest.TestCase):
    def test_perfect_and_reversed(self):
        y=np.arange(5.)
        self.assertEqual(regret(y,y),0.)
        self.assertEqual(regret(y,-y),1.)

    def test_ties_equal_random(self):
        self.assertAlmostEqual(regret(np.array([0.,1.,2.,7.,9.]),np.zeros(5)),.5)

    def test_library_scale_invariant(self):
        y=np.arange(5.);p=np.array([1.,3.,2.,5.,4.])
        self.assertAlmostEqual(regret(y,p),regret(y+12,p))

    def test_other_runs_closed(self):
        with self.assertRaises(PermissionError):count_run('HRR1883402',set())
