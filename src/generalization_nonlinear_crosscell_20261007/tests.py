"""Outcome-free synthetic/mock tests; never fit an actual estimator."""
import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from .common import np, pd, SRC, OUT, ART, TRACKS, WIDTHS, FEATURE_TRACKS, sha256, jsave, inner_regret, decisions
from . import routes, engine, ridge
from .splits import outer_masks, inner_masks
from src.generalization_crosscell_20261007.splits import outer_masks as original_outer, inner_masks as original_inner
from .bootstrap import shared_bootstrap
from .gate import compare
from .verify import replay_regret,check_choices


def frame():
    return pd.DataFrame({'intervention_id': ['a','b','c','d','e','f'],
        'dataset': ['mikl_gse173098']*6, 'cell_type': ['CAD']*6,
        'endpoint_class': ['projection']*6, 'parent_context_id': ['u','u','v','w','w','w'],
        'biological_component': ['g','g','g','h','h','h'], 'gene_transcript': ['G','G','G','H','H','H'],
        'held_parent_fold': [0,0,0,1,1,1], 'parent_sequence': ['AAAA']*3+['CCCC']*3,
        'mutant_sequence': ['AAAT','AATA','ATAA','CCCT','CCTC','CTCC'],
        'measured_delta': [-.2,.5,.3,-.4,.1,.2]})


def tree_model(width=2, iterations=2):
    tree = {'value': [0.,-.12,.23], 'feature_idx': [0,0,0],
        'num_threshold': [0.,0.,0.], 'missing_go_to_left': [0,0,0],
        'left': [1,0,0], 'right': [2,0,0], 'is_leaf': [0,1,1]}
    return {'kind':'numeric_hgb_json_v1','width':width,'baseline':.17,
            'trees':[copy.deepcopy(tree) for _ in range(iterations)],
            'sklearn_version':'1.5.2','iterations':iterations}


