"""Invented NPZ/list/roster/provenance tests; no actual pools or native calls."""
import ast
import copy
import io
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,inputs,build,worker as w,supervise as supervisor,calibration as cal
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc,spec as old


def old_document():
    ids=['invented_prefit_'+str(i) for i in range(6)];folds=[0,1,2,0,1,2]
    document={'status':old.PREFIT_STATUS,'counts':{**old.COUNTS,'all_rows':6},'arms':list(old.ARMS),'configs':list(old.CONFIGS),
        'numerical_threads':1,'resource_exception_applies':False,'runtime_binding_sha256':'a'*64,
        'metadata_admission_sha256':c.METADATA_ADMISSION_SHA,'feature_admission_sha256':c.ARRAY_CERTIFICATE_SHA,
        'label_admission_sha256':c.LABEL_CERTIFICATE_SHA,'fit_source_manifest_sha256':c.STABLE_SCIENTIFIC_BINDINGS['fit_source_manifest_sha256'],
        'all_row_ids':ids,'all_row_folds':folds,'source_pools':{},'input_admission_bindings':dict(c.STABLE_SCIENTIFIC_BINDINGS)}
    for outer in (0,1,2):
        for inner in (None,*[fold for fold in (0,1,2) if fold!=outer]):
            train=[item for item,fold in zip(ids,folds) if fold not in ({outer} if inner is None else {outer,inner})]
            target=[item for item,fold in zip(ids,folds) if fold==(outer if inner is None else inner)]
            document['source_pools'][lc.pool_key(outer,inner)]={'training_ids':train,'validation_ids':target,
                'training_ids_sha256':lc.id_hash(train),'validation_ids_sha256':lc.id_hash(target),'training_rows':len(train),
                'validation_rows':len(target),'training_pairs':1,'both_cells_confirmed':True,'full_original_menus_confirmed':True,
                'gene_component_allele_contradictions':0,**{field:'b'*64 for field in old.POOL_HASH_FIELDS}}
    return document


def run_record():
    return {'status':'FROZEN_ONE_ADMITTED_INPUT_NINE_POOL_PREFIT_RUN_NO_FIT','stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':'1'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),'runtime_import_authorized':True,
        'array_reload_authorized':True,'saved_label_read_authorized':True,'pool_preparation_authorized':True,
        'CORE_read_authorized':False,'model_fitting_authorized':False,'data_pins':{c.NPZ:c.NPZ_SHA},
        'input_pins':{**c.INPUT_PINS,c.REQUEST:'2'*64,c.STATIC_BINDING:'3'*64,c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix():'4'*64}}


def source_record():
    manifest={'files':{c.WORKER_SOURCE:'5'*64,c.runtime.PREPARATION:'6'*64,c.BRIDGE_READY:'7'*64}}
    record={'status':'REVIEWED_SOURCE_ONLY_PREFIT_CONTROLLER_NOT_INPUT_OR_FIT_AUTHORITY','stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':'1'*64,'controller_source':c.WORKER_SOURCE,'controller_source_sha256':'5'*64,
        'runtime_provider_preparation_sha256':'6'*64,'bridge_readiness_sha256':'7'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
        'actual_input_or_FIT_authority_granted':False,'stable_scientific_source_bindings':dict(c.STABLE_SCIENTIFIC_BINDINGS)}
    return record,manifest


