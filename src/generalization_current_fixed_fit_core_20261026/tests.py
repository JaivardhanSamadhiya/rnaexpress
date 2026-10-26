"""Invented list-array end-to-end tests; no scientific imports/real optimizer."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import plan as p,driver as d
from src.generalization_current_execution_context_20261025 import tests as old_fixture
from src.generalization_knowncell_joint_engine_20261023.tests import invented_rows,Frame,invented_sampler
from src.generalization_cdrive_forensic_execution_20261026.pools import one_pool
from src.generalization_knowncell_joint_engine_20261023 import adapter
from src.generalization_knowncell_joint_numeric_20261022.fake_array import Array,DType,FakeNP,expit
from src.generalization_knowncell_joint_numeric_20261022.tests import OptimizerSpy
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_current_fixed_fit_core_20261026'
OUT=ROOT/'results'/NS


def fixture():
    rows,matrix,effects=invented_rows();inp=SimpleNamespace(metadata=rows,matrix=matrix,effects=effects)
    pools={}
    for outer in (0,1,2):
        train,target=metadata.union_split(rows,outer)
        pools[lc.pool_key(outer,None)]=one_pool(FakeNP,SimpleNamespace(DataFrame=Frame),invented_sampler,inp,train,target,fresh=lambda:None)
        for inner in (fold for fold in (0,1,2) if fold!=outer):
            source=[rows[i] for i in train];left,right=metadata.union_split(source,inner)
            pools[lc.pool_key(outer,inner)]=one_pool(FakeNP,SimpleNamespace(DataFrame=Frame),invented_sampler,inp,
                [train[i] for i in left],[train[i] for i in right],fresh=lambda:None)
    old,actual,admission,reference,_,_,_=old_fixture.fixture()
    actual.update(counts=dict(lc.COUNTS),all_row_ids=[row['intervention_id'] for row in rows],
        all_row_folds=[row['held_parent_fold'] for row in rows],source_pools={key:pool['binding'] for key,pool in pools.items()})
    actual['input_admission_bindings'].update(input_row_ids_sha256=metadata.ids_sha(rows),
        input_metadata_sha256=metadata.metadata_sha(rows),input_features_sha256=adapter.array_hash(FakeNP,matrix),
        input_effects_sha256=adapter.array_hash(FakeNP,[effects[row['intervention_id']] for row in rows]))
    raw=p.c.canonical(actual)
    admission.update(prefit_sha256=p.c.digest(raw),input_admission_bindings_sha256=lc.hash_value(actual['input_admission_bindings']))
    projection=p.c.canonical(admission)
    reference['file_sha256'].update(prefit=p.c.digest(raw),projection=p.c.digest(projection))
    historical=p.original.from_supplied(raw,projection,p.c.canonical(reference))
    prepared=adapter.PreparedPools(rows,pools,historical.document())
    return historical,prepared


def current(historical):
    document=p.make_current_prefit(historical,{'status':'INVENTED_CREATOR_NO_REAL_AUTHORITY','owner':'invented'})
    raw=p.c.canonical(document)
    def reader(name,commit):
        assert name=='results/invented/new_prefit.json' and commit=='c'*40
        return raw
    return p.bind_current_plan('results/invented/new_prefit.json',raw,'c'*40,historical,committed_reader=reader)


class Cases(unittest.TestCase):
    def setUp(self):
        counts={**lc.COUNTS,'all_rows':12,'CAD_rows':6,'Neuro-2a_rows':6,'paired_rows':12,
            'paired_menus':3,'paired_contexts':6,'components':3,'unmatched_rows':0,'unmatched_contexts':0}
        self.patches=[patch.object(lc,'COUNTS',counts),patch.object(Array,'tobytes',
            lambda value,order='C':struct.pack('<'+'d'*len(value.flat()),*value.flat()),create=True),
            patch.object(DType,'itemsize',8,create=True)]
        for item in self.patches:item.start();self.addCleanup(item.stop)

    def test_new_raw_prefit_and_explicit_view_stable_identity(self):
        historical,_=fixture();plan=current(historical)
        self.assertTrue(plan.actual_document()['resource_exception_applies'])
        self.assertFalse(plan.document()['resource_exception_applies'])
        self.assertNotEqual(plan.prefit_sha256,historical.prefit_sha256)
        self.assertNotEqual(plan.runtime_binding_sha256,historical.runtime_binding_sha256)
        self.assertEqual(p.original.scientific_projection(plan.document()),p.original.scientific_projection(historical.document()))
        self.assertNotEqual(plan.actual_document()['prefit_execution'],historical.actual_document()['prefit_execution'])
        descriptor=plan.identity()['current_resource_compatibility_view']
        self.assertEqual(descriptor['actual_prefit_raw_sha256'],plan.prefit_sha256)
        self.assertFalse(descriptor['fresh_fit_or_replay_owner_included_in_campaign_identity'])

    def test_commit_mismatch_and_mutated_science_are_rejected(self):
        historical,_=fixture();plan=current(historical)
        with self.assertRaisesRegex(AssertionError,'exactly committed'):
            p.bind_current_plan(plan.prefit_relative_path,plan.prefit_raw,'c'*40,historical,committed_reader=lambda *_:b'wrong')
        actual=plan.actual_document();actual['source_pools'][next(iter(actual['source_pools']))]['common_scaling_sha256']='f'*64
        raw=p.c.canonical(actual)
        with self.assertRaises(AssertionError):p.bind_current_plan(plan.prefit_relative_path,raw,'c'*40,historical,committed_reader=lambda *_:raw)

    def test_checked_rebind_keeps_original_objects_and_rejects_binding_mutation(self):
        historical,prepared=fixture();plan=current(historical);new=p.rebind_prepared(plan,prepared)
        self.assertIs(new.metadata,prepared.metadata);self.assertIs(new.pools,prepared.pools)
        self.assertEqual(new.prefit_document,plan.document())
        first=next(iter(prepared.pools));prepared.pools[first]['binding']['prepared_z_sha256']='f'*64
        with self.assertRaises(AssertionError):p.rebind_prepared(plan,prepared)

    def test_full63_84_end_to_end_birth_options_full_shapes_and_six_inner_selection(self):
        historical,prepared=fixture();plan=current(historical);prepared=p.rebind_prepared(plan,prepared)
        active={};hooks=[];selector_calls=[]
        with tempfile.TemporaryDirectory(dir=OUT) as temporary:
            directory=Path(temporary)/'new_run'
            class Recording(OptimizerSpy):
                def __call__(self,*args,**kwargs):
                    assert (directory/'checkpoints'/(active['key']+'.birth.json')).exists()
                    return super().__call__(*args,**kwargs)
            optimizer=Recording()
            def hook(**values):
                hooks.append(values['task_key']);active['key']=values['task_key'];return True
            original=d.select_source_config
            def selector(rows,outer,truths,batches):
                held={row['intervention_id'] for row in rows if row['held_parent_fold']==outer}
                self.assertFalse(set(truths)&held)
                self.assertEqual(len(batches),3);self.assertTrue(all(len(value)==2 for value in batches.values()))
                result=original(rows,outer,truths,batches);selector_calls.append(result);return result
            with patch.object(d,'select_source_config',side_effect=selector), \
                 patch.object(adapter,'make_fit_callback',side_effect=AssertionError('Forbidden guarded factory')), \
                 patch.object(adapter,'prepare_pools',side_effect=AssertionError('Forbidden guarded factory')), \
                 patch.object(adapter,'select_outer',side_effect=AssertionError('Forbidden guarded selector')):
                result=d.run_fixed_campaign(FakeNP,optimizer,expit,prepared,plan,fresh=lambda:None,
                    before_checkpoint_integrity=hook,directory=directory)
            self.assertEqual(len(hooks),63);self.assertEqual(len(optimizer.calls),84)
            self.assertEqual(len(selector_calls),9)
            self.assertEqual([call['size'] for call in optimizer.calls].count(102),63)
            self.assertEqual([call['size'] for call in optimizer.calls].count(204),21)
            self.assertTrue(all(call['options']==d.OPTIONS for call in optimizer.calls))
            self.assertEqual(result['checkpoint_count'],63);self.assertEqual(result['optimizer_units'],84)
            self.assertFalse(result['independent_numeric_and_selection_replay_complete'])
            self.assertEqual(len(list((directory/'checkpoints').iterdir())),191)
            for item in selector_calls:self.assertEqual(item['selected_config'],dict(lc.CONFIGS[0]))
            for path in (directory/'checkpoints').glob('*.model.json'):
                saved=lc.strict_json(path.read_bytes());prediction=saved['predictions']
                self.assertEqual(prediction['canonical_shape'],[len(prediction['row_ids']),102])

    def test_integrity_failure_poison_and_no_optimizer_or_completion(self):
        historical,prepared=fixture();plan=current(historical);prepared=p.rebind_prepared(plan,prepared)
        captured={};optimizer=OptimizerSpy()
        def hook(**values):captured['campaign']=values['campaign'];return False
        with tempfile.TemporaryDirectory(dir=OUT) as temporary:
            directory=Path(temporary)/'failed'
            with self.assertRaisesRegex(AssertionError,'Mandatory actual integrity'):
                d.run_fixed_campaign(FakeNP,optimizer,expit,prepared,plan,fresh=lambda:None,
                    before_checkpoint_integrity=hook,directory=directory)
            self.assertEqual(optimizer.calls,[]);self.assertTrue(captured['campaign'].failed)
            self.assertFalse((directory/'checkpoints/campaign_complete.json').exists())
            self.assertTrue((directory/'driver_failure.json').exists())
            with self.assertRaises(AssertionError):captured['campaign'].write_checkpoint(next(iter(captured['campaign'].tasks)),lambda *_:None)

    def test_existing_directory_is_not_resumed(self):
        historical,prepared=fixture();plan=current(historical);prepared=p.rebind_prepared(plan,prepared)
        optimizer=OptimizerSpy()
        with tempfile.TemporaryDirectory(dir=OUT) as temporary,self.assertRaises(FileExistsError):
            d.run_fixed_campaign(FakeNP,optimizer,expit,prepared,plan,fresh=lambda:None,
                before_checkpoint_integrity=lambda **_:True,directory=Path(temporary))
        self.assertEqual(optimizer.calls,[])

    def test_resource_failure_before_second_independent_unit(self):
        historical,prepared=fixture();plan=current(historical);prepared=p.rebind_prepared(plan,prepared)
        optimizer=OptimizerSpy();active={}
        def hook(**values):active.update(task=values['task']);return True
        def fresh():
            if active.get('task',{}).get('arm')=='independent' and len(optimizer.calls)==22:
                raise RuntimeError('invented resource failure before second independent unit')
        with tempfile.TemporaryDirectory(dir=OUT) as temporary:
            directory=Path(temporary)/'failed'
            with self.assertRaisesRegex(RuntimeError,'second independent'):
                d.run_fixed_campaign(FakeNP,optimizer,expit,prepared,plan,fresh=fresh,before_checkpoint_integrity=hook,directory=directory)
            self.assertEqual(len(optimizer.calls),22)
            self.assertFalse((directory/'checkpoints/campaign_complete.json').exists())


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    import hashlib
    source=Path(__file__).parent
    receipt={'status':'PASS_INVENTED_CURRENT_FIXED_FIT_CORE_NOT_NATIVE_OR_ACTUAL_AUTHORITY',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'source_sha256':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in source.glob('*.py')},
        'actual_scientific_imports':0,'actual_data_reads':0,'actual_native_jobs':0,'actual_optimizer_calls':0,
        'invented_optimizer_spy_used':True,'private_invented_cohort_counts_only':True}
    path=OUT/'synthetic_tests_receipt.json'
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(receipt,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print('INVENTED_CORE_ONLY',result.testsRun,hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':run()
