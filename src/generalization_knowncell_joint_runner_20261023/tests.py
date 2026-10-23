"""Finite orchestration tests with invented stubs, never native/project calls."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from src.generalization_knowncell_joint_campaign_20261023 import contracts as c
from src.generalization_knowncell_joint_campaign_20261023.writer import write_new,unit_spec,UnitCalls
from src.generalization_knowncell_joint_campaign_20261023.tests import plan_for
from src.generalization_knowncell_joint_campaign_20261023.spec import CONFIGS
from . import runner

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_knowncell_joint_runner_20261023'
SRC,OUT=ROOT/'src'/NS,ROOT/'results'/NS
ENV={key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


class FakeCampaign:
    instances=[]
    write_error=False
    def __init__(self,directory,plan):
        self.directory=Path(directory);self.directory.mkdir()
        self.plan=plan;self.tasks={c.task_key(task):task for task in c.task_roster()}
        self.failed=False;self.completed=[];self.finish_calls=0
        write_new(self.directory/'campaign_birth.json',{'invented':True})
        type(self).instances.append(self)
    def write_checkpoint(self,key,callback,selection=None):
        assert not self.failed
        task=self.tasks[key]
        write_new(self.directory/(key+'.birth.json'),{'invented':True,'task_key':key})
        if type(self).write_error:raise OSError('invented checkpoint write error')
        units=UnitCalls(task['arm']);answer=callback(task,{'invented':True},units)
        calls=units.complete()
        write_new(self.directory/(key+'.model.json'),answer)
        receipt={'optimizer_units':len(calls),'invented':True}
        write_new(self.directory/(key+'.complete.json'),receipt)
        self.completed.append(key)
        return receipt
    def finish(self):
        assert not self.failed and len(self.completed)==63
        self.finish_calls+=1
        result={'status':'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
                'checkpoint_count':63,'optimizer_units':84,
                'independent_numeric_and_selection_replay_complete':False,'biological_or_gate_claim':False}
        write_new(self.directory/'campaign_complete.json',result)
        return result


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=plan_for()
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='invented_runner_',dir=OUT)
        self.home=Path(self.temporary.name).resolve()
        assert self.home.is_relative_to(OUT.resolve()) and self.home!=OUT.resolve()
        self.addCleanup(self.temporary.cleanup)
        self.path=self.home/'run';self.events=[];self.runtime=[];self.constructors=[]
        FakeCampaign.instances=[];FakeCampaign.write_error=False
        document=self.plan.document()
        self.prepared=runner.adapter.PreparedPools([],{key:{} for key in document['source_pools']},document)
        self.original_make_callback=runner.adapter.make_fit_callback
        self.patches=[patch.object(runner,'Campaign',FakeCampaign),
                      patch.object(runner.adapter,'make_fit_callback',self.make_callback),
                      patch.object(runner.adapter,'select_outer',self.select)]
        for value in self.patches:value.start();self.addCleanup(value.stop)
    def probe(self):return {'physical_available':3*2**30,'disk_available':2**30}
    def integrity(self,**kwargs):
        self.events.append(('hook',kwargs['task_key']))
        self.assertIs(kwargs['plan'],self.plan)
        return True
    def optimizer(self,tag):self.runtime.append(tag);return 'invented Python stub, not minimize'
    def make_callback(self,np,minimize,expit,prepared,plan,*,probe,environment):
        self.constructors.append('callback')
        def callback(task,birth,units):
            key=c.task_key(task);self.events.append(('fit',key))
            for name,width in unit_spec(task['arm']):units.invoke(name,width,minimize,key)
            return {'invented_only':True,'task_key':key}
        return callback
    def select(self,prepared,campaign,arm,outer_fold,*,probe,environment):
        self.events.append(('select',arm,outer_fold))
        inner=[key for key,task in campaign.tasks.items() if task['arm']==arm and task['outer_fold']==outer_fold and task['phase']=='inner']
        self.assertEqual(len(inner),6);self.assertTrue(all(key in campaign.completed for key in inner))
        return {'selected_config':dict(CONFIGS[1]),'invented_only':True}
    def run_one(self,probe=None,integrity=None):
        return runner.run_campaign(self.prepared,self.plan,object(),self.optimizer,lambda x:x,
            probe=probe or self.probe,environment=ENV,directory=self.path,
            before_checkpoint_integrity=integrity or self.integrity)
    def failure(self):return c.strict_json((self.path/'runner_failure.json').read_bytes())

    def test_exact_roster_order_63_trios_84_stub_units_and_six_inner_prerequisites(self):
        result=self.run_one();campaign=FakeCampaign.instances[0]
        expected=[c.task_key(task) for task in c.task_roster()]
        self.assertEqual(campaign.completed,expected)
        self.assertEqual([event[1] for event in self.events if event[0]=='fit'],expected)
        self.assertEqual([event[1] for event in self.events if event[0]=='hook'],expected)
        self.assertEqual(len([event for event in self.events if event[0]=='select']),9)
        self.assertEqual(len(self.runtime),84);self.assertEqual(self.constructors,['callback'])
        self.assertEqual(len(list(campaign.directory.glob('*.birth.json'))),63)
        self.assertEqual(len(list(campaign.directory.glob('*.model.json'))),63)
        self.assertEqual(len(list(campaign.directory.glob('*.complete.json'))),63)
        self.assertEqual(campaign.finish_calls,1)
        self.assertFalse(result['independent_numeric_and_selection_replay_complete'])
        self.assertFalse((self.path/'runner_failure.json').exists())

    def test_failed_selection_has_six_inners_and_no_outer_callback_or_finish(self):
        def fail(*args,**kwargs):raise RuntimeError('invented selection error')
        with patch.object(runner.adapter,'select_outer',fail):
            with self.assertRaises(RuntimeError):self.run_one()
        campaign=FakeCampaign.instances[0]
        self.assertEqual(len(campaign.completed),6);self.assertEqual(len(self.runtime),6)
        self.assertTrue(campaign.failed);self.assertEqual(campaign.finish_calls,0)
        self.assertEqual(self.failure()['stage'],'selection')
        self.assertFalse((campaign.directory/'campaign_complete.json').exists())

    def test_bad_integrity_prevents_even_callback_construction(self):
        def bad(**kwargs):raise RuntimeError('invented integrity error')
        with self.assertRaises(RuntimeError):self.run_one(integrity=bad)
        self.assertEqual(self.runtime,[]);self.assertEqual(self.constructors,[])
        campaign=FakeCampaign.instances[0]
        self.assertTrue(campaign.failed);self.assertEqual(campaign.finish_calls,0)
        self.assertEqual(self.failure()['stage'],'integrity_hook')

    def test_low_start_resource_has_failure_evidence_no_campaign_or_callbacks(self):
        def low():return {'physical_available':3*2**30-1,'disk_available':2**30}
        with self.assertRaises(AssertionError):self.run_one(probe=low)
        self.assertEqual(FakeCampaign.instances,[]);self.assertEqual(self.runtime,[])
        self.assertEqual(self.failure()['stage'],'start')

    def test_low_resource_before_next_checkpoint_stops_later_callback(self):
        def low_later():
            return {'physical_available':0 if self.runtime else 3*2**30,'disk_available':2**30}
        with self.assertRaises(AssertionError):self.run_one(probe=low_later)
        self.assertEqual(len(self.runtime),1)
        campaign=FakeCampaign.instances[0]
        self.assertEqual(len(campaign.completed),1);self.assertTrue(campaign.failed)
        self.assertEqual(campaign.finish_calls,0)

    def test_partial_checkpoint_error_is_preserved_and_run_poisoned(self):
        FakeCampaign.write_error=True
        with self.assertRaises(OSError):self.run_one()
        campaign=FakeCampaign.instances[0]
        self.assertTrue(campaign.failed);self.assertEqual(self.runtime,[])
        self.assertEqual(len(list(campaign.directory.glob('*.birth.json'))),1)
        self.assertEqual(len(list(campaign.directory.glob('*.model.json'))),0)
        self.assertEqual(campaign.finish_calls,0)
        self.assertEqual(self.failure()['stage'],'checkpoint')

    def test_existing_run_never_resumes_or_overwrites_failure(self):
        with self.assertRaises(RuntimeError):self.run_one(integrity=lambda **kwargs:(_ for _ in ()).throw(RuntimeError('invented stop')))
        before=(self.path/'runner_failure.json').read_bytes();count=len(self.runtime)
        with self.assertRaises(FileExistsError):self.run_one()
        self.assertEqual((self.path/'runner_failure.json').read_bytes(),before)
        self.assertEqual(len(self.runtime),count)

    def test_failure_evidence_error_keeps_original_error_and_poison(self):
        def fail_write(*args,**kwargs):raise PermissionError('invented evidence failure')
        def bad(**kwargs):raise RuntimeError('invented original integrity error')
        with patch.object(runner,'write_new',fail_write):
            with self.assertRaises(RuntimeError) as caught:self.run_one(integrity=bad)
        self.assertIn('original integrity',str(caught.exception))
        self.assertTrue(any('PermissionError' in note for note in caught.exception.__notes__))
        self.assertTrue(FakeCampaign.instances[0].failed)
        self.assertEqual(FakeCampaign.instances[0].finish_calls,0)

    def test_hook_must_return_true(self):
        with self.assertRaises(AssertionError):self.run_one(integrity=lambda **kwargs:None)
        self.assertEqual(self.runtime,[]);self.assertTrue(FakeCampaign.instances[0].failed)

    def test_hook_cannot_mutate_roster_before_any_fit(self):
        def mutate(**kwargs):
            first=next(iter(kwargs['campaign'].tasks))
            kwargs['campaign'].tasks[first]['phase']='outer'
            return True
        with self.assertRaises(AssertionError):self.run_one(integrity=mutate)
        self.assertEqual(self.runtime,[]);self.assertEqual(self.constructors,[])
        self.assertTrue(FakeCampaign.instances[0].failed)

    def test_no_cli_readers_or_scientific_import_and_original_callback_alias(self):
        self.assertIs(self.original_make_callback,runner.adapter.original.make_fit_callback)
        source=(SRC/'runner.py').read_text(encoding='utf-8');tree=ast.parse(source)
        self.assertNotIn('if __name__',source)
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertFalse(any(alias.name.split('.')[0] in ('numpy','pandas','scipy') for alias in node.names))
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in ('numpy','pandas','scipy'))


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    for path in SRC.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    receipt={'status':'PASS_INVENTED_FINITE_RUNNER_STUBS_NOT_NATIVE_OR_PROJECT_CAMPAIGN',
             'tests':result.testsRun,'scientific_imports':False,'native_optimizer_calls':0,
             'models_fitted':0,'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,
             'existing_project_checkpoint_reads':0,'successful_stub_roster':63,'successful_stub_units':84,
             'source_files':{path.relative_to(ROOT).as_posix():c.digest(path.read_bytes()) for path in SRC.glob('*.py')}}
    with (OUT/'synthetic_tests_receipt_reviewed.json').open('xb') as stream:stream.write(c.canonical_bytes(receipt))


if __name__=='__main__':run()
