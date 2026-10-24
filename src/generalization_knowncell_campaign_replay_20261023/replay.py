"""Full supplied63 checkpoint replay; no file reader, optimizer or runtime load."""
import math
import os
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_joint_campaign_20261023.writer import check_model,check_predictions,unit_spec
from src.generalization_knowncell_joint_implementation_20261022.admission import birth_identity
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata
from src.generalization_knowncell_joint_design_20261009.spec import ARMS,CONFIGS,FOLDS
from src.generalization_knowncell_joint_engine_20261023 import adapter
from src.generalization_knowncell_joint_replay_20261023 import arithmetic
from src.generalization_knowncell_joint_loader_20261022 import guard
from .selection import reselect

HASHES = ('training_ids_sha256','training_metadata_sha256','training_features_sha256','training_effects_sha256',
          'original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256')
BIRTH_FIELDS = {'task_key','identity','campaign_birth_sha256','source_pool_sha256','validation_ids_sha256',
                'validation_metadata_sha256','validation_features_sha256','validation_effects_sha256','validation_rows',
                'full_validation_shape','prefit_commit','source_only_selection_sha256','source_only_selection'}
COMPLETE_FIELDS = {'status','task_key','birth_sha256','model_sha256','optimizer_invocations','optimizer_units',
                   'configuration','source_only_selection_sha256','campaign_birth_sha256'}
SELECTION_FIELDS = {'arm','outer_fold','selected_config','source_only','primary_paired_only','selection_rule',
                    'prefit_sha256','runtime_binding_sha256','source_training_ids_sha256',
                    'configuration_metrics_sha256','inner_checkpoint_sha256'}
ERROR_FIELDS = ('maximum_scaling_difference','maximum_objective_difference',
                'maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference')


def _copy(value):
    return lifecycle.strict_json(lifecycle.canonical_bytes(value))


def _roster(records):
    assert isinstance(records,(list,tuple)) and len(records)==63
    expected = {lifecycle.task_key(task):task for task in lifecycle.task_roster()}
    parsed = {}
    for record in records:
        assert isinstance(record,dict) and set(record)=={'task_key','birth_raw','checkpoint_raw','completion_raw'}
        key = record['task_key']
        assert key in expected and key not in parsed,'Missing/extra/duplicated checkpoint key'
        parsed[key] = {name:lifecycle.strict_json(record[name+'_raw']) for name in ('birth','checkpoint','completion')}
        parsed[key]['sha256'] = {name:lifecycle.digest(record[name+'_raw']) for name in ('birth','checkpoint','completion')}
    assert set(parsed)==set(expected) and len(expected)==63
    return expected,parsed


def _creation(plan,task,item,campaign_birth_sha,pool):
    key = lifecycle.task_key(task)
    birth,saved,complete = item['birth'],item['checkpoint'],item['completion']
    assert set(birth)==BIRTH_FIELDS and set(complete)==COMPLETE_FIELDS
    assert set(saved)=={'task_key','birth_sha256','model','predictions'}
    assert birth['task_key']==saved['task_key']==complete['task_key']==key
    assert complete['status']=='CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY'
    assert complete['birth_sha256']==saved['birth_sha256']==item['sha256']['birth']
    assert complete['model_sha256']==item['sha256']['checkpoint']
    assert birth['campaign_birth_sha256']==complete['campaign_birth_sha256']==campaign_birth_sha
    assert birth['source_pool_sha256']==lifecycle.hash_value(pool)
    config = complete['configuration']
    assert config in CONFIGS
    expected_identity = birth_identity(arm=task['arm'],phase=task['phase'],outer_fold=task['outer_fold'],
        inner_fold=task['inner_fold'],configuration=config,runtime_binding_sha256=plan.runtime_binding_sha256,
        prefit_sha256=plan.prefit_sha256,**{name:pool[name] for name in HASHES})
    assert birth['identity']==expected_identity
    for name in ('validation_ids_sha256','validation_metadata_sha256','validation_features_sha256',
                 'validation_effects_sha256','validation_rows'):
        assert birth[name]==pool[name]
    assert birth['full_validation_shape']==[pool['validation_rows'],102] and birth['prefit_commit']==plan.prefit_commit
    assert birth['source_only_selection_sha256']==complete['source_only_selection_sha256']
    calls = complete['optimizer_invocations']
    assert isinstance(calls,list) and len(calls)==task['optimizer_units']
    assert all(isinstance(call,dict) and set(call)=={'name','dimension','started','returned'} for call in calls)
    assert [(call['name'],call['dimension']) for call in calls]==unit_spec(task['arm'])
    assert all(type(call['dimension']) is int for call in calls)
    assert all(call['started'] is True and call['returned'] is True for call in calls)
    assert type(complete['optimizer_units']) is int and complete['optimizer_units']==task['optimizer_units']==len(calls)
    check_model(saved['model'],task,config,pool)
    check_predictions(saved['predictions'],pool)
    assert all(type(value) is float for value in saved['predictions']['scores'])
    if task['phase']=='inner':
        assert config==next(value for value in CONFIGS if value['id']==task['configuration_id'])
        assert birth['source_only_selection'] is birth['source_only_selection_sha256'] is None
    else:
        value = birth['source_only_selection']
        assert isinstance(value,dict) and set(value)==SELECTION_FIELDS
        assert lifecycle.hash_value(value)==birth['source_only_selection_sha256']
    return saved['model'],saved['predictions']


