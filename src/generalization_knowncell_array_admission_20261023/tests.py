"""Invented bytes and mocked orchestration only; no actual resource/native calls."""
from contextlib import ExitStack
from datetime import datetime, timezone
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from . import admit as a
from .spec import *


def request():
    return {'status':REQUEST_STATUS,'namespace':NS,'label_access_authorized':False,
        'model_fitting_authorized':False,'runtime_import_authorized':True,
        'PUM_resource_exception_applies':False,'PRELib_resource_exception_applies':False,
        'numerical_threads':1,'data_pins':dict(DECLARED_PINS),'expected_row_ids_sha256':ROW_IDS_SHA,
        'array_contract_sha256':ARRAY_CONTRACT_SHA,'source_prefit_sha256':SOURCE_PREFIT_SHA,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':SOFTWARE_CERT_SHA,
        'metadata_bundle_sha256':'a'*64,'source_readiness_sha256':'b'*64,
        'provider_preparation_manifest_sha256':'c'*64,
        'provider_binding':{'source_path':'src/invented_provider.py','source_sha256':'d'*64,
            'module':'src.invented_provider','qualname':'provide','reviewed_deferred_only':True}}


def report(runtime_sha='e'*64,metadata_sha='f'*64):
    parity={'all_crosscell_matching_allele_bytes_equal':True,'crosscell_allele_groups':1,
            'tolerance_or_zero_filling_used':False}
    return {'status':'VALIDATED_SUPPLIED_ARRAY_BYTES_NOT_PROJECT_ADMISSION','rows':13781,'columns':102,
        'all_columns_finite':True,'supplied_npz_sha256':NPZ_SHA,'external_runtime_receipt_sha256':runtime_sha,
        'exact_astype_value_bits_replayed':True,'supplied_metadata_full_counts_and_split_contract_checked':True,
        'creation_identity':{'supplied_creation_receipt_sha256':CREATION_SHA,
            'supplied_metadata_receipt_sha256':METADATA_SHA,'row_ids_sha256':ROW_IDS_SHA,
            'creation_order_matches_supplied_metadata':True,'supplied_metadata_sha256':metadata_sha},
        'original_storage_parity':dict(parity),'native_astype_parity':dict(parity)}


