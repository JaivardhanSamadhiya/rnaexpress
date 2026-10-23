"""Invented lifecycle tests; no scientific packages, project inputs or fits."""
import ast
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import time
import unittest
from . import contracts as c
from . import writer as w
from .spec import (NS,ARMS,CELLS,CONFIGS,COUNTS,FOLDS,POOL_HASH_FIELDS,PREFIT_STATUS,
                   FEATURE_WIDTH as P,CANONICAL_MEAN,METHOD,OPTIONS,SCORER)

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/NS
SCALING={'pair_rms':[0.]*P,'scale':[1.]*P,'active':[False]*P,'mean':[0.]*P}


def fixture():
    ids=[f'invented_lifecycle_id_{i:05d}' for i in range(COUNTS['all_rows'])]
    folds=[i%3 for i in range(len(ids))]
    document={'status':PREFIT_STATUS,'counts':dict(COUNTS),'arms':list(ARMS),'configs':list(CONFIGS),
              'numerical_threads':1,'resource_exception_applies':False,'runtime_binding_sha256':'a'*64,
              'metadata_admission_sha256':'b'*64,'feature_admission_sha256':'c'*64,
              'label_admission_sha256':'d'*64,'fit_source_manifest_sha256':'e'*64,
              'all_row_ids':ids,'all_row_folds':folds,'source_pools':{}}
    for outer in FOLDS:
        for inner in (None,*[f for f in FOLDS if f!=outer]):
            excluded={outer} if inner is None else {outer,inner};held=outer if inner is None else inner
            train=[row_id for row_id,fold in zip(ids,folds) if fold not in excluded]
            target=[row_id for row_id,fold in zip(ids,folds) if fold==held]
            pool={'training_ids':train,'validation_ids':target,'training_ids_sha256':c.id_hash(train),
                  'validation_ids_sha256':c.id_hash(target),'training_rows':len(train),'validation_rows':len(target),
                  'training_pairs':len(train)//2,'both_cells_confirmed':True,'full_original_menus_confirmed':True,
                  'gene_component_allele_contradictions':0,**{field:'f'*64 for field in POOL_HASH_FIELDS}}
            pool['common_scaling_sha256']=c.hash_value(SCALING)
            document['source_pools'][c.pool_key(outer,inner)]=pool
    return document


def plan_for(document=None):
    raw=c.canonical_bytes(document or fixture())
    def committed_reader(name,commit):
        assert name=='results/invented_lifecycle/prefit.json' and commit=='1'*40
        return raw
    return c.bind_plan('results/invented_lifecycle/prefit.json',raw,'1'*40,committed_reader,'a'*64)


def model_for(task,birth,pool):
    summary={'objective':math.log(2.),'success':True,'message':'invented callback; no optimizer',
             'iterations':0,'maximum_gradient_abs':0.}
    model={'arm':task['arm'],'config':dict(birth['identity']['configuration']),
           'feature_width':P,'canonical_mean':CANONICAL_MEAN,'canonical_scorer':SCORER,
           'optimizer_method':METHOD,'optimizer_options':dict(OPTIONS),
           'training_rows':pool['training_rows'],'training_pairs':pool['training_pairs'],
           'optimizer_units':task['optimizer_units'],'scaling':deepcopy(SCALING),'objective':math.log(2.),
           'optimizer_summaries':{name:dict(summary) for name,_ in w.unit_spec(task['arm'])}}
    if task['arm']=='independent':model['heads']={cell:[0.]*P for cell in CELLS}
    else:
        model['beta']=[0.]*P
        if task['arm']=='joint_shrink10':model['delta']=[0.]*P
    return model


def callback_for(campaign,mutate=None,unit_error=False):
    def callback(task,birth,units):
        key=c.task_key(task);birth_path=campaign.paths(key)[0]
        assert birth_path.exists() and w.read_object(birth_path)==birth
        assert birth['identity']['prefit_sha256']==campaign.plan.prefit_sha256
        names=w.unit_spec(task['arm'])
        for name,dimension in names[:1] if unit_error else names:
            units.invoke(name,dimension,lambda:'invented unit invocation, not a native optimizer')
        pool=campaign.plan.pool(task)
        answer={'model':model_for(task,birth,pool),
                'predictions':{'row_ids':list(pool['validation_ids']),'scores':[0.]*pool['validation_rows'],
                               'canonical_shape':[pool['validation_rows'],P],'canonical_dtype':'float64',
                               'canonical_order':'C','canonical_scorer':SCORER}}
        if mutate:mutate(answer)
        return answer
    return callback


