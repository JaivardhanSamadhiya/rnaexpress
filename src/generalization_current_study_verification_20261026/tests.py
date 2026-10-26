"""Invented read-only controller tests. No actual source payloads or Jobs."""
import ast
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
    def test_fitting_stages_rejected_and_explicit_root_flag_required(self):
        for name in ('fit','prefit','../evaluate'):
            with self.assertRaises(AssertionError):c.Stage(name)
        with patch.object(c,'sources',side_effect=RuntimeError('must not run')):
            with self.assertRaises(AssertionError):s.run(c.Stage('replay'),'a'*64)

    def test_root_authority_cannot_claim_new_human_or_fit_permission(self):
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            root=Path(folder);scope=root/'scope';scope.write_bytes(b'invented scope');auth=root/'authority'
            for obj,name,value in ((c,'AUTH',auth),(c,'SCOPE',scope),(c,'source_mode',lambda:None)):stack.enter_context(patch.object(obj,name,value))
            value={'status':'ROOT_INITIATED_READONLY_VERIFICATION_UNDER_STANDING_RESEARCH_REQUEST',
                'source_manifest_sha256':'a'*64,'protocol_sha256':c.sha(scope),'stages':['replay','evaluate'],
                'new_human_approval_claimed':False,'FIT_authority_reused':False,'model_fitting_authorized':False,
                'automatic_retry':False,'spending_authorized':False}
            auth.write_bytes(c.canonical(value));self.assertEqual(c.authorization('a'*64)[1],value)
            value['new_human_approval_claimed']=True;auth.write_bytes(c.canonical(value))
            with self.assertRaises(AssertionError):c.authorization('a'*64)

    def test_production_has_no_fitting_calls(self):
        for name in ('common','owned','worker','validate','supervise','prepare'):
            tree=ast.parse((Path(__file__).parent/(name+'.py')).read_bytes())
            calls={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
                if isinstance(n,ast.Call) and isinstance(n.func,(ast.Attribute,ast.Name))}
            self.assertFalse(calls & {'minimize','fit_prepared','fit','run_fixed_campaign'},name)

    def parent(self,mode):
        events=[];clock=[0.]
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            out=Path(folder);stack.enter_context(patch.object(c,'OUT',out));stage=c.Stage('replay');stage.directory.mkdir()
            reference=out/'invented_reference';reference.write_bytes(b'invented reference')
            admitted={'input_pins':{},'checkpoint_pins':{},'read_only_authority_sha256':'b'*64,
                'current_prefit_relative_path':'results/invented/reference','current_prefit_sha256':c.sha(reference)}
            class Child:
                pid=21;process_handle=1
                def resume(self):
                    assert stage.path('owned_child_started.json').exists();events.append('resume')
                    c.save_new(stage.path('worker_report.json'),{'checkpoint_current_runtime_proof_sha256':{}})
                    c.save_new(stage.path('worker_completion.json'),{'invented':True})
                def exit_code(self):return 0
                def close(self):events.append('childclose')
            class JobDouble:
                def __enter__(self):events.append('job');return self
                def __exit__(self,*args):events.append('jobclose')
                def limits(self):return dict(c.CAPS)
                def _membership(self,*args):events.append('membership')
                def spawn(self,*args):events.append('spawn');return Child()
                def accounting(self):return dict(JOB)
                def terminate(self):events.append('terminate')
            original_write=c.write
            def write(stream,value):
                if mode=='telemetry' and value['status']=='MANDATORY_PARENT_TELEMETRY_COMPLETE':raise OSError('invented log failure')
                original_write(stream,value)
            def terminal(*args,**kwargs):
                if mode=='late':clock[0]=1801.
                return {'verified_stage':'replay','result_status':'INVENTED','model_fits_or_refits':0}
            for obj,name,value in ((c,'sources',lambda *a,**kw:{}),(c,'admission',lambda *a:(b'invented',admitted)),
                (c,'relative',lambda name:reference),(c,'old_absences',lambda:[]),(c,'write',write),
                (s.headless,'Job',JobDouble),(s.headless,'memory',lambda:dict(MEM)),(s.headless,'native_origins',lambda:{}),
                (s.headless,'process_memory',lambda _:dict(PROC)),(s.working_set,'apply',lambda *a:CAP),
                (s.working_set,'verify',lambda *a:None),(s.validate,'terminal',terminal),(s.time,'monotonic',lambda:clock[0])):
                stack.enter_context(patch.object(obj,name,value))
            stage.path('run_admission.json').write_bytes(b'invented')
            try:s.run(stage,'a'*64,root_start_readonly=True)
            except (AssertionError,OSError):
                if mode=='success':raise
            else:self.assertEqual(mode,'success')
            self.assertLess(events.index('membership'),events.index('resume'));self.assertIn('childclose',events);self.assertIn('jobclose',events)
            if mode=='telemetry':self.assertFalse(stage.path('supervisor_receipt.json').exists())
            else:
                result=c.decode(stage.path('supervisor_receipt.json').read_bytes())
                self.assertEqual(result['status'],'PASS_CURRENT_READONLY_VERIFICATION_STAGE' if mode=='success' else 'FAILED_CURRENT_READONLY_VERIFICATION_NO_RETRY')
            previous=events.count('spawn')
            with self.assertRaises(AssertionError):s.run(stage,'a'*64,root_start_readonly=True)
            self.assertEqual(events.count('spawn'),previous)

    def test_parent_closes_and_cannot_repeat(self):self.parent('success')
    def test_late_validation_cannot_pass(self):self.parent('late')
    def test_failed_mandatory_telemetry_cannot_pass(self):self.parent('telemetry')


def run():
    assert not any(n.split('.')[0] in ('numpy','pandas','scipy') for n in sys.modules)
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    print(stream.getvalue(),end='');assert result.wasSuccessful()
    value={'status':'PASS_INVENTED_READONLY_CONTROLLER_NO_REAL_JOBS_OR_BIOLOGICAL_READS',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'actual_biological_reads':0,'actual_native_jobs':0,
        'source_sha256':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in Path(__file__).parent.glob('*.py')}}
    c.save_new(c.OUT/'invented_tests_receipt.json',value)


if __name__=='__main__':run()
