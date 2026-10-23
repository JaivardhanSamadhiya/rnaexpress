"""Small invented domain-adapter tests; array doubles never call native code."""
import ast
from datetime import datetime,timezone
from itertools import combinations
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import adapter as a
from src.generalization_knowncell_joint_numeric_20261022.fake_array import Array,DType,FakeNP,expit
from src.generalization_knowncell_joint_numeric_20261022.tests import OptimizerSpy
from src.generalization_knowncell_joint_campaign_20261023.writer import UnitCalls

ROOT=Path(__file__).resolve().parents[2]
ENV={key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


def probe():return {'physical_available':3*2**30,'disk_available':2**30}


class Frame:
    def __init__(self,records,columns):self.records=list(records);self.columns=columns;self.index=list(range(99,99+len(records)))
    def reset_index(self,drop):
        assert drop is True;self.index=list(range(len(self.records)));return self


def invented_sampler(frame):
    assert frame.index==list(range(len(frame.records)))
    grouped={}
    for i,row in enumerate(frame.records):grouped.setdefault(row['parent_context_id'],[]).append(i)
    left=[];right=[];labels=[]
    for context in sorted(grouped):
        for one,two in combinations(grouped[context],2):
            delta=frame.records[one]['measured_delta']-frame.records[two]['measured_delta']
            if delta:left.append(one);right.append(two);labels.append(1 if delta>0 else -1)
    return Array(left),Array(right),Array(labels),Array([999.]*len(left)),Array(['mikl_gse173098']*len(left))


def invented_rows():
    result=[];effects={};matrix=[]
    for fold in (0,1,2):
        for cell in ('CAD','Neuro-2a'):
            for edit,value in enumerate((-1.,1.)):
                identity=f'invented_g{fold}_{cell}_{edit}'
                result.append({'intervention_id':identity,'dataset':'mikl_gse173098','cell_type':cell,
                    'endpoint_class':'projection','parent_context_id':f'invented_g{fold}_{cell}',
                    'biological_component':f'invented_g{fold}','gene_transcript':f'invented_g{fold}',
                    'held_parent_fold':fold,'parent_sequence':f'invented_parent_{fold}',
                    'mutant_sequence':f'invented_mutant_{fold}_{edit}'})
                effects[identity]=value;matrix.append([value,float(fold)]+[0.]*100)
    return result,Array(matrix),effects


def tiny_pool():
    rows,matrix,effects=invented_rows()
    train=[i for i,row in enumerate(rows) if row['held_parent_fold']!=0]
    target=[i for i,row in enumerate(rows) if row['held_parent_fold']==0]
    pool=a.one_pool(FakeNP,SimpleNamespace(DataFrame=Frame),invented_sampler,rows,matrix,effects,train,target,probe,ENV)
    document={'source_pools':{'outer0_final':pool['binding']},'runtime_binding_sha256':'a'*64,
              'input_admission_bindings':{'input_row_ids_sha256':a.reference.ids_sha(rows),
                                         'input_metadata_sha256':a.reference.metadata_sha(rows)}}
    prepared=a.PreparedPools(rows,{'outer0_final':pool},document)
    plan=SimpleNamespace(document=lambda:document,pool=lambda task:pool['binding'],
                         prefit_sha256='b'*64,runtime_binding_sha256='a'*64)
    return prepared,plan,pool


class ArrayDoubleTests(unittest.TestCase):
    def setUp(self):
        self.bytes_patch=patch.object(Array,'tobytes',lambda value,order='C':struct.pack('<'+'d'*len(value.flat()),*value.flat()),create=True)
        self.dtype_patch=patch.object(DType,'itemsize',8,create=True)
        self.bytes_patch.start();self.dtype_patch.start()
    def tearDown(self):self.dtype_patch.stop();self.bytes_patch.stop()
    def test_one_pool_reset_indices_original_pairs_new_cell_weights_and_common_scale(self):
        prepared,plan,pool=tiny_pool()
        self.assertEqual(pool['prepared']['weights'].tolist(),[.25]*4)
        self.assertEqual(pool['left'],[0,2,4,6]);self.assertEqual(pool['labels'],[-1]*4)
        self.assertEqual(pool['prepared']['scaling']['active'],[True]+[False]*101)
        self.assertEqual(pool['binding'],a.pool_binding(FakeNP,pool))
        self.assertEqual(pool['binding']['training_ids'],[row['intervention_id'] for row in pool['rows']])
        self.assertEqual(len(pool['binding']['validation_ids']),4)
    def test_hashes_include_shape_values_and_reject_nonfinite(self):
        self.assertNotEqual(a.array_hash(FakeNP,[[1.,2.]]),a.array_hash(FakeNP,[[1.],[2.]]))
        self.assertNotEqual(a.array_hash(FakeNP,[1.,2.]),a.array_hash(FakeNP,[1.,3.]))
        with self.assertRaises(AssertionError):a.array_hash(FakeNP,[float('nan')])
    def test_callback_three_arms_counts_full_predictions_and_fresh_each_unit(self):
        for arm in ('pooled','independent','joint_shrink10'):
            prepared,plan,pool=tiny_pool();events=[]
            def fresh():events.append('fresh');return probe()
            optimizer=OptimizerSpy();callback=a.make_fit_callback(FakeNP,optimizer,expit,prepared,plan,probe=fresh,environment=ENV)
            task={'arm':arm,'outer_fold':0,'inner_fold':None,'phase':'outer','configuration_id':'SOURCE_SELECTED',
                  'optimizer_units':2 if arm=='independent' else 1}
            birth={'identity':{'prefit_sha256':'b'*64,'runtime_binding_sha256':'a'*64,'configuration':dict(a.CONFIGS[0])},
                   'source_pool_sha256':a.lifecycle.hash_value(pool['binding'])}
            units=UnitCalls(arm);answer=callback(task,birth,units)
            self.assertEqual(len(optimizer.calls),task['optimizer_units']);units.complete()
            self.assertEqual(answer['predictions']['row_ids'],pool['binding']['validation_ids'])
            self.assertEqual(answer['predictions']['canonical_shape'],[4,102])
            self.assertEqual(len(events),task['optimizer_units']+3) # construction, callback, each unit, prediction
    def test_changed_native_pool_stops_before_optimizer(self):
        prepared,plan,pool=tiny_pool();optimizer=OptimizerSpy()
        callback=a.make_fit_callback(FakeNP,optimizer,expit,prepared,plan,probe=probe,environment=ENV)
        pool['prepared']['z'].data[0][0]+=1.
        task={'arm':'pooled','outer_fold':0,'inner_fold':None,'optimizer_units':1}
        with self.assertRaises(AssertionError):callback(task,{},UnitCalls('pooled'))
        self.assertEqual(optimizer.calls,[])
    def test_low_resource_before_second_independent_unit_prevents_second_optimizer(self):
        prepared,plan,pool=tiny_pool();optimizer=OptimizerSpy();events=[]
        def fresh():
            events.append('fresh')
            return {'physical_available':0,'disk_available':2**30} if len(events)==4 else probe()
        callback=a.make_fit_callback(FakeNP,optimizer,expit,prepared,plan,probe=fresh,environment=ENV)
        task={'arm':'independent','outer_fold':0,'inner_fold':None,'optimizer_units':2}
        birth={'identity':{'prefit_sha256':'b'*64,'runtime_binding_sha256':'a'*64,'configuration':dict(a.CONFIGS[0])},
               'source_pool_sha256':a.lifecycle.hash_value(pool['binding'])}
        units=UnitCalls('independent')
        with self.assertRaises(AssertionError):callback(task,birth,units)
        self.assertEqual(len(optimizer.calls),1);self.assertEqual(len(units.calls),1)


class StaticAndSelectionTests(unittest.TestCase):
    def test_nine_specs_retain_exact_reference_masks_and_reject_incomplete(self):
        rows,_,_=invented_rows();splits=[]
        for outer in (0,1,2):
            train,target=a.reference.union_split(rows,outer);source=[rows[i] for i in train];inner=[]
            for fold in (0,1,2):
                if fold==outer:continue
                left,right=a.reference.union_split(source,fold)
                inner.append({'validation_fold':fold,'training_indices':[train[i] for i in left],'validation_indices':[train[i] for i in right]})
            splits.append({'outer_fold':outer,'training_indices':train,'target_indices':target,'inner':inner})
        specs=a.source_specs({'splits':splits});self.assertEqual(len(specs),9)
        for key,train,target in specs:
            self.assertFalse(set(train)&set(target));self.assertEqual(len(target),4)
        with self.assertRaises(AssertionError):a.source_specs({'splits':splits[:-1]})
    def test_no_scientific_import_or_automatic_campaign_entrypoint(self):
        path=ROOT/'src'/a.NS/'adapter.py';text=path.read_text(encoding='utf-8');tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertFalse(any(v.name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for v in node.names))
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in ('numpy','pandas','scipy','torch','openvino'))
        self.assertNotIn('if __name__',text)
        self.assertIn('writer_v2 import Campaign',text)
    def test_selector_receives_only_source_truths_and_full_concatenated_oof_batches(self):
        with patch.object(Array,'tobytes',lambda value,order='C':struct.pack('<'+'d'*len(value.flat()),*value.flat()),create=True):
            prepared,plan,pool=tiny_pool()
        tasks={};saved={};paths={}
        for inner in (1,2):
            ids=[row['intervention_id'] for row in prepared.metadata if row['held_parent_fold']==inner]
            for config in a.CONFIGS:
                key=f'invented_{inner}_{config["id"]}';tasks[key]={'arm':'pooled','outer_fold':0,'inner_fold':inner,'phase':'inner','configuration_id':config['id']}
                paths[key]=Path(key);saved[str(paths[key])]={'predictions':{'row_ids':ids,'scores':[0.]*len(ids)}}
        tasks['outer']={'arm':'pooled','outer_fold':0,'inner_fold':None,'phase':'outer','configuration_id':'SOURCE_SELECTED'}
        class FakeCampaign:
            def __init__(self):self.plan=plan;self.tasks=tasks
            def check_saved(self,key):return {'model_sha256':'c'*64}
            def paths(self,key):return None,paths[key],None
        captured=[]
        def choose(metadata,outer,truths,batches):
            captured.append((truths,batches));self.assertEqual(set(truths),set(pool['binding']['training_ids']))
            self.assertFalse(set(truths)&set(pool['binding']['validation_ids']))
            for config in a.CONFIGS:
                self.assertEqual(set(batches[config['id']]),{1,2})
                self.assertEqual(set().union(*(set(v) for v in batches[config['id']].values())),set(truths))
            return {'selected_config':dict(a.CONFIGS[0]),'configuration_metrics':{'invented':True}}
        with patch.object(a,'Campaign',FakeCampaign),patch.object(a,'read_object',lambda path:saved[str(path)]),patch.object(a.selection,'select_source_config',choose):
            receipt=a.select_outer(prepared,FakeCampaign(),'pooled',0,probe=probe,environment=ENV)
        self.assertEqual(len(captured),1);self.assertEqual(len(receipt['inner_checkpoint_sha256']),6)
    def test_resource_policy_unchanged_and_two_threads_rejected(self):
        changed=dict(ENV);changed['OMP_NUM_THREADS']='2'
        with self.assertRaises(AssertionError):a.gate(probe,changed)
        with self.assertRaises(AssertionError):a.gate(lambda:{'physical_available':3*2**30-1,'disk_available':2**30},ENV)


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    paths=sorted((ROOT/'src'/a.NS).glob('*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt={'status':'PASS_INVENTED_DEFERRED_DOMAIN_ADAPTER_NOT_NATIVE_OR_PROJECT_ADMISSION','tests':result.testsRun,
             'elapsed_seconds':time.monotonic()-started,'generated_utc':datetime.now(timezone.utc).isoformat(),
             'scientific_imports':False,'native_optimizer_calls':0,'models_fitted':0,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,
             'full_real13781_cohort_pool_build_certified':False,'full_campaign_or_gate_implemented':False,
             'source_files':{path.relative_to(ROOT).as_posix():a.lifecycle.digest(path.read_bytes()) for path in paths}}
    path=ROOT/'results'/a.NS/'synthetic_tests_receipt.json'
    with path.open('xb') as stream:stream.write(a.lifecycle.canonical_bytes(receipt))
    print('DEFERRED_ENGINE_STDLIB_PASS',result.testsRun,a.lifecycle.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
