"""Invented pure portability tests; no numerical import, data or real guard."""
import ast
import copy
import struct
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import contracts as c,spec,plan,inputs,current,context,science,sampler
from src.generalization_knowncell_joint_campaign_20261023 import contracts as legacy
from src.generalization_knowncell_prefit_execution_20261024.tests import old_document
from src.generalization_knowncell_prefit_projection_v2_20261024 import projection as historical_v2


class Matrix:
    def __init__(self,bits):
        self.bits=bits;self.shape=(6,2)
        self.dtype=SimpleNamespace(kind='f',itemsize=8,isnative=True,hasobject=False)
    def tobytes(self,order):assert order=='C';return self.bits


def fixture():
    old=old_document();ids=old['all_row_ids']
    rows=[{'intervention_id':name,'parent_sequence':'AAAA'+str(i%3),'mutant_sequence':'AAAC'+str(i%3)} for i,name in enumerate(ids)]
    values=[.125,-0.,.25,-.5,.625,.75]
    bits=struct.pack('<12d',*[value for i in range(6) for value in (float(i%3),2.)])
    matrix=Matrix(bits);label_bits=c.pack_labels(ids,values)
    bundle={'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION','metadata':{'rows':rows}}
    array={'status':'PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY','rows':6,'columns':2,
        'same_allele_feature_bytes_equal':True,'original_row_ids_sha256':legacy.id_hash(ids),
        'underlying_report':{'post_original_astype_float_C_bytes_sha256':c.digest(bits)}}
    labels={'status':'PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT','labels_result':{
        'intervention_ids':ids,'numeric_outcome_rows_admitted':6,'original_truth_orientation':True,
        'old_interpreter_bitwise_parity_established':False,'measured_delta':values,
        'parsed_effects_float64_sha256':c.digest(label_bits)}}
    raws={key:c.canonical(value) for key,value in (('metadata',bundle),('array',array),('labels',labels))}
    data_pins={key:c.digest(raw) for key,raw in raws.items()}
    admissions={**spec.STABLE_SCIENTIFIC_BINDINGS,'status':'ADMITTED_MIKL_METADATA_SIMPLE102_ORIGINAL_EFFECTS',
        'runtime_binding_sha256':spec.HISTORICAL_ARRAY_ANCHOR,'metadata_admission_sha256':'1'*64,
        'feature_admission_sha256':data_pins['array'],'label_admission_sha256':data_pins['labels'],
        'original_sampler_source_sha256':'2'*64,'input_row_ids_sha256':legacy.id_hash(ids),'input_metadata_sha256':'3'*64,
        'input_features_sha256':c.digest(c.canonical({'shape':[6,2],'dtype':'float64','order':'C'})+bits),
        'input_effects_sha256':c.digest(c.canonical({'shape':[6],'dtype':'float64','order':'C'})+label_bits)}
    old.update(runtime_binding_sha256=spec.HISTORICAL_ARRAY_ANCHOR,input_admission_bindings=admissions,
        feature_admission_sha256=data_pins['array'],label_admission_sha256=data_pins['labels'])
    actual=copy.deepcopy(old);actual.update(resource_exception_applies=True,prefit_execution={'invented_historical':True})
    raws['prefit']=c.canonical(actual)
    admission={'status':plan.old_schema.ADMISSION_STATUS,'schema_version':1,
        'prefit_relative_path':'results/invented/prefit.json','prefit_commit':'a'*40,'prefit_sha256':c.digest(raws['prefit']),
        'runtime_binding_sha256':spec.HISTORICAL_ARRAY_ANCHOR,'projection_source_manifest_sha256':spec.PROJECTION_SOURCE_SHA,
        'approved_policy_manifest_sha256':spec.HISTORICAL_POLICY_SHA,'authorization_sha256':spec.HISTORICAL_AUTH_SHA,
        'approval_scope_sha256':spec.HISTORICAL_SCOPE_SHA,'prefit_owner_receipt_sha256':'4'*64,
        'input_admission_bindings_sha256':legacy.hash_value(admissions),'additional_top_level_provenance_fields':['prefit_execution'],
        'scientific_settings_changed':False,'permitted_projection':dict(plan.old_schema.PROJECTION),'actual_stage_authority_granted_here':False}
    raws['projection']=c.canonical(admission)
    reference={'status':'FROZEN_HISTORICAL_SCIENTIFIC_REFERENCE_NOT_CURRENT_RUNTIME_ADMISSION',
        'file_sha256':{key:c.digest(raw) for key,raw in raws.items()},
        'actual_prefit_relative_path':admission['prefit_relative_path'],'actual_prefit_commit':'a'*40,
        'projection_admission_relative_path':'results/invented/root.json','projection_admission_commit':'b'*40,
        'historical_runtime_anchor_sha256':spec.HISTORICAL_ARRAY_ANCHOR,
        'historical_native_profile_origin_sha256':spec.HISTORICAL_PROFILE_ORIGIN,'input_authority_granted_here':False}
    return old,actual,admission,reference,raws,matrix,data_pins


