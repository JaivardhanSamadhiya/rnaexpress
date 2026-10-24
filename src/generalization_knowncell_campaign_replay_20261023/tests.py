"""Invented supplied records with PRIVATE arithmetic/pool stubs; no native work."""
import ast
from datetime import datetime,timezone
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from . import replay as r,selection as independent
from src.generalization_knowncell_joint_implementation_20261022.tests import rows_fixture,truth_fixture,source_fixture
from src.generalization_knowncell_joint_implementation_20261022 import selection as original_selection
from src.generalization_knowncell_joint_numeric_20261022.spec import METHOD,OPTIONS,SCORER,CANONICAL_MEAN
from src.generalization_knowncell_joint_campaign_20261023.spec import POOL_HASH_FIELDS

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_campaign_replay_20261023'
SCALING = {'pair_rms':[0.]*102,'scale':[1.]*102,'active':[False]*102,'mean':[0.]*102}


class InventedPlan:
    """Small test plan; deliberately NOT the public BoundPlan/project schema."""
    prefit_commit = '1'*40
    runtime_binding_sha256 = 'a'*64
    def __init__(self,pools):
        self.bindings = {key:copy.deepcopy(pool['binding']) for key,pool in pools.items()}
        self.prefit_sha256 = r.lifecycle.hash_value(self.bindings)
    def pool(self,task):
        return copy.deepcopy(self.bindings[r.lifecycle.pool_key(task['outer_fold'],task['inner_fold'])])
    def identity(self):
        return {'prefit_relative_path':'results/invented_campaign_replay/prefit.json',
                'prefit_commit':self.prefit_commit,'prefit_sha256':self.prefit_sha256,
                'runtime_binding_sha256':self.runtime_binding_sha256,
                'source_pool_sha256':{key:r.lifecycle.hash_value(value) for key,value in self.bindings.items()},
                'checkpoint_roster':r.lifecycle.task_roster(),'checkpoint_count':63,'optimizer_units':84,
                'metadata_and_scientific_values_independently_certified_here':False}


def zero_model(task,pool,config):
    summaries = {name:{'objective':math.log(2.),'success':True,'message':'Invented record; no optimizer',
                       'iterations':0,'maximum_gradient_abs':0.} for name,_ in r.unit_spec(task['arm'])}
    model = {'arm':task['arm'],'config':dict(config),'feature_width':102,'canonical_mean':CANONICAL_MEAN,
             'canonical_scorer':SCORER,'optimizer_method':METHOD,'optimizer_options':dict(OPTIONS),
             'training_rows':pool['training_rows'],'training_pairs':pool['training_pairs'],
             'optimizer_units':task['optimizer_units'],'scaling':copy.deepcopy(SCALING),
             'objective':math.log(2.),'optimizer_summaries':summaries}
    if task['arm']=='independent':model['heads']={cell:[0.]*102 for cell in independent.CELLS}
    else:
        model['beta']=[0.]*102
        if task['arm']=='joint_shrink10':model['delta']=[0.]*102
    return model


