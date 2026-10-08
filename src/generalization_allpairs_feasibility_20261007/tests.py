"""Independent invented objective/gradient tests; zero project data or fitting."""
import ast
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import random
import sys
import unittest
from . import math_mock as m

ROOT=Path(__file__).resolve().parents[2];NS='generalization_allpairs_feasibility_20261007'
SRC,ART,OUT,REP=[ROOT/p/NS for p in ('src','artifacts','results','reports')]
HISTORY=['src/cross_assay_20260927/models.py','src/generalization_20261007/route_scaling.py','src/generalization_20261007/route_coverage.py',
 'src/probabilistic_ranking_20260928/prepare.py','src/modeling/v4_decision_models.py','src/mechanism_v2/ranking.py','reports/generalization_20261007/protocol.md']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fixture():
 x=[[1.,0.],[0.,1.],[-1.,2.],[2.,-1.],[.2,.6],[-.3,.7],[.5,-.1]];y=[0.,0.,1.,-1.,3.,2.,2.]
 contexts={'a':[0,1,2,3],'b':[4,5,6]};cap={'a':[(0,1),(0,2),(1,3)],'b':[(4,5)]}
 return x,y,m.prepare_contexts(y,contexts,cap,{'a':.25,'b':.75})

class Tests(unittest.TestCase):
 def test_all_vs_materialized_and_finite_difference(self):
  x,y,p=fixture();beta=[.3,-.2];penalty=.05
  for mode in ('all','cap'):
   loss,g,c,counts=m.objective_candidate(x,beta,y,p,penalty,mode);ref,rg=m.materialized_reference(x,beta,y,p,penalty,mode)
   self.assertAlmostEqual(loss,ref,places=14)
   for a,b in zip(g,rg):self.assertAlmostEqual(a,b,places=14)
   for j in range(2):
    left=beta.copy();right=beta.copy();left[j]-=1e-6;right[j]+=1e-6
    fd=(m.objective_candidate(x,right,y,p,penalty,mode)[0]-m.objective_candidate(x,left,y,p,penalty,mode)[0])/2e-6
    self.assertAlmostEqual(fd,g[j],delta=2e-9)
   for context in p.values():self.assertAlmostEqual(math.fsum(c[i] for i in context['indices']),0.,places=14)
 def test_exact_truth_ties_and_signed_zero(self):
  self.assertEqual(m.non_tied_pairs([0.,-0.,1.,1.],[0,1,2,3]),4)
  self.assertEqual(m.non_tied_pairs([2.,2.,2.],[0,1,2]),0)
 def test_empty_cap_context_not_revived_by_all(self):
  y=[0.,0.,1.,0.,1.];p=m.prepare_contexts(y,{'a':[0,1,2],'b':[3,4]},{'a':[(0,1)],'b':[(3,4)]},{'a':.5,'b':.5})
  self.assertEqual(set(p),{'b'});self.assertEqual(p['b']['mass'],1.)
 def test_full_cap_equals_all_exact_small_menu(self):
  x,y,p=fixture()
  for row in p.values():row['valid_cap_edges']=[(a,b) for a,b in itertools.combinations(row['indices'],2) if y[a]!=y[b]]
  a=m.objective_candidate(x,[.3,-.2],y,p,.05,'all');b=m.objective_candidate(x,[.3,-.2],y,p,.05,'cap');self.assertEqual(a,b)
 def test_fixed_old_cap_scaling_and_support_for_both(self):
  x=[[0.,0.],[1.,0.],[2.,100.]];y=[0.,1.,2.];p=m.prepare_contexts(y,{'a':[0,1,2]},{'a':[(0,1)]},{'a':1.})
  scale,active=m.cap_rms(x,y,p);self.assertEqual(scale,[1.,1.]);self.assertEqual(active,[True,False])
  reduced=[[row[j]/scale[j] for j in range(2) if active[j]] for row in x]
  self.assertEqual(len(reduced[0]),1)
  m.objective_candidate(reduced,[.2],y,p,.05,'cap');m.objective_candidate(reduced,[.2],y,p,.05,'all')
 def test_parent_translation_invariance(self):
  x,y,p=fixture();translated=[row.copy() for row in x]
  for k,row in p.items():
   offset=[10.,-4.] if k=='a' else [-12.,8.]
   for i in row['indices']:translated[i]=[a+b for a,b in zip(x[i],offset)]
  for mode in ('all','cap'):
   a=m.objective_candidate(x,[.3,-.2],y,p,.05,mode);b=m.objective_candidate(translated,[.3,-.2],y,p,.05,mode)
   self.assertAlmostEqual(a[0],b[0],places=14)
   for v,w in zip(a[1],b[1]):self.assertAlmostEqual(v,w,places=14)
 def test_sign_reverse_and_large_margin_stability(self):
  x,y,p=fixture();a=m.objective_candidate(x,[.3,-.2],y,p,.05);b=m.objective_candidate(x,[-.3,.2],[-v for v in y],p,.05)
  self.assertAlmostEqual(a[0],b[0],places=14)
  for v,w in zip(a[1],b[1]):self.assertAlmostEqual(v,-w,places=14)
  for margin in (-1000.,1000.):self.assertTrue(all(math.isfinite(v) for v in m.loss_residual(margin,1,.5)))
 def test_nonuniform_masses_do_not_weight_large_menu_more(self):
  x,y,p=fixture();_,_,_,counts=m.objective_candidate(x,[.3,-.2],y,p,.05)
  self.assertEqual(counts,{'a':5,'b':2});self.assertEqual([p[k]['mass'] for k in p],[.25,.75])
 def test_finite_parameters_and_unique_unordered_edges(self):
  with self.assertRaises(AssertionError):m.prepare_contexts([0.,1.],{'a':[0,1]},{'a':[(0,1),(0,1)]},{'a':1.})
  with self.assertRaises(AssertionError):m.loss_residual(float('inf'),1,.5)
 def test_random_invented_matrices_agree(self):
  rng=random.Random(20261007)
  for _ in range(12):
   x=[[rng.uniform(-2,2) for _ in range(3)] for i in range(8)];y=[float(rng.choice([0,1,2,3])) for i in range(8)]
   if len(set(y))==1:continue
   edges=list(itertools.combinations(range(8),2));p=m.prepare_contexts(y,{'a':list(range(8))},{'a':edges},{'a':1.});beta=[rng.uniform(-1,1) for _ in range(3)]
   a=m.objective_candidate(x,beta,y,p,.5);b=m.materialized_reference(x,beta,y,p,.5)
   self.assertAlmostEqual(a[0],b[0],places=13)
   for v,w in zip(a[1],b[1]):self.assertAlmostEqual(v,w,places=13)

