import math,random,unittest
from . import numeric as n
from src.generalization_pum2_fixed_math_20261008 import model as p
def zero():
 return ({str(k):{b:0. for b in 'ACGU'} for k in range(9)},{str(k):{b:0. for b in 'ACGU'} for k in range(3,7)},{'4':{'NN':0.},'5':{'NN':0.}},{'c1':{'1':0.},'c2':{'1':0.}})
class ReplayContracts(unittest.TestCase):
 def test_contacts_single(self):self.assertEqual(n.coordinates(0,'single',(3,)),(0,1,2,4,5,6,7,8,9))
 def test_contacts_two(self):self.assertEqual(n.coordinates(0,'two_singles',(3,4)),(0,1,2,4,6,7,8,9,10))
 def test_contacts_double5(self):self.assertEqual(n.coordinates(0,'adjacent_double',(5,)),(0,1,2,3,4,7,8,9,10))
 def test_contacts_double6(self):self.assertEqual(n.coordinates(7,'adjacent_double',(6,)),(7,8,9,10,11,12,15,16,17))
 def test_counts(self):
  for length,count in ((9,1),(10,6),(11,19),(12,32),(140,1696)):
   self.assertEqual(n.score('A'*length,zero(),'released_csv')['state_count'],count)
 def test_homopolymer_not_deduplicated(self):self.assertEqual(n.score('A'*11,zero(),'released_csv')['state_count'],19)
 def test_zero_partition(self):self.assertAlmostEqual(n.score('A'*11,zero(),'released_csv')['logZ'],math.log(19),places=13)
 def test_controls_absent_flips(self):
  for mode in n.MODES[:2]:self.assertEqual(n.score('A'*140,zero(),mode)['state_count'],132)
 def test_short(self):self.assertFalse(n.score('A'*8,zero(),'released_csv')['available'])
 def test_rna_dna(self):self.assertEqual(n.score('ACGTACGTAC',zero(),'released_csv'),n.score('ACGUACGUAC',zero(),'released_csv'))
 def test_reject_mixed(self):
  with self.assertRaises(AssertionError):n.score('ACGTUACGT',zero(),'released_csv')
 def test_position9_condition(self):
  z=zero();z[0]['8']['G']=5.
  self.assertEqual(n.score('AAAAAAACG',z,'no_flip_no_c1c2')['best_state_energy_kcal'],0.)
  self.assertEqual(n.score('AAAAAAAAG',z,'no_flip_no_c1c2')['best_state_energy_kcal'],5.)
 def test_c1_manual(self):
  z=zero();z[3]['c1']['1']=-2.
  self.assertEqual(n.score('AAAACAGCU',z,'coupled_consecutive')['best_state_energy_kcal'],-2.)
 def test_c2_manual(self):
  z=zero();z[3]['c2']['1']=-3.
  self.assertEqual(n.score('AAAAUCCGU',z,'coupled_consecutive')['best_state_energy_kcal'],-3.)
 def test_csv_double_row(self):
  z=zero();z[2]['4']['NN']=2.;z[2]['5']['NN']=3.
  observed={key[3]:energy for key,contact,energy in n.registers('A'*11,z,'released_csv') if key[2]=='adjacent_double'}
  self.assertEqual(observed,{(5,):2.,(6,):3.})
 def test_two_flipped_base_offsets(self):
  z=zero();z[1]['3']['U']=2.;z[1]['4']['C']=3.
  observed={key:energy for key,contact,energy in n.registers('ACGUACGUACG',z,'released_csv')}
  self.assertEqual(observed[(0,11,'two_singles',(3,4))],5.)
 def test_coupling_permissions_table(self):
  for mode in n.MODES:
   for length,kind,gaps,flags in n.configurations(mode):self.assertEqual(flags,p.guards(gaps,kind,mode))
 def test_invented_all_states_against_production(self):
  rng=random.Random(20261009);fixed=n.parameters();original=p.load_parameters()
  for length in (9,10,11,12,46,140):
   sequence=''.join(rng.choice('ACGU') for _ in range(length))
   for mode in n.MODES:
    independent={key:(contact,energy) for key,contact,energy in n.registers(sequence,fixed,mode)}
    original_states=list(p.states(sequence,original,mode));self.assertEqual(set(independent),{s.key for s in original_states})
    for state in original_states:
     contact,energy=independent[state.key]
     self.assertEqual(''.join(sequence[k] for k in contact),state.retained)
     self.assertLessEqual(abs(energy-state.energy_kcal),1e-10)
    scored=n.score(sequence,fixed,mode);other=p.score(sequence,original,mode)
    for field in ('logZ','relative_ensemble_energy_kcal','best_state_energy_kcal'):self.assertLessEqual(abs(scored[field]-other[field]),1e-10)
 def test_forward_only(self):
  z=zero();z[0]['0']['A']=2.
  self.assertNotEqual(n.score('A'*9,z,'coupled_consecutive')['logZ'],n.score('U'*9,z,'coupled_consecutive')['logZ'])
if __name__=='__main__':unittest.main()