def selection_for(campaign,task):
    inners={key:campaign.check_saved(key)['model_sha256'] for key,value in campaign.tasks.items()
            if value['arm']==task['arm'] and value['outer_fold']==task['outer_fold'] and value['phase']=='inner'}
    return {'arm':task['arm'],'outer_fold':task['outer_fold'],'selected_config':dict(CONFIGS[1]),
            'source_only':True,'primary_paired_only':True,
            'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
            'prefit_sha256':campaign.plan.prefit_sha256,'runtime_binding_sha256':'a'*64,
            'source_training_ids_sha256':campaign.plan.pool(task)['training_ids_sha256'],
            'configuration_metrics_sha256':'8'*64,'inner_checkpoint_sha256':inners}


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.document=fixture()
    def test_exact63_tasks84_units9_shared_pools(self):
        tasks=c.task_roster();self.assertEqual(len(tasks),63)
        self.assertEqual(sum(t['phase']=='inner' for t in tasks),54)
        self.assertEqual(sum(t['optimizer_units'] for t in tasks),84)
        self.assertEqual(len({c.pool_key(t['outer_fold'],t['inner_fold']) for t in tasks}),9)
    def test_committed_prefit_bytes_and_runtime_match_before_use(self):
        raw=c.canonical_bytes(self.document)
        with self.assertRaises(AssertionError):c.bind_plan('results/invented/prefit.json',raw,'1'*40,lambda *_:b'changed','a'*64)
        with self.assertRaises(AssertionError):c.bind_plan('results/invented/prefit.json',raw,'1'*40,lambda *_:raw,'2'*64)
        plan=plan_for(self.document);self.assertEqual(plan.prefit_sha256,c.digest(raw))
    def test_unordered_partial_outer_or_inner_targets_and_wrong_training_ids_fail(self):
        for key,field in [('outer0_final','validation_ids'),('outer0_inner1','validation_ids'),('outer0_inner1','training_ids')]:
            changed=deepcopy(self.document);changed['source_pools'][key][field].reverse()
            with self.assertRaises(AssertionError):c.validate_prefit(changed)
        changed=deepcopy(self.document);changed['source_pools']['outer0_final']['validation_ids'].pop()
        with self.assertRaises(AssertionError):c.validate_prefit(changed)
    def test_source_identity_hash_cells_menu_or_resource_declarations_fail(self):
        for field,value in [('training_ids_sha256','0'*64),('both_cells_confirmed',False),('full_original_menus_confirmed',False),('gene_component_allele_contradictions',1)]:
            changed=deepcopy(self.document);changed['source_pools']['outer0_final'][field]=value
            with self.assertRaises(AssertionError):c.validate_prefit(changed)
        changed=deepcopy(self.document);changed['resource_exception_applies']=True
        with self.assertRaises(AssertionError):c.validate_prefit(changed)
    def test_unsafe_alias_duplicate_json_and_nonfinite_tokens_rejected(self):
        raw=c.canonical_bytes(self.document)
        for name in ('../x','results/../x','C:/x','results\\x','results//x'):
            with self.assertRaises(AssertionError):c.bind_plan(name,raw,'1'*40,lambda *_:raw,'a'*64)
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(AssertionError):c.strict_json(raw)


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=plan_for()
    def run_directory(self):return tempfile.TemporaryDirectory(prefix='invented_only_',dir=OUT)
    def first(self,campaign,arm='pooled'):
        return next(key for key,task in campaign.tasks.items() if task['arm']==arm and task['phase']=='inner')
    def test_birth_durable_before_callback_and_all_identity_hashes_bound(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);key=self.first(campaign)
            receipt=campaign.write_checkpoint(key,callback_for(campaign))
            saved=campaign.check_saved(key);self.assertEqual(receipt,saved)
            birth=w.read_object(campaign.paths(key)[0]);self.assertEqual(birth['identity']['prefit_sha256'],self.plan.prefit_sha256)
            self.assertEqual(birth['source_pool_sha256'],c.hash_value(self.plan.pool(campaign.tasks[key])))
            self.assertFalse(campaign.paths(key)[2].is_dir())
    def test_existing_campaign_or_checkpoint_cannot_resume_or_overwrite(self):
        with self.run_directory() as temporary:
            directory=Path(temporary)/'run';campaign=w.Campaign(directory,self.plan);key=self.first(campaign)
            campaign.write_checkpoint(key,callback_for(campaign))
            with self.assertRaises(FileExistsError):w.Campaign(directory,self.plan)
            before=campaign.paths(key)[1].read_bytes()
            with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback_for(campaign))
            self.assertEqual(before,campaign.paths(key)[1].read_bytes())
    def test_missing_extra_or_failed_optimizer_units_leave_failed_no_resume_evidence(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);key=self.first(campaign,'independent')
            with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback_for(campaign,unit_error=True))
            self.assertTrue(campaign.paths(key)[0].exists());self.assertFalse(campaign.paths(key)[1].exists())
            self.assertEqual(w.read_object(campaign.directory/(key+'.failure.json'))['status'],'FAILED_NO_RESUME')
            with self.assertRaises(AssertionError):campaign.finish()
            with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback_for(campaign))
        units=w.UnitCalls('pooled');units.invoke('pooled',102,lambda:None)
        with self.assertRaises(AssertionError):units.invoke('pooled',102,lambda:None)
        units=w.UnitCalls('joint_shrink10')
        with self.assertRaises(RuntimeError):units.invoke('joint',204,lambda:(_ for _ in ()).throw(RuntimeError('invented failure')))
        with self.assertRaises(AssertionError):units.complete()
    def test_prediction_id_order_full_shape_and_finiteness_fail(self):
        mutators=[lambda a:a['predictions']['row_ids'].reverse(),lambda a:a['predictions']['scores'].pop(),
                  lambda a:a['predictions']['canonical_shape'].__setitem__(1,101),
                  lambda a:a['predictions']['scores'].__setitem__(0,float('nan'))]
        for mutate in mutators:
            with self.run_directory() as temporary:
                campaign=w.Campaign(Path(temporary)/'run',self.plan)
                with self.assertRaises(AssertionError):campaign.write_checkpoint(self.first(campaign),callback_for(campaign,mutate))
    def test_callback_cannot_mutate_birth_dictionary_or_frozen_file_silently(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);key=self.first(campaign)
            original=callback_for(campaign)
            def callback(task,birth,units):
                result=original(task,birth,units)
                birth['identity']['training_features_sha256']='0'*64
                return result
            campaign.write_checkpoint(key,callback)
            self.assertEqual(campaign.check_saved(key)['status'],'CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY')
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);key=self.first(campaign);original=callback_for(campaign)
            def callback(task,birth,units):
                result=original(task,birth,units)
                campaign.paths(key)[0].write_bytes(b'invented mutation')
                return result
            with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback)
    def test_wrong_config_scaler_extrahead_and_failed_summary_fail(self):
        mutators=[lambda a:a['model'].__setitem__('config',dict(CONFIGS[2])),
                  lambda a:a['model']['scaling']['mean'].__setitem__(0,1.),
                  lambda a:a['model'].__setitem__('direction_head',[0.]),
                  lambda a:a['model']['optimizer_summaries']['pooled'].__setitem__('success',False)]
        for mutate in mutators:
            with self.run_directory() as temporary:
                campaign=w.Campaign(Path(temporary)/'run',self.plan)
                with self.assertRaises(AssertionError):campaign.write_checkpoint(self.first(campaign),callback_for(campaign,mutate))
    def test_incomplete_or_unknown_roster_never_finishes(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan)
            with self.assertRaises(AssertionError):campaign.finish()
            with self.assertRaises(AssertionError):campaign.write_checkpoint('foreign',callback_for(campaign))
    def test_full63_roster84_actual_invented_invocations_outer_source_bindings_and_completion(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);callback=callback_for(campaign)
            for key,task in campaign.tasks.items():
                if task['phase']=='inner':campaign.write_checkpoint(key,callback)
            for key,task in campaign.tasks.items():
                if task['phase']!='outer':continue
                selected=selection_for(campaign,task)
                bad=deepcopy(selected);bad['source_only']=False
                with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback,bad)
                bad=deepcopy(selected);bad['inner_checkpoint_sha256'].pop(next(iter(bad['inner_checkpoint_sha256'])))
                with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback,bad)
                campaign.write_checkpoint(key,callback,selected)
            complete=campaign.finish()
            self.assertEqual(complete['checkpoint_count'],63);self.assertEqual(complete['optimizer_units'],84)
            self.assertFalse(complete['independent_numeric_and_selection_replay_complete'])
            with self.assertRaises(AssertionError):campaign.finish()
    def test_saved_model_mutation_rejected_against_creation_receipt(self):
        with self.run_directory() as temporary:
            campaign=w.Campaign(Path(temporary)/'run',self.plan);key=self.first(campaign)
            campaign.write_checkpoint(key,callback_for(campaign))
            saved=w.read_object(campaign.paths(key)[1]);saved['predictions']['scores'][0]=1.
            campaign.paths(key)[1].write_bytes(c.canonical_bytes(saved))
            with self.assertRaises(AssertionError):campaign.check_saved(key)


class SourceTests(unittest.TestCase):
    def test_scientific_imports_and_native_execution_absent(self):
        for name in ('contracts.py','writer.py','spec.py'):
            tree=ast.parse((ROOT/'src'/NS/name).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in ('numpy','pandas','scipy','torch','openvino'))


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    paths=sorted((ROOT/'src'/NS).glob('*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt={'status':'PASS_INVENTED_STDLIB_LIFECYCLE_NOT_SCIENTIFIC_CAMPAIGN','tests':result.testsRun,
             'elapsed_seconds':time.monotonic()-started,'generated_utc':datetime.now(timezone.utc).isoformat(),
             'python_executable':sys.executable,'python_version':sys.version,'scientific_imports':False,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'native_optimizer_calls':0,'models_fitted':0,
             'invented_roster_fixture_ids':COUNTS['all_rows'],'source_files':{p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in paths}}
    path=OUT/'synthetic_tests_receipt.json'
    with path.open('xb') as handle:handle.write(c.canonical_bytes(receipt))
    print('INVENTED_LIFECYCLE_CHECKS_PASS',result.testsRun,c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
