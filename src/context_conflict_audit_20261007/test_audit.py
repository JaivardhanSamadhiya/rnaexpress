"""Outcome-free arithmetic and matching tests only."""
import unittest
import numpy as np
import pandas as pd
from .audit import optimal,match_menus,TOL


class ExactMenuTests(unittest.TestCase):
    def test_agreement_has_common_zero(self):
        r=optimal([[0,.2,1],[3,4,9]])
        self.assertEqual((r['j'],r['k']),(2,0))
        self.assertEqual(r['minimum_pooled_regret'],0)
        self.assertTrue(r['exact_zero_feasible'])

    def test_reverse_two_candidate_empirical_conflict(self):
        r=optimal([[0,1],[1,0]])
        self.assertEqual(r['minimum_pooled_regret'],.5)
        self.assertFalse(r['exact_zero_feasible'])
        self.assertTrue(r['numerical_conflict'])
        self.assertNotEqual(r['j'],r['k'])

    def test_partial_overlap_not_common_minimum(self):
        r=optimal([[0,.5,1],[.5,0,1]])
        self.assertEqual(r['minimum_pooled_regret'],.125)
        self.assertEqual((r['j'],r['k']),(2,0))
        self.assertEqual(r['common_exact_max_count'],1)
        self.assertEqual(r['common_exact_min_count'],0)

    def test_normalization_affine_and_cell_permutation(self):
        y=np.asarray([[0,.2,1],[.6,0,1.]])
        r=optimal(y)
        for transformed in [y*np.asarray([3.,17.])[:,None]+np.asarray([8.,-9.])[:,None],y[::-1]]:
            t=optimal(transformed)
            self.assertAlmostEqual(r['minimum_pooled_regret'],t['minimum_pooled_regret'],places=12)
            self.assertEqual((r['j'],r['k']),(t['j'],t['k']))

    def test_exact_truth_ties_distinct_and_constant_arithmetic(self):
        r=optimal([[0,0,1],[0,0,7]])
        self.assertEqual((r['j'],r['k']),(2,0))
        self.assertEqual(r['common_exact_min_count'],2)
        self.assertEqual(r['constant_score_regret'],.5)
        for y in [[[0,0],[0,1]],[[0,float('nan')],[0,1]]]:
            with self.assertRaises(AssertionError): optimal(y)

    def test_independent_closed_form_bound(self):
        rng=np.random.default_rng(812)
        for n in range(2,11):
            y=rng.normal(size=(2,n))
            r=optimal(y)
            standardized=(y-y.min(axis=1)[:,None])/np.ptp(y,axis=1)[:,None]
            a=standardized.mean(axis=0)
            expected=(1-(a.max()-a.min()))/2
            self.assertLessEqual(abs(r['minimum_pooled_regret']-expected),TOL)

    def test_exact_menu_scope_and_duplicate_exclusion(self):
        rows=[]
        def add(ds,axis,level,ctx,parent,seqs):
            for seq in seqs:
                rows.append(dict(dataset=ds,cell_type=level if axis=='cell_type' else 'CAD',reporter=level if axis=='reporter' else 'GFP',parent_context_id=ctx,parent_sequence=parent,mutant_sequence=seq,biological_component='component',row0=len(rows),intervention_id=str(len(rows))))
        add('mikl_gse173098','cell_type','CAD','a','AAA',['AAC','AAG'])
        add('mikl_gse173098','cell_type','Neuro-2a','b','AAA',['AAG','AAC'])
        add('mikl_gse173098','cell_type','CAD','dup','CCC',['CCA','CCA'])
        add('moffatt_gse334718','reporter','GFP','c','TTT',['TTC','TTG'])
        add('moffatt_gse334718','reporter','Firefly','d','TTT',['TTC','TTA'])
        matched,excluded,coverage=match_menus(pd.DataFrame(rows))
        self.assertEqual(len(matched),1)
        self.assertEqual(coverage['mikl_gse173098']['matched_rows'],4)
        self.assertEqual(coverage['moffatt_gse334718']['exact_shared_menus'],0)
        self.assertEqual({e['reason'] for e in excluded},{'duplicate_sequence_or_small_menu','nonmatching_menu'})


if __name__=='__main__': unittest.main()
