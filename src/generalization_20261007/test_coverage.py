import unittest
from .route_coverage import *
from scipy.optimize._numdiff import approx_derivative

class Tests(unittest.TestCase):
    def test_roster_coverage_determinism_and_no_test_labels(self):
        n=400
        f=pd.DataFrame({'dataset':['a']*n,'biological_component':['p']*n,'parent_context_id':['c']*n,
            'intervention_id':[str(i) for i in range(n)],'measured_delta':np.arange(n,dtype=float)})
        a,b,y,w,s=pairs_for(f,'connected')
        self.assertEqual(len(set(a)|set(b)),n)
        self.assertEqual(len(y),2048)
        p=f.copy();p.measured_delta=-p.measured_delta
        aa,bb,yy,ww,ss=pairs_for(p,'connected')
        np.testing.assert_array_equal(a,aa);np.testing.assert_array_equal(b,bb)
        np.testing.assert_array_equal(y,-yy);np.testing.assert_allclose(w,ww)
        self.assertAlmostEqual(float(w.sum()),1)
    def test_small_pair_roster_matches_original(self):
        f=pd.DataFrame({'dataset':['a']*5,'biological_component':['p']*5,'parent_context_id':['c']*5,
            'intervention_id':list('abcde'),'measured_delta':[0.,1,1,-2,3]})
        for x,y in zip(pairs_for(f,'connected'),pairs_for(f,'historical')):
            np.testing.assert_array_equal(x,y)
    def test_robust_gradient(self):
        rng=np.random.default_rng(2);z=rng.normal(size=(60,7));y=rng.choice([-1,1],60)
        w=np.full(60,1/60);s=np.array(['a']*20+['b']*20+['c']*20);beta=rng.normal(size=7)
        for robust in (False,True):
            analytic=objective(beta,z,y,w,s,.05,robust)[1]
            numeric=approx_derivative(lambda b: objective(b,z,y,w,s,.05,robust)[0],beta).ravel()
            np.testing.assert_allclose(analytic,numeric,rtol=1e-6,atol=1e-8)
    def test_decision_metric_and_constant_shift(self):
        f=pd.DataFrame({'dataset':['a']*3,'biological_component':['p']*3,'parent_context_id':['c']*3,
            'intervention_id':list('abc'),'measured_delta':[-1.,0,2]})
        d=decisions(f,np.array([-1.,0,2]),'x')
        self.assertTrue((d.regret==0).all())
        self.assertTrue((d.wrong_direction==0).all())
        shifted=decisions(f,np.array([5.,6,8]),'x')
        self.assertEqual(list(d.selected_id),list(shifted.selected_id))

if __name__=='__main__':unittest.main()
