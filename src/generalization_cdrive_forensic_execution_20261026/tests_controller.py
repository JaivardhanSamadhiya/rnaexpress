"""Invented controller/owner boundary tests; no actual probes, Jobs or data."""
import ast
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,supervise as s,runtime_or_owner as r


MEM={'physical_available':600*2**20,'physical_total':16*2**30,'commit_headroom':3*2**30,'disk_available':4*2**30}
PROC={'working_set':100*2**20,'peak_working_set':150*2**20,'private_commit':180*2**20,'peak_private_commit':200*2**20}
JOB={'active_processes':0,'peak_job_memory_used':200*2**20,'peak_process_memory_used':200*2**20}
CAP={'after':{'minimum':204800,'maximum':c.RESIDENT_REQUEST,'flags':6},'before':{'minimum':204800,'maximum':1413120,'flags':10}}


def report_fixture(generation,birth,identity,owner,parent,child):
    keys={c.lifecycle.task_key(task) for task in c.lifecycle.task_roster()}
    proof={'stage':c.STAGE,'current_pid':child,'parent_pid':parent,'generation_manifest_sha256':generation,
        'birth_sha256':birth,'owned_child_identity_sha256':identity,'current_child_record_sha256':owner,
        'in_owned_job_now':True,'actual_old_campaign_owner_claimed':False}
    diagnostic={'status':'PASS_READONLY_SAVED_CHECKPOINT_NUMERIC_CONSISTENCY_NOT_CAMPAIGN',
        'exact_canonical_scores_equal':True,'new_optimizer_calls':0,'outer_performance_computed':False,
        'old_campaign_closure_or_current_owner_certified':False,'tolerance_strictly_below':1e-9,
        **{name:0. for name in ('maximum_scaling_difference','maximum_objective_difference',
            'maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference')}}
    result={'status':'PASS_FORENSIC_SAVED63_NUMERIC_CONSISTENCY_NOT_CLOSED_CAMPAIGN',
        'verified_checkpoints':63,'recorded_optimizer_units_not_refitted':84,'source_only_reselections_equal':9,
        'checkpoint_numeric_diagnostics':{key:dict(diagnostic) for key in keys},
        'old_campaign_completion_missing':True,'old_supervisor_completion_missing':True,
        'original_formal_replay_still_ineligible':True,'outer_performance_computed_or_published':False,
        'evaluation_or_gate_run':False}
    common={'generation_manifest_sha256':generation,'birth_sha256':birth,'owned_child_identity_sha256':identity,
        'current_child_record_sha256':owner,'parent_pid':parent,'worker_pid':child,'biological_inputs_read':True,
        'biological_rows_read':13781,'new_optimizer_calls':0,'original_formal_replay_still_ineligible':True,
        'outer_performance_computed_or_published':False,'evaluation_or_gate_run':False}
    report={**common,'status':c.REPORT_STATUS,'forensic_numeric_diagnostics':result,
        'saved_declarations':{'status':'PASS190_SAVED_DECLARATIONS_NOT_CAMPAIGN_OR_CURRENT_OWNER',
            'saved_checkpoints':63,'recorded_completed_optimizer_units':84,
            'saved_filename_sha256':{'invented_'+str(i):'8'*64 for i in range(190)},
            'old_campaign_complete_missing':True,'current_owner_or_runtime_admission_granted':False},
        'checkpoint_current_runtime_proof_sha256':{key:'9'*64 for key in keys},
        'runtime_before_inputs':dict(proof),'runtime_after_forensics':dict(proof)}
    complete={**common,'status':c.WORKER_PASS,'report_sha256':c.digest(c.canonical(report)+b'\n')}
    return report,complete


