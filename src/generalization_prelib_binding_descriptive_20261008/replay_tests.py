import unittest
from .replay import independent_contrast

def row(v):return {'raw_counts':{key:{'value':x} for key,x in zip(('Input_1.raw','Input_2.raw','PUM1_IP_1.raw','PUM1_IP_2.raw'),v)}}
class ReplayContracts(unittest.TestCase):
 def test_manually_exact_delta(self):self.assertEqual(independent_contrast(row([0,0,1,1]),row([0,0,0,0]),'PUM1',1.)['delta'],1.)
 def test_missing_stays_unavailable(self):self.assertIsNone(independent_contrast(row([None,0,1,1]),row([0,0,0,0]),'PUM1',1.))
 def test_parent_self_control(self):self.assertEqual(independent_contrast(row([3,9,0,5]),row([3,9,0,5]),'PUM1',.5)['delta'],0.)
 def test_input_pair_permutation(self):
  a=row([3,9,0,5]);b=row([7,2,3,4]);self.assertAlmostEqual(independent_contrast(a,b,'PUM1',.5)['delta'],independent_contrast(row([9,3,0,5]),row([2,7,3,4]),'PUM1',.5)['delta'])
if __name__=='__main__':unittest.main()