def _selection(plan,task,pool,items,expected,verified):
    batches = {config['id']:{} for config in CONFIGS}
    hashes = {}
    for key,inner in expected.items():
        if inner['phase']!='inner' or inner['arm']!=task['arm'] or inner['outer_fold']!=task['outer_fold']:continue
        assert key in verified,'Source selector cannot consume an unverified checkpoint'
        batches[inner['configuration_id']][inner['inner_fold']] = items[key]['checkpoint']['predictions']
        hashes[key] = items[key]['sha256']['checkpoint']
    assert len(hashes)==6
    assert pool['binding']==plan.pool(task)
    assert metadata.ids_sha(pool['rows'])==pool['binding']['training_ids_sha256']
    assert metadata.metadata_sha(pool['rows'])==pool['binding']['training_metadata_sha256']
    assert lifecycle.hash_value(pool['effects'])==pool['binding']['training_effects_json_sha256']
    chosen = reselect(pool['rows'],pool['effects'],task['outer_fold'],batches,pool['binding']['validation_ids'])
    receipt = {'arm':task['arm'],'outer_fold':task['outer_fold'],'selected_config':chosen['selected_config'],
        'source_only':True,'primary_paired_only':True,
        'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
        'prefit_sha256':plan.prefit_sha256,'runtime_binding_sha256':plan.runtime_binding_sha256,
        'source_training_ids_sha256':pool['binding']['training_ids_sha256'],
        'configuration_metrics_sha256':lifecycle.hash_value(chosen['configuration_metrics']),
        'inner_checkpoint_sha256':hashes}
    return receipt,chosen['configuration_metrics']


