"""Invented runtime state/owner checks; no native import, job or probe."""
from contextlib import ExitStack
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import provider as p,contracts as c
from .spec import *


def binding():
    return {'request_relative_path':REQUEST,'request_sha256':'a'*64,'provider_preparation_manifest_sha256':'b'*64,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_ADMISSION_SHA}


def evidence():return {'parent_pid':os.getppid(),'birth_sha256':'c'*64,'run_admission_sha256':'d'*64}


def request():
    return {'namespace':'generalization_knowncell_replay_v3_execution_20261025','status':REQUEST_STATUS,'stage':'replay',
        'invocation':'independent_checkpoint_and_source_selection_replay','numerical_threads':1,'runtime_import_authorized':True,'array_reload_authorized':True,
        'saved_label_read_authorized':True,'pool_preparation_authorized':True,'checkpoint_refresh_keys':[],'optimizer_units':0,'CORE_read_authorized':False,'model_fitting_authorized':False,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'provider_preparation_manifest_sha256':'b'*64,'provider_binding':{'source_path':SOURCE,'source_sha256':'e'*64,
            'module':MODULE,'qualname':'provide','reviewed_deferred_only':True},
        'approved_policy_manifest_sha256':'a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9',
        'authorization_sha256':'b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3',
        **{key:'f'*64 for key in ('generation_manifest_sha256','static_root_binding_sha256',
            'controller_source_admission_sha256','stable_admitted_runtime_binding_sha256','actual_prefit_sha256','projection_root_admission_sha256')}}


