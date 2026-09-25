import unittest
from .inventory import geometry
from .features import features
from .common import pd,np


class SmallEditTests(unittest.TestCase):
    def test_swap_is_two_substitutions(self):
        x=geometry('AACCGG','ACACGG')
        self.assertEqual(x['changed_bases'],2)
        self.assertEqual(x['total_edit_distance'],2)
        self.assertEqual(x['edit_positions'],'2;3')

    def test_cheap_alignment_does_not_relabel_many_substitutions(self):
        x=geometry('ACACACAC','CACACACA')
        self.assertEqual(x['changed_bases'],8)
        self.assertEqual(x['total_edit_distance'],2)
        self.assertEqual(x['edit_size_band'],'>6')

    def test_local_context_and_parent_interactions_survive(self):
        frame=pd.DataFrame({'parent_sequence':['AAAAACAAAAA','GGGGGCGGGGG'],
                            'mutant_sequence':['AAAAATAAAAA','GGGGGTGGGGG']})
        x=features(frame)
        self.assertTrue(np.allclose(x['delta_1mer'][0],x['delta_1mer'][1]))
        self.assertFalse(np.allclose(x['paired'][0],x['paired'][1]))

    def test_identity_is_not_an_edit(self):
        x=geometry('ACGT','ACGT')
        self.assertEqual(x['changed_bases'],0)

    def test_gene_weights_do_not_count_many_variants_as_many_genes(self):
        from .predict import weights
        w=weights(np.array(['a','a','a','b']))
        self.assertAlmostEqual(w[:3].sum(),w[3])

    def test_two_candidate_rank_is_defined(self):
        from .evaluate import corr
        self.assertAlmostEqual(corr(np.array([1.,2.]),np.array([2.,1.]),'spearman'),-1)

    def test_no_change_is_not_a_correct_signed_prediction(self):
        from .evaluate import gene_metrics
        g=pd.DataFrame({'localization_change':[-1.,1.]})
        m=gene_metrics(g,np.zeros(2),np.full(2,.5))
        self.assertEqual(m['sign_accuracy'],0)
        self.assertEqual(m['balanced_accuracy'],.5)


if __name__=='__main__': unittest.main()