def _verify(prepared,plan,campaign_birth_raw,records,campaign_complete_raw,*,pool_check,arithmetic_check,fresh):
    """Private stubs are for invented roster tests; public dependencies are fixed."""
    fresh()
    expected,items = _roster(records)
    identity = plan.identity()
    campaign_birth = lifecycle.strict_json(campaign_birth_raw)
    assert campaign_birth=={'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**identity}
    campaign_birth_sha = lifecycle.digest(campaign_birth_raw)
    complete = lifecycle.strict_json(campaign_complete_raw)
    expected_complete = {'status':'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
        **identity,'campaign_birth_sha256':campaign_birth_sha,'inner_checkpoints':54,'outer_checkpoints':9,
        'checkpoint_receipt_sha256':{key:item['sha256']['completion'] for key,item in items.items()},
        'independent_numeric_and_selection_replay_complete':False,'biological_or_gate_claim':False}
    assert complete==expected_complete,'Campaign completion, roster or predecessor hashes differ'
    verified,arithmetic_receipts,selections,outer = set(),{},{},[]
    units = 0
    for key,task in expected.items():
        fresh()
        pool = pool_check(task)
        assert pool['binding']==plan.pool(task)
        model,predictions = _creation(plan,task,items[key],campaign_birth_sha,pool['binding'])
        if task['phase']=='outer':
            selection,metrics = _selection(plan,task,pool,items,expected,verified)
            assert items[key]['birth']['source_only_selection']==selection,'Independent source-only reselection differs'
            assert model['config']==selection['selected_config']
            selections[key] = {'selection':selection,'configuration_metrics':metrics}
        fresh()
        receipt = arithmetic_check(pool,task,model,predictions)
        assert receipt['status']=='PASS_SUPPLIED_CHECKPOINT_SCALAR_AND_CANONICAL_ARITHMETIC_ONLY'
        assert receipt['arm']==task['arm'] and receipt['optimizer_units_not_refitted']==task['optimizer_units']
        assert receipt['source_rows']==pool['binding']['training_rows'] and receipt['source_pairs']==pool['binding']['training_pairs']
        assert receipt['target_rows']==pool['binding']['validation_rows']
        assert receipt['exact_canonical_scores_equal'] is True and receipt['tolerance']==1e-9
        assert receipt['new_optimizer_calls']==0 and receipt['input_provenance_or_optimizer_optimality_certified_here'] is False
        for name in ERROR_FIELDS:
            assert type(receipt[name]) in (int,float) and math.isfinite(receipt[name]) and 0<=receipt[name]<1e-9
        # Bind the exact supplied values again after primitive replay, so an
        # input mutation during numerical work cannot receive a clean result.
        fresh()
        assert pool_check(task)['binding']==pool['binding']
        arithmetic_receipts[key] = _copy(receipt)
        verified.add(key);units += task['optimizer_units']
        if task['phase']=='outer':
            outer.append({'arm':task['arm'],'outer_fold':task['outer_fold'],'predictions':_copy(predictions)})
    assert len(verified)==63 and units==84 and len(selections)==len(outer)==9
    assert {(row['arm'],row['outer_fold']) for row in outer}=={(arm,fold) for arm in ARMS for fold in FOLDS}
    fresh()
    # No partial outputs are exposed. Canonical outer records leave this step
    # only after EVERY lifecycle, arithmetic and source-selection check passed.
    return {'status':'PASS_SUPPLIED63_CHECKPOINT84_UNIT_ARITHMETIC_AND_SOURCE_RESELECTION',
        'campaign_birth_sha256':campaign_birth_sha,'campaign_complete_sha256':lifecycle.digest(campaign_complete_raw),
        'prefit_sha256':plan.prefit_sha256,'runtime_binding_sha256':plan.runtime_binding_sha256,
        'verified_checkpoints':63,'verified_optimizer_units_not_refitted':84,'verified_inner_checkpoints':54,
        'source_only_outer_reselections':selections,'arithmetic_receipts':arithmetic_receipts,
        'canonical_outer_records':outer,'new_optimizer_calls':0,'gate_or_evaluation_run':False,
        'maximum_arithmetic_differences':{name:max(value[name] for value in arithmetic_receipts.values()) for name in ERROR_FIELDS},
        'optimizer_count_is_verified_recorded_invocations_not_independent_execution_proof':True,
        'input_runtime_Git_or_physical_write_order_provenance_certified_here':False,
        'independent_confirmation':False,'unknown_cell_generalization':False,'novelty_certified':False}


def verify_campaign(np,prepared,plan,campaign_birth_raw,records,campaign_complete_raw):
    """Full in-memory replay after external source/input/runtime/Git admission.

    There is no reader, native import, provider, public guard override or fit.
    The original real guard is used. This API is not invoked in preparation.
    """
    guard.fresh_gate()
    assert isinstance(plan,lifecycle.BoundPlan) and isinstance(prepared,adapter.PreparedPools)
    assert lifecycle.digest(plan.prefit_raw)==plan.prefit_sha256
    document = lifecycle.validate_prefit(plan.document())
    assert document['runtime_binding_sha256']==plan.runtime_binding_sha256
    lifecycle.valid_hash(plan.prefit_commit,40)
    assert prepared.prefit_document==document and set(prepared.pools)==set(document['source_pools'])
    metadata_contract = metadata.full_metadata_contract(prepared.metadata)
    assert [row['intervention_id'] for row in prepared.metadata]==document['all_row_ids']
    assert [row['held_parent_fold'] for row in prepared.metadata]==document['all_row_folds']
    admissions = document['input_admission_bindings']
    assert metadata_contract['row_ids_sha256']==admissions['input_row_ids_sha256']
    assert metadata_contract['metadata_sha256']==admissions['input_metadata_sha256']
    by_id = {row['intervention_id']:row for row in prepared.metadata}
    def pool_check(task):
        guard.fresh_gate()
        pool = adapter.check_pool(np,prepared,plan,task)
        binding = plan.pool(task)
        assert pool['rows']==[by_id[identifier] for identifier in binding['training_ids']]
        assert pool['validation_metadata']==[by_id[identifier] for identifier in binding['validation_ids']]
        return pool
    def arithmetic_check(pool,task,model,predictions):
        return arithmetic.replay_checkpoint(np,pool,task,model,predictions,probe=guard.live_resources,environment=os.environ)
    return _verify(prepared,plan,campaign_birth_raw,records,campaign_complete_raw,
                   pool_check=pool_check,arithmetic_check=arithmetic_check,fresh=guard.fresh_gate)
