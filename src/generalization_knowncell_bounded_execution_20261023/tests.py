"""Invented resource/lifecycle checks; no jobs, probes or payload readers."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from . import common as c
from . import supervise


def snapshot(physical=1024 * 2**20, commit=4 * 2**30, disk=2 * 2**30):
    return {'physical_available': physical, 'commit_headroom': commit, 'disk_available': disk}


class FakeChild:
    process_handle = object()
    def __init__(self, exits): self.exits = iter(exits)
    def exit_code(self): return next(self.exits)


class FakeJob:
    def __init__(self): self.killed = False
    def terminate(self): self.killed = True
    def accounting(self):
        return {'active_processes': 1, 'peak_process_memory_used': 20, 'peak_job_memory_used': 40}


class Checks(unittest.TestCase):
    def test_policy_is_exact(self):
        policy = c.resource_policy()
        self.assertEqual((policy['startup_physical_available'], policy['active_physical_available']), (512*2**20, 256*2**20))
        self.assertEqual((policy['process_cap'], policy['job_cap']), (768*2**20, 896*2**20))
        self.assertEqual(policy['numerical_threads'], 1)
        self.assertFalse(policy['spending_authorized'])

    def test_startup_boundary(self):
        self.assertIsNone(c.resource_failure(snapshot(512*2**20, c.JOB_CAP+2**30, 2**30), 0, startup=True))
        self.assertIsNotNone(c.resource_failure(snapshot(512*2**20-1), 0, startup=True))

    def test_live_boundary(self):
        self.assertIsNone(c.resource_failure(snapshot(256*2**20, 2**30, 2**30), 1800))
        self.assertIsNotNone(c.resource_failure(snapshot(256*2**20-1), 0))

    def test_commit_boundaries(self):
        self.assertIsNotNone(c.resource_failure(snapshot(commit=c.JOB_CAP+2**30-1), 0, startup=True))
        self.assertIsNotNone(c.resource_failure(snapshot(commit=2**30-1), 0))

    def test_disk_and_deadline(self):
        self.assertIsNotNone(c.resource_failure(snapshot(disk=2**30-1), 0))
        self.assertIsNotNone(c.resource_failure(snapshot(), 1800.0001))

    def test_invalid_snapshots(self):
        for key in snapshot():
            value = snapshot(); value[key] = True
            with self.assertRaises(AssertionError): c.resource_failure(value, 0)
        with self.assertRaises(AssertionError): c.resource_failure(snapshot(), float('nan'))

    def test_duplicate_json_rejected(self):
        with self.assertRaises(AssertionError): c.decode(b'{"x":1,"x":2}')
        with self.assertRaises(AssertionError): c.decode(b'{"x":NaN}')

    def test_relative_path_rejects_escape(self):
        for name in ('../x', '/x', 'C:/x', 'src\\x.py'):
            with self.assertRaises(AssertionError): c.relative(name)

    def valid_approval(self):
        return {'status':'EXACT_HUMAN_KNOWNCELL_RESOURCE_APPROVAL_RECORDED',
            'execution_manifest_sha256':'a'*64,'approved_stages':list(c.STAGES),
            'resource_policy':c.resource_policy(),'spending_authorized':False,
            'scientific_protocol_changes_authorized':False,'automatic_retry_authorized':False,
            'scheduled_tasks_authorized':False,'question':'INVENTED UNIT TEST ONLY',
            'answer':'Approve this exact known-cell resource calibration','question_item_id':'INVENTED'}

    def test_approval_contract_exact(self):
        value = self.valid_approval()
        self.assertTrue(c.approval_contract(value, 'a'*64))
        for field, replacement in (('execution_manifest_sha256','b'*64),('approved_stages',['metadata']),
                ('answer','Approve PRELib'),('spending_authorized',True),('scientific_protocol_changes_authorized',True)):
            copy = dict(value); copy[field] = replacement
            with self.assertRaises(AssertionError): c.approval_contract(copy, 'a'*64)

    def test_absent_approval_cannot_admit(self):
        with patch.object(c, 'verify_sources', return_value={}), patch.object(c, 'committed'), \
             patch.object(Path, 'read_bytes', side_effect=[b'{}', FileNotFoundError('invented absent approval')]):
            with self.assertRaises(FileNotFoundError): c.admit_authorization(c.sha(b'{}'))

    def test_changed_manifest_before_git_rejected(self):
        with patch.object(c, 'committed') as committed, patch.object(Path, 'read_bytes', return_value=b'{}'):
            with self.assertRaises(AssertionError): c.admit_authorization('a'*64)
            committed.assert_not_called()

    def observe(self, states=None, exits=None, process=None, clock=None, memory=None):
        job = FakeJob(); child = FakeChild([0] if exits is None else exits)
        states = [snapshot()] if states is None else states
        sequence = iter(states + [states[-1]])
        process = (lambda handle: {'peak_working_set':30,'peak_private_commit':40}) if process is None else process
        times = iter([0, 0.01, 0.02] if clock is None else clock)
        result = supervise.observe(job, child, (lambda:next(sequence)) if memory is None else memory, process,
            lambda:next(times), lambda value:None)
        return result, job

    def test_monitor_fast_exit_final_peak(self):
        result, job = self.observe()
        self.assertIsNone(result['failure']);self.assertEqual(result['exit_code'],0)
        self.assertIn('final_process_handle_peak_sample',result);self.assertFalse(job.killed)

    def test_monitor_physical_stop(self):
        result, job = self.observe(states=[snapshot(255*2**20)])
        self.assertIn('256 MiB',result['failure']);self.assertTrue(job.killed)

    def test_monitor_commit_and_disk_stop(self):
        for state in (snapshot(commit=2**30-1),snapshot(disk=2**30-1)):
            result, job = self.observe(states=[state]);self.assertTrue(job.killed)

    def test_monitor_deadline_stop(self):
        result, job = self.observe(clock=[0,1801,1801.01]);self.assertTrue(job.killed)
        self.assertIn('30-minute',result['failure'])

    def test_monitor_probe_failure_kills(self):
        def reject(): raise AssertionError('Invented unavailable probe')
        result, job = self.observe(exits=[None], memory=reject)
        self.assertTrue(job.killed);self.assertIn('unavailable probe',result['failure'])

    def test_monitor_final_peak_failure_kills(self):
        calls = iter([{'peak_working_set':30,'peak_private_commit':40}, {'peak_working_set':0,'peak_private_commit':0}])
        result, job = self.observe(process=lambda handle:next(calls))
        self.assertTrue(job.killed);self.assertIn('Final lifetime peak',result['failure'])

    def test_monitor_active_limit_failure_kills(self):
        with patch.object(FakeJob,'accounting',return_value={'active_processes':3,'peak_process_memory_used':20,'peak_job_memory_used':40}):
            result, job=self.observe()
        self.assertTrue(job.killed)

    def test_monitor_terminal_job_cap_failure_kills(self):
        normal={'active_processes':1,'peak_process_memory_used':20,'peak_job_memory_used':40}
        terminal=dict(normal,peak_job_memory_used=c.JOB_CAP+1)
        with patch.object(FakeJob,'accounting',side_effect=[normal,terminal]):
            result, job=self.observe()
        self.assertTrue(job.killed);self.assertIsNotNone(result['failure'])

    def test_monitor_terminal_reserve_failure_kills(self):
        result, job=self.observe(states=[snapshot(),snapshot(255*2**20)])
        self.assertTrue(job.killed);self.assertIn('256 MiB',result['failure'])

    def test_other_stage_rejected_before_admission(self):
        with patch.object(c,'admit_authorization',side_effect=AssertionError('MUST NOT REACH')) as admit:
            with self.assertRaises(AssertionError): supervise.run('fit',root_start=True)
            admit.assert_not_called()

    def test_owner_parent_mismatch_before_native(self):
        with patch.object(c,'source_mode',return_value={}),patch.object(c.os,'getppid',return_value=10):
            with self.assertRaises(AssertionError): c.verify_owner('metadata','a'*64,{'parent_pid':11,'birth_sha256':'b'*64})

    def test_nonmetadata_requires_extra_source_admission(self):
        with patch.object(c,'source_mode',return_value={}):
            with self.assertRaises(AssertionError): c.verify_owner('fit','a'*64,{'parent_pid':10,'birth_sha256':'b'*64})
        with patch.object(Path,'read_bytes',side_effect=FileNotFoundError('Invented missing fit controller admission')):
            with self.assertRaises(FileNotFoundError): c.verify_stage_admission('fit','a'*64,'b'*64)

    def test_changed_stage_admission_rejected_before_git(self):
        with patch.object(Path,'read_bytes',return_value=b'{}'),patch.object(c,'committed') as git:
            with self.assertRaises(AssertionError): c.verify_stage_admission('fit','a'*64,'b'*64)
            git.assert_not_called()

    def test_future_admission_declared_closure_and_parent_pins(self):
        with tempfile.TemporaryDirectory(prefix='invented_knowncell_stage_') as directory:
            root=Path(directory);output=root/'results'/c.NS;output.mkdir(parents=True)
            module='src.generalization_knowncell_invented.controller'
            source=module.replace('.','/')+'.py';review='reports/generalization_knowncell_invented/review.md'
            values={source:b'# invented source only\n',review:b'Invented review only\n','src/__init__.py':b'# invented parent\n'}
            for name,raw in values.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            packet={'status':'FROZEN_INDEPENDENTLY_REVIEWED_KNOWNCELL_STAGE_CONTROLLER','stage':'fit',
                'resource_execution_manifest_sha256':'a'*64,'scientific_protocol_settings_changed':False,
                'spending_authorized':False,'controller_module':module,'controller_source_sha256':c.sha(values[source]),
                'independent_source_review':review,'independent_source_review_sha256':c.sha(values[review]),
                'files':{name:c.sha(raw) for name,raw in values.items()}}
            path=output/'fit_controller_admission.json'
            def write():
                raw=c.canonical(packet);path.write_bytes(raw);return c.sha(raw)
            with patch.object(c,'ROOT',root),patch.object(c,'OUT',output),patch.object(c,'committed'):
                accepted=c.verify_stage_admission('fit','a'*64,write())
                self.assertTrue(accepted['declared_source_closure_verified'])
                self.assertFalse(accepted['scientific_input_and_FIT_admissions_verified_here'])
                packet['files'].pop('src/__init__.py')
                with self.assertRaisesRegex(AssertionError,'parent package'):c.verify_stage_admission('fit','a'*64,write())
                packet['files']['src/__init__.py']=c.sha(values['src/__init__.py'])
                (root/source).write_bytes(b'# changed invented source\n')
                with self.assertRaises(AssertionError):c.verify_stage_admission('fit','a'*64,write())

    def test_command_uses_source_mode(self):
        command = supervise.command('metadata','a'*64,'b'*64)
        self.assertEqual(command[1:4],['-S','-B','-X'])
        self.assertEqual(command[4],'pycache_prefix='+str(c.CACHE_PREFIX))
        with self.assertRaises(AssertionError): supervise.command('fit','a'*64,'b'*64)


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(stream.getvalue(),end='')
    assert result.wasSuccessful()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    c.save_new(c.OUT/'controller_tests_receipt.json',{
        'status':'PASS_INVENTED_CONTROLLER_CONTRACTS_NOT_NATIVE_OR_DATA_EXECUTION',
        'tests':result.testsRun,'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_workers':0,'native_resource_probes':0,'project_payloads':0,'model_fits':0})


if __name__=='__main__':run()
