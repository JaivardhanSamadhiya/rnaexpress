import unittest
from .common import *
from .models import *
from src.cross_assay_20260927.models import pair_indices,purge

class Tests(unittest.TestCase):
    def test_targets_and_missing(self):
        s=pair_stats(np.array([[1.,-1],[1,1],[0,0],[np.nan,np.nan]]));np.testing.assert_allclose(s['q1'][:3],[.5,1,.5]);np.testing.assert_allclose(s['q2'],[.5,5/6,.5,.5]);self.assertTrue(np.isnan(s['q1'][3]))
    def test_binary_soft_matches_hard(self):
        rng=np.random.default_rng(7);z=rng.normal(size=(80,7));q=rng.integers(0,2,80);w=np.full(80,1/80);a,_,_=optimize(z,2*q-1,w);b,_,_=fit_soft(z,q,w);np.testing.assert_allclose(a,b,atol=1e-7)
    def test_complement_and_nontransitivity(self):
        a=np.zeros((3,22));angles=np.arange(3)*2*np.pi/3;a[:,0]=np.cos(angles);a[:,1]=np.sin(angles);b=np.roll(a,-1,axis=0);beta=np.zeros(39);beta[22]=1;m={'kind':'pairfree','beta':beta,'wedge_scale':np.ones(17)};p=probabilities(m,a,b);self.assertTrue((p>.5).all());np.testing.assert_allclose(p+probabilities(m,b,a),1,atol=1e-14)
    def test_probit_complement(self):
        rng=np.random.default_rng(4);a=rng.normal(size=(6,22));b=rng.normal(size=(6,22));m={'kind':'hetero','beta':rng.normal(size=22),'noise_head':rng.normal(size=19)*.1};np.testing.assert_allclose(probabilities(m,a,b)+probabilities(m,b,a),1,atol=1e-14)
    def test_probit_optimization(self):
        rng=np.random.default_rng(3);z=rng.normal(size=(90,4));sigma=np.linspace(.25,4,90);q=ndtr(z[:,0]/sigma);beta,loss,_=fit_soft(z,q,np.full(90,1/90),True,sigma);self.assertTrue(np.isfinite(loss));self.assertGreater(beta[0],0)
    def test_single_replicate_unidentified(self):
        p=pd.DataFrame({'dataset':['a','a']});s=pair_stats(np.array([[1.],[2.]]));q,_,identified,pools=noise_targets(p,s,np.array([.5,.5]));np.testing.assert_allclose(q,s['q2']);self.assertFalse(identified.any());self.assertIsNone(pools['a'])
    def test_source_only_noise(self):
        # Two source studies and a third completely held study; poison only held measurements.
        rng=np.random.default_rng(2);rows=[]
        for study in ('a','b','c'):
            for parent in range(2):
                for candidate in range(3):rows.append({'dataset':study,'parent_context_id':study+str(parent),'biological_component':study+str(parent),'intervention_id':study+str(parent)+str(candidate),'measured_delta':float(candidate-1)})
        f=pd.DataFrame(rows);x=rng.normal(size=(len(f),22));r=rng.normal(size=(len(f),3));pairs=[]
        for _,g in f.groupby('parent_context_id'):
            for i,j in itertools.combinations(g.index,2):pairs.append({'left':i,'right':j,'pair_id':str(i)+'_'+str(j),'dataset':f.loc[i,'dataset'],'parent_context_id':f.loc[i,'parent_context_id'],'biological_component':f.loc[i,'biological_component'],'q_H0':float(f.loc[i,'measured_delta']>f.loc[j,'measured_delta']),'historical_train_eligible':True})
        p=pd.DataFrame(pairs);train=f.dataset.ne('c').to_numpy();a=fit_all_inputs(f,x,r,p,train);poison=r.copy();poison[~train]=1e10;b=fit_all_inputs(f,x,poison,p,train);np.testing.assert_array_equal(a['q3'],b['q3']);self.assertEqual(a['base'],b['base'])
    def test_historical_pair_roster(self):
        f,_,_,p=load();a,b,y,w,_=pair_indices(f);pp=p[p.historical_train_eligible].reset_index(drop=True);np.testing.assert_array_equal(a,pp.left);np.testing.assert_array_equal(b,pp.right);np.testing.assert_array_equal(y,2*pp.q_H0.to_numpy()-1);np.testing.assert_allclose(w,pair_weights(f,pp),atol=1e-16)
    def test_whole_study_purge(self):
        f,_,_,_=load()
        for study in STUDIES:
            test=f.dataset.eq(study).to_numpy();train=purge(f,~test,test);self.assertFalse(set(f.loc[train,'biological_component'])&set(f.loc[test,'biological_component']))

if __name__=='__main__':unittest.main()
