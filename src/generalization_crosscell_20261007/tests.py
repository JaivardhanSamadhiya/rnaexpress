"""Outcome-free synthetic split, control and aggregation invariants."""
import unittest
from .common import np,pd,inner_regret,jsave,OUT,sha256
from .splits import outer_masks,inner_masks
from .gate import compare
from .bootstrap import shared_bootstrap
from .verify import replay_regret
from src.cross_assay_20260927.features import build


def toy():
    rows=[]
    for cell in ('CAD','Neuro-2a'):
        for fold in (0,1,2):
            for candidate in (0,1):
                rows.append({'intervention_id':cell+str(fold)+str(candidate),
                    'dataset':'mikl_gse173098','cell_type':cell,'held_parent_fold':fold,
                    'biological_component':'gene'+str(fold),'gene_transcript':'G'+str(fold),
                    'parent_context_id':cell+'_parent'+str(fold),
                    'parent_sequence':['AAAAC','CCCCA','GGGGA'][fold],
                    'mutant_sequence':['AAAAT','CCCCT','GGGGT'][fold]+str(candidate),
                    'measured_delta':float(candidate)})
    return pd.DataFrame(rows)


class CrossCellTests(unittest.TestCase):
    def test_both_outer_cells_genes_and_exact_alleles_excluded(self):
        frame=toy()
        for task,source,target in [('CAD_to_N2A','CAD','Neuro-2a'),('N2A_to_CAD','Neuro-2a','CAD')]:
            for fold in (0,1,2):
                train,test=outer_masks(frame,task,fold)
                self.assertEqual(set(frame.loc[train,'cell_type']),{source})
                self.assertEqual(set(frame.loc[test,'cell_type']),{target})
                self.assertFalse(set(frame.loc[train,'gene_transcript'])&set(frame.loc[test,'gene_transcript']))
                self.assertFalse(set(frame.loc[train,'parent_sequence'])&set(frame.loc[test,'parent_sequence']))
                subset=frame.loc[train].reset_index(drop=True)
                for inner in subset.held_parent_fold.unique():
                    a,b=inner_masks(subset,int(inner))
                    self.assertFalse(set(subset.loc[a,'biological_component'])&set(subset.loc[b,'biological_component']))

    def test_invalid_gene_grouping_is_rejected(self):
        frame=toy()
        frame.loc[frame.held_parent_fold.eq(1),'gene_transcript']='G0'
        with self.assertRaises(AssertionError):outer_masks(frame,'CAD_to_N2A',0)

    def test_additive_prefix_exact_feature_and_name_equality(self):
        frame=pd.DataFrame({'parent_sequence':['ACGTACGT','AAAAACCC','GGGTTTAA'],
                            'mutant_sequence':['ACGTTCGT','AAATACCC','GGGCTTAA']})
        matrices,names=build(frame)
        self.assertEqual(matrices['kmer123'].shape,(3,102))
        np.testing.assert_array_equal(matrices['interaction_3'][:,:102],matrices['kmer123'])
        self.assertEqual(names['interaction_3'][:102],names['kmer123'])

    def test_source_oof_component_weight_not_fold_mean(self):
        frame=toy();source=frame[frame.cell_type.eq('CAD')].reset_index(drop=True)
        score=np.array([0.,1.,0.,-1.,0.,-1.])
        self.assertAlmostEqual(inner_regret(source,score),2/3)
        fold_average=np.mean([inner_regret(source.iloc[:2].reset_index(drop=True),score[:2]),
                              inner_regret(source.iloc[2:].reset_index(drop=True),score[2:])])
        self.assertAlmostEqual(fold_average,.5)

    def test_independent_selection_replay_including_lexical_ties(self):
        frame=toy();source=frame[frame.cell_type.eq('CAD')].reset_index(drop=True)
        for score in (np.zeros(6),np.array([0.,1.,0.,-1.,0.,-1.]),np.arange(6,dtype=float)):
            self.assertAlmostEqual(replay_regret(source,score),inner_regret(source,score))

    def test_global_component_draw_shared_between_cells(self):
        a=pd.Series([1.,-1.],index=['g1','g2']);b=-a
        np.testing.assert_allclose(shared_bootstrap({'CAD_to_N2A':a,'N2A_to_CAD':b},64,4),0.,atol=1e-15,rtol=0)

    def test_best_fold_removal_retains_component_and_cell_weighting(self):
        rows=[]
        for task in ('CAD_to_N2A','N2A_to_CAD'):
            for fold,gain in enumerate([.05,.01,.02]):
                rows.append({'task':task,'biological_component':'gene'+str(fold),
                    'gene_fold':fold,'regret':.5-gain,'wrong_direction':.1})
        candidate=pd.DataFrame(rows);control=candidate.assign(regret=.5)
        result=compare(candidate,control)
        self.assertEqual(result['removed_best_gene_fold'],0)
        self.assertAlmostEqual(result['remaining_gain'],.015)
        self.assertAlmostEqual(result['mean_gain'],.08/3)
        self.assertEqual(result['macro_wrong_direction_harm'],0.)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(CrossCellTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    jsave(OUT/'tests_receipt.json',{'status':'PASS','tests':result.testsRun,
        'test_source_sha256':sha256(__file__),'biological_fits_run':False,
        'scope':'Synthetic split/purge, additive-prefix, source-OOF weighting and paired-gate invariants'})
