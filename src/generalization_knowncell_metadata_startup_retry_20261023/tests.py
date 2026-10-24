"""Invented path/identity/resource tests only; no actual Job or payload."""
import ast
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
from . import common as c
from . import supervise as s

SRC=c.ROOT/'src'/c.NS


def state(physical=3*2**30,disk=2**30,commit=2**30):
    return {'physical_available':physical,'disk_available':disk,'commit_headroom':commit}


def invented_block():
    return {'status':'BLOCKED_ORIGINAL_METADATA_V2_STARTUP_FLOOR_NO_WORKER',
            'worker_started':False,'project_payloads_opened':0,'model_fits':0,
            'automatic_retry':False,'original_resource_guards_unchanged':True,
            'initial_committed_execution_manifest_sha256':c.V2_SHA,
            'source_mode':{'pycache_prefix':str(c.v2.CACHE_PREFIX),'cache_prefix_absent':True}}


class FakeJob:
    instances=[]
    def __init__(self):self.spawns=[];self.terminated=False;self.__class__.instances.append(self)
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def limits(self):return {'process_memory_limit':768*2**20,'job_memory_limit':896*2**20,
                            'active_process_limit':2,'limit_flags':s.headless.original.LIMIT_FLAGS}
    def spawn(self,*args):
        self.spawns.append(args);raise RuntimeError('Invented spawn prohibited')
    def terminate(self):self.terminated=True