def fixture():
    rows = rows_fixture(unequal=True,unmatched=True)
    pools = {}
    for outer in r.FOLDS:
        for inner in (None,*[fold for fold in r.FOLDS if fold!=outer]):
            excluded = {outer} if inner is None else {outer,inner}
            held = outer if inner is None else inner
            source = [copy.deepcopy(row) for row in rows if row['held_parent_fold'] not in excluded]
            target = [copy.deepcopy(row) for row in rows if row['held_parent_fold']==held]
            truths = truth_fixture(source)
            effects = [truths[row['intervention_id']] for row in source]
            binding = {name:'f'*64 for name in POOL_HASH_FIELDS}
            binding.update(training_ids=[row['intervention_id'] for row in source],
                           validation_ids=[row['intervention_id'] for row in target],
                           training_ids_sha256=r.metadata.ids_sha(source),validation_ids_sha256=r.metadata.ids_sha(target),
                           training_metadata_sha256=r.metadata.metadata_sha(source),validation_metadata_sha256=r.metadata.metadata_sha(target),
                           training_rows=len(source),validation_rows=len(target),training_pairs=len({row['parent_context_id'] for row in source}),
                           both_cells_confirmed=True,full_original_menus_confirmed=True,gene_component_allele_contradictions=0,
                           common_scaling_sha256=r.lifecycle.hash_value(SCALING),training_effects_json_sha256=r.lifecycle.hash_value(effects))
            pools[r.lifecycle.pool_key(outer,inner)] = {'binding':binding,'rows':source,'effects':effects,'validation_metadata':target}
    plan = InventedPlan(pools)
    campaign_birth = r.lifecycle.canonical_bytes({'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**plan.identity()})
    birth_sha = r.lifecycle.digest(campaign_birth)
    records = []
    tasks = r.lifecycle.task_roster()
    by_key = {}
    for task in tasks:
        key = r.lifecycle.task_key(task);pool = plan.pool(task)
        selected = None
        if task['phase']=='inner':
            config = next(dict(config) for config in r.CONFIGS if config['id']==task['configuration_id'])
        else:
            batches = {config['id']:{} for config in r.CONFIGS};hashes={}
            for previous in tasks:
                if previous['phase']!='inner' or previous['arm']!=task['arm'] or previous['outer_fold']!=task['outer_fold']:continue
                previous_key = r.lifecycle.task_key(previous);record = by_key[previous_key]
                predictions = r.lifecycle.strict_json(record['checkpoint_raw'])['predictions']
                batches[previous['configuration_id']][previous['inner_fold']] = dict(zip(predictions['row_ids'],predictions['scores']))
                hashes[previous_key] = r.lifecycle.digest(record['checkpoint_raw'])
            source_pool = pools[r.lifecycle.pool_key(task['outer_fold'],None)]
            source_truths = dict(zip(pool['training_ids'],source_pool['effects']))
            # Use the OLD independent reference selector to build test records,
            # rather than the new selector under test.
            old = original_selection.select_source_config(rows,task['outer_fold'],source_truths,batches)
            config = old['selected_config']
            selected = {'arm':task['arm'],'outer_fold':task['outer_fold'],'selected_config':config,
                        'source_only':True,'primary_paired_only':True,
                        'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
                        'prefit_sha256':plan.prefit_sha256,'runtime_binding_sha256':plan.runtime_binding_sha256,
                        'source_training_ids_sha256':pool['training_ids_sha256'],
                        'configuration_metrics_sha256':r.lifecycle.hash_value(old['configuration_metrics']),
                        'inner_checkpoint_sha256':hashes}
        selection_sha = None if selected is None else r.lifecycle.hash_value(selected)
        birth = {'task_key':key,'identity':r.birth_identity(arm=task['arm'],phase=task['phase'],outer_fold=task['outer_fold'],
                    inner_fold=task['inner_fold'],configuration=config,runtime_binding_sha256=plan.runtime_binding_sha256,
                    prefit_sha256=plan.prefit_sha256,**{name:pool[name] for name in r.HASHES}),
                 'campaign_birth_sha256':birth_sha,'source_pool_sha256':r.lifecycle.hash_value(pool),
                 **{name:pool[name] for name in ('validation_ids_sha256','validation_metadata_sha256','validation_features_sha256','validation_effects_sha256','validation_rows')},
                 'full_validation_shape':[pool['validation_rows'],102],'prefit_commit':plan.prefit_commit,
                 'source_only_selection_sha256':selection_sha,'source_only_selection':selected}
        raw_birth = r.lifecycle.canonical_bytes(birth)
        checkpoint = {'task_key':key,'birth_sha256':r.lifecycle.digest(raw_birth),'model':zero_model(task,pool,config),
                      'predictions':{'row_ids':pool['validation_ids'],'scores':[0.]*pool['validation_rows'],
                                     'canonical_shape':[pool['validation_rows'],102],'canonical_dtype':'float64',
                                     'canonical_order':'C','canonical_scorer':SCORER}}
        raw_checkpoint = r.lifecycle.canonical_bytes(checkpoint)
        complete = {'status':'CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY','task_key':key,
                    'birth_sha256':r.lifecycle.digest(raw_birth),'model_sha256':r.lifecycle.digest(raw_checkpoint),
                    'optimizer_invocations':[{'name':name,'dimension':dimension,'started':True,'returned':True} for name,dimension in r.unit_spec(task['arm'])],
                    'optimizer_units':task['optimizer_units'],'configuration':config,
                    'source_only_selection_sha256':selection_sha,'campaign_birth_sha256':birth_sha}
        record = {'task_key':key,'birth_raw':raw_birth,'checkpoint_raw':raw_checkpoint,'completion_raw':r.lifecycle.canonical_bytes(complete)}
        records.append(record);by_key[key] = record
    answer = SimpleNamespace(prepared=SimpleNamespace(pools=pools),plan=plan,birth=campaign_birth,records=records)
    answer.complete = seal_campaign(answer)
    return answer


def seal_campaign(case):
    return r.lifecycle.canonical_bytes({'status':'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
        **case.plan.identity(),'campaign_birth_sha256':r.lifecycle.digest(case.birth),'inner_checkpoints':54,'outer_checkpoints':9,
        'checkpoint_receipt_sha256':{record['task_key']:r.lifecycle.digest(record['completion_raw']) for record in case.records},
        'independent_numeric_and_selection_replay_complete':False,'biological_or_gate_claim':False})


def reseal_record(record,*,birth=None,checkpoint=None,completion=None):
    birth = copy.deepcopy(birth or r.lifecycle.strict_json(record['birth_raw']))
    checkpoint = copy.deepcopy(checkpoint or r.lifecycle.strict_json(record['checkpoint_raw']))
    completion = copy.deepcopy(completion or r.lifecycle.strict_json(record['completion_raw']))
    selected = birth['source_only_selection']
    birth['source_only_selection_sha256'] = None if selected is None else r.lifecycle.hash_value(selected)
    record['birth_raw'] = r.lifecycle.canonical_bytes(birth)
    checkpoint['birth_sha256'] = r.lifecycle.digest(record['birth_raw'])
    record['checkpoint_raw'] = r.lifecycle.canonical_bytes(checkpoint)
    completion.update(birth_sha256=checkpoint['birth_sha256'],model_sha256=r.lifecycle.digest(record['checkpoint_raw']),
                      source_only_selection_sha256=birth['source_only_selection_sha256'])
    record['completion_raw'] = r.lifecycle.canonical_bytes(completion)


def run_private(case,*,reject_last=False):
    stats = {'arithmetic':[],'pool_checks':0,'fresh_calls':0}
    def fresh():stats['fresh_calls']+=1
    def pool_check(task):
        stats['pool_checks']+=1
        return case.prepared.pools[r.lifecycle.pool_key(task['outer_fold'],task['inner_fold'])]
    def arithmetic(pool,task,model,predictions):
        stats['arithmetic'].append(r.lifecycle.task_key(task))
        assert predictions['scores']==[0.]*len(predictions['scores']),'Invented exact canonical score failure'
        if reject_last and len(stats['arithmetic'])==63:raise AssertionError('Invented final arithmetic failure')
        return {'status':'PASS_SUPPLIED_CHECKPOINT_SCALAR_AND_CANONICAL_ARITHMETIC_ONLY','arm':task['arm'],
                'optimizer_units_not_refitted':task['optimizer_units'],'source_rows':pool['binding']['training_rows'],
                'source_pairs':pool['binding']['training_pairs'],'target_rows':pool['binding']['validation_rows'],
                'exact_canonical_scores_equal':True,'tolerance':1e-9,'new_optimizer_calls':0,
                'input_provenance_or_optimizer_optimality_certified_here':False,**{name:0. for name in r.ERROR_FIELDS}}
    result = r._verify(case.prepared,case.plan,case.birth,case.records,case.complete,
                       pool_check=pool_check,arithmetic_check=arithmetic,fresh=fresh)
    return result,stats


class Cases(unittest.TestCase):
    def test_public_API_has_no_probe_reader_optimizer_or_arithmetic_callback(self):
        self.assertEqual(set(inspect.signature(r.verify_campaign).parameters),
                         {'np','prepared','plan','campaign_birth_raw','records','campaign_complete_raw'})
        tree = ast.parse(inspect.getsource(r.verify_campaign))
        self.assertTrue(any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='fresh_gate' for node in ast.walk(tree)))

    def test_full_63_84_logical_roster_reselection_and_outer_release_with_PRIVATE_stubs(self):
        result,stats = run_private(fixture())
        self.assertEqual(result['verified_checkpoints'],63);self.assertEqual(result['verified_optimizer_units_not_refitted'],84)
        self.assertEqual(len(stats['arithmetic']),63);self.assertEqual(stats['pool_checks'],126)
        self.assertEqual(len(result['source_only_outer_reselections']),9);self.assertEqual(len(result['canonical_outer_records']),9)
        self.assertFalse(result['gate_or_evaluation_run'])
        self.assertFalse(result['input_runtime_Git_or_physical_write_order_provenance_certified_here'])
        self.assertTrue(result['optimizer_count_is_verified_recorded_invocations_not_independent_execution_proof'])

    def test_missing_extra_and_duplicate_records_reject(self):
        for mode in ('missing','extra','duplicate'):
            case = fixture()
            if mode=='missing':case.records.pop()
            elif mode=='extra':case.records.append(copy.deepcopy(case.records[0]))
            else:case.records[-1]=copy.deepcopy(case.records[0])
            with self.subTest(mode=mode),self.assertRaises(AssertionError):run_private(case)

    def test_raw_birth_or_campaign_completion_hash_changes_reject(self):
        case = fixture();case.records[0]['birth_raw'] += b' '
        with self.assertRaises(AssertionError):run_private(case)
        case = fixture();completion = r.lifecycle.strict_json(case.complete);completion['optimizer_units']=83
        case.complete = r.lifecycle.canonical_bytes(completion)
        with self.assertRaises(AssertionError):run_private(case)

    def test_self_consistently_rehashed_wrong_source_birth_still_rejects(self):
        case = fixture();record = case.records[0]
        birth = r.lifecycle.strict_json(record['birth_raw']);birth['identity']['training_ids_sha256']='0'*64
        reseal_record(record,birth=birth);case.complete=seal_campaign(case)
        with self.assertRaises(AssertionError):run_private(case)

    def test_wrong_call_dimensions_or_missing_second_head_reject(self):
        for mode in ('dimension','second_head'):
            case = fixture();record = next(record for record in case.records if record['task_key'].startswith('independent__'))
            completion = r.lifecycle.strict_json(record['completion_raw'])
            if mode=='dimension':completion['optimizer_invocations'][0]['dimension']=204
            else:completion['optimizer_invocations'].pop()
            reseal_record(record,completion=completion);case.complete=seal_campaign(case)
            with self.subTest(mode=mode),self.assertRaises(AssertionError):run_private(case)

    def test_outer_config_cannot_be_self_consistently_changed_to_nonselected_value(self):
        case = fixture();record = next(record for record in case.records if '_final__SOURCE_SELECTED' in record['task_key'])
        birth = r.lifecycle.strict_json(record['birth_raw']);checkpoint = r.lifecycle.strict_json(record['checkpoint_raw'])
        completion = r.lifecycle.strict_json(record['completion_raw']);changed = dict(r.CONFIGS[1])
        birth['identity']['configuration']=changed;birth['source_only_selection']['selected_config']=changed
        checkpoint['model']['config']=changed;completion['configuration']=changed
        reseal_record(record,birth=birth,checkpoint=checkpoint,completion=completion);case.complete=seal_campaign(case)
        with self.assertRaisesRegex(AssertionError,'reselection differs'):run_private(case)

    def test_outer_metrics_digest_and_inner_predecessor_hashes_are_replayed(self):
        for field in ('configuration_metrics_sha256','inner_checkpoint_sha256'):
            case=fixture();record=next(record for record in case.records if '_final__SOURCE_SELECTED' in record['task_key'])
            birth=r.lifecycle.strict_json(record['birth_raw'])
            if field=='configuration_metrics_sha256':birth['source_only_selection'][field]='0'*64
            else:birth['source_only_selection'][field][next(iter(birth['source_only_selection'][field]))]='0'*64
            reseal_record(record,birth=birth);case.complete=seal_campaign(case)
            with self.subTest(field=field),self.assertRaisesRegex(AssertionError,'reselection differs'):run_private(case)

    def test_sub_tolerance_saved_score_change_is_not_a_choice_tolerance(self):
        case=fixture();record=case.records[0];checkpoint=r.lifecycle.strict_json(record['checkpoint_raw'])
        checkpoint['predictions']['scores'][0]=1e-12
        reseal_record(record,checkpoint=checkpoint);case.complete=seal_campaign(case)
        with self.assertRaisesRegex(AssertionError,'exact canonical'):run_private(case)

    def test_no_outer_records_return_if_final_arithmetic_primitive_fails(self):
        case=fixture();released=None
        with self.assertRaisesRegex(AssertionError,'final arithmetic'):
            released=run_private(case,reject_last=True)
        self.assertIsNone(released)

    def test_source_selector_matches_original_on_unequal_folds_instead_of_fold_average(self):
        rows,truths,batches=source_fixture(unmatched=True)
        source=[row for row in rows if row['held_parent_fold']!=0]
        held=[row['intervention_id'] for row in rows if row['held_parent_fold']==0]
        actual_batches={config:{fold:{'row_ids':[row['intervention_id'] for row in source if row['held_parent_fold']==fold],
                    'scores':[scores[row['intervention_id']] for row in source if row['held_parent_fold']==fold]}
                    for fold,scores in by_fold.items()} for config,by_fold in batches.items()}
        actual=independent.reselect(source,[truths[row['intervention_id']] for row in source],0,actual_batches,held)
        expected=original_selection.select_source_config(rows,0,truths,batches)
        self.assertEqual(actual['configuration_metrics'],expected['configuration_metrics'])
        self.assertEqual(actual['selected_config'],r.CONFIGS[1])

    def test_exact_lexical_choice_ties_and_missing_unmatched_OOF_rows(self):
        case=fixture();task=next(task for task in r.lifecycle.task_roster() if task['phase']=='outer')
        pool=case.prepared.pools[r.lifecycle.pool_key(task['outer_fold'],None)]
        batches={config['id']:{fold:{'row_ids':[row['intervention_id'] for row in pool['rows'] if row['held_parent_fold']==fold],
                        'scores':[0. for row in pool['rows'] if row['held_parent_fold']==fold]}
                    for fold in set(r.FOLDS)-{task['outer_fold']}} for config in r.CONFIGS}
        tied=independent.reselect(pool['rows'],pool['effects'],task['outer_fold'],batches,pool['binding']['validation_ids'])
        self.assertEqual(tied['selected_config'],r.CONFIGS[0])
        self.assertEqual(tied['configuration_metrics'][r.CONFIGS[0]['id']]['macro_regret'],.5)
        damaged=copy.deepcopy(batches)
        fold=next(fold for fold,prediction in damaged[r.CONFIGS[0]['id']].items() if any(value.startswith('unmatched:') for value in prediction['row_ids']))
        prediction=damaged[r.CONFIGS[0]['id']][fold];index=next(i for i,value in enumerate(prediction['row_ids']) if value.startswith('unmatched:'))
        prediction['row_ids'].pop(index);prediction['scores'].pop(index)
        with self.assertRaisesRegex(AssertionError,'OOF target order'):
            independent.reselect(pool['rows'],pool['effects'],task['outer_fold'],damaged,pool['binding']['validation_ids'])

    def test_source_selector_rejects_held_IDs_and_never_accepts_held_truth_argument(self):
        self.assertEqual(set(inspect.signature(independent.reselect).parameters),{'rows','effects','outer_fold','batches','held_ids'})
        rows=rows_fixture();source=[row for row in rows if row['held_parent_fold']!=0]
        effects=list(truth_fixture(source).values())
        with self.assertRaises(AssertionError):independent.reselect(source,effects,0,{},[source[0]['intervention_id']])


def run():
    forbidden=('numpy','pandas','scipy','torch','sklearn','openvino')
    def clean():return not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in forbidden)
    assert clean()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt={'status':'PASS_INVENTED_SUPPLIED63_REPLAY_CONTRACTS_WITH_PRIVATE_ARITHMETIC_STUBS_NOT_PROJECT_REPLAY',
             'UTC':datetime.now(timezone.utc).isoformat(),'tests':result.testsRun,
             'sources':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
             'actual_resource_probes':0,'scientific_imports':False,'project_payload_reads':0,
             'actual_optimizer_calls':0,'actual_provider_or_worker_calls':0,
             'actual63_native_arithmetic_replays':0,'private_stubs_used_for_roster_tests':True,
             'actual_input_runtime_commit_admission_or_generalization_certified':False}
    with (ROOT/'results'/NS/'synthetic_tests_receipt.json').open('xb') as stream:
        stream.write((json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


if __name__=='__main__':run()
