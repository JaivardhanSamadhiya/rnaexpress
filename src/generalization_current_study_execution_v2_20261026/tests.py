"""Invented ownership/admission tests; no actual process Job or project rows."""
from contextlib import ExitStack
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as Obj
import unittest
from unittest.mock import patch
from . import common as c,supervise as s

MEM={'physical_available':700*2**20,'physical_total':16*2**30,'commit_headroom':4*2**30,'disk_available':4*2**30}
PROC={'private_commit':100*2**20,'peak_private_commit':120*2**20,'working_set':80*2**20,'peak_working_set':90*2**20}
JOB={'active_processes':0,'peak_job_memory_used':120*2**20,'peak_process_memory_used':120*2**20}
CAP={'after':{'maximum':c.RESIDENT,'minimum':204800,'flags':6},'before':{'maximum':1413120,'minimum':204800,'flags':10}}


class Cases(unittest.TestCase):
    def test_optimized_python_cannot_disable_scientific_checks(self):
        with patch.object(c.sys,'flags',Obj(optimize=1)),self.assertRaises(RuntimeError):c.source_mode()

    def test_resource_boundaries_keep_original_live_reserves(self):
        self.assertIsNone(c.resource_failure(MEM,1800,startup=True))
        self.assertIsNotNone(c.resource_failure(MEM,1800.00001))
        for field,bound in (('physical_available',256*2**20),('commit_headroom',2**30),('disk_available',2**30)):
            value=dict(MEM);value[field]=bound-1
            self.assertIsNotNone(c.resource_failure(value,1))
        value=dict(MEM);value['physical_available']=512*2**20-1
        self.assertIsNotNone(c.resource_failure(value,0,startup=True))
        for bad in (-1,float('nan'),float('inf')):
            with self.assertRaises(AssertionError):c.resource_failure(MEM,bad)

    def test_stage_names_cannot_escape_or_enable_evaluation(self):
        for name in ('../fit','replay','evaluate','fit_retry',''):
            with self.assertRaises(AssertionError):c.Stage(name)

    def test_explicit_root_flag_is_required_before_io(self):
        with patch.object(c,'sources',side_effect=AssertionError('must not read sources')):
            with self.assertRaises(AssertionError):s.run(c.Stage('fit'),'a'*64)

    def test_absent_new_human_authorization_fails_before_any_native_probe(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(c,'AUTH',Path(folder)/'absent.json'),patch.object(c,'source_mode'):
            with self.assertRaises(FileNotFoundError):c.authorization('a'*64)

    def test_authority_binds_exact_new_generation_scope_and_no_retry(self):
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            root=Path(folder);scope=root/'scope.md';scope.write_bytes(b'invented scope')
            authority=root/'auth.json'
            stack.enter_context(patch.object(c,'source_mode'));stack.enter_context(patch.object(c,'AUTH',authority));stack.enter_context(patch.object(c,'SCOPE',scope))
            value={'status':'NEW_HUMAN_APPROVAL_CURRENT_PREFIT_AND_ONE_FRESH_FIXED_FIT','source_manifest_sha256':'a'*64,
                'approval_scope_sha256':c.sha(scope),'approved_stages':['prefit','fit'],'attempts_per_stage':1,
                'automatic_retry':False,'resume_authorized':False,'spending_authorized':False,
                'new_manual_approval_after_old_attempt_consumed':True,'actual_user_response':'invented test answer',
                'question_item_id':'invented-only','actual_user_response_recorded_verbatim':True}
            authority.write_bytes(c.canonical(value));self.assertEqual(c.authorization('a'*64)[1],value)
            with self.assertRaises(AssertionError):c.authorization('b'*64)
            value['automatic_retry']=True;authority.write_bytes(c.canonical(value))
            with self.assertRaises(AssertionError):c.authorization('a'*64)

    def test_exact_commit_reader_resolves_revision_and_bounds_body(self):
        name='results/'+c.NS+'/prefit/current_prefit.json';calls=[]
        outputs=[b'a'*40+b'\n',b'8\n',b'invented']
        def run(args,**kwargs):
            calls.append((args,kwargs));return Obj(stdout=outputs.pop(0))
        with patch.object(c,'sha',return_value=c.GIT_SHA),patch.object(c.subprocess,'run',side_effect=run):
            self.assertEqual(c.committed(name,'a'*40),b'invented')
        self.assertEqual(calls[1][0][-1],'a'*40+':'+name)
        self.assertEqual(calls[2][0][-1],calls[1][0][-1])
        self.assertTrue(all(call[1]['timeout']==30 and 'shell' not in call[1] for call in calls))
        self.assertTrue(all(call[1]['creationflags']==0x00000008 for call in calls))
        with patch.object(c.subprocess,'run',side_effect=AssertionError('must not run Git')):
            with self.assertRaises(AssertionError):c.committed('results/protected/outcome.json')
            with self.assertRaises(AssertionError):c.committed(name,'main;anything')

    def test_oversize_git_body_refused_before_capture(self):
        calls=[]
        def run(args,**kwargs):calls.append(args);return Obj(stdout=b'a'*40+b'\n' if len(calls)==1 else str(33*2**20).encode())
        with patch.object(c,'sha',return_value=c.GIT_SHA),patch.object(c.subprocess,'run',side_effect=run),self.assertRaises(AssertionError):
            c.committed('results/'+c.NS+'/prefit/current_prefit.json')
        self.assertEqual(len(calls),2)

    def parent(self,mode):
        events=[];clock=[0.];generation='a'*64
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            out=Path(folder);stack.enter_context(patch.object(c,'OUT',out));stage=c.Stage('prefit');stage.directory.mkdir()
            admitted={'input_pins':{},'new_manual_authorization_sha256':'b'*64}
            original_write=c.write
            def write(stream,value):
                if mode=='telemetry' and value['status']=='MANDATORY_PARENT_TELEMETRY_COMPLETE':raise OSError('invented durable-log failure')
                original_write(stream,value)
            class Child:
                pid=21;process_handle=1
                def resume(self):
                    events.append('resume');assert stage.path('owned_child_started.json').exists()
                    digest=c.save_new(stage.path('current_prefit.json'),{'invented':True})
                    c.save_new(stage.path('worker_report.json'),{'current_prefit_sha256':digest,'checkpoint_current_runtime_proof_sha256':{}})
                    c.save_new(stage.path('worker_completion.json'),{'invented':True})
                def exit_code(self):return None if mode=='reserve' else 0
                def close(self):events.append('childclose')
            class JobDouble:
                def __enter__(self):events.append('job');return self
                def __exit__(self,*args):events.append('jobclose')
                def limits(self):return dict(c.CAPS)
                def _membership(self,*args):events.append('membership')
                def spawn(self,command,cwd):events.append('spawn');return Child()
                def accounting(self):return dict(JOB)
                def terminate(self):events.append('terminate')
            readings=[0]
            def memory():
                readings[0]+=1;value=dict(MEM)
                if mode=='reserve' and readings[0]>=3:value['physical_available']=128*2**20
                return value
            def terminal(*args,**kwargs):
                if mode=='late':clock[0]=1801.
                return {'current_prefit_sha256':c.sha(stage.path('current_prefit.json')),'saved_checkpoint_files_sha256':{}}
            for obj,name,value in ((c,'sources',lambda *args,**kwargs:{'original_input_pins':{}}),
                (c,'admission',lambda *args:(b'invented',admitted)),(c,'old_absences',lambda:[]),(c,'write',write),
                (s.headless,'Job',JobDouble),(s.headless,'memory',memory),(s.headless,'native_origins',lambda:{}),
                (s.headless,'process_memory',lambda _:dict(PROC)),(s.working_set,'apply',lambda *args:CAP),
                (s.working_set,'verify',lambda *args:None),(s.validate,'terminal',terminal),(s.time,'monotonic',lambda:clock[0])):
                stack.enter_context(patch.object(obj,name,value))
            stage.path('run_admission.json').write_bytes(b'invented')
            try:s.run(stage,generation,root_start_authorized=True)
            except (OSError,AssertionError):
                if mode=='success':raise
            else:self.assertEqual(mode,'success')
            self.assertLess(events.index('membership'),events.index('resume'))
            self.assertIn('childclose',events);self.assertIn('jobclose',events)
            if mode=='telemetry':self.assertFalse(stage.path('supervisor_receipt.json').exists())
            else:
                result=c.decode(stage.path('supervisor_receipt.json').read_bytes())
                self.assertEqual(result['status'],'PASS_NEW_CURRENT_STUDY_STAGE_NOT_REPLAY_OR_GATE' if mode=='success' else 'FAILED_NEW_CURRENT_STUDY_STAGE_NO_RETRY')
                if mode=='reserve':
                    self.assertIn('terminate',events)
                    self.assertIn('physical reserve',stage.path('parent.jsonl').read_text())
            before=events.count('spawn')
            with self.assertRaises(AssertionError):s.run(stage,generation,root_start_authorized=True)
            self.assertEqual(events.count('spawn'),before)

    def test_parent_binds_child_before_resume_and_cannot_repeat(self):self.parent('success')
    def test_offending_resource_sample_is_preserved_and_job_stopped(self):self.parent('reserve')
    def test_late_validation_cannot_publish_success(self):self.parent('late')
    def test_telemetry_failure_cannot_publish_success(self):self.parent('telemetry')


def run(receipt_name='invented_tests_receipt.json'):
    assert Path(receipt_name).name==receipt_name and receipt_name.endswith('.json')
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    print(stream.getvalue(),end='');assert result.wasSuccessful()
    value={'status':'INVENTED_CURRENT_STUDY_OWNERSHIP_NO_ACTUAL_AUTHORITY_OR_EXECUTION',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'actual_data_reads':0,'actual_native_jobs':0,
        'source_sha256':{path.relative_to(c.ROOT).as_posix():c.sha(path) for path in Path(__file__).parent.glob('*.py')}}
    c.save_new(c.OUT/receipt_name,value)


if __name__=='__main__':run()