class Cases(unittest.TestCase):
    def setUp(self):
        self.data=fixture();old,actual,admission,reference,raws,matrix,data_pins=self.data
        self.patches=[patch.object(legacy,'COUNTS',old['counts']),patch.object(spec,'ROW_COUNT',6),
            patch.object(spec,'FEATURE_WIDTH',2),patch.object(spec,'ROW_IDS_SHA',legacy.id_hash(old['all_row_ids'])),
            patch.object(spec,'DATA_PINS',data_pins),patch.object(spec,'FEATURE_BYTES_SHA',c.digest(matrix.bits)),
            patch.object(spec,'LABEL_BITS_SHA',c.digest(c.pack_labels(old['all_row_ids'],[.125,-0.,.25,-.5,.625,.75])))]
        for item in self.patches:item.start();self.addCleanup(item.stop)

    def historical(self):
        *_,reference,raws,matrix,pins=self.data
        return plan.from_supplied(raws['prefit'],raws['projection'],c.canonical(reference))

    def new_plan(self):
        historical=self.historical();document=copy.deepcopy(historical.actual_document())
        document.pop('prefit_execution')
        document['input_admission_bindings']=plan.current_admission_references(document['input_admission_bindings'])
        document['runtime_binding_sha256']=legacy.hash_value(plan.current_epoch_reference())
        document['current_execution']={'current_software_epoch_reference':plan.current_epoch_reference(),
            'historical_reference_sha256':c.digest(historical.historical_reference_raw),
            'status':'INVENTED_PURE_CANDIDATE_NOT_ACTUAL_OWNER','actual_stage_authority_granted_here':False}
        raw=c.canonical(document)
        return plan.CurrentScientificPlan('results/invented/current_prefit.json','c'*40,raw,c.digest(raw),
            document['runtime_binding_sha256'],historical)

    def test_current_epoch_uses_new_evidence_without_old_current_claim(self):
        value=plan.current_epoch_reference()
        self.assertNotEqual(legacy.hash_value(value),spec.HISTORICAL_ARRAY_ANCHOR)
        self.assertEqual(value['current_profile_receipt_sha256'],spec.PROFILE_RECEIPT_SHA)
        declaration=context.CurrentExecutionContext('1'*64,'2'*64).declaration()
        self.assertFalse(declaration['current_software_identity']['actual_current_process_native_origins_verified_here'])
        self.assertFalse(declaration['current_owned_execution']['actual_stage_authority_granted'])

    def test_historical_identity_matches_pure_old_V2_but_grants_no_authority(self):
        historical=self.historical();_,_,admission,reference,raws,*_=self.data
        old_context={'status':plan.old_schema.CONTEXT_STATUS,'root_admission_relative_path':reference['projection_admission_relative_path'],
            'root_admission_commit':'b'*40,'root_admission_sha256':c.digest(raws['projection']),
            'prefit_sha256':c.digest(raws['prefit']),'current_runtime_binding_sha256':spec.HISTORICAL_ARRAY_ANCHOR,
            'projection_source_manifest_sha256':spec.PROJECTION_SOURCE_SHA,'approved_policy_manifest_sha256':spec.HISTORICAL_POLICY_SHA,
            'authorization_sha256':spec.HISTORICAL_AUTH_SHA,'approval_scope_sha256':spec.HISTORICAL_SCOPE_SHA,
            'prefit_owner_receipt_sha256':'4'*64,'current_owner_receipt_sha256':'5'*64,
            'input_admission_bindings_sha256':admission['input_admission_bindings_sha256'],
            'actual_owner_resource_runtime_and_source_closure_verified':True,'actual_stage_authority_granted_by_this_library':False}
        # Pure invented declaration comparison only; no old authoritative binder.
        old=historical_v2.CalibratedBoundPlan(historical.prefit_relative_path,'a'*40,raws['prefit'],c.digest(raws['prefit']),
            spec.HISTORICAL_ARRAY_ANCHOR,raws['projection'],legacy.canonical_bytes(old_context))
        self.assertEqual(legacy.canonical_bytes(historical.identity()),legacy.canonical_bytes(old.identity()))
        self.assertFalse(historical.historical_descriptor()['actual_stage_authority_granted_here'])

    def test_current_operational_plan_differs_but_all_nine_scientific_pools_match(self):
        value=self.new_plan();historical=value.historical_plan
        self.assertIsInstance(value,legacy.BoundPlan)
        self.assertNotEqual(value.prefit_sha256,historical.prefit_sha256)
        self.assertNotEqual(value.identity(),historical.identity())
        self.assertEqual(plan.scientific_projection(value.document()),plan.scientific_projection(historical.document()))
        self.assertTrue(value.stable_scientific_identity()['all_nine_scientific_pool_bindings_equal'])
        self.assertEqual(len(value.document()['source_pools']),9)
        self.assertEqual(value.actual_document()['input_admission_bindings']['native_profile_receipt_sha256'],spec.PROFILE_RECEIPT_SHA)

    def test_changed_pool_masks_features_labels_or_scaling_cannot_make_current_plan(self):
        value=self.new_plan()
        for field in ('training_features_sha256','training_effects_sha256','common_scaling_sha256','original_pair_roster_sha256'):
            document=value.actual_document();key=next(iter(document['source_pools']))
            document['source_pools'][key][field]='f'*64;raw=c.canonical(document)
            with self.subTest(field=field),self.assertRaises(AssertionError):
                plan.CurrentScientificPlan(value.prefit_relative_path,'c'*40,raw,c.digest(raw),value.runtime_binding_sha256,value.historical_plan)

    def test_old_operational_epoch_cannot_be_presented_as_new(self):
        value=self.new_plan();document=value.actual_document();document['runtime_binding_sha256']=spec.HISTORICAL_ARRAY_ANCHOR
        raw=c.canonical(document)
        with self.assertRaises(AssertionError):plan.CurrentScientificPlan(value.prefit_relative_path,'c'*40,raw,c.digest(raw),spec.HISTORICAL_ARRAY_ANCHOR,value.historical_plan)

    def test_supplied_labels_feature_bits_and_exact_row_order(self):
        _,_,_,reference,raws,matrix,_=self.data
        result=inputs.validate_supplied(SimpleNamespace(ndarray=Matrix),matrix,raws,c.canonical(reference))
        self.assertIs(result['features'],matrix)
        self.assertEqual(list(result['effects']),result['plan'].actual_document()['all_row_ids'])
        self.assertFalse(result['historical_input_report']['actual_stage_authority_granted_here'])
        matrix.bits=struct.pack('<12d',*[0.]*12)
        with self.assertRaises(AssertionError):inputs.validate_supplied(SimpleNamespace(ndarray=Matrix),matrix,raws,c.canonical(reference))

    def test_raw_input_repair_or_extra_live_field_is_not_historical_reference(self):
        _,_,_,reference,raws,matrix,_=self.data
        bad=dict(raws);bad['labels']=raws['labels']+b' '
        with self.assertRaises(AssertionError):inputs.validate_supplied(SimpleNamespace(ndarray=Matrix),matrix,bad,c.canonical(reference))
        bad=copy.deepcopy(reference);bad['current_native_identity_passes']=True
        with self.assertRaises(AssertionError):c.reference_contract(bad)

    def test_signed_zero_and_nonfinite_or_integer_labels(self):
        self.assertNotEqual(c.pack_labels(['x'],[-0.]),c.pack_labels(['x'],[0.]))
        for values in ([0],[float('inf')],[float('nan')]):
            with self.subTest(values=repr(values)),self.assertRaises(AssertionError):c.pack_labels(['x'],values)

    def test_rebinding_keeps_actual_pool_objects_and_rejects_mutation(self):
        value=self.new_plan();doc=value.document();doc.pop('current_execution')
        pools={key:{'binding':copy.deepcopy(binding)} for key,binding in doc['source_pools'].items()}
        prepared=plan.PreparedPools([],pools,doc)
        rebound=plan.rebind_current_prepared(value,prepared)
        self.assertIs(rebound.pools,pools);self.assertIs(rebound.metadata,prepared.metadata)
        pools[next(iter(pools))]['binding']['prepared_z_sha256']='f'*64
        with self.assertRaises(AssertionError):plan.rebind_current_prepared(value,prepared)

    def test_scientific_delegates_are_exact_original_objects(self):
        from src.generalization_knowncell_joint_engine_20261023 import adapter_v2
        from src.generalization_knowncell_joint_runner_20261023.runner import run_campaign
        from src.generalization_knowncell_joint_evaluation_20261023.evaluation import evaluate
        values=science.deferred_scientific_objects()
        self.assertIs(values['prepare_pools'],adapter_v2.prepare_pools)
        self.assertIs(values['selector'],adapter_v2.select_outer);self.assertIs(values['runner'],run_campaign)
        self.assertIs(values['evaluator'],evaluate)
        self.assertNotIn('sampler_factory',values)
        self.assertEqual(sum(t['optimizer_units'] for t in legacy.task_roster()),84)
        self.assertEqual(len(legacy.task_roster()),63)

    def test_new_compile_factory_reuses_exact_AST_wrapper_without_old_runtime_contract(self):
        old=sampler.original
        model=(spec.ROOT/old.MODEL_SOURCE).read_bytes();common=(spec.ROOT/old.COMMON_SOURCE).read_bytes();np=object()
        with patch.object(old,'load_original_sampler',side_effect=AssertionError('Forbidden old factory')),\
             patch.object(old.c,'runtime_contract',side_effect=AssertionError('Forbidden old current proof')):
            handle=sampler._compile_supplied(np,model,common,'a'*64)
        self.assertIsInstance(handle,old.GuardedSampler)
        self.assertIs(handle._np,np);self.assertEqual(handle._cache,{})
        self.assertFalse(handle.identity['old_sampler_runtime_contract_called'])
        self.assertNotIn(old.ORIGINAL_MODULE,sys.modules)

    def test_actual_FIT_and_sampler_entries_fail_before_IO_imports_or_aliases(self):
        with patch.object(current,'_bound',side_effect=AssertionError('No IO')) as read:
            for action in (lambda:science.run_current_fixed_fit({'all_flags':True}),
                    lambda:sampler.load_current_sampler(object(),{'invented_native_PASS':True}),
                    lambda:context.CurrentExecutionContext('a'*64,'b'*64).require_fit_authority()):
                with self.assertRaises(current.PendingCurrentContext):action()
            read.assert_not_called()

    def test_pure_JSON_paths_hashes_and_source_has_no_old_authoritative_calls(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":1e999}'):
            with self.assertRaises((AssertionError,ValueError)):c.decode(raw)
        for key in ('../outside','C:/outside','a\\b','a//b'):
            with self.assertRaises(AssertionError):c.relative(key)
        for path in (spec.ROOT/'src'/spec.NS).glob('*.py'):
            if path.name=='tests.py':continue
            tree=ast.parse(path.read_text())
            calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
            for call in calls:
                self.assertFalse(isinstance(call.func,ast.Attribute) and call.func.attr in
                    ('admit_authorization','load_original_sampler','runtime_contract','bind_calibrated_plan'),str(path))
        self.assertEqual(spec.ROOT.drive.casefold(),'c:')


def run(*,reviewed=False):
    assert type(reviewed) is bool
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    spec.OUT.mkdir(parents=True,exist_ok=True)
    value={'status':'PASS_INVENTED_PURE_CURRENT_CONTEXT_PROTOTYPE_NOT_RUNTIME_OR_FIT_ADMISSION','tests':result.testsRun,
        'sources':{p.relative_to(spec.ROOT).as_posix():c.digest(p.read_bytes()) for p in (spec.ROOT/'src'/spec.NS).glob('*.py')},
        'actual_data_or_model_reads':0,'actual_resource_native_or_owner_probes':0,'scientific_imports':False,
        'actual_jobs_fits_replays_evaluations':0,'authority_records_created':0,'only_C_workspace_used':True,
        'current_owned_controller_and_FIT_integration':'NOT_IMPLEMENTED_FAIL_CLOSED'}
    name='synthetic_tests_receipt_reviewed.json' if reviewed else 'synthetic_tests_receipt.json'
    with (spec.OUT/name).open('xb') as stream:stream.write(c.canonical(value))


if __name__=='__main__':run()