class Contracts(unittest.TestCase):
    def test_request_requires_explicit_import_but_forbids_labels_and_fits(self):
        self.assertIs(a.request_contract(request())['runtime_import_authorized'],True)
        for field,value in [('runtime_import_authorized',False),('label_access_authorized',True),
                            ('model_fitting_authorized',True),('PUM_resource_exception_applies',True),
                            ('PRELib_resource_exception_applies',True),('numerical_threads',2)]:
            item=request();item[field]=value
            with self.assertRaises(AssertionError):a.request_contract(item)

    def test_changed_array_receipt_and_provider_pins_rejected(self):
        for field in ('array_contract_sha256','source_prefit_sha256','software_status_sha256','software_certificate_sha256'):
            item=request();item[field]='0'*64
            with self.assertRaises(AssertionError):a.request_contract(item)
        item=request();item['data_pins'][NPZ]='0'*64
        with self.assertRaises(AssertionError):a.request_contract(item)
        item=request();item['provider_binding']['source_path']='../outside.py'
        with self.assertRaises(AssertionError):a.request_contract(item)

    def test_normalizes_original_windows_keys_without_mutating_and_rejects_alias(self):
        original={name.replace('/','\\'):value for name,value in DECLARED_PINS.items()}
        saved=dict(original);self.assertEqual(a.normalize_map(original),DECLARED_PINS);self.assertEqual(original,saved)
        original[NPZ]=NPZ_SHA
        with self.assertRaisesRegex(AssertionError,'collision'):a.normalize_map(original)

    def test_source_mode_requires_shared_absent_prefix_and_no_site_no_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            absent=Path(directory)/'absent'
            with patch.object(a,'CACHE_PREFIX',absent),patch.object(sys,'flags',types.SimpleNamespace(no_site=1)),\
                 patch.object(sys,'dont_write_bytecode',True),patch.object(sys,'pycache_prefix',str(absent)):
                a.source_mode();absent.mkdir()
                with self.assertRaises(AssertionError):a.source_mode()
            with patch.object(a,'CACHE_PREFIX',absent),patch.object(sys,'flags',types.SimpleNamespace(no_site=0)):
                with self.assertRaises(AssertionError):a.source_mode()

    def test_original_fresh_gate_cannot_be_replaced_through_public_api(self):
        with patch.object(a,'source_mode') as source,patch.object(a,'fresh_gate',return_value={'invented':True}) as gate:
            self.assertEqual(a.fresh(),{'invented':True});source.assert_called_once_with();gate.assert_called_once_with()
        self.assertEqual(tuple(__import__('inspect').signature(a.admit_simple102).parameters),('runtime_provider','root_start'))

    def test_read_guard_precedes_open_and_commit_checks(self):
        events=[];raw=b'invented'
        with patch.object(a,'fresh',side_effect=lambda:events.append('fresh')),\
             patch.object(a,'guarded_bytes',side_effect=lambda *args,**kwargs:events.append('read') or raw),\
             patch.object(a.loader,'_committed',side_effect=lambda *args:events.append('commit')):
            self.assertEqual(a.read_bound('src/invented.py',a.sha(raw),committed=True),raw)
        self.assertEqual(events,['fresh','read','fresh','commit'])

    def test_bounded_payload_hash_and_growth_cap_use_only_tempbytes(self):
        def payload(path,want,parser):
            raw=Path(path).read_bytes();self.assertEqual(a.sha(raw),want)
            return parser(io.BytesIO(raw)),{'actual_sha256':a.sha(raw)}
        with tempfile.TemporaryDirectory() as directory,patch.object(a,'fresh'),patch.object(a,'guarded_payload',side_effect=payload),patch.object(a,'MAX_NPZ',8):
            path=Path(directory)/'invented.bin';path.write_bytes(b'1234')
            raw,_=a.bounded_array_bytes(path,a.sha(b'1234'));self.assertEqual(raw,b'1234')
            path.write_bytes(b'123456789')
            with self.assertRaises(AssertionError):a.bounded_array_bytes(path,a.sha(path.read_bytes()))
            with patch.object(Path,'stat',return_value=types.SimpleNamespace(st_size=4)):
                with self.assertRaises(AssertionError):a.bounded_array_bytes(path,a.sha(path.read_bytes()))

    def test_report_requires_exact_byte_identity_and_runtime_metadata_bindings(self):
        a.validate_report(report(),'e'*64,'f'*64)
        changes=[('rows',13780),('columns',101),('all_columns_finite',False),('exact_astype_value_bits_replayed',False)]
        for key,value in changes:
            item=report();item[key]=value
            with self.assertRaises(AssertionError):a.validate_report(item,'e'*64,'f'*64)
        for key in ('original_storage_parity','native_astype_parity'):
            item=report();item[key]['tolerance_or_zero_filling_used']=True
            with self.assertRaises(AssertionError):a.validate_report(item,'e'*64,'f'*64)
        with self.assertRaises(AssertionError):a.validate_report(report(),'0'*64,'f'*64)
        with self.assertRaises(AssertionError):a.validate_report(report(),'e'*64,'0'*64)

    def test_static_readiness_cannot_smuggle_payloads_or_labels(self):
        self.assertTrue(a.static_pin_allowed('src/invented.py'))
        self.assertTrue(a.static_pin_allowed(SOFTWARE_STATUS))
        for name in (NPZ,CREATION,METADATA,METADATA_BUNDLE,'data/core.csv','results/unknown/labels.json'):
            self.assertFalse(a.static_pin_allowed(name))

    def test_no_root_start_performs_no_read_or_guard(self):
        with patch.object(a,'fresh',side_effect=RuntimeError('must not probe')):
            with self.assertRaisesRegex(AssertionError,'root'):a.admit_simple102(lambda:None)