class Cases(unittest.TestCase):
    def test_resource_boundaries_and_total_clock(self):
        self.assertIsNone(c.resource_failure(MEM,1800,startup=True))
        self.assertIsNotNone(c.resource_failure(MEM,1800.000001))
        for name,bound in (('physical_available',256*2**20),('commit_headroom',2**30),('disk_available',2**30)):
            value=dict(MEM);value[name]=bound-1
            with self.subTest(name=name):self.assertIsNotNone(c.resource_failure(value,1))
        for bad in (-1,float('nan'),float('inf')):
            with self.assertRaises(AssertionError):c.resource_failure(MEM,bad)

    def test_report_excludes_gate_and_missing_closure_cannot_be_cured(self):
        report,complete=report_fixture('a'*64,'b'*64,'c'*64,'d'*64,5,7)
        self.assertTrue(c.terminal(report,complete,'a'*64,'b'*64,'c'*64,'d'*64,5,7))
        for key in ('outer_performance_computed_or_published','evaluation_or_gate_run'):
            changed=copy.deepcopy(report);changed[key]=True
            with self.assertRaises(AssertionError):c.terminal(changed,complete,'a'*64,'b'*64,'c'*64,'d'*64,5,7)
        changed=copy.deepcopy(report);changed['forensic_numeric_diagnostics']['old_campaign_completion_missing']=False
        with self.assertRaises(AssertionError):c.terminal(changed,complete,'a'*64,'b'*64,'c'*64,'d'*64,5,7)

    def test_report_rejects_wrong_current_owner_and_corrupt_numeric_diagnostic(self):
        report,complete=report_fixture('a'*64,'b'*64,'c'*64,'d'*64,5,7)
        for mutate in ('owner','score','missing'):
            changed=copy.deepcopy(report)
            if mutate=='owner':changed['runtime_before_inputs']['current_pid']=8
            if mutate=='score':next(iter(changed['forensic_numeric_diagnostics']['checkpoint_numeric_diagnostics'].values()))['exact_canonical_scores_equal']=False
            if mutate=='missing':changed['checkpoint_current_runtime_proof_sha256'].pop(next(iter(changed['checkpoint_current_runtime_proof_sha256'])))
            with self.subTest(mutate=mutate),self.assertRaises(AssertionError):c.terminal(changed,complete,'a'*64,'b'*64,'c'*64,'d'*64,5,7)

    def test_counters_fail_closed(self):
        s.counts_ok(PROC,JOB)
        for key,bad in (('peak_private_commit',c.PRIVATE_CAP+1),('peak_working_set',c.RESIDENT_CEILING+1)):
            changed=dict(PROC);changed[key]=bad
            with self.assertRaises(AssertionError):s.counts_ok(changed,JOB)
        changed=dict(JOB);changed['active_processes']=3
        with self.assertRaises(AssertionError):s.counts_ok(PROC,changed)

    def test_explicit_flag_required_before_any_source_or_native_call(self):
        with patch.object(c,'sources',side_effect=RuntimeError('not reached')):
            with self.assertRaises(AssertionError):s.run('a'*64)

    def test_source_mode_requires_no_site_no_cache_and_one_thread(self):
        with patch.object(c.sys,'pycache_prefix','wrong'),self.assertRaises(AssertionError):c.source_mode()

    def test_actual_owner_boundary_uses_current_pid_job_and_immutable_initial_bytes(self):
        with tempfile.TemporaryDirectory() as temporary,ExitStack() as stack:
            out=Path(temporary)
            for name,filename in (('OUT',None),('BIRTH','birth.json'),('CHILD_IDENTITY','identity.json'),('CHILD_OWNER','owner.json')):
                stack.enter_context(patch.object(c,name,out if filename is None else out/filename))
            generation='a'*64
            birth=c.save_new(c.BIRTH,{'status':'NEW_EXCLUSIVE_READONLY_FORENSIC_ATTEMPT_NOT_FIT_RETRY',
                'stage':c.STAGE,'generation_manifest_sha256':generation,'parent_pid':17,
                'total_started_monotonic':100.,'automatic_retry':False,'input_pin_map_sha256':c.digest(c.canonical({}))})
            identity=c.save_new(c.CHILD_IDENTITY,{'parent_pid':17,'birth_sha256':birth,'generation_manifest_sha256':generation,
                'prospective_job_limits':c.JOB_LIMITS,'resident_request':c.RESIDENT_REQUEST})
            original={'worker_pid':23,'parent_pid':17,'birth_sha256':birth,'generation_manifest_sha256':generation,
                'owned_child_identity_sha256':identity,'exact_parent_owned_Job_membership_checked_before_resume':True,
                'job_limits':c.JOB_LIMITS,'resident_cap':CAP}
            c.save_new(c.CHILD_OWNER,original)
            def current_job(process,job,answer):answer._obj.value=1;return True
            kernel=SimpleNamespace(GetCurrentProcess=unittest.mock.Mock(return_value=1))
            api=SimpleNamespace(kernel32=kernel,IsProcessInJob=current_job)
            for obj,name,value in ((c,'source_mode',lambda:None),(c,'bind_read_set',lambda _:{}),
                (r.os,'getpid',lambda:23),(r.os,'getppid',lambda:17),(r.time,'monotonic',lambda:102.),
                (r.headless.original,'_api',lambda:api),(r.headless,'memory',lambda:MEM),
                (r.headless,'process_memory',lambda _:PROC),
                (r.working_set,'native',lambda:SimpleNamespace(query=lambda _:CAP['after']))):
                stack.enter_context(patch.object(obj,name,value))
            owner=r.CurrentOwner(17,generation,birth,identity,100.,{})
            self.assertEqual(owner.descriptor()['current_pid'],23)
            self.assertFalse(owner.descriptor()['actual_old_campaign_owner_claimed'])
            changed=dict(original);changed['worker_pid']=24
            c.CHILD_OWNER.write_bytes(c.canonical(changed)+b'\n')
            with self.assertRaises(AssertionError):owner.fresh()

    def test_runtime_keeps_objects_and_duplicate_proofs_cannot_resume(self):
        from src.generalization_cdrive_numeric_profile_20261025 import runtime as original
        owner=r.CurrentOwner.__new__(r.CurrentOwner)
        owner.fresh=lambda:None;owner.descriptor=lambda:{'invented_owner_boundary':True}
        objects=[SimpleNamespace() for _ in range(9)]
        with tempfile.TemporaryDirectory() as temporary,patch.object(c,'OUT',Path(temporary)), \
             patch.object(original,'bootstrap',return_value=tuple(objects)),patch.object(original,'actual_proof',return_value={'invented':True}):
            runtime=r.Runtime(owner,{})
            runtime.proof('invented_key')
            with self.assertRaisesRegex(AssertionError,'duplicate'):runtime.proof('invented_key')
            runtime.np=object()
            with self.assertRaisesRegex(AssertionError,'objects changed'):runtime.proof('other_key')

    def _parent(self,mode):
        generation='a'*64;events=[];clock=[0.];state={}
        with tempfile.TemporaryDirectory() as temporary,ExitStack() as stack:
            out=Path(temporary)
            for name,filename in (('OUT',None),('BIRTH','birth.json'),('CHILD_IDENTITY','identity.json'),('CHILD_OWNER','owner.json'),
                ('REPORT','report.json'),('COMPLETION','completion.json'),('SUPERVISOR','supervisor.json'),('JOURNAL','parent.jsonl'),('FAULT_LOG','fault.log')):
                stack.enter_context(patch.object(c,name,out if filename is None else out/filename))
            class Child:
                pid=51;process_handle=1
                def resume(self):
                    events.append('resume');assert c.CHILD_OWNER.exists()
                    birth,identity,owner=(c.sha(path) for path in (c.BIRTH,c.CHILD_IDENTITY,c.CHILD_OWNER))
                    report,complete=report_fixture(generation,birth,identity,owner,s.os.getpid(),self.pid)
                    for key in report['checkpoint_current_runtime_proof_sha256']:
                        report['checkpoint_current_runtime_proof_sha256'][key]=c.save_new(out/('runtime_'+key+'.json'),{'invented_only':True})
                    complete['report_sha256']=c.digest(c.canonical(report)+b'\n')
                    c.save_new(c.REPORT,report);c.save_new(c.COMPLETION,complete)
                def exit_code(self):return 0
                def close(self):events.append('childclose')
            class JobDouble:
                def __enter__(self):events.append('job');return self
                def __exit__(self,*args):events.append('jobclose')
                def limits(self):return dict(c.JOB_LIMITS)
                def spawn(self,command,cwd):
                    events.append('spawn');state['command']=command;return Child()
                def _membership(self,handle):events.append('membership')
                def accounting(self):return dict(JOB)
                def terminate(self):events.append('terminate')
            original_write=c.write
            def write(stream,value):
                if mode=='telemetry' and value['status']=='MANDATORY_PARENT_TELEMETRY_COMPLETE':raise OSError('invented fsync failure')
                original_write(stream,value)
            def rehash(*args,**kwargs):
                events.append('finalhash')
                if mode=='late':clock[0]=1801.
            for obj,name,value in ((c,'sources',lambda *args,**kwargs:{'readonly_input_pins':{}}),
                (c,'bind_read_set',lambda _:{}),(c,'old_absences',lambda:[]),(c,'rehash_read_set',rehash),(c,'write',write),
                (s.headless,'Job',JobDouble),(s.headless,'memory',lambda:dict(MEM)),
                (s.headless,'native_origins',lambda:{}),(s.headless,'process_memory',lambda _:dict(PROC)),
                (s.resident,'apply',lambda *args:CAP),(s.time,'monotonic',lambda:clock[0])):
                stack.enter_context(patch.object(obj,name,value))
            try:s.run(generation,root_start_readonly=True)
            except (AssertionError,OSError):
                if mode=='success':raise
            else:self.assertEqual(mode,'success')
            if mode=='telemetry':self.assertFalse(c.SUPERVISOR.exists())
            else:
                saved=c.decode(c.SUPERVISOR.read_bytes())
                self.assertEqual(saved['status'],c.PARENT_PASS if mode=='success' else 'FAILED_NEW_FORENSIC_JOB_NO_RETRY')
            self.assertLess(events.index('membership'),events.index('resume'))
            self.assertIn('childclose',events);self.assertIn('jobclose',events)
            self.assertNotIn('PLACEHOLDER',' '.join(state['command']))
        return events

    def test_mock_parent_binds_real_pid_record_before_resume_and_closes(self):self._parent('success')
    def test_delayed_terminal_cannot_publish_pass(self):self._parent('late')
    def test_mandatory_telemetry_failure_cannot_publish_supervisor_pass(self):self._parent('telemetry')

    def test_production_modules_never_call_optimizer_or_formal_gate(self):
        forbidden={'minimize','fit_prepared','run_campaign','evaluate','verify_campaign'}
        for name in ('common.py','runtime_or_owner.py','worker.py','supervise.py'):
            tree=ast.parse((c.SRC/name).read_text(encoding='utf8'))
            called={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id
                for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
            self.assertFalse(called & forbidden,name)


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    own=('__init__.py','spec.py','common.py','runtime_or_owner.py','worker.py','supervise.py','prepare.py','tests_controller.py')
    receipt={'status':'PASS_INVENTED_READONLY_FORENSIC_CONTROLLER_NO_ACTUAL_JOBS_OR_DATA',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'source_sha256':{(c.SRC/name).relative_to(c.ROOT).as_posix():c.sha(c.SRC/name) for name in own},
        'actual_data_reads':0,'actual_native_jobs':0,'actual_numerical_imports':0}
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    c.save_new(c.OUT/'controller_tests_receipt_reviewed.json',receipt)
    print('INVENTED_CONTROLLER_ONLY',result.testsRun,c.sha(c.OUT/'controller_tests_receipt_reviewed.json'),flush=True)


if __name__=='__main__':run()
