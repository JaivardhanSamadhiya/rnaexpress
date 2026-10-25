"""Invented ordered-runtime and immutable-anchor tests; no scientific imports."""
from contextlib import ExitStack
import copy
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
    return {'namespace':'generalization_knowncell_fit_roomy_execution_20261025','status':REQUEST_STATUS,'stage':'fit',
        'invocation':'fixed_63_checkpoint_84_optimizer_unit_fit','numerical_threads':1,
        'runtime_import_authorized':True,'array_reload_authorized':True,'saved_label_read_authorized':True,
        'pool_preparation_authorized':True,'model_fitting_authorized':True,'CORE_read_authorized':False,
        'checkpoint_refresh_keys':list(CHECKPOINT_KEYS),'optimizer_units':84,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'provider_preparation_manifest_sha256':'b'*64,
        'provider_binding':{'source_path':SOURCE,'source_sha256':'e'*64,'module':MODULE,'qualname':'provide','reviewed_deferred_only':True},
        'approved_policy_manifest_sha256':'a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9',
        'authorization_sha256':'b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3',
        **{key:'f'*64 for key in ('generation_manifest_sha256','static_root_binding_sha256',
            'controller_source_admission_sha256','stable_admitted_runtime_binding_sha256',
            'actual_prefit_sha256','projection_root_admission_sha256')}}


