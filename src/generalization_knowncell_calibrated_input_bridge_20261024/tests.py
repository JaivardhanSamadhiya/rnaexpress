"""Invented-only supplied doubles; no real guards/Git/native/data operations."""
from contextlib import ExitStack,contextmanager
import copy
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
from src.generalization_knowncell_joint_input_bridge_20261023.tests import fixture as old_fixture,NP
from . import bridge as b,contracts as c
from .spec import *


def calibration(value,stage,invocation):
    value.update(invocation=invocation,generation_manifest_sha256='1'*64,run_admission_sha256='2'*64,
        birth_sha256='3'*64,approved_policy_manifest_sha256=POLICY_SHA,authorization_sha256=AUTH_SHA,
        approval_scope_sha256=SCOPE_SHA,resource_exception_applies=True,original_resource_guards_unchanged=False,
        parent_pid=111,worker_pid=112)
    value['resource_calibration']={'status':'EXPLICITLY_AUTHORIZED_BOUNDED_KNOWNCELL_RESOURCE_CALIBRATION',
        'stage':stage,'invocation':invocation,'execution_manifest_sha256':'1'*64,'authorization_sha256':AUTH_SHA,
        'birth_sha256':'3'*64,'scientific_protocol_settings_changed':False,
        'scientific_metadata_and_contracts_unchanged':True,'startup_physical_floor':512*2**20,
        'live_physical_floor':256*2**20,'disk_floor':2**30,'live_global_commit_reserve':2**30,
        'callbacks_restored_at_annotation':False,'fresh_calibrated_guard_calls':8,
        'hard_job_caps_and_continuous_monitoring_owned_by_controller':True,'current_pid':112,'parent_pid':111}