def provenance():
    binding={'request_relative_path':c.REQUEST,'request_sha256':'2'*64,'provider_preparation_manifest_sha256':'6'*64,
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA}
    proofs={name:{'status':c.runtime.PROVIDER_STATUS,'stage':c.STAGE,'phase':phase,'current_pid':456,'parent_pid':123,
        'caller_birth_sha256':'8'*64,'static_root_binding_sha256':'3'*64,'reviewed_controller_admission_sha256':'4'*64,
        'stable_admitted_runtime_binding_sha256':'a'*64,'invented_only':False,'fresh_current_python_and_loaded_native_origins_checked':True,
        'optimizer_calls':0,'runtime_and_FIT_authority_granted_here':False,'request_binding':binding,
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'software_certificate_sha256':c.runtime.PANDAS_ADMISSION_SHA,
        'actual_origin_receipt_sha256':c.runtime.PROFILE_ORIGIN_SHA,'numerical_threads':1,'source_cache_remained_absent':True,
        'numpy_version':'1.26.4','pandas_version':'2.2.3','scipy_version':'1.14.1','old_interpreter_bitwise_parity_established':False}
        for name,phase in (('runtime_acceptance','before_supplied_input_bridge'),('runtime_acceptance_after_prefit','after_pool_preparation'))}
    context={'status':'SUPPLIED_CURRENT_OWNER_CONTEXT_REQUIRES_ACTUAL_FIXED_CALLER_VERIFICATION','stage':c.STAGE,
        'current_stage_origin_proof_sha256':w.bc.digest(w.bc.canonical(proofs['runtime_acceptance'])),
        'caller_birth_sha256':'8'*64,'current_pid':456,'parent_pid':123,'static_root_binding_sha256':'3'*64,
        'reviewed_controller_admission_sha256':'4'*64,'actual_parent_Job_and_native_origins_checked_by_fixed_caller':True,
        'runtime_and_FIT_authority_granted_here':False}
    protected={**proofs,'current_owner_context':context}
    return {'stage':c.STAGE,'invocation':c.INVOCATION,'generation_manifest_sha256':'1'*64,'run_admission_sha256':'9'*64,
        'birth_sha256':'8'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'metadata_bundle_sha256':c.METADATA_SHA,'array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,
        'label_certificate_sha256':c.LABEL_CERTIFICATE_SHA,'saved_label_bits_sha256':c.LABEL_BITS_SHA,
        'original_resource_guards_unchanged':False,'source_pools_prepared':9,'source_npz_read':{'actual_sha256':c.NPZ_SHA,
            'fresh_original_resource_gate_before_open':False},'CORE_reread':False,'label_reparse_recast_or_recomputation':False,
        'optimizer_calls':0,'campaign_started':False,'runtime_and_FIT_authority_granted_here':False,
        'stable_admitted_runtime_binding_sha256':'a'*64,'static_root_binding_sha256':'3'*64,
        'controller_source_admission_sha256':'4'*64,'runtime_request_sha256':'2'*64,'parent_pid':123,'worker_pid':456,
        **protected,'protected_current_provenance_sha256':c.sha(c.canonical(protected)),
        'resource_calibration':{'stage':c.STAGE,'execution_manifest_sha256':'1'*64,'birth_sha256':'8'*64,'authorization_sha256':c.AUTH_SHA,
            'current_pid':456,'parent_pid':123,'invocation':c.INVOCATION,'scientific_protocol_settings_changed':False,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA}}


class Matrix:
    shape=(2,3)
    dtype=SimpleNamespace(kind='f',itemsize=8,isnative=True,hasobject=False)
    def __init__(self):self.bits=struct.pack('<6d',1.,2.,3.,4.,5.,-0.);self.casts=[]
    def astype(self,dtype):self.casts.append(dtype);return self
    def tobytes(self,*,order):assert order=='C';return self.bits


class Archive:
    files=['features']
    def __init__(self,matrix):self.matrix=matrix
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def __getitem__(self,key):assert key=='features';return self.matrix


