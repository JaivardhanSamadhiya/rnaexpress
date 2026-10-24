"""Invented provider state tests; never bootstrap, probe or import science."""
from contextlib import ExitStack
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import provider as p,contracts as c
from .spec import *


def binding():
    return {'request_relative_path':REQUEST,'request_sha256':'a'*64,'provider_preparation_manifest_sha256':'b'*64,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_ADMISSION_SHA}


def request():
    return {'namespace':'generalization_knowncell_labels_execution_20261024','status':REQUEST_STATUS,
        'runtime_import_authorized':True,'label_access_authorized':True,'model_fitting_authorized':False,
        'numerical_threads':1,'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'provider_preparation_manifest_sha256':'b'*64,'provider_binding':{'source_path':SOURCE,'source_sha256':'c'*64,
            'module':MODULE,'qualname':'provide','reviewed_deferred_only':True},
        'resource_policy_manifest_sha256':'a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9',
        'authorization_sha256':'b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3',
        'invocation':'original_pandas_label_admission',**{key:'d'*64 for key in ('generation_manifest_sha256',
            'metadata_bundle_sha256','array_certificate_sha256','array_supervisor_sha256')}}


class Cases(unittest.TestCase):
    def setUp(self):p._OWNED=None;p._FAILED=False
    def tearDown(self):p._OWNED=None;p._FAILED=False

    def fake(self):
        stack=ExitStack();events=[]
        np=SimpleNamespace(__file__=str(ROOT/'invented_numpy.py'),__version__='1.26.4')
        pd=SimpleNamespace(__file__=str(ROOT/'invented_pandas.py'),__version__='2.2.3')
        inventory={'files':{'numpy/__init__.py':'1'*64,'pandas/__init__.py':'2'*64}}
        values=(np,pd,object(),lambda:None,lambda:None,object(),{},inventory,{})
        proof={'invented_origin_only':True}
        functions=SimpleNamespace(actual_proof=lambda *args:(events.append('proof') or dict(proof)))
        stack.enter_context(patch.object(p.guard,'fresh_gate',side_effect=lambda:events.append('gate')))
        stack.enter_context(patch.object(p.original,'source_mode',side_effect=lambda:events.append('source_mode')))
        stack.enter_context(patch.object(p,'admit',side_effect=lambda value:(events.append('admit') or {'origin':{},'manifest':{},'certificate':{}})))
        runtime=stack.enter_context(patch.object(p.original,'runtime_module',return_value=functions))
        bootstrap=stack.enter_context(patch.object(p.original,'bootstrap_runtime',return_value=values))
        stack.enter_context(patch.object(p.original,'software_objects',return_value=(np,pd,values[3],values[4])))
        stack.enter_context(patch.object(c,'fresh_proof_contract',side_effect=lambda *args:events.append('validate_proof')))
        return stack,events,np,pd,runtime,bootstrap

    def test_new_request_does_not_infer_or_reuse_array_authority(self):
        self.assertEqual(c.binding_contract(binding()),binding())
        self.assertTrue(c.request_contract(request(),binding(),'c'*64))
        invalid=request();invalid['label_access_authorized']=False
        with self.assertRaises(AssertionError):c.request_contract(invalid,binding(),'c'*64)
        invalid=binding();invalid['request_relative_path']='results/generalization_knowncell_array_admission_20261023/array_request_manifest.json'
        with self.assertRaises(AssertionError):c.binding_contract(invalid)

    def test_one_bootstrap_then_same_owned_objects_with_two_fresh_proofs_per_phase(self):
        stack,events,np,pd,runtime,bootstrap=self.fake()
        with stack:
            first=p.provide(binding(),phase='before_labels',root_start=True)
            second=p.provide(binding(),phase='after_labels',root_start=True)
        self.assertIs(first['np'],second['np']);self.assertIs(first['pd'],second['pd'])
        self.assertEqual(runtime.call_count,1);self.assertEqual(bootstrap.call_count,1)
        self.assertEqual(events.count('proof'),4)
        for index,event in enumerate(events):
            if event=='proof':self.assertEqual(events[index-1],'gate')
        self.assertEqual(first['actual_origin_receipt_sha256'],PROFILE_ORIGIN_SHA)
        self.assertEqual(c.digest(c.canonical(first['fresh_origin_proof'])),first['fresh_origin_proof_sha256'])
        self.assertTrue(first['fresh_origin_proof']['bootstrap_this_call'])
        self.assertFalse(second['fresh_origin_proof']['bootstrap_this_call'])

    def test_low_resources_fail_before_admission_bootstrap_and_poison_process(self):
        with patch.object(p.guard,'fresh_gate',side_effect=AssertionError('low actual RAM')),\
             patch.object(p,'admit') as admit,patch.object(p.original,'bootstrap_runtime') as bootstrap:
            with self.assertRaisesRegex(AssertionError,'low actual RAM'):p.provide(binding(),phase='before_labels',root_start=True)
            admit.assert_not_called();bootstrap.assert_not_called()
        with self.assertRaises(AssertionError):p.provide(binding(),phase='before_labels',root_start=True)

    def test_wrong_phase_request_change_and_duplicate_after_phase_reject(self):
        stack,*_=self.fake()
        with stack:
            with self.assertRaises(AssertionError):p.provide(binding(),phase='after_array',root_start=True)
        self.setUp();stack,*_=self.fake()
        with stack:
            p.provide(binding(),phase='before_labels',root_start=True)
            changed=binding();changed['request_sha256']='0'*64
            with self.assertRaises(AssertionError):p.provide(changed,phase='after_labels',root_start=True)
        self.setUp();stack,*_=self.fake()
        with stack:
            p.provide(binding(),phase='before_labels',root_start=True)
            p.provide(binding(),phase='after_labels',root_start=True)
            with self.assertRaises(AssertionError):p.provide(binding(),phase='after_labels',root_start=True)

    def test_failed_current_origin_proof_cannot_return_acceptance(self):
        stack,*_=self.fake()
        with stack,patch.object(c,'fresh_proof_contract',side_effect=AssertionError('native origin changed')):
            with self.assertRaisesRegex(AssertionError,'native origin'):p.provide(binding(),phase='before_labels',root_start=True)
        self.assertTrue(p._FAILED);self.assertIsNone(p._OWNED)

    def test_root_start_required_before_any_guard_or_software(self):
        with patch.object(p.guard,'fresh_gate') as gate:
            with self.assertRaises(AssertionError):p.provide(binding(),phase='before_labels')
            gate.assert_not_called()


def run():
    from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    def clean():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    saved.save_new(ROOT/'results'/NS/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_LABELS_RUNTIME_STATE_NOT_ACTUAL_PROVIDER',
        'tests':result.testsRun,'sources':{path.relative_to(ROOT).as_posix():saved.sha(path.read_bytes()) for path in sources},
        'actual_runtime_invocations':0,'actual_resource_probes':0,'project_payload_reads':0,'model_fits':0,
        'scientific_imports':False,'proofs_in_tests_are_mocked_not_actual_acceptance':True})


if __name__=='__main__':run()
