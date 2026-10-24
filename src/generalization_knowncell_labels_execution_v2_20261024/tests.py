"""Invented original-parser/label provenance tests; no data, jobs or runtime."""
import ast
import copy
import csv
import io
import math
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,admit as a,calibration as cal,supervise as supervisor


class Vector:
    def __init__(self,values):
        self.values=list(values);self.shape=(len(values),);self.tolist_calls=0
        self.dtype=SimpleNamespace(kind='f',itemsize=8,isnative=True,hasobject=False)
    def __len__(self):return len(self.values)
    def __iter__(self):return iter(self.values)
    def tolist(self):self.tolist_calls+=1;return list(self.values)


class FakePandas:
    def __init__(self):self.calls=[];self.conversions=[];self.vector=None
    def read_csv(self,stream,**kwargs):
        self.calls.append(kwargs)
        rows=list(csv.DictReader(io.TextIOWrapper(stream,encoding='utf8')))
        kept=[row for number,row in enumerate(rows,1) if not kwargs['skiprows'](number)]
        self.vector=Vector([float(row['measured_delta']) for row in kept])
        def convert(dtype):self.conversions.append(dtype);return self.vector
        return SimpleNamespace(intervention_id=[row['intervention_id'] for row in kept],
            measured_delta=SimpleNamespace(to_numpy=convert))


def parsed_fixture():
    pd=FakePandas()
    stream=io.BytesIO(b'intervention_id,measured_delta,ignored\nother,999,a\none,0.12345678912345678,b\nother2,-3,c\ntwo,-0.0,d\n')
    metadata={'one_csv_record_per_physical_line':True,'rows':[{'intervention_id':'one'},{'intervention_id':'two'}],
              'original_core_rows':[1,3]}
    return a.parsers.pandas_effects(stream,pd,metadata),pd


def run_fixture():
    return {'status':'FROZEN_ORIGINAL_PANDAS_LABEL_EXECUTION_INPUT_ADMISSION','invocation':c.INVOCATION,'stage':c.STAGE,
        'generation_manifest_sha256':'e'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
        'runtime_import_authorized':True,'label_access_authorized':True,'model_fitting_authorized':False,
        'input_pins':{c.REQUEST:'1'*64,c.METADATA_BUNDLE:c.METADATA_SHA,c.ARRAY_CERTIFICATE:c.ARRAY_CERTIFICATE_SHA,
            c.ARRAY_SUPERVISOR:c.ARRAY_SUPERVISOR_SHA,c.INDEPENDENT_REPORT:c.INDEPENDENT_REPORT_SHA,
            c.INDEPENDENT_SUPERVISOR:c.INDEPENDENT_SUPERVISOR_SHA}}


def array_fixture():
    fields={'generation_manifest_sha256':c.ARRAY_GENERATION_SHA,'run_admission_sha256':'7'*64,'birth_sha256':'8'*64,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA}
    protected={key:{'status':'PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_ARRAY_REQUEST','phase':phase,'invented_only':False,
        'fresh_current_python_and_loaded_native_origins_checked':True,'actual_origin_receipt_sha256':c.runtime.PROFILE_ORIGIN_SHA,'model_fits':0}
        for key,phase in (('runtime_acceptance','before_array'),('runtime_acceptance_after_array','after_array'))}
    certificate={'status':'PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY','invocation':'array_admission',**fields,
        'metadata_bundle_sha256':c.METADATA_SHA,'actual_npz_sha256':c.NPZ_SHA,'original_row_ids_sha256':c.ROW_IDS_SHA,
        'rows':c.COUNT,'columns':102,'same_allele_feature_bytes_equal':True,
        'underlying_report':{'post_original_astype_float_C_bytes_sha256':c.ARRAY_CAST_SHA},
        'original_resource_guards_unchanged':False,'resource_exception_applies':True,'numeric_labels_admitted':False,
        'FIT_admission_granted':False,'models_fitted':0,'independent_metadata_report_sha256':c.INDEPENDENT_REPORT_SHA,
        **protected,'protected_runtime_payloads_sha256':c.sha(c.canonical(protected))}
    raw=c.canonical(certificate)
    supervisor_value={'status':'PASS_EXACT_ARRAY_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT','failure':None,
        'invocation':'array_admission',**fields,'certificate_sha256':c.sha(raw),'resource_policy':c.resource_policy(),
        'automatic_retry':False,'numerical_outcomes_admitted':0,'model_fits':0}
    admission={'input_pins':{c.ARRAY_CERTIFICATE:c.sha(raw)}}
    return raw,certificate,supervisor_value,admission