class Cases(unittest.TestCase):
    def fixture(self,folder,probe,job):
        out=Path(folder)/'new';out.mkdir()
        old=Path(folder)/'old';old.mkdir()
        paths=(old/'bundle.json',old/'worker.log',old/'worker_completion.json')
        admission=c.Admission(b'{}','a'*64,b'{}',c.V2_SHA)
        stack=ExitStack();self.addCleanup(stack.close)
        for target,name,value in ((s,'OUT',out),(s,'admitted',Mock(return_value=admission)),
                 (s,'worker_paths',Mock(return_value=paths)),(s,'verify_sources',Mock(return_value={})),
                 (s,'source_mode',Mock(return_value={'invented':True})),
                 (s.headless,'memory',probe),(s.headless,'Job',job)):
            stack.enter_context(patch.object(target,name,value))
        return out,paths

    def test_original_block_must_have_zero_worker_and_payload(self):
        doc=invented_block();self.assertFalse(c.blocked_document(c.v2.canonical(doc))['worker_started'])
        for key,value in (('worker_started',True),('project_payloads_opened',1),('model_fits',1),
                          ('initial_committed_execution_manifest_sha256','b'*64)):
            bad=dict(doc);bad[key]=value
            with self.assertRaises(AssertionError):c.blocked_document(c.v2.canonical(bad))

    def test_duplicate_block_json_keys_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Duplicate'):
            c.blocked_document(b'{"worker_started":false,"worker_started":false}')

    def test_every_old_partial_worker_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/name for name in ('bundle.json','worker.log','worker_completion.json')]
            c.require_absent(paths)
            for path in paths:
                path.write_text('invented retained')
                with self.assertRaisesRegex(AssertionError,'no resume'):c.require_absent(paths)
                self.assertEqual(path.read_text(),'invented retained');path.unlink()

    def test_broken_link_or_nonregular_existing_path_is_rejected(self):
        with patch.object(c.os.path,'lexists',return_value=True):
            with self.assertRaisesRegex(AssertionError,'Preserve'):c.require_absent((Path('invented'),))

    def test_root_start_required_before_any_admission(self):
        admission=Mock(side_effect=AssertionError('must not admit'))
        with patch.object(s,'admitted',admission):
            with self.assertRaisesRegex(AssertionError,'root-start'):s.run()
        admission.assert_not_called()

    def test_low_ram_writes_separate_block_and_consumes_one_opportunity_no_job(self):
        with tempfile.TemporaryDirectory() as folder:
            job=Mock(side_effect=AssertionError('No job below original floor'))
            out,paths=self.fixture(folder,Mock(return_value=state(3*2**30-1)),job)
            result=s.run(root_start=True)
            self.assertEqual(result['status'],'BLOCKED_ONE_EXPLICIT_METADATA_STARTUP_OPPORTUNITY_NO_WORKER')
            self.assertFalse(result['worker_started']);self.assertEqual(result['project_payloads_opened'],0)
            self.assertEqual(result['initial_committed_execution_manifest_sha256'],c.V2_SHA)
            self.assertEqual(result['preserved_first_blocked_receipt_sha256'],c.OLD_BLOCKED_SHA)
            self.assertEqual(result['initial_committed_addon_manifest_sha256'],'a'*64)
            self.assertEqual(result['attempt_birth_sha256'],c.sha((out/'attempt_birth.json').read_bytes()))
            before={p:p.read_bytes() for p in out.iterdir()}
            with self.assertRaisesRegex(AssertionError,'no resume'):s.run(root_start=True)
            self.assertEqual(before,{p:p.read_bytes() for p in out.iterdir()})
            self.assertTrue(all(not p.exists() for p in paths));job.assert_not_called()

    def test_preexisting_worker_path_prevents_new_birth_and_job(self):
        with tempfile.TemporaryDirectory() as folder:
            job=Mock(side_effect=AssertionError('No job'))
            out,paths=self.fixture(folder,Mock(return_value=state()),job)
            paths[1].write_text('invented earlier worker')
            with self.assertRaisesRegex(AssertionError,'no resume'):s.run(root_start=True)
            self.assertEqual(list(out.iterdir()),[]);job.assert_not_called()

    def test_wait_is_explicit_bounded_resource_sampling_not_worker_retry(self):
        now=[0.];probe=Mock(return_value=state(0))
        def advance(value):self.assertLessEqual(value,.25);now[0]+=value
        result=c.wait_for_floor(60,probe,lambda:now[0],advance)
        self.assertEqual(result[2],60.);self.assertEqual(result[3],241)
        self.assertIn('three-GiB',result[1])
        for value in (-1,61,True,.5):
            with self.assertRaises(AssertionError):c.wait_for_floor(value,probe,lambda:0,advance)

    def test_wait_returns_on_first_readiness_without_launch(self):
        now=[0.]
        result=c.wait_for_floor(60,Mock(side_effect=[state(0),state()]),lambda:now[0],
                                lambda value:now.__setitem__(0,now[0]+value))
        self.assertIsNone(result[1]);self.assertEqual(result[2],.25);self.assertEqual(result[3],2)

    def test_original_resource_boundaries_are_unchanged(self):
        self.assertIs(c.resource_failure,c.v2.original.resource_failure)
        self.assertIsNone(c.resource_failure(state(),300,2))
        for sample,elapsed,active in ((state(3*2**30-1),0,0),(state(disk=2**30-1),0,0),
                                      (state(commit=2**30-1),0,0),(state(),300.001,0),(state(),0,3)):
            self.assertIsNotNone(c.resource_failure(sample,elapsed,active))

    def test_fresh_post_job_floor_cannot_be_replaced_by_earlier_readiness(self):
        FakeJob.instances=[]
        with tempfile.TemporaryDirectory() as folder:
            out,paths=self.fixture(folder,Mock(side_effect=[state(),state(0),state()]),FakeJob)
            with self.assertRaisesRegex(AssertionError,'three-GiB'):s.run(root_start=True)
            self.assertEqual(len(FakeJob.instances),1)
            self.assertEqual(FakeJob.instances[0].spawns,[]);self.assertTrue(FakeJob.instances[0].terminated)
            result=c.read_json((out/'supervisor_receipt.json').read_bytes())
            self.assertEqual(result['status'],'FAILED_ONE_EXPLICIT_METADATA_OPPORTUNITY_PRESERVED')
            self.assertFalse(result['worker_started']);self.assertTrue(all(not p.exists() for p in paths))

    def test_changed_addon_manifest_cannot_redefine_initial_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'manifest.json';path.write_bytes(b'{"invented":1}')
            expected=c.sha(path.read_bytes());path.write_bytes(b'{"invented":2}')
            with patch.object(c,'MANIFEST',path):
                with self.assertRaisesRegex(AssertionError,'initially Git-verified'):
                    c.verify_sources(expected,c.V2_SHA)

    def test_exact_original_worker_command_and_no_global_rebinding(self):
        command=s.original.worker_command(c.V2_SHA)
        self.assertEqual(command[-4:],[
            '-m','src.generalization_knowncell_metadata_execution_v2_20261023.worker','--manifest-sha',c.V2_SHA])
        self.assertIn('pycache_prefix='+str(c.v2.CACHE_PREFIX),command)
        for path in SRC.glob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf-8'))
            if path.name in ('common.py','supervise.py'):
                for node in ast.walk(tree):
                    if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                        targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                        self.assertFalse(any(isinstance(x,ast.Attribute) for x in targets),'No module globals may be rebound')
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertFalse(any(x.name.split('.')[0] in ('numpy','pandas','scipy','torch') for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in ('numpy','pandas','scipy','torch'))


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    c.save_new(c.OUT/'synthetic_tests_receipt.json',{
        'status':'PASS_INVENTED_ONE_STARTUP_OPPORTUNITY_CONTROLS_NOT_EXECUTION',
        'tests':result.testsRun,'source_files':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in SRC.glob('*.py')},
        'actual_jobs_or_workers_started':0,'project_payloads_read':0,'native_scientific_imports':False,'model_fits':0})


if __name__=='__main__':run()
