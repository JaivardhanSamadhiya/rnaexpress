import unittest
from .core import *
from .fit import design,fit_fold
from .evaluate import sufficient,calculate


class Tests(unittest.TestCase):
    def test_purge_count_distance_bound(self):
        f=pd.DataFrame({'kmer':['AAAACC','AAACCC','AACCGG','CCGGTT','TTTTTT'],'test':[True,False,False,False,False]})
        mask=training_mask(f,'purged_composition_holdout','4200')
        self.assertEqual(mask.tolist(),[False,False,False,True,True])
        for s in f.loc[mask,'kmer']:
            self.assertGreater(np.abs(counts([s])[0]-np.array([4,2,0,0])).sum(),4)

    def test_held_out_outcomes_cannot_change_fit(self):
        seq=['AACCGG','AGACCG','GGCCAA','CGAAGC','TTCCAA','ACTTCA','ATCCTA','TTTTCC']
        f=pd.DataFrame({'kmer':seq,'group':keys(seq),'nrs':np.arange(8)/7})
        train=np.array([True,True,True,False,True,True,False,False]);x=design(seq)
        first,_=fit_fold(f,x,train)
        f.loc[~train,'nrs']=np.array([1000,-1000,9000])
        second,_=fit_fold(f,x,train)
        for key in first:np.testing.assert_array_equal(first[key],second[key])

    def test_one_mer_adds_no_order(self):
        seq=['AACCGG','AGACCG','GGCCAA','CGAAGC','TTCCAA','ACTTCA']
        f=pd.DataFrame({'kmer':seq,'group':keys(seq),'nrs':[1.,2.,3.,4.,5.,6.]})
        p,_=fit_fold(f,design(seq),np.array([True,True,False,False,True,True]))
        np.testing.assert_array_equal(p['composition'],p['1mer'])
        self.assertEqual(p['composition'][0],p['composition'][1])

    def test_perfect_prediction_metrics(self):
        v=calculate(sufficient(np.array([-2.,-1.,1.,2.]),np.array([-2.,-1.,1.,2.])).sum(0,keepdims=True))
        for key in ('pearson','r2','pairwise_accuracy_tie_half','balanced_accuracy_tie_half'):self.assertAlmostEqual(v[key][0],1)
        self.assertEqual(v['rmse'][0],0)

    def test_flat_prediction_is_tie_not_direction_success(self):
        v=calculate(sufficient(np.array([-2.,-1.,1.,2.]),np.zeros(4)).sum(0,keepdims=True))
        self.assertEqual(v['sign_accuracy_strict'][0],0)
        self.assertEqual(v['pairwise_accuracy_tie_half'][0],.5)
        self.assertEqual(v['balanced_accuracy_tie_half'][0],.5)
        self.assertTrue(np.isnan(v['pearson'][0]))

    def test_bootstrap_clusters_preserved(self):
        draws=bootstrap_counts(5)
        self.assertEqual(draws.shape,(2000,5))
        np.testing.assert_array_equal(draws.sum(1),np.full(2000,5))


if __name__=='__main__':unittest.main()