class Cases(unittest.TestCase):
    def setUp(self):p._OWNED=None;p._FAILED=False
    def tearDown(self):p._OWNED=None;p._FAILED=False

    def fake(self):
        stack=ExitStack();events=[]
        np=SimpleNamespace(__file__=str(ROOT/'invented_numpy.py'),__version__='1.26.4')
        pd=SimpleNamespace(__file__=str(ROOT/'invented_pandas.py'),__version__='2.2.3')
        inventory={'files':{'numpy/__init__.py':'1'*64,'pandas/__init__.py':'2'*64}}
        values=(np,pd,SimpleNamespace(__version__='1.14.1'),object(),object(),object(),{},inventory,{})
        functions=SimpleNamespace(actual_proof=lambda *args:(events.append('proof') or {'invented_test_only':True}))
        owner={'current_pid':os.getpid(),'parent_pid':os.getppid(),'birth_sha256':'c'*64,'in_owned_job':True}
        admitted={'manifest':{},'request':request(),'origin':{},'software_status':{}}
        stack.enter_context(patch.object(p.guard,'fresh_gate',side_effect=lambda:events.append('gate')))
        stack.enter_context(patch.object(p.original,'source_mode'))
        admit=stack.enter_context(patch.object(p,'admit',side_effect=lambda *_:copy.deepcopy(admitted)))
        verify=stack.enter_context(patch.object(p,'actual_owner',return_value=owner))
        cache=stack.enter_context(patch.object(p,'cached_source_anchors',return_value=True))
        stack.enter_context(patch.object(p.original,'runtime_module',return_value=functions))
        bootstrap=stack.enter_context(patch.object(p.original,'bootstrap_runtime',return_value=values))
        stack.enter_context(patch.object(p.original,'software_objects',return_value=(np,pd,values[3],values[4])))
        stack.enter_context(patch.object(c,'fresh_proof_contract'))
        return stack,events,values,admit,verify,cache,bootstrap

    def test_request_rejects_future_hashes_CORE_and_changed_checkpoint_roster(self):
        c.request_contract(request(),binding(),'e'*64)
        for field,value in [('caller_birth_sha256','0'*64),('run_admission_sha256','0'*64),
                ('current_stage_origin_proof_sha256','0'*64),('CORE_read_authorized',True),
                ('checkpoint_refresh_keys',list(reversed(CHECKPOINT_KEYS))),('optimizer_units',83)]:
            item=request();item[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):c.request_contract(item,binding(),'e'*64)

    def test_exact63_order_single_bootstrap_and_full_admission_only_before_after(self):
        stack,events,values,admit,owner,cache,bootstrap=self.fake()
        with stack:
            before=p.provide(binding(),evidence(),phase='before_fit',root_start=True)
            for index,key in enumerate(CHECKPOINT_KEYS,1):
                result=p.provide(binding(),evidence(),phase='checkpoint',task_key=key,root_start=True)
                self.assertEqual(result['fresh_origin_proof']['checkpoint_refresh_count'],index)
                self.assertIs(result['np'],before['np']);self.assertIs(result['minimize'],values[3])
                self.assertFalse(result['fresh_origin_proof']['full_committed_evidence_admission_this_call'])
            after=p.provide(binding(),evidence(),phase='after_fit',root_start=True)
        self.assertIs(before['np'],after['np']);self.assertIs(before['pd'],after['pd'])
        self.assertEqual(admit.call_count,2);self.assertEqual(bootstrap.call_count,1)
        self.assertEqual(owner.call_count,130);self.assertEqual(cache.call_count,130)
        self.assertEqual(events.count('proof'),130)
        for index,event in enumerate(events):
            if event=='proof':self.assertEqual(events[index-1],'gate')
        self.assertEqual(after['fresh_origin_proof']['checkpoint_refresh_count'],63)
        self.assertEqual(c.digest(c.canonical(after['fresh_origin_proof'])),after['fresh_origin_proof_sha256'])

    def test_skip_reorder_duplicate_or_after_without63_poison(self):
        for kind in ('skip','reorder','duplicate','early_after'):
            self.setUp();stack,*_=self.fake()
            with stack:
                p.provide(binding(),evidence(),phase='before_fit',root_start=True)
                phase,key='checkpoint',CHECKPOINT_KEYS[1]
                if kind=='duplicate':
                    p.provide(binding(),evidence(),phase='checkpoint',task_key=CHECKPOINT_KEYS[0],root_start=True)
                    key=CHECKPOINT_KEYS[0]
                if kind=='early_after':phase,key='after_fit',None
                with self.subTest(kind=kind),self.assertRaises(AssertionError):
                    p.provide(binding(),evidence(),phase=phase,task_key=key,root_start=True)
                self.assertTrue(p._FAILED)

    def test_low_resources_precedes_admission_and_bootstrap(self):
        with patch.object(p.guard,'fresh_gate',side_effect=AssertionError('low reserve')),patch.object(p,'admit') as admit,\
                patch.object(p.original,'bootstrap_runtime') as bootstrap:
            with self.assertRaisesRegex(AssertionError,'low reserve'):p.provide(binding(),evidence(),phase='before_fit',root_start=True)
            admit.assert_not_called();bootstrap.assert_not_called()
        self.assertTrue(p._FAILED)

    def test_actual_owner_or_native_failure_prevents_success(self):
        for kind in ('owner','native'):
            self.setUp();stack,*_=self.fake()
            with stack:
                target=p if kind=='owner' else c
                attr='actual_owner' if kind=='owner' else 'fresh_proof_contract'
                with patch.object(target,attr,side_effect=AssertionError('changed '+kind)):
                    with self.assertRaisesRegex(AssertionError,kind):p.provide(binding(),evidence(),phase='before_fit',root_start=True)
                self.assertTrue(p._FAILED)

    def test_changed_binding_owner_or_cached_evidence_rejected(self):
        for kind in ('binding','owner','cache'):
            self.setUp();stack,*_=self.fake()
            with stack:
                p.provide(binding(),evidence(),phase='before_fit',root_start=True)
                b,e=binding(),evidence()
                if kind=='binding':b['request_sha256']='0'*64
                if kind=='owner':e['birth_sha256']='0'*64
                if kind=='cache':p._OWNED.admitted['request']['optimizer_units']=83
                with self.subTest(kind=kind),self.assertRaises(AssertionError):
                    p.provide(b,e,phase='checkpoint',task_key=CHECKPOINT_KEYS[0],root_start=True)

    def test_cached_anchors_require_every_static_byte_in_fresh_generation(self):
        b=binding();admitted={'manifest':{'files':{'src/invented.py':'1'*64}},'request':request(),
            'software_status':{'verified_files':{'supervisor_receipt.json':'2'*64}}}
        pins={'src/invented.py':'1'*64,PREPARATION:'b'*64,SOFTWARE_STATUS:SOFTWARE_STATUS_SHA,
            PANDAS_ADMISSION:PANDAS_ADMISSION_SHA,PROFILE_ORIGIN:PROFILE_ORIGIN_SHA,PROFILE_MANIFEST:PROFILE_MANIFEST_SHA,
            PROFILE_OUT+'supervisor_receipt.json':'2'*64}
        fake=SimpleNamespace(verify_sources=lambda *_:{'files':pins},read_run=lambda *args,**kw:{'input_pins':{REQUEST:'a'*64}})
        with patch.object(p.importlib,'import_module',return_value=fake):
            self.assertTrue(p.cached_source_anchors(admitted,b,evidence()))
            pins['src/invented.py']='0'*64
            with self.assertRaises(AssertionError):p.cached_source_anchors(admitted,b,evidence())

    def test_root_start_required_before_any_probe(self):
        with patch.object(p.guard,'fresh_gate') as gate:
            with self.assertRaises(AssertionError):p.provide(binding(),evidence(),phase='before_fit')
            gate.assert_not_called()


def run():
    from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    clean=lambda:not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    saved.save_new(ROOT/'results'/NS/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_FIXED_FIT_RUNTIME_NOT_ACTUAL_PROVIDER',
        'tests':result.testsRun,'sources':{path.relative_to(ROOT).as_posix():saved.sha(path.read_bytes()) for path in sources},
        'actual_runtime_invocations':0,'actual_resource_probes':0,'project_payload_reads':0,'optimizer_calls':0,
        'scientific_imports':False,'actual_owner_and_proofs_in_tests_are_private_mocks':True})


if __name__=='__main__':run()