class NonlinearTests(unittest.TestCase):
    def test_exact_masks_and_fixed_grid(self):
        self.assertIs(outer_masks, original_outer); self.assertIs(inner_masks, original_inner)
        self.assertEqual(FEATURE_TRACKS,['simple','base','raw','structure','lookup','bert','combined'])
        self.assertEqual(len(TRACKS),14)
        self.assertEqual([WIDTHS[t] for t in TRACKS[:7]],[102,246,251,262,502,502,518])
        self.assertEqual([c['max_leaf_nodes'] for c in routes.CONFIGS],[7,15,31])
        self.assertEqual([c['alpha'] for c in ridge.CONFIGS],[.005,.05,.5])
        for config in routes.CONFIGS:
            params=routes.make_estimator(config).get_params()
            for key,value in routes.FIXED.items(): self.assertEqual(params[key],value)
            self.assertEqual(params['max_leaf_nodes'],config['max_leaf_nodes'])

    def test_equal_gene_context_candidate_weights(self):
        f=frame(); w=routes.row_weights(f)
        np.testing.assert_allclose(w,[.75,.75,1.5,1.,1.,1.],atol=1e-12)
        masses=pd.Series(w).groupby(f.biological_component).sum()
        np.testing.assert_allclose(masses,[3.,3.],atol=1e-12)
        np.testing.assert_allclose(w.mean(),1.,atol=1e-12)

    def test_numeric_native_independent_boundary_and_json_parity(self):
        model=tree_model(); x=np.asarray([[-1.,8.],[0.,-2.],[np.nextafter(0.,1.),3.],[1.,4.]])
        expected=np.asarray([-.07,-.07,.63,.63])
        np.testing.assert_allclose(routes.predict_model(model,x),expected,atol=1e-15)
        np.testing.assert_array_equal(routes.predict_model(model,x),routes.independent_predict(model,x))
        restored=json.loads(json.dumps(model))
        np.testing.assert_array_equal(routes.predict_model(restored,x),routes.predict_model(model,x))

    def test_malformed_graph_and_nonfinite_input_rejected(self):
        malformed=tree_model(); malformed['trees'][0]['left'][0]=0
        with self.assertRaises(AssertionError): routes.validate_model(malformed)
        malformed=tree_model(); malformed['trees'][0]['feature_idx'][0]=2
        with self.assertRaises(AssertionError): routes.validate_model(malformed)
        with self.assertRaises(AssertionError): routes.predict_model(tree_model(),np.asarray([[np.nan,1.]]))

    def test_mocked_fit_receives_original_labels_and_balanced_weights(self):
        f=frame(); original=f.copy(deep=True); x=np.arange(12,dtype=float).reshape(6,2)
        saved=tree_model(iterations=200); captures={}
        class FakeEstimator:
            n_trees_per_iteration_=1; n_iter_=200
            _baseline_prediction=np.asarray([[saved['baseline']]])
            def __init__(self):
                from sklearn.ensemble._hist_gradient_boosting.common import PREDICTOR_RECORD_DTYPE
                self._predictors=[]
                for tree in saved['trees']:
                    nodes=np.zeros(3,dtype=PREDICTOR_RECORD_DTYPE)
                    for field in routes.FIELDS: nodes[field]=tree[field]
                    self._predictors.append([SimpleNamespace(nodes=nodes)])
            def fit(self,features,labels,sample_weight):
                captures.update(x=features.copy(),y=labels.copy(),w=sample_weight.copy())
                return self
            def predict(self,features): return routes.independent_predict(saved,features)
        with patch('src.generalization_nonlinear_crosscell_20261007.common.freeze_check'), \
             patch.object(routes,'runtime_binding',return_value={'synthetic':True}), \
             patch.object(routes,'readj',return_value={'synthetic':True}), \
             patch.object(routes,'make_estimator',return_value=FakeEstimator()), \
             patch.dict(os.environ,{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}):
            model=routes.fit_model(f,x,routes.CONFIGS[0])
        pd.testing.assert_frame_equal(f,original)
        np.testing.assert_array_equal(captures['y'],f.measured_delta.to_numpy(float))
        np.testing.assert_array_equal(captures['x'],x)
        np.testing.assert_array_equal(captures['w'],routes.row_weights(f))
        self.assertLess(model['native_export_max_error'],1e-9)

    def test_checkpoint_binds_labels_metadata_matrix_weights_and_resume(self):
        f=frame(); x=np.zeros((6,2)); calls=[]
        def fake_fit(training,matrix,config):
            calls.append(1)
            return {'training_weights_sha256':hashlib.sha256(routes.row_weights(training).tobytes()).hexdigest()}
        ART.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ART) as directory:
            location=Path(directory).resolve(); assert location.is_relative_to(ART.resolve())
            (location/'prefit_manifest.json').write_text('{}',encoding='utf-8')
            with patch.object(engine,'OUT',location),patch.object(engine,'module',return_value=SimpleNamespace(fit_model=fake_fit)):
                first=engine.checkpoint('hgb/base','test',f,x,routes.CONFIGS[0])
                self.assertEqual(engine.checkpoint('hgb/base','test',f,x,routes.CONFIGS[0]),first)
                self.assertEqual(len(calls),1)
                checkpoint=location/'hgb/base/fits/test_hgb_7.json'
                original_bytes=checkpoint.read_bytes()
                checkpoint.write_bytes(original_bytes+b' ')
                with self.assertRaises(AssertionError):engine.checkpoint('hgb/base','test',f,x,routes.CONFIGS[0])
                checkpoint.write_bytes(original_bytes)
                sidecar=checkpoint.with_suffix('.sha256.json');sidecar_bytes=sidecar.read_bytes()
                sidecar.unlink()
                with self.assertRaises(AssertionError):engine.checkpoint('hgb/base','test',f,x,routes.CONFIGS[0])
                sidecar.write_bytes(sidecar_bytes)
                altered=x.copy();altered[0,0]=1.
                with self.assertRaises(AssertionError): engine.checkpoint('hgb/base','test',f,altered,routes.CONFIGS[0])
                altered=f.copy();altered.loc[0,'measured_delta']+=.01
                with self.assertRaises(AssertionError): engine.checkpoint('hgb/base','test',altered,x,routes.CONFIGS[0])
                altered=f.copy();altered.loc[0,'mutant_sequence']='GAAA'
                with self.assertRaises(AssertionError): engine.checkpoint('hgb/base','test',altered,x,routes.CONFIGS[0])
                checkpoint.unlink()
                with self.assertRaises(AssertionError):engine.checkpoint('hgb/base','test',f,x,routes.CONFIGS[0])

    def test_ridge_source_moments_normal_equation_cutoff_and_json(self):
        f=frame();x=np.c_[np.arange(6,dtype=float),np.ones(6)*7.,np.arange(6)*1e-15]
        captured={}
        def fake_solve(lhs,rhs):
            captured.update(lhs=lhs.copy(),rhs=rhs.copy())
            return np.asarray([.2])
        with patch('src.generalization_nonlinear_crosscell_20261007.common.freeze_check'), \
             patch.object(ridge.np.linalg,'solve',side_effect=fake_solve), \
             patch.dict(os.environ,{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}):
            model=ridge.fit_model(f,x,ridge.CONFIGS[0])
        weights=np.asarray([.75,.75,1.5,1.,1.,1.]);mean=(weights*x[:,0]).sum()/6
        rms=np.sqrt((weights*(x[:,0]-mean)**2).sum()/6);z=(x[:,0]-mean)/rms
        intercept=(weights*f.measured_delta.to_numpy()).sum()/6
        np.testing.assert_allclose(captured['lhs'],[[(weights*z*z).sum()/6+.005]],atol=1e-14)
        np.testing.assert_allclose(captured['rhs'],[(weights*z*(f.measured_delta-intercept)).sum()/6],atol=1e-14)
        self.assertEqual(model['supported'],[True,False,False]);self.assertEqual(model['beta'][1:],[0.,0.])
        held=np.asarray([[2.,1234.,900.]])
        expected=intercept+(2.-mean)/rms*.2
        np.testing.assert_allclose(ridge.predict_model(model,held),[expected],atol=1e-14)
        np.testing.assert_allclose(ridge.predict_model(model,held),ridge.independent_predict(model,held),atol=1e-14)
        np.testing.assert_array_equal(ridge.predict_model(model,held),ridge.predict_model(json.loads(json.dumps(model)),held))

    def test_nested_source_reselection_lexical_ties_ignore_outer_truth(self):
        rows=[]
        parents=['AAAAC','CCCCA','GGGGA'];mutants=[['AAAAT','AAAAG'],['CCCCT','CCCCG'],['GGGGT','GGGGC']]
        for cell in ('CAD','Neuro-2a'):
            for fold in (0,1,2):
                for candidate in (0,1):
                    rows.append({'intervention_id':cell+str(fold)+str(candidate),'dataset':'mikl_gse173098',
                        'cell_type':cell,'held_parent_fold':fold,'biological_component':'gene'+str(fold),
                        'gene_transcript':'G'+str(fold),'parent_context_id':cell+str(fold),
                        'parent_sequence':parents[fold],'mutant_sequence':mutants[fold][candidate],
                        'measured_delta':[-.2,.3][candidate],'candidate':candidate})
        whole=pd.DataFrame(rows)
        def select(data):
            tr,te=outer_masks(data,'CAD_to_N2A',0);source=data.loc[tr].reset_index(drop=True)
            scores=[]
            for config in routes.CONFIGS:
                oof=np.full(len(source),np.nan)
                for fold in sorted(source.held_parent_fold.unique()):
                    train,validation=inner_masks(source,int(fold))
                    self.assertEqual(set(source.loc[train,'cell_type']),{'CAD'})
                    self.assertNotIn('gene0',set(source.loc[train,'biological_component']))
                    native=np.zeros(int(validation.sum())) if config['max_leaf_nodes']<31 else source.loc[validation,'candidate'].to_numpy(float)
                    oof[validation]=native
                scores.append(inner_regret(source,oof))
                self.assertAlmostEqual(scores[-1],replay_regret(source,oof))
            return engine.choose_configuration(routes.CONFIGS,scores),source,scores
        selected,source,values=select(whole)
        self.assertEqual(selected['id'],'hgb_31');self.assertEqual(values,[.5,.5,0.])
        changed=whole.copy();changed.loc[changed.cell_type.eq('Neuro-2a'),'measured_delta']*= -100.
        self.assertEqual(select(changed)[0],selected)
        self.assertEqual(engine.choose_configuration(routes.CONFIGS,[.3,.3-5e-13,.5])['id'],'hgb_7')
        native=np.zeros(len(source));alternate=source.candidate.to_numpy(float)*1e-13
        self.assertLess(np.max(abs(native-alternate)),1e-9)
        chosen=decisions(source,native,'synthetic');other=decisions(source,alternate,'synthetic')
        self.assertTrue(chosen.selected_id.str.endswith('0').all())
        self.assertFalse(list(chosen.selected_id)==list(other.selected_id))

    def test_bootstrap_shared_gene_draw_and_unequal_best_fold_removal(self):
        a=pd.Series([1.,-1.],index=['g1','g2']);b=(-a).iloc[::-1]
        np.testing.assert_allclose(shared_bootstrap({'CAD_to_N2A':a,'N2A_to_CAD':b},64,4),0.,atol=1e-15,rtol=0)
        rows=[]
        for task in ('CAD_to_N2A','N2A_to_CAD'):
            for gene,fold,gain in [('g0',0,.04),('g1',0,.06),('g2',1,.01),('g3',2,.015),('g4',2,.025)]:
                rows.append({'task':task,'biological_component':gene,'gene_fold':fold,
                             'regret':.5-gain,'wrong_direction':.1})
        candidate=pd.DataFrame(rows);control=candidate.assign(regret=.5)
        result=compare(candidate,control)
        self.assertEqual(result['removed_best_gene_fold'],0)
        self.assertAlmostEqual(result['mean_gain'],.03)
        self.assertAlmostEqual(result['remaining_gain'],.05/3)
        self.assertNotAlmostEqual(result['remaining_gain'],.015)
        self.assertEqual(result['macro_wrong_direction_harm'],0.)

    def test_decision_roster_dataset_component_corruption_rejected(self):
        target=frame().loc[lambda f:f.parent_context_id.ne('v')].reset_index(drop=True)
        score=np.arange(len(target),dtype=float);saved=decisions(target,score,'synthetic')
        check_choices(target,score,saved)
        corrupt=saved.copy();corrupt.loc[0,'biological_component']='wrong_gene'
        with self.assertRaises(AssertionError):check_choices(target,score,corrupt)
        corrupt=saved.copy();corrupt.loc[0,'dataset']='wrong_source'
        with self.assertRaises(AssertionError):check_choices(target,score,corrupt)
        duplicate=pd.concat([saved,saved.iloc[[0]]],ignore_index=True)
        with self.assertRaises(AssertionError):check_choices(target,score,duplicate)
        with self.assertRaises(AssertionError):check_choices(target,score,saved.iloc[:-1])


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NonlinearTests))
    assert result.wasSuccessful()
    jsave(OUT/'tests_receipt_v3.json',{'status':'PASS','tests':result.testsRun,
        'source_hashes':{p.name:sha256(p) for p in sorted(SRC.glob('*.py'))},
        'scope':'Synthetic tree arithmetic and mocked-fitting only','real_estimator_fits':0,
        'project_outcome_columns_read':False,'gene_cell_masks_reused':True,
        'ridge_linear_solve_mocked':True,'prior_six_test_receipt_preserved':True,
        'sidecar_corruption_orphans_checked':True,'canonical_ties_source_reselection_checked':True,
        'shared_bootstrap_unequal_fold_weighting_checked':True,
        'decision_dataset_component_full_roster_checked':True,'prior_v2_receipt_preserved':True})


if __name__=='__main__':run()