def certificate_fixture():
    labels,_=parsed_fixture()
    with patch.object(a.guard,'fresh_gate'):labels=a.serialize_original_result(labels,SimpleNamespace(ndarray=Vector),['one','two'])
    binding={'request_relative_path':c.REQUEST,'request_sha256':'1'*64,'provider_preparation_manifest_sha256':c.RUNTIME_PREPARATION_SHA,
             'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA}
    proofs={key:{'status':c.runtime.PROVIDER_STATUS,'phase':phase,'request_binding':binding,
        'actual_origin_receipt_sha256':c.runtime.PROFILE_ORIGIN_SHA,'invented_only':False,
        'fresh_current_python_and_loaded_native_origins_checked':True,'old_interpreter_bitwise_parity_established':False,'model_fits':0,
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'software_certificate_sha256':c.runtime.PANDAS_ADMISSION_SHA,
        'same_owned_software_objects_retained':True,'source_cache_remained_absent':True,'numpy_version':'1.26.4','pandas_version':'2.2.3'}
        for key,phase in (('runtime_acceptance','before_labels'),('runtime_acceptance_after_labels','after_labels'))}
    return {'status':c.LABEL_STATUS,'invocation':c.INVOCATION,'generation_manifest_sha256':'e'*64,
        'run_admission_sha256':'f'*64,'birth_sha256':'2'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'metadata_bundle_sha256':c.METADATA_SHA,
        'array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,'array_supervisor_sha256':c.ARRAY_SUPERVISOR_SHA,
        'label_request_sha256':'1'*64,'rows':2,'original_row_ids_sha256':c.sha(b'one|two'),
        'metadata_sha256':c.METADATA_CONTENT_SHA,'labels_result':labels,'models_fitted':0,'actual_feature_reads':0,
        'label_access_does_not_authorize_fitting':True,'source_core_read':{'actual_sha256':c.CORE_SHA,'raw_bytes_traversed':123,
            'fresh_original_resource_gate_before_open':False},'original_resource_guards_unchanged':False,
        'resource_exception_applies':True,**proofs,'protected_runtime_payloads_sha256':c.sha(c.canonical(proofs)),
        'parent_pid':123,'worker_pid':456,
        'resource_calibration':{'stage':'labels','execution_manifest_sha256':'e'*64,'birth_sha256':'2'*64,
            'authorization_sha256':c.AUTH_SHA,'invocation':c.INVOCATION,'scientific_protocol_settings_changed':False,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA,'parent_pid':123,'current_pid':456}}


class Cases(unittest.TestCase):
    def test_exact_frozen_original_parser_options_skiprows_and_float_conversion(self):
        result,pd=parsed_fixture();options=pd.calls[0]
        self.assertEqual(set(options),{'usecols','low_memory','skiprows'})
        self.assertEqual(options['usecols'],['intervention_id','measured_delta']);self.assertIs(options['low_memory'],False)
        self.assertEqual([options['skiprows'](number) for number in range(5)],[False,True,False,True,False])
        self.assertEqual(pd.conversions,[float]);self.assertEqual(result['intervention_ids'],['one','two'])
        self.assertEqual(pd.vector.tolist_calls,0)
        self.assertEqual(result['parser'],c.PARSER)

    def test_vector_serializes_via_only_tolist_and_preserves_all_exact_bits(self):
        result,pd=parsed_fixture();np=SimpleNamespace(ndarray=Vector)
        with patch.object(a.guard,'fresh_gate') as gate:
            saved=a.serialize_original_result(result,np,['one','two'])
        self.assertEqual(pd.vector.tolist_calls,1);gate.assert_called_once()
        self.assertIs(result['measured_delta'],pd.vector)
        self.assertEqual(saved['parsed_effects_float64_sha256'],c.sha(b''.join(struct.pack('<d',value) for value in saved['measured_delta'])))
        self.assertEqual(struct.pack('<d',saved['measured_delta'][1]),struct.pack('<d',-0.0))
        self.assertEqual(set(saved),set(result));self.assertEqual(c.decode(c.canonical(saved)),saved)

    def test_changed_id_bits_dtype_or_nonfinite_vector_rejects_without_reparse(self):
        for mode in ('ids','bits','dtype','nan'):
            result,pd=parsed_fixture()
            if mode=='ids':result['intervention_ids'].reverse()
            if mode=='bits':result['parsed_effects_float64_sha256']='0'*64
            if mode=='dtype':pd.vector.dtype.itemsize=4
            if mode=='nan':pd.vector.values[0]=float('nan')
            with self.subTest(mode=mode),patch.object(a.guard,'fresh_gate'),self.assertRaises(AssertionError):
                a.serialize_original_result(result,SimpleNamespace(ndarray=Vector),['one','two'])
            self.assertEqual(len(pd.calls),1)

    def test_labels_run_admission_binds_only_completed_actual_array_hashes(self):
        self.assertEqual(c.run_contract(run_fixture(),'e'*64)['stage'],'labels')
        for key in (c.ARRAY_CERTIFICATE,c.ARRAY_SUPERVISOR,c.METADATA_BUNDLE):
            value=run_fixture();value['input_pins'][key]='0'*64
            with self.subTest(key=key),self.assertRaises(AssertionError):c.run_contract(value,'e'*64)
        value=run_fixture();value['model_fitting_authorized']=True
        with self.assertRaises(AssertionError):c.run_contract(value,'e'*64)

    def test_array_success_chain_rejects_failure_generation_and_false_resource_provenance(self):
        raw,certificate,saved,admission=array_fixture()
        self.assertIs(a.array_prerequisite(raw,certificate,saved,admission),certificate)
        for field,value in (('metadata_bundle_sha256','0'*64),('original_resource_guards_unchanged',True),
                            ('generation_manifest_sha256','0'*64)):
            raw,certificate,saved,admission=array_fixture();certificate[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):a.array_prerequisite(raw,certificate,saved,admission)
        raw,certificate,saved,admission=array_fixture();saved['failure']='invented failure'
        with self.assertRaises(AssertionError):a.array_prerequisite(raw,certificate,saved,admission)

    def test_terminal_exact_label_bits_and_runtime_protected_subtrees_reject_mutation(self):
        with patch.object(c,'COUNT',2),patch.object(c,'ROW_IDS_SHA',c.sha(b'one|two')),patch.object(c,'read_run',return_value=run_fixture()):
            value=certificate_fixture();self.assertIs(a.validate_certificate(value,'e'*64,'f'*64,'2'*64),value)
            for kind in ('value','order','truth','io_guard','proof','phase','request','preparation','worker','scope'):
                value=certificate_fixture()
                if kind=='value':value['labels_result']['measured_delta'][0]+=1.
                if kind=='order':value['labels_result']['intervention_ids'].reverse()
                if kind=='truth':value['labels_result']['original_truth_orientation']=False
                if kind=='io_guard':value['source_core_read']['fresh_original_resource_gate_before_open']=True
                if kind=='proof':value['runtime_acceptance_after_labels']['pandas_version']='changed'
                if kind=='phase':value['runtime_acceptance_after_labels']['phase']='after_array'
                if kind=='request':value['runtime_acceptance_after_labels']['request_binding']['request_sha256']='0'*64
                if kind=='preparation':value['runtime_acceptance_after_labels']['request_binding']['provider_preparation_manifest_sha256']='0'*64
                if kind=='worker':value['resource_calibration']['current_pid']=999
                if kind=='scope':value['resource_calibration']['approval_scope_sha256']='0'*64
                if kind in ('proof','phase','request','preparation'):
                    value['protected_runtime_payloads_sha256']=c.sha(c.canonical({name:value[name] for name in
                        ('runtime_acceptance','runtime_acceptance_after_labels')}))
                with self.subTest(kind=kind),self.assertRaises(AssertionError):a.validate_certificate(value,'e'*64,'f'*64,'2'*64)
        value=run_fixture();value['input_pins']['results/extra.json']='a'*64
        with self.assertRaises(AssertionError):c.run_contract(value,'e'*64)

    def test_full_parent_terminal_pair_binds_completion_bits_and_exact_processes(self):
        with patch.object(c,'COUNT',2),patch.object(c,'ROW_IDS_SHA',c.sha(b'one|two')),\
             patch.object(c,'read_run',return_value=run_fixture()),patch.object(c,'source_mode',return_value={}):
            certificate=certificate_fixture()
            completion={'status':'PASS_EXACT_LABELS_WORKER_CALLBACKS_RESTORED','invocation':c.INVOCATION,
                'generation_manifest_sha256':'e'*64,'run_admission_sha256':'f'*64,'birth_sha256':'2'*64,
                'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
                'approval_scope_sha256':c.SCOPE_SHA,'parent_pid':123,'worker_pid':456,'callbacks_restored':True,
                'fresh_calibrated_guard_calls':10,'numerical_outcomes_admitted':2,'model_fits':0,'core_label_reads':1,
                'source_mode':{},'resource_policy':c.resource_policy(),'certificate_sha256':'9'*64,
                'parsed_effects_float64_sha256':certificate['labels_result']['parsed_effects_float64_sha256']}
            self.assertIs(supervisor.terminal_pair(completion,certificate,'e'*64,'f'*64,'2'*64,123,456),certificate)
            for field,wrong in (('parsed_effects_float64_sha256','0'*64),('worker_pid',789),('parent_pid',789),('callbacks_restored',False)):
                changed=copy.deepcopy(completion);changed[field]=wrong
                with self.subTest(field=field),self.assertRaises(AssertionError):
                    supervisor.terminal_pair(changed,certificate,'e'*64,'f'*64,'2'*64,123,456)

    def test_resource_body_targets_and_live_policy_stay_frozen(self):
        original=c.ROOT/'src/generalization_knowncell_metadata_verification_execution_20261024/calibration.py'
        def functions(path):
            return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(path.read_text(encoding='utf8')).body
                    if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        old,new=functions(original),functions(Path(cal.__file__))
        for name in ('_environment','_snapshot','_installed','_source_module','_hash','_sha','_plain_copy',
                     '_resource_key','_check_scientific_subtree','_annotated_copy'):
            self.assertEqual(old[name],new[name],name)
        from src.generalization_knowncell_metadata_verification_execution_20261024 import calibration as original_calibration
        self.assertEqual(cal.TARGETS,original_calibration.TARGETS);self.assertEqual(len(cal.TARGETS),5)
        self.assertEqual(cal.STARTUP_PHYSICAL,512*2**20);self.assertEqual(cal.LIVE_PHYSICAL,256*2**20)
        self.assertEqual(c.resource_policy()['startup_commit_headroom'],1920*2**20)
        self.assertEqual(c.PROCESS_CAP,768*2**20);self.assertEqual(c.JOB_CAP,896*2**20)

    def test_new_calibration_factory_fixed_real_common_and_labels_scope(self):
        with patch.object(cal.importlib,'import_module') as imported:
            imported.return_value=SimpleNamespace(admit_authorization=lambda value:(_ for _ in ()).throw(FileNotFoundError('future committed admission')))
            with self.assertRaises(FileNotFoundError):
                with cal.calibrated('labels','e'*64,{}):self.fail('No actual context may run')
            imported.assert_called_once_with('src.'+c.NS+'.common')
        with self.assertRaises(AssertionError):
            with cal.calibrated('fit','e'*64,{}):self.fail()

    def test_controller_command_labels_generation_and_absent_owned_outputs_only(self):
        command=supervisor.command('e'*64,'f'*64,'1'*64)
        self.assertIn('src.'+c.NS+'.worker',command)
        self.assertEqual(command[1:4],['-S','-B','-X'])
        with patch.object(c.os.path,'lexists',side_effect=lambda path:path==c.OUTPUT):
            with self.assertRaisesRegex(AssertionError,'Preserve prior'):c.require_new_outputs()

    def test_low_resource_gate_before_original_pandas_parser(self):
        # The only actual CORE reader is the unchanged guarded_payload helper.
        with patch.object(a.guard,'fresh_gate',side_effect=AssertionError('low reserve')),\
             patch.object(Path,'open') as opened:
            with self.assertRaisesRegex(AssertionError,'low reserve'):
                a.guard.guarded_payload(c.ROOT/c.CORE,c.CORE_SHA,lambda stream:self.fail('No parser'))
            opened.assert_not_called()

    def test_annotator_preserves_label_bits_and_truthfully_changes_source_io_claim_only(self):
        result,pd=parsed_fixture()
        with patch.object(a.guard,'fresh_gate'):labels=a.serialize_original_result(result,SimpleNamespace(ndarray=Vector),['one','two'])
        owner={'current_pid':cal.os.getpid(),'parent_pid':cal.os.getppid(),'birth_sha256':'1'*64}
        auth={'approval_sha256':c.AUTH_SHA,'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA}
        session=cal._Session(c.STAGE,'e'*64,auth,owner,{},lambda:self.fail('No actual or fake probe'),SimpleNamespace())
        payload={'labels_result':labels,'source_core_read':{'actual_sha256':c.CORE_SHA,'raw_bytes_traversed':123,
                 'fresh_original_resource_gate_before_open':True},'original_scientific_guards_changed':False}
        annotated=session.annotate(payload)
        self.assertEqual(c.canonical(annotated['labels_result']),c.canonical(labels))
        self.assertFalse(annotated['source_core_read']['fresh_original_resource_gate_before_open'])
        self.assertFalse(annotated['original_scientific_guards_changed'])
        self.assertEqual(annotated['resource_calibration']['invocation'],c.INVOCATION)


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    def clean():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean() and not c.RUN_ADMISSION.exists() and not (c.ROOT/c.REQUEST).exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    c.save_new(c.OUT/'synthetic_tests_receipt_reviewed.json',{'status':'PASS_INVENTED_ORIGINAL_PARSER_LABEL_EXECUTION_NOT_ACTUAL_ADMISSION',
        'tests':result.testsRun,'sources':{path.relative_to(c.ROOT).as_posix():c.sha(path.read_bytes()) for path in sources},
        'actual_jobs':0,'actual_resource_probes':0,'actual_provider_invocations':0,'project_payload_reads':0,
        'label_rows_admitted':0,'model_fits':0,'scientific_imports':False,
        'parser_spy_is_invented_not_native_pandas_compatibility_evidence':True})


if __name__=='__main__':run()
