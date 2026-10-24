"""Invented array/vector doubles and source AST only; no numerical imports."""
import ast
from contextlib import ExitStack,contextmanager
from datetime import datetime,timezone
import copy
import hashlib
import math
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import contracts as c,sampler as s,bridge as b
from .spec import *


class NativeArray:
    def __init__(self,values):
        self.values=copy.deepcopy(values);self.events=[]
        self.shape=(len(values),len(values[0])) if values and isinstance(values[0],list) else (len(values),)
        self.dtype=SimpleNamespace(kind='f',itemsize=8,isnative=True,hasobject=False)
    def flat(self):return [value for row in self.values for value in row] if len(self.shape)==2 else self.values
    def tobytes(self,*,order):
        assert order=='C';self.events.append('tobytes_C')
        return b''.join(struct.pack('<d',value) for value in self.flat())
    def tolist(self):self.events.append('tolist');return copy.deepcopy(self.values)


class NumpyDouble:
    __name__='numpy';__version__='1.26.4';__file__=str(NUMPY_PATH);ndarray=NativeArray
    @staticmethod
    def isfinite(value):return SimpleNamespace(all=lambda:all(math.isfinite(x) for x in value.flat()))


NP=NumpyDouble()


def proof():
    return {'status':PROVIDER_STATUS,'phase':'after_array','invented_only':False,
        'provider_opened_project_array':False,'fresh_current_python_and_loaded_native_origins_checked':True,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_SHA,
        'actual_origin_receipt_sha256':V4_ORIGIN_SHA,'same_owned_software_objects_retained':True,
        'numpy_module_path':str(NUMPY_PATH),'numpy_module_sha256':NUMPY_SHA,'numpy_version':'1.26.4',
        'request_binding':{'request_relative_path':'results/generalization_knowncell_array_admission_20261023/array_request_manifest.json',
            'request_sha256':'1'*64,'provider_preparation_manifest_sha256':'2'*64,
            'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_SHA}}


def source_function():
    # Source text only: no import of either old module/common.
    return (ROOT/MODEL_SOURCE).read_bytes(),(ROOT/COMMON_SOURCE).read_bytes()


class SamplerTests(unittest.TestCase):
    def factory(self):
        model,common=source_function()
        def source(name,want):
            raw=model if name==MODEL_SOURCE else common;self.assertEqual(c.digest(raw),want);return raw
        with patch.object(c,'fresh'),patch.object(c,'source_bytes',side_effect=source),\
             patch.object(c.guard,'guarded_bytes',return_value=b'invented wrapper source'),patch.object(c,'committed_bytes'):
            return s.load_original_sampler(NP,proof(),root_start=True)

    def test_exact_function_AST_seed_and_globals_without_old_module_import(self):
        before=set(sys.modules);handle=self.factory();model,common=source_function()
        node,identity=s.extract_function(model,common)
        original=next(node for node in ast.parse(model).body if isinstance(node,ast.FunctionDef) and node.name=='pair_indices')
        self.assertEqual(ast.dump(node,include_attributes=False),ast.dump(original,include_attributes=False))
        self.assertEqual(identity['original_model_source_sha256'],MODEL_SHA)
        self.assertEqual(identity['original_common_source_sha256'],COMMON_SHA)
        self.assertEqual(handle.__module__,ORIGINAL_MODULE);self.assertEqual(handle.__name__,'pair_indices')
        scope=handle._original.__globals__
        self.assertIs(scope['np'],NP);self.assertIs(scope['hashlib'],hashlib)
        self.assertEqual(scope['SEED'],20260927);self.assertEqual(scope['PAIR_CACHE'],{})
        self.assertTrue(handle.identity['wrapper_is_new_bridge_code_not_original_function'])
        self.assertFalse(handle.identity['original_algorithm_native_parity_certified_here'])
        self.assertNotIn(ORIGINAL_MODULE,set(sys.modules)-before)
        self.assertNotIn('src.cross_assay_20260927.common',set(sys.modules)-before)

    def test_original_cache_path_returns_unchanged_roster_and_still_guards(self):
        handle=self.factory();raw=struct.pack('<2d',-1.,1.)
        frame=SimpleNamespace(intervention_id=['invented_a','invented_b'],
            measured_delta=SimpleNamespace(to_numpy=lambda dtype:SimpleNamespace(tobytes=lambda:raw)))
        key=hashlib.sha256(b'invented_a|invented_b'+raw).hexdigest();sentinel=object()
        handle._cache[key]=sentinel;events=[]
        with patch.object(c,'fresh',side_effect=lambda:events.append('actual_gate')):
            self.assertIs(handle(frame),sentinel)
        self.assertEqual(events,['actual_gate','actual_gate'])

    def test_low_resource_failure_precedes_original_call_and_poisons_handle(self):
        handle=self.factory()
        class NoAccess:
            @property
            def intervention_id(self):raise RuntimeError('sampler must not run')
        def reject():
            from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
            require_resources({'physical_available':3*2**30-1,'disk_available':2**30},
                {key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
        with patch.object(c,'fresh',side_effect=reject):
            with self.assertRaisesRegex(AssertionError,'three-GiB'):handle(NoAccess())
        with patch.object(c,'fresh',side_effect=RuntimeError('no retry')):
            with self.assertRaisesRegex(AssertionError,'cannot resume'):handle(NoAccess())

    def test_guard_rejects_changed_original_global_without_call(self):
        handle=self.factory();handle._original.__globals__['SEED']=0
        with patch.object(c,'fresh'):
            with self.assertRaises(AssertionError):handle(object())

    def test_only_function_is_compiled_top_level_statements_never_run(self):
        model,common=source_function();model+=b'\nraise RuntimeError("must not execute module")\n'
        node,_=s.extract_function(model,common);scope={'__name__':ORIGINAL_MODULE}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'invented_extraction','exec'),scope)
        self.assertEqual(scope['pair_indices'].__module__,ORIGINAL_MODULE)

    def test_seed_duplicate_function_and_nonempty_cache_changes_rejected(self):
        model,common=source_function()
        for changed_model,changed_common in ((model,common.replace(b'SEED=20260927',b'SEED=1')),
            (model+b'\ndef pair_indices(frame):\n return None\n',common),
            (model.replace(b'PAIR_CACHE={}',b'PAIR_CACHE={"extra":1}'),common)):
            with self.assertRaises(AssertionError):s.extract_function(changed_model,changed_common)

    def test_factory_requires_root_before_any_resource_or_source_access(self):
        with patch.object(c,'fresh',side_effect=RuntimeError('must not probe')):
            with self.assertRaises(AssertionError):s.load_original_sampler(NP,proof())


def fixture():
    rows=[];values=[];features=[]
    for fold in (0,1,2):
        for cell in ('CAD','Neuro-2a'):
            for edit,value in enumerate((-0.0,1.0)):
                rows.append({'intervention_id':f'invented:{fold}:{cell}:{edit}','dataset':'mikl_gse173098',
                    'cell_type':cell,'endpoint_class':'projection','parent_context_id':f'invented:{fold}:{cell}',
                    'biological_component':f'invented_g{fold}','gene_transcript':f'invented_g{fold}',
                    'held_parent_fold':fold,'parent_sequence':f'invented_parent{fold}',
                    'mutant_sequence':f'invented_mutant{fold}_{edit}'})
                values.append(value);features.append([value]+[0.0]*101)
    small={'all_rows':12,'CAD_rows':6,'Neuro-2a_rows':6,'components':3,'paired_menus':3,
        'paired_contexts':6,'paired_rows':12,'paired_directional_decisions':12,'unmatched_contexts':0,'unmatched_rows':0}
    with patch.object(b.reference,'COUNTS',small):contract=b.reference.full_metadata_contract(rows)
    rowsha=b.reference.ids_sha(rows);matrix=NativeArray(features);vector=NativeArray(values)
    bundle={'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION','numeric_outcome_rows_admitted':0,
        'actual_feature_reads':0,'models_fitted':0,'metadata_admission_sha256':'3'*64,'core_sha256':CORE_SHA,
        'declared_simple102_sha256_not_loaded':NPZ_SHA,'metadata':{'rows':rows,'row_ids_sha256':rowsha},'contract':contract}
    bundle_raw=c.canonical(bundle);runtime=proof()
    array={'status':ARRAY_STATUS,'actual_npz_sha256':NPZ_SHA,'metadata_bundle_sha256':c.digest(bundle_raw),
        'rows':12,'columns':102,'same_allele_feature_bytes_equal':True,'original_row_ids_sha256':rowsha,
        'numeric_labels_admitted':False,'FIT_admission_granted':False,'models_fitted':0,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_SHA,
        'runtime_acceptance_after_array':runtime,'array_request_sha256':runtime['request_binding']['request_sha256'],
        'underlying_report':{'post_original_astype_float_C_bytes_sha256':c.digest(matrix.tobytes(order='C')),
            'creation_identity':{'supplied_metadata_sha256':contract['metadata_sha256']}}}
    array_raw=c.canonical(array)
    fit={'namespace':'generalization_knowncell_joint_loader_20261022','mode':'fit_labels',
        'status':'FROZEN_MIKL_MEAN_EFFECT_ADMISSION_JOINT_KNOWNCELL','label_access_authorized':True,
        'model_fitting_authorized':False,'PUM_resource_exception_applies':False,'numerical_threads':1,
        'metadata_bundle_sha256':c.digest(bundle_raw),'array_admission_sha256':c.digest(array_raw),
        'pandas_admission_sha256':PANDAS_SHA,'data_pins':{CORE_PATH:CORE_SHA}}
    fit_raw=c.canonical(fit)
    labels={'fit_label_admission_sha256':c.digest(fit_raw),'metadata_bundle_sha256':c.digest(bundle_raw),
        'pandas_admission_sha256':PANDAS_SHA,'source_core_read':{'actual_sha256':CORE_SHA,
            'fresh_original_resource_gate_before_open':True,'raw_bytes_traversed':123},
        'intervention_ids':[row['intervention_id'] for row in rows],'numeric_outcome_rows_admitted':len(rows),
        'parser':'original_pandas_default_read_csv_low_memory_False_then_to_numpy_float',
        'original_truth_orientation':True,'old_interpreter_bitwise_parity_established':False,
        'pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required':True,
        'actual_feature_reads':0,'models_fitted':0,'label_access_does_not_authorize_fitting':True,
        'measured_delta':vector,'parsed_effects_float64_sha256':c.digest(vector.tobytes(order='C'))}
    expected={name:'4'*64 for name in BINDING_HASHES}
    expected.update(metadata_bundle_sha256=c.digest(bundle_raw),array_certificate_sha256=c.digest(array_raw),
        fit_label_admission_sha256=c.digest(fit_raw),runtime_binding_sha256=c.digest(c.canonical(runtime)),
        native_profile_receipt_sha256=V4_ORIGIN_SHA)
    vector.events.clear();matrix.events.clear()
    return {'rows':rows,'small':small,'bundle_raw':bundle_raw,'matrix':matrix,'array_raw':array_raw,
            'labels':labels,'fit_raw':fit_raw,'expected':expected,'rowsha':rowsha}


@contextmanager
def supplied_fixture(f):
    calls=[]
    def committed(name,raw,want=None):
        if want is not None:assert c.digest(raw)==want
        calls.append(name);return c.digest(raw)
    with ExitStack() as stack:
        stack.enter_context(patch.object(c,'fresh'))
        stack.enter_context(patch.object(c,'committed_bytes',side_effect=committed))
        stack.enter_context(patch.object(b,'COUNTS',{'rows':12,'columns':102}))
        stack.enter_context(patch.object(b,'ROW_IDS_SHA',f['rowsha']))
        stack.enter_context(patch.object(b.reference,'COUNTS',f['small']))
        yield calls


def invoke(f):
    return b.bridge_inputs(NP,f['bundle_raw'],f['matrix'],f['array_raw'],f['labels'],f['fit_raw'],
                           expected_bindings=f['expected'],root_start=True)


class BridgeTests(unittest.TestCase):
    def test_exact_original_tolist_bits_order_and_engine_hashes(self):
        f=fixture()
        with supplied_fixture(f) as calls:result=invoke(f)
        self.assertIs(result['features'],f['matrix']);self.assertEqual(list(result['effects']),f['labels']['intervention_ids'])
        self.assertEqual(f['labels']['measured_delta'].events,['tolist'])
        self.assertEqual(struct.pack('<d',next(iter(result['effects'].values()))),struct.pack('<d',-0.0))
        self.assertEqual(calls,[METADATA_PATH,ARRAY_PATH,FIT_PATH])
        matrix_bytes=f['matrix'].tobytes(order='C')
        self.assertEqual(result['admissions']['input_features_sha256'],c.bits_hash(matrix_bytes,(12,102)))
        values=list(result['effects'].values());raw=b''.join(struct.pack('<d',value) for value in values)
        self.assertEqual(result['admissions']['input_effects_sha256'],c.bits_hash(raw,(12,)))
        self.assertFalse(result['bridge_report']['training_authorized_here'])
        self.assertFalse(result['bridge_report']['committed_prefit_created'])

    def test_missing_extra_reordered_label_ids_are_rejected(self):
        for change in ('missing','extra','reverse'):
            f=fixture();ids=f['labels']['intervention_ids']
            if change=='missing':ids.pop()
            elif change=='extra':ids.append('invented_extra')
            else:ids.reverse()
            with supplied_fixture(f),self.assertRaisesRegex(AssertionError,'ID/order'):invoke(f)

    def test_changed_label_bits_and_unknown_label_types_are_not_coerced(self):
        for value in (2.0,1,True,'1.0',float('nan')):
            f=fixture();f['labels']['measured_delta'].values[0]=value
            with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)

    def test_changed_matrix_bits_and_nonfinite_values_are_rejected(self):
        for value in (3.0,float('nan')):
            f=fixture();f['matrix'].values[0][0]=value
            with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)

    def test_wrong_dtype_shape_or_nonordinary_array_is_rejected(self):
        for change in ('dtype','shape','object'):
            f=fixture()
            if change=='dtype':f['labels']['measured_delta'].dtype.itemsize=4
            elif change=='shape':f['matrix'].shape=(102,12)
            else:f['labels']['measured_delta']=SimpleNamespace(shape=(12,),dtype=f['matrix'].dtype,tolist=lambda:[])
            with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)

    def test_mismatched_metadata_array_software_and_runtime_bindings_rejected(self):
        for key in ('metadata_bundle_sha256','array_certificate_sha256','fit_label_admission_sha256','runtime_binding_sha256'):
            f=fixture();f['expected'][key]='0'*64
            with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)
        f=fixture();f['labels']['pandas_admission_sha256']='0'*64
        with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)

    def test_wrong_parser_orientation_or_permission_rejected(self):
        for key,value in (('parser','replacement_python_float_parser'),('original_truth_orientation',False),
                          ('label_access_does_not_authorize_fitting',False)):
            f=fixture();f['labels'][key]=value
            with supplied_fixture(f),self.assertRaises(AssertionError):invoke(f)

    def test_no_guard_override_or_io_before_root_start(self):
        f=fixture()
        with patch.object(c,'fresh',side_effect=RuntimeError('must not probe')):
            with self.assertRaises(AssertionError):b.bridge_inputs(None,None,None,None,None,None,expected_bindings={})
        self.assertNotIn('probe',__import__('inspect').signature(b.bridge_inputs).parameters)

    def test_actual_resource_contract_is_three_GiB_before_supplied_input_access(self):
        from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
        def reject():return require_resources({'physical_available':3*2**30-1,'disk_available':2**30},
            {key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
        with patch.object(c,'fresh',side_effect=reject):
            with self.assertRaisesRegex(AssertionError,'three-GiB'):
                b.bridge_inputs(None,None,None,None,None,None,expected_bindings={},root_start=True)


class PureContracts(unittest.TestCase):
    def test_fresh_uses_actual_default_guard_no_injected_probe(self):
        with patch.object(c,'source_mode') as mode,patch.object(c.guard,'fresh_gate',return_value={'invented':True}) as gate:
            self.assertEqual(c.fresh(),{'invented':True});mode.assert_called_once_with();gate.assert_called_once_with()

    def test_runtime_proof_old_profile_vs_fresh_binding_distinct_and_wrong_phase_rejected(self):
        value=proof();digest=c.runtime_contract(NP,value);self.assertNotEqual(digest,V4_ORIGIN_SHA)
        for key,changed in (('phase','before_array'),('invented_only',True),('actual_origin_receipt_sha256','0'*64)):
            value=proof();value[key]=changed
            with self.assertRaises(AssertionError):c.runtime_contract(NP,value)

    def test_bits_hash_matches_existing_engine_header_and_preserves_negative_zero(self):
        raw=struct.pack('<2d',-0.0,1.0)
        expected=hashlib.sha256(c.canonical({'shape':[2],'dtype':'float64','order':'C'})+raw).hexdigest()
        self.assertEqual(c.bits_hash(raw,(2,)),expected)
        self.assertNotEqual(c.bits_hash(raw,(2,)),c.bits_hash(struct.pack('<2d',0.0,1.0),(2,)))


def run():
    start=time.perf_counter();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    assert ORIGINAL_MODULE not in sys.modules and 'src.cross_assay_20260927.common' not in sys.modules
    sources=sorted(SRC.glob('*.py'))
    receipt={'status':'PASS_INVENTED_STDLIB_EXACT_SAMPLER_AND_INPUT_BRIDGE','tests':result.testsRun,
        'UTC':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-start,
        'sources':{path.relative_to(ROOT).as_posix():c.digest(path.read_bytes()) for path in sources},
        'scientific_imports':False,'actual_native_resource_probes':0,'actual_provider_calls':0,
        'project_payload_reads':0,'actual_NumPy_calls':0,'optimizer_calls':0,'models_fitted':0,
        'actual_pandas_sampler_roster_parity_run':False,'source_AST_and_invented_cache_path_only':True,
        'actual_fullsize_input_bridge_run':False,'small_counts_used_only_in_invented_tests':True,
        'biological_or_FIT_admission_granted':False}
    with (OUT/'synthetic_tests_receipt.json').open('xb') as handle:handle.write(c.canonical(receipt))


if __name__=='__main__':run()