def run():
 assert not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for n in sys.modules)
 target=OUT/'synthetic_receipt_v2.json';assert not target.exists()
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));print(stream.getvalue());assert result.wasSuccessful()
 files={p.relative_to(ROOT).as_posix():sha(p) for p in SRC.glob('*.py')};files[ (REP/'feasibility.md').relative_to(ROOT).as_posix()]=sha(REP/'feasibility.md')
 for path in SRC.glob('*.py'):ast.parse(path.read_text())
 history={name:sha(ROOT/name) for name in HISTORY}
 target.parent.mkdir(parents=True,exist_ok=True)
 output=stream.getvalue()
 with target.open('x',encoding='utf-8') as receipt_stream:json.dump({'status':'PASS_STDLIB_SYNTHETIC_OBJECTIVE_FEASIBILITY_ONLY','tests':result.testsRun,'source_report_sha256':files,'historical_source_sha256':history,'project_data_read':False,'outcomes_read':False,'features_or_models_read':False,'numerical_packages_imported':False,'model_fits':0,'production_or_fitting_authorized':False,'test_output':output},receipt_stream,indent=2,sort_keys=True);receipt_stream.write('\n')
 print('Exact-pair synthetic gradient feasibility PASS',sha(target),flush=True)

if __name__=='__main__':run()
