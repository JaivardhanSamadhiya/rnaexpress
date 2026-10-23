"""Invented Python-list/array-double checks; no native numerical execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import unittest
from .fake_array import Array, FakeNP, expit
from . import numeric as n
from . import prepare as preparation
from .spec import NS, ARMS, CELLS, CONFIGS, FEATURE_WIDTH as P, METHOD, OPTIONS, SCORER
from src.generalization_knowncell_joint_implementation_20261022 import kernels as reference

ROOT = Path(__file__).resolve().parents[2]


def row(a, b=0.): return [a, b] + [0.] * (P-2)


def fixture():
    z = FakeNP.array([row(1.,-.2), row(-.7,.5), row(.9,.8), row(-1.,-.4)], dtype=FakeNP.float64)
    y, w, signs = [FakeNP.array(value, dtype=FakeNP.float64) for value in
                    ([1,-1,-1,1],[.1,.4,.2,.3],[1,1,-1,-1])]
    return z,y,w,signs


def prepared_fixture():
    x = [row(2.,3.),row(0.,1.),row(4.,2.),row(1.,0.),row(3.,2.),row(0.,-1.),row(2.,1.),row(-1.,0.)]
    return n.prepare_training(FakeNP,x,[0,2,4,6],[1,3,5,7],[1,-1,-1,1],[.1,.4,.2,.3],['CAD','CAD','Neuro-2a','Neuro-2a'])


class OptimizerSpy:
    def __init__(self, answers=None, success=True, drift=False):
        self.answers = list(answers or []); self.calls = []; self.success=success; self.drift=drift
    def __call__(self, fun, initial, *, jac, method, options):
        assert jac is True and method == METHOD and options == OPTIONS
        assert initial.tolist() == [0.] * len(initial)
        theta = FakeNP.array(self.answers.pop(0) if self.answers else initial.tolist(),dtype=FakeNP.float64)
        if self.drift: theta.data[-1]=1e-20
        value, gradient = fun(theta)
        self.calls.append({'size':len(initial),'value':value,'gradient':gradient.tolist(),'options':dict(options)})
        return SimpleNamespace(success=self.success,message='invented optimizer spy; no optimization',x=theta,fun=value,nit=0)


class ObjectiveTests(unittest.TestCase):
    def test_all_three_global_objectives_and_gradients_match_scalar_reference(self):
        z,y,w,signs=fixture(); cells=['CAD','CAD','Neuro-2a','Neuro-2a']
        for arm in ARMS:
            theta=row(.2,-.4) + (row(.6,.7) if arm!='pooled' else [])
            for config in CONFIGS:
                actual=n.objective_value_gradient(FakeNP,expit,arm,Array(theta),z,y,w,signs,config['penalty'])
                f={'pooled':reference.pooled_value_gradient,'independent':reference.independent_value_gradient,'joint_shrink10':reference.joint_value_gradient}[arm]
                expected=f(theta,z.tolist(),y.tolist(),w.tolist(),cells,config['penalty'])
                self.assertAlmostEqual(actual[0],expected[0],places=13)
                self.assertLess(max(abs(a-b) for a,b in zip(actual[1].tolist(),expected[1])),1e-13)

    def test_finite_difference_active_gradients(self):
        z,y,w,signs=fixture()
        for arm in ARMS:
            theta=row(.2,-.4)+(row(.6,.7) if arm!='pooled' else [])
            _,gradient=n.objective_value_gradient(FakeNP,expit,arm,Array(theta),z,y,w,signs,.05)
            for j in ([0,1] if arm=='pooled' else [0,1,P,P+1]):
                lo,hi=list(theta),list(theta);lo[j]-=1e-6;hi[j]+=1e-6
                value=lambda v:n.objective_value_gradient(FakeNP,expit,arm,Array(v),z,y,w,signs,.05)[0]
                self.assertLess(abs((value(hi)-value(lo))/2e-6-gradient[j]),2e-9)

    def test_large_margins_stable(self):
        z=Array([row(1.),row(-1.)]);y=Array([1.,1.]);w=Array([.5,.5]);signs=Array([1.,-1.])
        for arm in ARMS:
            value,gradient=n.objective_value_gradient(FakeNP,expit,arm,Array(row(1000.)+(row(500.) if arm!='pooled' else [])),z,y,w,signs,.05)
            self.assertTrue(math.isfinite(value) and all(math.isfinite(v) for v in gradient.tolist()))

    def test_rejects_wrong_width_cell_mass_and_penalty(self):
        z,y,w,signs=fixture()
        for args in ((Array([[1.]]*4),y,w,signs,.05),(z,y,Array([.1,.3,.2,.4]),signs,.05),(z,y,w,signs,.01)):
            with self.assertRaises(AssertionError):n.objective_value_gradient(FakeNP,expit,'pooled',Array(row(0.)),*args)


class PreparationTests(unittest.TestCase):
    def test_rms_support_matches_scalar_reference_and_common_zero_mean(self):
        prepared=prepared_fixture()
        differences=[row(2.,2.),row(3.,2.),row(3.,3.),row(3.,1.)]
        expected=reference.common_scale(differences,[.1,.4,.2,.3])
        self.assertEqual(prepared['scaling'],expected)
        self.assertEqual(prepared['z'].shape,(4,P))
        self.assertTrue(all(v==0. for r in prepared['z'].tolist() for v in r[2:]))

    def test_original_pair_order_and_labels_not_filtered(self):
        prepared=prepared_fixture()
        self.assertEqual(prepared['labels'].tolist(),[1.,-1.,-1.,1.])
        self.assertEqual(prepared['training_pairs'],4);self.assertEqual(prepared['training_rows'],8)

    def test_rejects_fractional_duplicate_reversed_and_foreign_cell_pairs(self):
        x=[row(1.),row(0.),row(2.),row(-1.)]
        cases=([0.,2.],[0,0],[1,2])
        rights=([1,3],[1,1],[0,3])
        for left,right in zip(cases,rights):
            with self.assertRaises(AssertionError):n.prepare_training(FakeNP,x,left,right,[1,1],[.5,.5],list(CELLS))
        with self.assertRaises(AssertionError):n.prepare_training(FakeNP,x,[0,2],[1,3],[1,1],[.5,.5],['CAD','N2A'])


class FitContractTests(unittest.TestCase):
    def test_exact_optimizer_options_dimensions_counts_and_no_head_extras(self):
        prepared=prepared_fixture()
        for arm in ARMS:
            spy=OptimizerSpy(); model=n.fit_prepared(FakeNP,spy,expit,prepared,arm,CONFIGS[1])
            self.assertEqual([c['size'] for c in spy.calls],[P,P] if arm=='independent' else [2*P if arm=='joint_shrink10' else P])
            self.assertEqual(model['optimizer_units'],2 if arm=='independent' else 1)
            self.assertEqual(model['scaling'],prepared['scaling'])
            self.assertEqual(model['config'],CONFIGS[1]);self.assertEqual(model['canonical_scorer'],SCORER)
            self.assertEqual(model['objective'],math.log(2.))
            self.assertEqual(set(model.get('heads',{})),set(CELLS) if arm=='independent' else set())

    def test_independent_fitter_uses_conditional2w_and_common_lambda(self):
        prepared=prepared_fixture();answers=[row(.2,-.3),row(.4,.1)]
        spy=OptimizerSpy(answers);model=n.fit_prepared(FakeNP,spy,expit,prepared,'independent',CONFIGS[1])
        z,y,w,signs=[prepared[key] for key in ('z','labels','weights','signs')]
        expected=n.objective_value_gradient(FakeNP,expit,'independent',Array(answers[0]+answers[1]),z,y,w,signs,.05)
        self.assertAlmostEqual(model['objective'],expected[0],places=13)
        for cell,call in zip(CELLS,spy.calls):
            indices=[i for i,v in enumerate(signs.tolist()) if v==(1 if cell=='CAD' else -1)]
            theta=answers[0 if cell=='CAD' else 1]
            value=math.fsum(reference.residual(y[i]*reference.dot(z[i],theta),y[i],2*w[i])[0] for i in indices)+.05/2*reference.dot(theta,theta)
            self.assertAlmostEqual(value,call['value'],places=13)

    def test_optimizer_failure_and_inactive_drift_rejected_without_clipping(self):
        for spy in (OptimizerSpy(success=False),OptimizerSpy(drift=True)):
            with self.assertRaises(AssertionError):n.fit_prepared(FakeNP,spy,expit,prepared_fixture(),'pooled',CONFIGS[0])

    def test_all_unsupported_keeps_full_dimensions_zero_and_fixed_call_count(self):
        prepared=n.prepare_training(FakeNP,[row(0.)]*4,[0,2],[1,3],[1,-1],[.5,.5],list(CELLS))
        spy=OptimizerSpy();model=n.fit_prepared(FakeNP,spy,expit,prepared,'joint_shrink10',CONFIGS[0])
        self.assertEqual(spy.calls[0]['size'],2*P)
        self.assertEqual(model['beta']+model['delta'],[0.]*(2*P))


class PredictionTests(unittest.TestCase):
    def test_all_arms_scores_match_scalar_reference(self):
        prepared=prepared_fixture();x=[row(3.,1.),row(3.,1.),row(-2.,4.)];cells=['CAD','Neuro-2a','CAD']
        for arm in ARMS:
            answers=[row(.3,-.2),row(-.4,.1)] if arm=='independent' else [row(.3,-.2)+(row(-.4,.1) if arm=='joint_shrink10' else [])]
            model=n.fit_prepared(FakeNP,OptimizerSpy(answers),expit,prepared,arm,CONFIGS[1])
            actual=n.canonical_scores(FakeNP,model,x,cells).tolist()
            expected=reference.reference_scores(arm,x,cells,model)
            self.assertLess(max(abs(a-b) for a,b in zip(actual,expected)),1e-13)

    def test_both_heads_use_full_validation_shape_before_cell_selection(self):
        prepared=prepared_fixture(); model=n.fit_prepared(FakeNP,OptimizerSpy([row(.5),row(-.5)]),expit,prepared,'independent',CONFIGS[0])
        shapes=[];original=Array.__matmul__
        def observed(left,right):shapes.append(left.shape);return original(left,right)
        Array.__matmul__=observed
        try:n.canonical_scores(FakeNP,model,[row(2.),row(1.),row(-1.)],['CAD','Neuro-2a','CAD'])
        finally:Array.__matmul__=original
        self.assertEqual(shapes,[(3,P),(3,P)])

    def test_zero_coefficients_and_exact_equal_scores_remain_exact_ties(self):
        model=n.fit_prepared(FakeNP,OptimizerSpy(),expit,prepared_fixture(),'joint_shrink10',CONFIGS[0])
        self.assertEqual(n.canonical_scores(FakeNP,model,[row(1.),row(-2.)],list(CELLS)).tolist(),[0.,0.])

    def test_changed_scaler_width_cell_and_inactive_coefficients_fail(self):
        model=n.fit_prepared(FakeNP,OptimizerSpy(),expit,prepared_fixture(),'pooled',CONFIGS[0])
        with self.assertRaises(AssertionError):n.canonical_scores(FakeNP,model,[[1.]],['CAD'])
        with self.assertRaises(AssertionError):n.canonical_scores(FakeNP,model,[row(1.)],['N2A'])
        model['scaling']['mean'][0]=1.
        with self.assertRaises(AssertionError):n.canonical_scores(FakeNP,model,[row(1.)],['CAD'])
        model['scaling']['mean'][0]=0.;model['beta'][-1]=1e-20
        with self.assertRaises(AssertionError):n.canonical_scores(FakeNP,model,[row(1.)],['CAD'])


class SourceSafetyTests(unittest.TestCase):
    def test_historical_optimizer_source_options_checked_without_import(self):
        text="def optimize(z,y,w):\n    return minimize(fun, zeros(102), jac=True, method='L-BFGS-B', options={'maxiter':500,'ftol':1e-11,'gtol':1e-7})\n"
        self.assertEqual(preparation.historical_optimizer_contract(text)['options'],OPTIONS)
        with self.assertRaises(AssertionError):preparation.historical_optimizer_contract(text.replace('500','501'))

    def test_no_scientific_imports_reader_writer_bootstrap_or_execution_entrypoint(self):
        source=ROOT/'src'/NS/'numeric.py';tree=ast.parse(source.read_text(encoding='utf-8'))
        allowed={'math','spec'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertTrue(all(alias.name in allowed for alias in node.names))
            if isinstance(node,ast.ImportFrom):self.assertIn(node.module,allowed)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):self.assertNotIn(node.func.id,{'open','exec','eval','__import__'})
        self.assertNotIn('if __name__',source.read_text(encoding='utf-8'))


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful()
    assert not any(name in sys.modules for name in forbidden)
    paths=sorted((ROOT/'src'/NS).glob('*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    payload={'status':'PASS_INVENTED_STDLIB_DEFERRED_NUMERIC_CONTRACTS_NOT_NATIVE_PARITY','tests':result.testsRun,
             'elapsed_seconds':time.monotonic()-started,'generated_utc':datetime.now(timezone.utc).isoformat(),
             'python_executable':sys.executable,'python_version':sys.version,
             'scientific_runtime_imports':False,'actual_native_optimizer_calls':0,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'array_double_uses_Python_loops_and_fsum_not_BLAS':True,
             'source_files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    target=ROOT/'results'/NS/'synthetic_tests_receipt.json'
    with target.open('xb') as handle:handle.write((json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    print('STDLIB_DEFERRED_NUMERIC_CHECKS_PASS',result.testsRun,hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':run()