class Cases(unittest.TestCase):
    def test_source_admission_is_acyclic_and_keeps_scientific_hashes_stable(self):
        record,manifest=source_record();c.source_admission_contract(record,'1'*64,manifest)
        for field in ('run_admission_sha256','caller_birth_sha256','static_root_binding_sha256','request_sha256'):
            changed=dict(record);changed[field]='0'*64
            with self.subTest(field=field),self.assertRaises(AssertionError):c.source_admission_contract(changed,'1'*64,manifest)
        record['stable_scientific_source_bindings']['fit_source_manifest_sha256']='0'*64
        with self.assertRaises(AssertionError):c.source_admission_contract(record,'1'*64,manifest)

    def test_run_admission_forbids_CORE_fit_extra_inputs_and_changed_saved_data(self):
        c.run_contract(run_record(),'1'*64)
        for field in ('CORE_read_authorized','model_fitting_authorized'):
            record=run_record();record[field]=True
            with self.subTest(field=field),self.assertRaises(AssertionError):c.run_contract(record,'1'*64)
        record=run_record();record['input_pins'][c.LABEL_CERTIFICATE]='0'*64
        with self.assertRaises(AssertionError):c.run_contract(record,'1'*64)

    def test_exact_original_NPZ_load_feature_astype_and_C_byte_contract(self):
        raw=b'invented_npz';matrix=Matrix();archive=Archive(matrix);calls=[]
        np=SimpleNamespace(ndarray=Matrix,load=lambda stream,**kw:(calls.append(kw) or archive),
            isfinite=lambda value:SimpleNamespace(all=lambda:True))
        cert={'actual_npz_sha256':c.sha(raw),'rows':2,'columns':3,'same_allele_feature_bytes_equal':True,
              'underlying_report':{'post_original_astype_float_C_bytes_sha256':c.sha(matrix.bits)}}
        with patch.object(c,'SHAPE',(2,3)),patch.object(c,'NPZ_SHA',c.sha(raw)),patch.object(c,'ARRAY_CAST_SHA',c.sha(matrix.bits)),\
             patch.object(inputs.guard,'fresh_gate'):
            self.assertIs(inputs.matrix_from_bytes(np,raw,cert),matrix)
            self.assertEqual(calls,[{'allow_pickle':False}]);self.assertEqual(matrix.casts,[float])
            matrix.bits=struct.pack('<6d',1.,2.,3.,4.,5.,0.)
            with self.assertRaises(AssertionError):inputs.matrix_from_bytes(np,raw,cert)

    def test_wrong_NPZ_hash_stops_before_native_load(self):
        np=SimpleNamespace(load=lambda *args,**kw:self.fail('No native call'))
        with self.assertRaises(AssertionError):inputs.matrix_from_bytes(np,b'invented wrong bytes',{})

    def test_persisted_labels_repack_exact_signed_zero_bits_without_CORE_parser(self):
        ids=['one','two'];values=[.125,-0.];bits=c.sha(struct.pack('<2d',*values))
        bundle={'metadata':{'rows':[{'intervention_id':value} for value in ids]}}
        fields={'generation_manifest_sha256':'1'*64,'run_admission_sha256':'2'*64,'birth_sha256':'3'*64,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA}
        label={'status':'PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT',**fields,'metadata_bundle_sha256':c.METADATA_SHA,
            'array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,'array_supervisor_sha256':c.ARRAY_SUPERVISOR_SHA,
            'resource_exception_applies':True,'original_resource_guards_unchanged':False,'models_fitted':0,'actual_feature_reads':0,
            'label_access_does_not_authorize_fitting':True,'labels_result':{'intervention_ids':ids,'numeric_outcome_rows_admitted':2,
                'parser':c.labels.PARSER,'original_truth_orientation':True,'old_interpreter_bitwise_parity_established':False,
                'measured_delta':values,'parsed_effects_float64_sha256':bits}}
        saved={'status':'PASS_EXACT_LABELS_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT','failure':None,
            'certificate_sha256':c.LABEL_CERTIFICATE_SHA,**fields,'model_fits':0,'numerical_outcomes_admitted':2}
        with patch.object(c,'COUNT',2),patch.object(c,'ROW_IDS_SHA',c.sha(b'one|two')),patch.object(c,'LABEL_BITS_SHA',bits):
            self.assertEqual(inputs.persisted_label_contract(bundle,label,saved),ids)
            label['labels_result']['measured_delta'][1]=0.
            with self.assertRaises(AssertionError):inputs.persisted_label_contract(bundle,label,saved)

    def test_true_prefit_preserves_every_original_field_and_pool_binding(self):
        doc=old_document();original=copy.deepcopy(doc)
        with patch.object(lc,'COUNTS',doc['counts']):actual=build.actual_prefit_document(doc,provenance())
        self.assertTrue(actual['resource_exception_applies']);self.assertEqual(doc,original)
        self.assertEqual(set(actual)-set(doc),{'prefit_execution'})
        self.assertEqual(actual['source_pools'],doc['source_pools'])
        for key in doc:
            if key!='resource_exception_applies':self.assertEqual(lc.canonical_bytes(actual[key]),lc.canonical_bytes(doc[key]))

    def test_original_scientific_mask_mutation_rejects_before_prefit_copy(self):
        doc=old_document();next(iter(doc['source_pools'].values()))['training_ids'].reverse()
        with patch.object(lc,'COUNTS',doc['counts']),self.assertRaises(AssertionError):build.actual_prefit_document(doc,provenance())

    def test_terminal_true_prefit_checks_dynamic_proofs_context_and_calibration(self):
        doc=old_document()
        with patch.object(lc,'COUNTS',doc['counts']),patch.object(c,'ROW_IDS_SHA',lc.id_hash(doc['all_row_ids'])),\
             patch.object(c,'read_run',return_value=run_record()):
            actual=build.actual_prefit_document(doc,provenance());w.validate_prefit(actual,'1'*64,'9'*64,'8'*64)
            for kind in ('resource','stable','worker','phase','proof','input'):
                item=copy.deepcopy(actual)
                if kind=='resource':item['resource_exception_applies']=False
                if kind=='stable':item['prefit_execution']['stable_admitted_runtime_binding_sha256']='0'*64
                if kind=='worker':item['prefit_execution']['resource_calibration']['current_pid']=999
                if kind=='phase':item['prefit_execution']['runtime_acceptance_after_prefit']['phase']='after_labels'
                if kind=='proof':item['prefit_execution']['protected_current_provenance_sha256']='0'*64
                if kind=='input':item['input_admission_bindings']['fit_source_manifest_sha256']='0'*64
                with self.subTest(kind=kind),self.assertRaises(AssertionError):w.validate_prefit(item,'1'*64,'9'*64,'8'*64)

    def test_full_parent_completion_pair_binds_exact_processes_rows_and_label_bits(self):
        doc=old_document();row_sha=lc.id_hash(doc['all_row_ids'])
        completion={'status':'PASS_EXACT_NINE_POOL_PREFIT_WORKER_CALLBACKS_RESTORED','invocation':c.INVOCATION,
            'generation_manifest_sha256':'1'*64,'run_admission_sha256':'9'*64,'birth_sha256':'8'*64,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
            'parent_pid':123,'worker_pid':456,'callbacks_restored':True,'fresh_calibrated_guard_calls':10,'source_pools_prepared':9,
            'optimizer_calls':0,'campaign_started':False,'CORE_reread':False,'saved_label_bits_sha256':c.LABEL_BITS_SHA,
            'all_row_ids_sha256':row_sha,'source_mode':{},'resource_policy':c.resource_policy(),'prefit_sha256':'f'*64}
        with patch.object(lc,'COUNTS',doc['counts']),patch.object(c,'ROW_IDS_SHA',row_sha),\
             patch.object(c,'read_run',return_value=run_record()),patch.object(c,'source_mode',return_value={}):
            actual=build.actual_prefit_document(doc,provenance())
            self.assertIs(supervisor.terminal_pair(completion,actual,'1'*64,'9'*64,'8'*64,123,456),actual)
            for field,value in (('worker_pid',999),('saved_label_bits_sha256','0'*64),('source_pools_prepared',8),('optimizer_calls',1)):
                changed=dict(completion);changed[field]=value
                with self.subTest(field=field),self.assertRaises(AssertionError):
                    supervisor.terminal_pair(changed,actual,'1'*64,'9'*64,'8'*64,123,456)

    def test_exact_nine_pool_adapter_and_sampler_factory_forwarding(self):
        doc=old_document();sampler=object.__new__(build.original_sampler.GuardedSampler);sampler.identity={'invented_sampler_identity':True}
        pools={key:{'binding':value} for key,value in doc['source_pools'].items()}
        prepared=build.adapter.PreparedPools([],pools,doc)
        data={'metadata':[],'features':object(),'effects':{},'admissions':{}}
        with patch.object(lc,'COUNTS',doc['counts']),patch.object(build.guard,'fresh_gate'),\
             patch.object(build.original_sampler,'load_original_sampler',return_value=sampler) as factory,\
             patch.object(build.adapter,'prepare_pools',return_value=prepared) as adapter,\
             patch.object(build.adapter.original,'pool_binding',side_effect=lambda np,pool:pool['binding']) as rebound:
            result,identity=build.prepare_original_pools(object(),object(),data,{'runtime_acceptance_after_array':{'stable_anchor_only':True}})
            self.assertIs(result,prepared);self.assertIs(identity,sampler.identity);self.assertEqual(rebound.call_count,9)
            self.assertEqual(factory.call_args.kwargs,{'root_start':True});self.assertEqual(adapter.call_count,1)
            self.assertEqual(adapter.call_args.kwargs['admissions'],data['admissions'])

    def test_guard_alias_transaction_bodies_and_caps_unchanged(self):
        from src.generalization_knowncell_labels_execution_v2_20261024 import calibration as oldcal
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(path).read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef)}
        oldf,newf=functions(oldcal.__file__),functions(cal.__file__)
        for name in ('_snapshot','_installed','_plain_copy','_annotated_copy','_source_module'):
            self.assertEqual(oldf[name],newf[name])
        self.assertEqual(cal.TARGETS,oldcal.TARGETS);self.assertEqual(c.PROCESS_CAP,768*2**20);self.assertEqual(c.JOB_CAP,896*2**20)
        self.assertEqual(c.resource_policy()['startup_commit_headroom'],1920*2**20)

    def test_fixed_calibration_scope_and_controller_module(self):
        with patch.object(cal.importlib,'import_module') as imported:
            imported.return_value=SimpleNamespace(admit_authorization=lambda value:(_ for _ in ()).throw(FileNotFoundError('future source admission')))
            with self.assertRaises(FileNotFoundError):
                with cal.calibrated('prefit','1'*64,{}):self.fail('No actual guard context')
            imported.assert_called_once_with('src.'+c.NS+'.common')
        self.assertIn('src.'+c.NS+'.worker',supervisor.command('1'*64,'9'*64,'8'*64))

    def test_partial_outputs_reject_without_probe_or_worker(self):
        with patch.object(c.os.path,'lexists',side_effect=lambda path:path==c.OUTPUT),self.assertRaises(AssertionError):c.require_new_outputs()

    def test_runtime_binding_uses_generation_manifest_not_literal_or_live_values(self):
        from src.generalization_knowncell_prefit_runtime_20261024.tests import request
        req=request();manifest={'files':{c.runtime.PREPARATION:'b'*64,c.runtime.SOURCE:'e'*64}}
        self.assertEqual(w.runtime_binding(req,'a'*64,manifest)['provider_preparation_manifest_sha256'],'b'*64)
        req['provider_preparation_manifest_sha256']='0'*64
        with self.assertRaises(AssertionError):w.runtime_binding(req,'a'*64,manifest)


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    def clean():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean() and not c.RUN_ADMISSION.exists() and not c.SOURCE_ADMISSION.exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    c.save_new(c.OUT/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_PREFIT_EXECUTION_NOT_INPUT_POOL_OR_FIT_ADMISSION',
        'tests':result.testsRun,'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_jobs':0,'actual_resource_probes':0,'actual_provider_invocations':0,'project_payload_reads':0,
        'actual_pools_prepared':0,'optimizer_calls':0,'scientific_imports':False,
        'numeric_pool_and_runtime_edges_in_tests_are_private_mocks':True,'scientific_mask_fixture_counts_test_only':True})


if __name__=='__main__':run()