class Provider(unittest.TestCase):
    def setup_provider(self,mutate=None):
        item=request();numpy_raw=b'invented numpy source'
        np=types.SimpleNamespace(__name__='numpy',__version__='1.26.4',__file__=str(NUMPY_PATH))
        holder={}
        def invoke(binding,phase,root_start):
            self.assertTrue(root_start)
            proof={'status':PROVIDER_STATUS,'request_binding':binding,'phase':phase,
                'fresh_current_python_and_loaded_native_origins_checked':True,'invented_only':False,
                'provider_opened_project_array':False,'numpy_module_path':str(NUMPY_PATH),
                'numpy_module_sha256':a.sha(numpy_raw),'numpy_version':'1.26.4'}
            result={'np':np,'pd':None,'minimize':None,'expit':None,'actual_origin_receipt_sha256':V4_ORIGIN_SHA,
                    'fresh_origin_proof':proof,'fresh_origin_proof_sha256':a.sha(a.canonical(proof))}
            if mutate:mutate(result)
            holder['proof']=proof;return result
        namespace={'invoke':invoke,'__name__':'src.invented_provider'}
        exec(compile('def provide(binding, *, phase, root_start):\n return invoke(binding,phase,root_start)\n',str(ROOT/item['provider_binding']['source_path']),'exec'),namespace)
        return item,namespace['provide'],numpy_raw,np,holder

    def run_provider(self,mutate=None,phase='before_array'):
        item,provider,numpy_raw,np,holder=self.setup_provider(mutate)
        with patch.object(a,'read_bound',return_value=b'invented provider source'),patch.object(a,'fresh'),\
             patch.object(a,'guarded_bytes',return_value=numpy_raw),patch.object(a,'NUMPY_SHA',a.sha(numpy_raw)):
            actual,proof=a.accepted_runtime(provider,item,'e'*64,{}, {},phase)
        self.assertIs(actual,np);return proof

    def test_fresh_actual_binding_is_distinct_from_original_v4_origin(self):
        proof=self.run_provider();self.assertEqual(proof['phase'],'before_array')
        self.assertNotEqual(a.sha(a.canonical(proof)),V4_ORIGIN_SHA)
        self.assertEqual(self.run_provider(phase='after_array')['phase'],'after_array')

    def test_wrong_fresh_hash_v4_origin_phase_and_invented_flag_rejected(self):
        mutations=[lambda r:r.__setitem__('fresh_origin_proof_sha256','0'*64),
                   lambda r:r.__setitem__('actual_origin_receipt_sha256','0'*64),
                   lambda r:r['fresh_origin_proof'].__setitem__('phase','after_array'),
                   lambda r:r['fresh_origin_proof'].__setitem__('invented_only',True)]
        for mutate in mutations:
            with self.assertRaises(AssertionError):self.run_provider(mutate)

    def test_no_injected_resource_callback_or_import_and_wrong_function_rejected(self):
        item,provider,numpy_raw,np,holder=self.setup_provider()
        with patch.object(a,'read_bound',return_value=b'source'),patch.object(a,'fresh'):
            with self.assertRaises(AssertionError):a.accepted_runtime(lambda:None,item,'e'*64,{}, {},'before_array')


