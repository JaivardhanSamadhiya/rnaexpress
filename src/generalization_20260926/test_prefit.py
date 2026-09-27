import unittest
from .common import *
from .features import matrices,disjoint_train
from .evaluation import correlations,cluster_stat,signflip
from .test_b import fit_predict,select_alpha

class PrefitTests(unittest.TestCase):
    def test_overlap_counts(self):self.assertEqual(count('AAAAAA')[4],5)
    def test_snp_delta_composition(self):
        a=count('AACGT');b=count('AATGT');self.assertEqual((b-a)[:4].tolist(),[0,-1,0,1])
    def test_unchanged_context_cancels(self):
        a=count('GGGACGTCAGGG')-count('GGGACATCAGGG');b=count('ACGTCA')-count('ACATCA');self.assertTrue(np.array_equal(a,b))
    def test_identity_edit(self):self.assertTrue(np.all(count('ACGTAC')-count('ACGTAC')==0))
    def test_composition_gauge(self):
        d=count('GACGTA')-count('AACGTA');self.assertAlmostEqual(d[4:20].sum(),0)
    def test_constant_prediction(self):self.assertEqual(correlations(np.array([1,2,3]),np.zeros(3))[0],0)
    def test_constant_target_stops(self):
        with self.assertRaises(AssertionError):correlations(np.ones(3),np.arange(3))
    def test_overlap_exclusion(self):
        f=pd.DataFrame({'parent_id':['a','b','c'],'overlap_component':['x','x','z']})
        self.assertEqual(disjoint_train(f,'a').tolist(),[False,False,True])
    def test_cluster_point_parent_weighted(self):
        f=pd.DataFrame({'overlap_component':['a','a','b'],'x':[1,1,0]})
        self.assertAlmostEqual(cluster_stat(f,'x')[0],2/3)
    def test_exact_signflip(self):
        f=pd.DataFrame({'overlap_component':list('abcde'),'x':[1]*5})
        self.assertEqual(signflip(f,'x'),1/32)
    def test_training_parent_balance(self):
        x=np.arange(6.)[:,None];p=np.array(['a','a','b','b','b','b'])
        pred,fit=fit_predict(x,x[:,0],p,np.array([[2.5]]),10.)
        self.assertEqual(fit['training_weight_by_parent'],{'a':3.,'b':3.})
        self.assertTrue(np.isfinite(pred).all())
        self.assertTrue(np.allclose(fit['scaler_mean'][-2:],0))
    def test_outer_labels_cannot_select_alpha(self):
        p=np.repeat(list('abcd'),4);f=pd.DataFrame({'parent_id':p,'overlap_component':p,'observed_delta':np.arange(16.)})
        x=np.arange(16.)[:,None];mask=disjoint_train(f,'a')
        alpha,scores=select_alpha(f,x,mask)
        f.loc[~mask,'observed_delta']=np.array([1e9,-1e9,2e9,-2e9])
        other,other_scores=select_alpha(f,x,mask)
        self.assertEqual(alpha,other);self.assertEqual(scores,other_scores)

if __name__=='__main__':unittest.main()