class Cases(unittest.TestCase):
    def setUp(self):p._OWNED=None;p._FAILED=False
    def tearDown(self):p._OWNED=None;p._FAILED=False
    def fake(self):
        stack=ExitStack();events=[]
        np=SimpleNamespace(__file__=str(ROOT/'invented_numpy.py'),__version__='1.26.4')
        pd=SimpleNamespace(__file__=str(ROOT/'invented_pandas.py'),__version__='2.2.3')
        inventory={'files':{'numpy/__init__.py':'1'*64,'pandas/__init__.py':'2'*64}}
        values=(np,pd,SimpleNamespace(__version__='1.14.1'),lambda:None,lambda:None,object(),{},inventory,{})
        functions=SimpleNamespace(actual_proof=lambda *args:(events.append('proof') or {'invented_only_test':True}))
        owner={'current_pid':os.getpid(),'parent_pid':os.getppid(),'birth_sha256':'c'*64,'in_owned_job':True}
        stack.enter_context(patch.object(p.guard,'fresh_gate',side_effect=lambda:events.append('gate')))
        stack.enter_context(patch.object(p.original,'source_mode',side_effect=lambda:events.append('source')))
        stack.enter_context(patch.object(p,'admit',return_value={'manifest':{},'request':request(),'origin':{}}))
        verify=stack.enter_context(patch.object(p,'actual_owner',return_value=owner))
        stack.enter_context(patch.object(p,'cached_source_anchors',return_value=True))
        runtime=stack.enter_context(patch.object(p.original,'runtime_module',return_value=functions))
        bootstrap=stack.enter_context(patch.object(p.original,'bootstrap_runtime',return_value=values))
        stack.enter_context(patch.object(p.original,'software_objects',return_value=(np,pd,values[3],values[4])))
        stack.enter_context(patch.object(c,'fresh_proof_contract',side_effect=lambda *args:events.append('verify')))
        return stack,events,np,pd,verify,runtime,bootstrap

    def test_acyclic_request_excludes_live_hashes_and_forbids_CORE_and_fit(self):
        c.binding_contract(binding());c.request_contract(request(),binding(),'e'*64)
        for field,value in (('caller_birth_sha256','0'*64),('current_stage_origin_proof_sha256','0'*64),('run_admission_sha256','0'*64),
                            ('CORE_read_authorized',True),('model_fitting_authorized',True)):
            item=request();item[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):c.request_contract(item,binding(),'e'*64)

    def test_same_owned_objects_one_bootstrap_two_actual_proofs_each_phase(self):
        stack,events,np,pd,owner,runtime,bootstrap=self.fake()
        with stack:
            before=p.provide(binding(),evidence(),phase='before_replay',root_start=True)
            after=p.provide(binding(),evidence(),phase='after_replay',root_start=True)
        self.assertIs(before['np'],after['np']);self.assertIs(before['pd'],after['pd'])
        self.assertEqual(runtime.call_count,1);self.assertEqual(bootstrap.call_count,1);self.assertEqual(owner.call_count,4)
        self.assertEqual(events.count('proof'),4)
        for index,event in enumerate(events):
            if event=='proof':self.assertEqual(events[index-1],'gate')
        proof=before['fresh_origin_proof']
        self.assertEqual(proof['phase'],'before_supplied_input_bridge')
        self.assertEqual(after['fresh_origin_proof']['phase'],'after_independent_replay')
        self.assertEqual(c.digest(c.canonical(proof)),before['fresh_origin_proof_sha256'])
        self.assertEqual(proof['caller_birth_sha256'],'c'*64)

    def test_low_resources_before_admit_owner_bootstrap_and_process_poisoned(self):
        with patch.object(p.guard,'fresh_gate',side_effect=AssertionError('low reserve')),patch.object(p,'admit') as admit,\
             patch.object(p,'actual_owner') as owner,patch.object(p.original,'bootstrap_runtime') as bootstrap:
            with self.assertRaisesRegex(AssertionError,'low reserve'):p.provide(binding(),evidence(),phase='before_replay',root_start=True)
            admit.assert_not_called();owner.assert_not_called();bootstrap.assert_not_called()
        self.assertTrue(p._FAILED)

    def test_owner_failure_precedes_scientific_bootstrap(self):
        stack,*_=self.fake()
        with stack,patch.object(p,'actual_owner',side_effect=AssertionError('not actual owned child')),\
             patch.object(p.original,'bootstrap_runtime') as bootstrap:
            with self.assertRaisesRegex(AssertionError,'owned child'):p.provide(binding(),evidence(),phase='before_replay',root_start=True)
            bootstrap.assert_not_called()

    def test_changed_owner_request_duplicate_and_wrong_phase_reject(self):
        for kind in ('owner','request','duplicate','phase'):
            self.setUp();stack,*_=self.fake()
            with stack:
                p.provide(binding(),evidence(),phase='before_replay',root_start=True)
                b,e,phase=binding(),evidence(),'after_replay'
                if kind=='owner':e['birth_sha256']='0'*64
                if kind=='request':b['request_sha256']='0'*64
                if kind=='phase':phase='after_labels'
                if kind=='duplicate':p.provide(b,e,phase='after_replay',root_start=True)
                with self.subTest(kind=kind),self.assertRaises(AssertionError):p.provide(b,e,phase=phase,root_start=True)

    def test_changed_native_proof_poisoned_and_root_start_required(self):
        stack,*_=self.fake()
        with stack,patch.object(c,'fresh_proof_contract',side_effect=AssertionError('native changed')):
            with self.assertRaisesRegex(AssertionError,'native changed'):p.provide(binding(),evidence(),phase='before_replay',root_start=True)
        self.assertTrue(p._FAILED);self.setUp()
        with patch.object(p.guard,'fresh_gate') as gate:
            with self.assertRaises(AssertionError):p.provide(binding(),evidence(),phase='before_replay')
            gate.assert_not_called()


def run():
    from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    def clean():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    saved.save_new(ROOT/'results'/NS/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_INDEPENDENT_REPLAY_RUNTIME_NOT_ACTUAL_PROVIDER',
        'tests':result.testsRun,'sources':{path.relative_to(ROOT).as_posix():saved.sha(path.read_bytes()) for path in sources},
        'actual_runtime_invocations':0,'actual_resource_probes':0,'project_payload_reads':0,'optimizer_calls':0,
        'scientific_imports':False,'actual_owner_and_proofs_in_tests_are_private_mocks':True})


if __name__=='__main__':run()