def fixture():
    f=old_fixture();array=c.decode(f['array_raw']);calibration(array,'array','array_admission')
    array_raw=c.canonical(array);labels={key:copy.deepcopy(f['labels'][key]) for key in LABEL_KEYS if key!='measured_delta'}
    labels['measured_delta']=f['labels']['measured_delta'].tolist()
    request={'request_relative_path':LABEL_REQUEST,'request_sha256':'4'*64,
        'provider_preparation_manifest_sha256':'5'*64,'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_SHA}
    def label_proof(phase):
        return {'status':LABEL_PROVIDER_STATUS,'phase':phase,'request_binding':request,
            'actual_origin_receipt_sha256':V4_ORIGIN_SHA,'software_status_sha256':SOFTWARE_STATUS_SHA,
            'software_certificate_sha256':PANDAS_SHA,'invented_only':False,
            'fresh_current_python_and_loaded_native_origins_checked':True,'same_owned_software_objects_retained':True,
            'source_cache_remained_absent':True,'numpy_version':'1.26.4','pandas_version':'2.2.3',
            'old_interpreter_bitwise_parity_established':False,'model_fits':0}
    protected={'runtime_acceptance':label_proof('before_labels'),'runtime_acceptance_after_labels':label_proof('after_labels')}
    certificate={'status':LABEL_STATUS,'metadata_bundle_sha256':c.digest(f['bundle_raw']),
        'array_certificate_sha256':c.digest(array_raw),'array_supervisor_sha256':'6'*64,
        'rows':12,'original_row_ids_sha256':f['rowsha'],'metadata_sha256':b.reference.metadata_sha(f['rows']),
        'pandas_admission_sha256':PANDAS_SHA,'software_status_sha256':SOFTWARE_STATUS_SHA,
        'actual_origin_receipt_sha256':V4_ORIGIN_SHA,'label_request_sha256':'4'*64,
        'models_fitted':0,'actual_feature_reads':0,'label_access_does_not_authorize_fitting':True,
        'source_core_read':{'actual_sha256':CORE_SHA,'raw_bytes_traversed':999,'fresh_original_resource_gate_before_open':False},
        'labels_result':labels,**protected,'protected_runtime_payloads_sha256':c.digest(c.operational_canonical(protected))}
    calibration(certificate,'labels','original_pandas_label_admission');label_raw=c.canonical(certificate)
    binding={key:'7'*64 for key in HASH_FIELDS}
    binding.update(status=BINDING_STATUS,namespace=NS,stage='prefit',reviewed_controller_source='src/generalization_knowncell_invented/controller.py',
        reviewed_owned_caller_required=True,runtime_and_FIT_authority_granted_here=False,
        approved_policy_manifest_sha256=POLICY_SHA,authorization_sha256=AUTH_SHA,approval_scope_sha256=SCOPE_SHA,
        metadata_bundle_sha256=c.digest(f['bundle_raw']),array_certificate_sha256=c.digest(array_raw),
        array_supervisor_sha256='6'*64,label_certificate_sha256=c.digest(label_raw),
        runtime_binding_sha256=c.digest(c.canonical(array['runtime_acceptance_after_array'])),native_profile_receipt_sha256=V4_ORIGIN_SHA)
    current={'status':STAGE_PROOF_STATUS,'stage':'prefit','phase':'before_supplied_input_bridge',
        'current_pid':os.getpid(),'parent_pid':os.getppid(),'caller_birth_sha256':binding['caller_birth_sha256'],
        'reviewed_controller_admission_sha256':binding['reviewed_controller_admission_sha256'],
        'stable_admitted_runtime_binding_sha256':binding['runtime_binding_sha256'],'invented_only':False,
        'fresh_current_python_and_loaded_native_origins_checked':True,'software_status_sha256':SOFTWARE_STATUS_SHA,
        'software_certificate_sha256':PANDAS_SHA,'actual_origin_receipt_sha256':V4_ORIGIN_SHA,
        'numpy_module_path':str(NUMPY_PATH),'numpy_module_sha256':NUMPY_SHA,'numpy_version':'1.26.4',
        'pandas_version':'2.2.3','scipy_version':'1.14.1','numerical_threads':1,'source_cache_remained_absent':True,
        'old_interpreter_bitwise_parity_established':False,'runtime_and_FIT_authority_granted_here':False,'UTC':'invented-UTC-not-real-proof'}
    binding['current_stage_origin_proof_sha256']=c.digest(c.canonical(current))
    f.update(array_raw=array_raw,label_raw=label_raw,binding=binding,current=current)
    f['matrix'].events.clear()
    return f


@contextmanager
def supplied(f):
    with ExitStack() as stack:
        stack.enter_context(patch.object(c,'fresh'))
        committed=stack.enter_context(patch.object(c,'committed_bytes'))
        stack.enter_context(patch.object(c,'ARRAY_SHA',c.digest(f['array_raw'])))
        stack.enter_context(patch.object(b,'ROW_IDS_SHA',f['rowsha']))
        stack.enter_context(patch.object(b,'COUNTS',{'rows':12,'columns':102}))
        stack.enter_context(patch.object(b.reference,'COUNTS',f['small']))
        yield committed


def invoke(f):
    return b.bridge_inputs(NP,f['bundle_raw'],f['matrix'],f['array_raw'],f['label_raw'],
        c.canonical(f['binding']),f['current'],root_start=True)


class Tests(unittest.TestCase):
    def test_exact_supplied_objects_original_engine_hashes_and_no_cast(self):
        f=fixture();before=copy.deepcopy(f)
        with supplied(f) as committed:result=invoke(f)
        self.assertIs(result['features'],f['matrix']);self.assertEqual(f['matrix'].events,['tobytes_C'])
        self.assertEqual(result['metadata'],f['rows'])
        self.assertEqual(list(result['effects']),[row['intervention_id'] for row in f['rows']])
        raw=b''.join(struct.pack('<d',v) for v in result['effects'].values())
        self.assertEqual(result['admissions']['input_effects_sha256'],c.bits_hash(raw,(12,)))
        self.assertEqual(result['admissions']['label_admission_sha256'],f['binding']['label_certificate_sha256'])
        self.assertEqual(result['admissions']['input_features_sha256'],c.bits_hash(f['matrix'].tobytes(order='C'),(12,102)))
        self.assertEqual([call.args[0] for call in committed.call_args_list],
            [binding_path('prefit'),METADATA_PATH,ARRAY_PATH,LABEL_PATH])
        self.assertEqual(f['bundle_raw'],before['bundle_raw']);self.assertEqual(f['label_raw'],before['label_raw'])
        self.assertFalse(result['bridge_report']['actual_parent_Job_or_reviewed_caller_execution_certified_here'])
        self.assertFalse(result['bridge_report']['runtime_or_input_or_FIT_authority_granted_here'])

    def test_signed_zero_and_subnormal_float_bits_are_preserved(self):
        f=fixture();doc=c.decode(f['label_raw']);values=doc['labels_result']['measured_delta']
        values[0]=-0.0;values[1]=5e-324;raw=b''.join(struct.pack('<d',v) for v in values)
        doc['labels_result']['parsed_effects_float64_sha256']=c.digest(raw)
        f['label_raw']=c.canonical(doc);f['binding']['label_certificate_sha256']=c.digest(f['label_raw'])
        with supplied(f):result=invoke(f)
        self.assertEqual(b''.join(struct.pack('<d',v) for v in result['effects'].values()),raw)

    def test_no_root_stops_before_real_gate_or_input_parse(self):
        with patch.object(c,'fresh',side_effect=RuntimeError('must not probe')):
            with self.assertRaises(AssertionError):b.bridge_inputs(None,None,None,None,None,None,None)

    def test_failed_real_guard_precedes_commit_or_supplied_matrix_access(self):
        with patch.object(c,'fresh',side_effect=AssertionError('invented resource stop')),patch.object(c,'committed_bytes') as git:
            with self.assertRaisesRegex(AssertionError,'resource stop'):
                b.bridge_inputs(None,None,None,None,None,None,None,root_start=True)
        git.assert_not_called()

    def test_uncommitted_bindings_stop_before_matrix(self):
        f=fixture()
        with supplied(f),patch.object(c,'committed_bytes',side_effect=AssertionError('uncommitted')):
            with self.assertRaisesRegex(AssertionError,'uncommitted'):invoke(f)
        self.assertEqual(f['matrix'].events,[])

    def test_float_bits_or_id_order_or_extra_original_label_key_rejected(self):
        for kind in ('bits','order','extra'):
            f=fixture();doc=c.decode(f['label_raw'])
            if kind=='bits':doc['labels_result']['measured_delta'][0]=1.25
            elif kind=='order':doc['labels_result']['intervention_ids'].reverse()
            else:doc['labels_result']['new_parser']=False
            f['label_raw']=c.canonical(doc)
            with supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_nonfloat_nonfinite_and_bool_labels_rejected(self):
        for value in (0,True,'1.0'):
            f=fixture();doc=c.decode(f['label_raw']);doc['labels_result']['measured_delta'][0]=value
            f['label_raw']=c.canonical(doc)
            with supplied(f),self.assertRaises(AssertionError):invoke(f)
        for token in ('NaN','Infinity','-Infinity'):
            with self.assertRaises(AssertionError):c.decode(('{"value":'+token+'}').encode())

    def test_matrix_mutation_dtype_and_nonfinite_rejected(self):
        for kind in ('bits','dtype','nonfinite'):
            f=fixture()
            if kind=='dtype':f['matrix'].dtype.itemsize=4
            else:f['matrix'].values[0][0]=float('inf') if kind=='nonfinite' else .125
            with supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_truthful_calibration_required_for_array_and_labels(self):
        for key in ('array_raw','label_raw'):
            f=fixture();doc=c.decode(f[key]);doc['resource_exception_applies']=False;f[key]=c.canonical(doc)
            with supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_protected_proof_mutation_or_wrong_schema_fails(self):
        for key in ('protected_runtime_payloads_sha256','status','source_core_read'):
            f=fixture();doc=c.decode(f['label_raw'])
            if key=='source_core_read':doc[key]['fresh_original_resource_gate_before_open']=True
            elif key=='status':doc[key]='failed-original-acquisition'
            else:doc[key]='0'*64
            f['label_raw']=c.canonical(doc)
            with supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_dynamic_current_proof_is_distinct_from_stable_anchor(self):
        f=fixture()
        self.assertNotEqual(f['binding']['runtime_binding_sha256'],f['binding']['current_stage_origin_proof_sha256'])
        with supplied(f):result=invoke(f)
        self.assertEqual(result['admissions']['runtime_binding_sha256'],f['binding']['runtime_binding_sha256'])
        self.assertEqual(result['bridge_report']['current_stage_origin_proof_sha256'],f['binding']['current_stage_origin_proof_sha256'])

    def test_wrong_current_owner_stage_or_native_declaration_fails(self):
        for key,value in (('current_pid',-1),('parent_pid',-1),('stage','labels'),('numpy_version','2.4.6'),('numerical_threads',2)):
            f=fixture();f['current'][key]=value
            f['binding']['current_stage_origin_proof_sha256']=c.digest(c.canonical(f['current']))
            with supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_unknown_binding_key_and_duplicate_JSON_rejected(self):
        f=fixture();f['binding']['invented_override']=True
        with supplied(f),self.assertRaises(AssertionError):invoke(f)
        with self.assertRaises(AssertionError):c.decode(b'{"x":1,"x":2}')

    def test_real_helpers_are_reused_without_public_DI_or_eager_native_import(self):
        from src.generalization_knowncell_joint_input_bridge_20261023 import contracts as old
        for name in ('fresh','committed_bytes','bits_hash','runtime_contract'):self.assertIs(getattr(c,name),getattr(old,name))
        for name in ('numpy','pandas','scipy','torch','openvino','sklearn','src.cross_assay_20260927.models'):
            self.assertNotIn(name,sys.modules)


def run():
    import ast
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful()
    sources=sorted(SRC.glob('*.py'))
    for path in sources:ast.parse(path.read_text(encoding='utf8'))
    payload={'status':'PASS_INVENTED_CALIBRATED_SUPPLIED_INPUT_BRIDGE_NOT_ACTUAL_EXECUTION',
        'tests':result.testsRun,'source_files':{p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources},
        'project_payloads_read':0,'actual_Git_calls':0,'actual_resource_probes':0,'native_scientific_imports':False,
        'sampler_or_pool_calls':0,'optimizer_calls':0,'actual_root_binding_created':False}
    path=OUT/'synthetic_tests_receipt.json'
    with path.open('xb') as stream:stream.write(c.canonical(payload))
    print('INVENTED_CALIBRATED_BRIDGE_PASS',result.testsRun,c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