class Orchestration(unittest.TestCase):
    def simulate(self,*,changed_after_module=False,mutate_readiness=False):
        events=[];item=request();matrix=object();np=object();meta_sha='f'*64
        bundle={'contract':{'metadata_sha256':meta_sha}}
        ready={'status':'SOURCE_ONLY_GUARDED_ARRAY_API_NOT_PROJECT_ADMISSION','files':{}}
        if mutate_readiness:ready['files'][NPZ]=NPZ_SHA
        data={READY:a.canonical(ready),ARRAY_CONTRACT:a.canonical({'status':'SOURCE_ONLY_SUPPLIED_ARRAY_CONTRACT_NOT_PROJECT_ADMISSION'}),
            SOURCE_PREFIT:a.canonical({'status':'FROZEN_PREFIT','files':{k.replace('/','\\'):v for k,v in DECLARED_PINS.items()}}),
            SOFTWARE_STATUS:b'{}',SOFTWARE_CERT:b'{}',METADATA_BUNDLE:a.canonical(bundle),CREATION:b'creation',METADATA:b'metadata'}
        item['metadata_bundle_sha256']=a.sha(data[METADATA_BUNDLE]);item['source_readiness_sha256']=a.sha(data[READY])
        data[REQUEST]=a.canonical(item)
        def read(name,*args,**kwargs):events.append(('read',name));return data[name]
        def accepted(provider,request,request_sha,status,certificate,phase):
            events.append(('provider',phase));return (object() if phase=='after_array' and changed_after_module else np),{'phase':phase}
        def validation(raw,rows,creation,metadata,**kwargs):
            events.append(('validate',None));self.assertIs(kwargs['np'],np)
            self.assertEqual(kwargs['expected_npz_sha256'],NPZ_SHA)
            self.assertTrue(kwargs['external_runtime_accepted']);self.assertIs(kwargs['resource_probe'],a.live_resources)
            return matrix,report(kwargs['external_runtime_receipt_sha256'],meta_sha)
        with ExitStack() as stack:
            for name,replacement in [('fresh',lambda:events.append(('fresh',None))),('read_bound',read),
                ('software_contract',lambda *args:True),('metadata_contract',lambda *args:[{'invented':'row'}]),
                ('accepted_runtime',accepted),('bounded_array_bytes',lambda *args:(b'invented NPZ',{'actual_sha256':NPZ_SHA})),
                ('validate_supplied_array',validation)]:stack.enter_context(patch.object(a,name,replacement))
            actual,certificate=a.admit_simple102(lambda:None,root_start=True)
        self.assertIs(actual,matrix);return events,certificate

    def test_mocked_end_to_end_keeps_full_rows_order_and_no_certificate_writer(self):
        events,certificate=self.simulate();self.assertEqual(certificate['status'],STATUS)
        self.assertEqual(certificate['rows'],13781);self.assertEqual(certificate['columns'],102)
        self.assertFalse(certificate['numeric_labels_admitted']);self.assertFalse(certificate['FIT_admission_granted'])
        self.assertFalse(certificate['certificate_persisted_here']);self.assertEqual(certificate['models_fitted'],0)
        self.assertLess(events.index(('provider','before_array')),events.index(('validate',None)))
        self.assertLess(events.index(('validate',None)),events.index(('provider','after_array')))
        self.assertEqual(sum(event==('read',REQUEST) for event in events),2)
        self.assertEqual(sum(event==('read',METADATA_BUNDLE) for event in events),2)

    def test_changed_after_runtime_and_smuggled_array_in_readiness_stop(self):
        with self.assertRaises(AssertionError):self.simulate(changed_after_module=True)
        with self.assertRaises(AssertionError):self.simulate(mutate_readiness=True)


def run():
    start=time.perf_counter();suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in {'numpy','pandas','scipy','torch','openvino'} for name in sys.modules)
    sources=sorted(SRC.glob('*.py'))
    receipt={'status':'PASS_INVENTED_STDLIB_GUARDED_ARRAY_API_TESTS','tests_run':result.testsRun,
        'elapsed_seconds':time.perf_counter()-start,'generated_utc':datetime.now(timezone.utc).isoformat(),
        'source_files':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        'actual_native_resource_probes':0,'actual_NumPy_calls':0,'project_array_reads':0,'project_metadata_reads':0,
        'project_outcome_reads':0,'models_fitted':0,'scientific_runtimes_imported':False,
        'actual_runtime_acceptance_established':False,'full_shape_native_validation_run':False,
        'project_admission_granted':False,'mocked_orchestration_is_not_actual_admission':True}
    with (OUT/'synthetic_tests_receipt.json').open('xb') as handle:handle.write(a.canonical(receipt))


if __name__=='__main__':run()
