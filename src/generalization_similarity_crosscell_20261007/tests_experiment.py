"""Outcome-free/mocked supervised controls; no project or estimator fitting."""
from .experiment_common import *
from . import engine,routes,verify,gate
from .bootstrap import family_bootstrap,shared_bootstrap
from .splits import outer_masks,inner_masks,attach_groups
from .tests import fixture
import unittest,tempfile,shutil
from unittest import mock

def ranking_frame():
    rows=[]
    for gene,fold in [('A',0),('B',1),('C',2)]:
        for i,effect in enumerate([-1.,0.,1.]):
            rows.append({'intervention_id':gene+str(i),'dataset':'mikl_gse173098','cell_type':'CAD',
                         'endpoint_class':'projection','parent_context_id':gene,'biological_component':gene,
                         'gene_transcript':gene,'held_parent_fold':fold,'parent_sequence':gene*150,
                         'mutant_sequence':gene*149+str(i),'similarity_component':gene,'measured_delta':effect})
    return pd.DataFrame(rows)

class Tests(unittest.TestCase):
    def test_original_preanalysis_sources_preserved(self):
        receipt=readj(OUT/'metadata_graph_receipt.json');before=readj(OUT/'preanalysis_manifest.json')
        for name,digest in receipt['source_hashes'].items():self.assertEqual(sha256(ROOT/name),digest)
        self.assertEqual(sha256(REP/'protocol.md'),before['protocol_sha256'])
        self.assertEqual(receipt['cutoff'],30);self.assertTrue(receipt['all_outer_inner_support_nonempty'])

    def test_global_family_source_inner_exclusion(self):
        meta=fixture();families=pd.DataFrame({'biological_component':list('ABCDEF'),'similarity_component':['abc','abc','abc','d','e','f']})
        grouped=attach_groups(meta,families)
        before=grouped.copy(deep=True)
        tr,te=outer_masks(grouped,'CAD_to_N2A',0)
        self.assertEqual(set(grouped.loc[tr,'gene_transcript']),{'D','E'})
        self.assertEqual(set(grouped.loc[te,'gene_transcript']),{'A','F'})
        source=grouped[(grouped.cell_type=='CAD')&grouped.gene_transcript.isin(['B','C','D'])].reset_index(drop=True)
        itr,iva=inner_masks(source,1);self.assertFalse(itr.any());self.assertTrue(iva.any())
        pd.testing.assert_frame_equal(grouped,before)

    def test_source_only_nested_configuration_and_exact_ties(self):
        frame=ranking_frame();score=frame.measured_delta.to_numpy();inverse=-score
        good=verify.replay_regret(frame,score);bad=verify.replay_regret(frame,inverse)
        self.assertEqual(engine.choose_configuration(routes.CONFIGS,[bad,good,bad]),routes.CONFIGS[1])
        self.assertEqual(engine.choose_configuration(routes.CONFIGS,[good,good,good]),routes.CONFIGS[0])
        lexical=verify.replay_regret(frame,np.zeros(len(frame)));self.assertEqual(lexical,.5)
        held_truths=np.array([999.,-999.]);held_truths*=-1
        self.assertEqual(engine.choose_configuration(routes.CONFIGS,[bad,good,bad]),routes.CONFIGS[1])

    def test_checkpoint_creation_hash_orphans_and_training_binding(self):
        temp=Path(tempfile.mkdtemp(prefix='similarity_mock_',dir=ART)).resolve();self.assertTrue(temp.is_relative_to(ART))
        try:
            save(temp/'prefit_manifest.json',b'{"mock":true}\n');frame=ranking_frame();x=np.arange(len(frame)*2,dtype=float).reshape(len(frame),2)
            config=routes.CONFIGS[0];calls=[]
            def fakefit(training,matrix,c):
                calls.append(len(training));return {'training_weights_sha256':hashlib.sha256(routes.row_weights(training).tobytes()).hexdigest(),
                    'training_pair_roster_sha256':routes.pair_hash(training),'mean':[0.,0.],'scale':[1.,1.],'beta':[1.,0.],'active':[True,False]}
            fake=mock.Mock(fit_model=fakefit)
            with mock.patch.object(engine,'OUT',temp),mock.patch.object(engine,'freeze_check',lambda **kwargs:None),mock.patch.object(engine,'module',return_value=fake):
                engine.checkpoint('base','synthetic',frame,x,config);engine.checkpoint('base','synthetic',frame,x,config)
                self.assertEqual(calls,[len(frame)])
                changed=frame.copy();changed.loc[0,'measured_delta']=7
                with self.assertRaises(AssertionError):engine.checkpoint('base','synthetic',changed,x,config)
                with self.assertRaises(AssertionError):engine.checkpoint('base','synthetic',frame,x+1,config)
                changed=frame.copy();changed.loc[0,'similarity_component']='other'
                with self.assertRaises(AssertionError):engine.checkpoint('base','synthetic',changed,x,config)
                path=temp/'base/fits/synthetic_pair_005.json';path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaises(AssertionError):engine.checkpoint('base','synthetic',frame,x,config)
                path.unlink()
                with self.assertRaises(AssertionError):engine.checkpoint('base','synthetic',frame,x,config)
        finally:
            assert temp.is_relative_to(ART);shutil.rmtree(temp)

    def test_independent_coefficients_and_original_choice_roster(self):
        frame=ranking_frame();x=np.column_stack([frame.measured_delta,np.arange(len(frame))])
        model={'mean':[0.,0.],'scale':[1.,1.],'beta':[1.,0.],'active':[True,False]}
        canonical=routes.predict_model(model,x);independent=routes.independent_predict(model,x)
        np.testing.assert_allclose(canonical,independent,rtol=0,atol=1e-12)
        d=decisions(frame,canonical,'base');verify.check_choices(frame,canonical,d)
        corrupt=d.copy();corrupt.loc[0,'biological_component']='other'
        with self.assertRaises(AssertionError):verify.check_choices(frame,canonical,corrupt)
        with self.assertRaises(AssertionError):verify.check_choices(frame,canonical,pd.concat([d,d.iloc[[0]]]))

    def test_shared_family_draws_retain_equal_gene_estimand(self):
        a=pd.Series([1.,3.,5.],index=['a','b','c']);b=pd.Series([-5.,-3.,-1.],index=['c','b','a'])
        family={'a':'shared','b':'shared','c':'other'}
        np.testing.assert_allclose(family_bootstrap({'one':a,'two':b},100,7,family),0,atol=1e-12,rtol=0)
        result=family_bootstrap({'one':a},1,7,family)[0]
        draws=np.random.default_rng(7).exponential(1,size=(1,2))[0] # sorted other/shared
        expected=(draws[1]*1+draws[1]*3+draws[0]*5)/(2*draws[1]+draws[0])
        self.assertAlmostEqual(result,expected)
        self.assertNotAlmostEqual(result,(draws[1]*2+draws[0]*5)/(draws[1]+draws[0]))

    def test_gate_requires_both_gene_and_family_lowerbound(self):
        decisions_by_track={}
        for track in TRACKS:
            value={'simple':.3,'base':.3,'raw':.2,'lookup':.2,'structure':.1,'bert':.1,'combined':.1}[track]
            decisions_by_track[track]=pd.DataFrame([{'model':track,'task':task,'biological_component':gene,'gene_fold':fold,
                'regret':value,'wrong_direction':0.,'avoidable_wrong':0.,'pairwise_accuracy':1.}
                for task in TASKS for fold,gene in enumerate(['a','b','c'])])
        outputs={}
        def read(path):
            path=Path(path)
            if path.name=='verification_receipt.json':return {'status':'PASS','result_files':{}}
            if path.name=='run_complete.json':return {'status':'PASS'}
            return outputs[path.name]
        with mock.patch.object(gate,'freeze_check',lambda:None),mock.patch.object(gate,'readj',side_effect=read),\
             mock.patch.object(gate.pd,'read_csv',side_effect=lambda path,**kwargs:decisions_by_track[Path(path).parent.name]),\
             mock.patch.object(gate,'family_bootstrap',return_value=np.full(5000,-.1)),\
             mock.patch.object(gate,'unpurged_diagnostic',return_value={}),\
             mock.patch.object(gate,'jsave',side_effect=lambda path,data:outputs.update({Path(path).name:data})),\
             mock.patch.object(gate,'csvsave',lambda *args:None):
            gate.run()
        structure=next(row for row in outputs['gate_verdict.json']['tracks'] if row['track']=='structure')
        self.assertTrue(structure['checks']['base_paired_bootstrap_lower_above_zero'])
        self.assertFalse(structure['checks']['base_family_bootstrap_lower_above_zero'])
        self.assertFalse(structure['passes'])

    def test_prediction_configuration_false_report_rejected(self):
        saved=pd.DataFrame({'configuration':['pair_05','pair_05']})
        verify.check_prediction_configuration(saved,routes.CONFIGS[1])
        with self.assertRaises(AssertionError):verify.check_prediction_configuration(saved,routes.CONFIGS[0])
        saved.loc[0,'configuration']='pair_5'
        with self.assertRaises(AssertionError):verify.check_prediction_configuration(saved,routes.CONFIGS[1])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));assert result.wasSuccessful()
    jsave(OUT/'experiment_tests_receipt_v2.json',{'status':'PASS','tests':result.testsRun,'project_fits':0,'actual_estimator_fits':0,
        'source_hashes':{path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(SRC.glob('*.py'))}})
