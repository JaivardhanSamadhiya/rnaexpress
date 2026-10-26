"""Complete supplied closed-campaign replay under a new fixed real owner.

Original public guarded wrappers remain untouched. No optimizer, file loader,
runtime bootstrap, current-owner admission or evaluation is implemented here.
"""
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_engine_20261023 import adapter
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata
from src.generalization_knowncell_campaign_replay_20261023.replay import _roster,_creation,_selection
from src.generalization_cdrive_checkpoint_forensics_20261026.arithmetic import inspect_checkpoint,ERROR_FIELDS


def replay(np,prepared,plan,campaign_birth_raw,records,campaign_complete_raw,*,fresh,before_checkpoint):
    assert callable(fresh) and callable(before_checkpoint)
    fresh();document=lc.validate_prefit(plan.document())
    assert isinstance(plan,lc.BoundPlan) and isinstance(prepared,adapter.PreparedPools)
    assert lc.digest(plan.prefit_raw)==plan.prefit_sha256
    assert prepared.prefit_document==document and set(prepared.pools)==set(document['source_pools'])
    contract=metadata.full_metadata_contract(prepared.metadata)
    assert [row['intervention_id'] for row in prepared.metadata]==document['all_row_ids']
    assert [row['held_parent_fold'] for row in prepared.metadata]==document['all_row_folds']
    assert contract['row_ids_sha256']==document['input_admission_bindings']['input_row_ids_sha256']
    assert contract['metadata_sha256']==document['input_admission_bindings']['input_metadata_sha256']
    expected,items=_roster(records);identity=plan.identity();birth_sha=lc.digest(campaign_birth_raw)
    assert lc.strict_json(campaign_birth_raw)=={'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**identity}
    complete={'status':'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
        **identity,'campaign_birth_sha256':birth_sha,'inner_checkpoints':54,'outer_checkpoints':9,
        'checkpoint_receipt_sha256':{key:item['sha256']['completion'] for key,item in items.items()},
        'independent_numeric_and_selection_replay_complete':False,'biological_or_gate_claim':False}
    assert lc.strict_json(campaign_complete_raw)==complete
    by_id={row['intervention_id']:row for row in prepared.metadata}
    checked=set();diagnostics={};selections={};outer=[];units=0
    for key,task in expected.items():
        fresh();assert before_checkpoint(key,task) is True
        pool=adapter.check_pool(np,prepared,plan,task)
        assert pool['rows']==[by_id[i] for i in pool['binding']['training_ids']]
        assert pool['validation_metadata']==[by_id[i] for i in pool['binding']['validation_ids']]
        model,predictions=_creation(plan,task,items[key],birth_sha,pool['binding'])
        if task['phase']=='outer':
            selected,metrics=_selection(plan,task,pool,items,expected,checked)
            assert selected==items[key]['birth']['source_only_selection'] and model['config']==selected['selected_config']
            selections[key]={'selection':selected,'configuration_metrics':metrics}
        result=inspect_checkpoint(np,pool,task,model,predictions,fresh=fresh)
        assert result['exact_canonical_scores_equal'] is True and result['new_optimizer_calls']==0
        assert result['recorded_optimizer_units_not_refitted']==task['optimizer_units']
        fresh();assert adapter.check_pool(np,prepared,plan,task)['binding']==pool['binding']
        diagnostics[key]=lc.strict_json(lc.canonical_bytes(result));checked.add(key);units+=task['optimizer_units']
        if task['phase']=='outer':outer.append({'arm':task['arm'],'outer_fold':task['outer_fold'],
            'predictions':lc.strict_json(lc.canonical_bytes(predictions))})
    assert len(checked)==63 and units==84 and len(selections)==len(outer)==9
    fresh()
    return {'status':'PASS_CURRENT_CLOSED63_ARITHMETIC_AND_SOURCE_RESELECTION',
        'campaign_birth_sha256':birth_sha,'campaign_complete_sha256':lc.digest(campaign_complete_raw),
        'prefit_sha256':plan.prefit_sha256,'runtime_binding_sha256':plan.runtime_binding_sha256,
        'verified_checkpoints':63,'recorded_optimizer_units_not_refitted':84,
        'source_only_outer_reselections':selections,'checkpoint_numeric_diagnostics':diagnostics,
        'canonical_outer_records':outer,'new_optimizer_calls':0,'evaluation_or_gate_run':False,
        'maximum_arithmetic_differences':{name:max(row[name] for row in diagnostics.values()) for name in ERROR_FIELDS},
        'input_runtime_or_current_owner_certified_by_this_library':False,
        'new_current_campaign_completion_supplied_and_checked':True,
        'original_old_missing_completion_synthesized':False,'independent_confirmation':False,
        'unknown_cell_generalization':False,'novelty_certified':False}
