import math,unittest
from . import contracts as c
def row(g,b,i):return {'lineage':g,'parent_excel_row':b,'source_variant_excel_row':i,'source_variant_ID':str(i)}
def raw(v):return {name:{'value':x} for name,x in zip(('Input_1.raw','Input_2.raw','PUM2_IP_1.raw','PUM2_IP_2.raw'),v)}
class StudyContracts(unittest.TestCase):
 def test_feature_width_and_order(self):self.assertEqual((len(c.KMERS),c.KMERS[:4],c.KMERS.index('TGT')),(84,('A','C','G','T'),79))
 def test_identical_self_features(self):self.assertEqual(c.delta_vector('ACGTACGT','ACGTACGT'),[0.]*84)
 def test_antisymmetric(self):
  a=c.delta_vector('ACGTACGT','ACGTTCGT');b=c.delta_vector('ACGTTCGT','ACGTACGT');self.assertEqual(a,[-x for x in b])
 def test_single_base_count(self):
  value=c.delta_vector('AAAA','AATA');self.assertAlmostEqual(value[0],-.25);self.assertAlmostEqual(value[3],.25)
 def test_background_weights(self):
  rows=[row('A',1,1),row('A',1,2),row('A',2,3),row('B',3,4)]
  self.assertEqual(c.weights(rows),[.125,.125,.25,.5])
 def test_macro_matches_weighted_error(self):
  rows=[row('A',1,1),row('A',1,2),row('A',2,3),row('B',3,4)];truth=[0.,1.,2.,3.];pred=[0.]*4
  macro,per=c.macro_errors(rows,truth,pred);self.assertEqual(macro,sum(w*y for w,y in zip(c.weights(rows),truth)))
 def test_tie_larger_penalty(self):self.assertEqual(c.choose_lambda({.005:1.,.05:1.,.5:1.}),.5)
 def test_selection_no_outer_dependency(self):self.assertEqual(c.choose_lambda({.005:.8,.05:.5,.5:.9}),.05)
 def test_pooled_no_pairing_needed(self):
  counts=raw([10,20,30,40]);view=(.5,'mean','mean');value=c.sample_effect(counts,'PUM2',view)
  expected=.5*(math.log2(30.5/10.5)+math.log2(40.5/20.5))
  self.assertAlmostEqual(value,expected,places=13)
 def test_crossed_average_equals_pooled(self):
  counts=raw([0,20,30,40]);pooled=c.sample_effect(counts,'PUM2',(.5,'mean','mean'))
  crossed=[c.sample_effect(counts,'PUM2',(.5,a,b)) for a in ('1','2') for b in ('1','2')]
  self.assertAlmostEqual(pooled,sum(crossed)/4,places=13)
 def test_eighteen_views(self):self.assertEqual((len(c.VIEWS),len(set(c.VIEWS)),c.PRIMARY),(18,18,'pc0.5_IPmean_Inputmean'))
 def test_zero_counts_retained(self):self.assertTrue(math.isfinite(c.sample_effect(raw([0,0,0,0]),'PUM2',c.VIEWS[0])))
 def test_tied_ranks(self):self.assertEqual(c.average_ranks([3.,1.,1.]),[3.,1.5,1.5])
 def test_flat_metrics(self):
  x=c.menu_metrics(['b','a'],[1.,1.],[0.,0.]);self.assertTrue(x['flat_truth']);self.assertEqual(x['normalized_regret_both'],0.);self.assertIsNone(x['spearman']);self.assertEqual(x['selected_max_ID'],'a')
 def test_both_direction_regret(self):
  x=c.menu_metrics(['a','b','c'],[0.,1.,2.],[2.,1.,0.]);self.assertEqual(x['normalized_regret_both'],1.);self.assertAlmostEqual(x['spearman'],-1.)
 def test_prediction_tie_choice(self):
  x=c.menu_metrics(['b','a','c'],[2.,0.,1.],[3.,3.,0.]);self.assertEqual(x['selected_max_ID'],'a');self.assertEqual(x['normalized_regret_max'],1.)
 def test_quantiles(self):self.assertEqual(c.quantile([0.,10.],.25),2.5)
 def test_zero_control_not_divided(self):
  genes=list('ABCDEFG');x=c.comparison({g:0. for g in genes},{g:0. for g in genes});self.assertIsNone(x['relative_MAE_gain']);self.assertTrue(x['zero_control_MAE'])
 def test_leave_best(self):
  genes=list('ABCDEFG');candidate={g:1. for g in genes};control={g:(8. if g=='A' else 2.) for g in genes};x=c.comparison(candidate,control);self.assertEqual(x['best_lineage'],'A');self.assertEqual(x['leave_best_lineage_out_gain'],1.)
if __name__=='__main__':unittest.main()
