import math,unittest
from .model import Parameters,RT,MODES,table,normalize,bound_energy,guards,states,score,log_partition,load_parameters

def zero():return Parameters({(i,b):0. for i in range(9) for b in 'ACGU'},{(i,b):0. for i in range(3,7) for b in 'ACGU'},{4:0.,5:0.},{'c1':0.,'c2':0.})
class Contracts(unittest.TestCase):
 def test_csv_named_columns(self):self.assertEqual(table(',U,G,C,A\n0,4,3,2,1',['A','C','G','U'],['0'])['0']['A'],1.)
 def test_csv_duplicate(self):
  with self.assertRaises(AssertionError):table(',A\n0,1\n0,2',['A'],['0'])
 def test_csv_nonfinite(self):
  with self.assertRaises(AssertionError):table(',A\n0,nan',['A'],['0'])
 def test_short_unavailable(self):self.assertFalse(score('ACGTACGT',zero())['available'])
 def test_alphabet(self):
  self.assertEqual(normalize('ACGT'),'ACGU')
  for s in ('acgt','ACGN','ACTU'):
   with self.assertRaises(AssertionError):normalize(s)
 def test_state_counts(self):
  for n,expected in ((9,1),(10,6),(11,19),(12,32),(140,1696)):
   self.assertEqual(len(list(states('A'*n,zero()))),expected)
 def test_control_counts(self):
  for mode in ('no_flip_no_c1c2','coupled_consecutive'):self.assertEqual(len(list(states('A'*140,zero(),mode))),132)
 def test_two_single_deletion_offsets(self):
  seq='ACGUACGUACG'
  for s in states(seq,zero()):
   if s.kind=='two_singles':
    g,h=s.gaps;self.assertEqual(s.removed,(g,h+1));self.assertEqual(s.retained,''.join(b for i,b in enumerate(seq) if i not in (g,h+1)))
 def test_adjacent_csv_offset(self):
  p=zero();p.double[4]=2.;p.double[5]=3.
  for s in states('A'*11,p):
   if s.kind=='adjacent_double':self.assertEqual(s.energy_kcal,{(5,):2.,(6,):3.}[s.gaps])
 def test_unique_states_not_sequences(self):
  s=list(states('A'*11,zero()));self.assertEqual(len({x.key for x in s}),19);self.assertEqual(len({x.retained for x in s}),1)
 def test_zero_state_partition(self):self.assertAlmostEqual(score('A'*11,zero())['relative_ensemble_energy_kcal'],-RT*math.log(19))
 def test_position9_condition(self):
  p=zero();p.base[(8,'G')]=5.
  self.assertEqual(bound_energy('AAAAAAACG',p,(True,True)),0.)
  self.assertEqual(bound_energy('AAAAAAAAG',p,(True,True)),5.)
 def test_c1_motif(self):
  p=zero();p.coupling['c1']=-2.
  self.assertEqual(bound_energy('AAAACAGCU',p,(True,True)),-2.)
  self.assertEqual(bound_energy('AAAACAGAU',p,(True,True)),0.)
  self.assertEqual(bound_energy('AAAACAGCU',p,(False,True)),0.)
 def test_c2_motif(self):
  p=zero();p.coupling['c2']=-3.
  self.assertEqual(bound_energy('AAAAUCCGU',p,(True,True)),-3.)
  self.assertEqual(bound_energy('AAAAUACGU',p,(True,True)),0.)
  self.assertEqual(bound_energy('AAAAUCCGU',p,(True,False)),0.)
 def test_negative_parameters_kept(self):
  p=zero();p.base[(4,'A')]=-.03;self.assertEqual(bound_energy('AAAAAAAAA',p,(False,False)),-.03)
 def test_single_guard_discrepancy(self):
  self.assertEqual(guards((4,),'single','released_csv'),(False,True))
  self.assertEqual(guards((4,),'single','fit_region_truncated'),(True,True))
  self.assertEqual(guards((5,),'single','released_csv'),(False,False))
  self.assertEqual(guards((5,),'single','fit_region_truncated'),(False,True))
 def test_adjacent_guard_asymmetry(self):
  self.assertEqual(guards((5,),'adjacent_double','released_csv'),(False,True))
  self.assertEqual(guards((5,),'single','released_csv'),(False,False))
 def test_two_guard_discrepancy(self):
  self.assertEqual(guards((3,4),'two_singles','released_csv'),(False,True))
  self.assertEqual(guards((3,4),'two_singles','fit_region_truncated'),(True,True))
  self.assertEqual(guards((3,5),'two_singles','fit_region_truncated'),(False,True))
 def test_state_energy_guard_discrepancy(self):
  p=zero();p.coupling['c1']=-1.53
  retained='AAAACAGCU';seq=retained[:4]+'A'+retained[4:]
  def selected(mode):return next(s for s in states(seq,p,mode) if s.start==0 and s.kind=='single' and s.gaps==(4,))
  self.assertEqual(selected('released_csv').energy_kcal,0.)
  self.assertEqual(selected('fit_region_truncated').energy_kcal,-1.53)
 def test_logsumexp_extreme(self):
  self.assertTrue(math.isfinite(log_partition([-1000.,1000.])))
  self.assertAlmostEqual(-RT*log_partition([-1000.,1000.]),-1000.)
 def test_logsumexp_translation(self):
  self.assertAlmostEqual(-RT*log_partition([1.,2.,3.])+5.,-RT*log_partition([6.,7.,8.]))
 def test_manual_two_state(self):self.assertAlmostEqual(log_partition([0.,RT*math.log(2)]),math.log(1.5))
 def test_only_forward_strand(self):
  p=zero();p.base[(0,'A')]=2.
  self.assertNotEqual(score('AAAAAAAAA',p)['logZ'],score('UUUUUUUUU',p)['logZ'])
 def test_operative_parameter_bytes(self):
  p=load_parameters();self.assertEqual(p.base[(4,'A')],-.03);self.assertEqual(p.single[(4,'C')],3.);self.assertEqual(p.double,{4:2.18,5:2.04});self.assertEqual(p.coupling,{'c1':-1.53,'c2':-.91})
 def test_published_consensus(self):self.assertEqual(bound_energy('UGUAUAUAU',load_parameters(),(True,True)),0.)
 def test_published_manual_c1(self):self.assertAlmostEqual(bound_energy('UGUACAGCU',load_parameters(),(True,True)),1.80)
 def test_published_manual_c2(self):self.assertAlmostEqual(bound_energy('UGUAUCCGU',load_parameters(),(True,True)),4.22)
if __name__=='__main__':unittest.main()
