import unittest
from .common import *
from .features import build,counts
from .models import row_weights,pair_indices,purge,fit,predict
from .metrics import pair_accuracy

def fixture():
    rows=[]
    for d in ('a','b'):
        for u in range(2):
            for i in range(3):rows.append({'dataset':d,'biological_component':d+str(u),'parent_context_id':d+str(u),'intervention_id':d+str(u)+str(i),'measured_delta':float(i-1),'parent_sequence':d+str(u),'mutant_sequence':d+str(u)+str(i)})
    return pd.DataFrame(rows)
class Tests(unittest.TestCase):
    def test_hierarchical_weights(self):
        f=fixture();w=row_weights(f);self.assertAlmostEqual(w.sum(),1)
        for d in f.dataset.unique():self.assertAlmostEqual(w[f.dataset.eq(d)].sum(),.5)
    def test_pair_truth(self):
        f=fixture();l,r,y,w,s=pair_indices(f);self.assertTrue(np.all(y==np.sign(f.measured_delta.to_numpy()[l]-f.measured_delta.to_numpy()[r])))
        self.assertTrue((f.parent_context_id.to_numpy()[l]==f.parent_context_id.to_numpy()[r]).all())
    def test_pair_sampling_label_independent(self):
        f=fixture();a=pair_indices(f);f.measured_delta=-f.measured_delta;b=pair_indices(f)
        self.assertTrue(np.array_equal(a[0],b[0]));self.assertTrue(np.array_equal(a[2],-b[2]))
    def test_pair_accuracy_ties(self):
        self.assertEqual(pair_accuracy(np.arange(4),np.ones(4)),.5);self.assertEqual(pair_accuracy(np.arange(4),np.arange(4)),1);self.assertEqual(pair_accuracy(np.arange(4),-np.arange(4)),0)
    def test_truth_ties(self):self.assertAlmostEqual(pair_accuracy(np.array([0,0,1]),np.array([0,1,2])),1)
    def test_source_scale_invariance(self):
        f=fixture();a=pair_indices(f)[2];f.measured_delta=10*f.measured_delta+7;self.assertTrue(np.array_equal(a,pair_indices(f)[2]))
    def test_purge_same_gene(self):
        f=fixture();f.loc[6,'biological_component']=f.biological_component.iloc[0];tr=f.dataset.eq('b').to_numpy();te=~tr;p=purge(f,tr,te);self.assertFalse(p[6])
    def test_held_residual_zero(self):
        f=fixture();x=np.column_stack([f.measured_delta,np.arange(len(f))%3]);m=fit(f,x,'hierarchical');a,r,p=predict(m,x,np.array(['unseen']*len(f)));self.assertTrue(np.all(r==0));self.assertTrue(np.isfinite(a).all())
    def test_parent_interactions_do_not_cancel(self):
        f=pd.DataFrame({'parent_sequence':['AAAAACAAAAA','GGGGGCGGGGG'],'mutant_sequence':['AAAAATAAAAA','GGGGGTGGGGG']});x,_=build(f)
        self.assertFalse(np.array_equal(x['interaction_3'][0,-144:],x['interaction_3'][1,-144:]))
    def test_local_delta_cancellation(self):
        self.assertTrue(np.array_equal(counts('GGGACATCAGGG')-counts('GGGACGTCAGGG'),counts('ACATCA')-counts('ACGTCA')))
    def test_training_labels_only(self):
        f=fixture();tr=f.dataset.eq('a');x=np.column_stack([np.arange(len(f))%3]);m=fit(f[tr],x[tr]);f.loc[~tr,'measured_delta']=1e9;n=fit(f[tr],x[tr]);self.assertEqual(m,n)
if __name__=='__main__':unittest.main()
