"""All63 supplied-artifact arithmetic, without campaign completion admission.

No file reader/provider/optimizer/controller is implemented here. Historical
plans describe saved scientific identities only; they confer no current owner.
"""
import math
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_engine_20261023 import adapter
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata
from src.generalization_knowncell_campaign_replay_20261023.replay import _roster, _creation, _selection
from . import spec
from .arithmetic import inspect_checkpoint, ERROR_FIELDS


def _inspect(np, prepared, historical_plan, campaign_birth_raw, records, *, fresh, pool_check, numeric_check):
    """Private dependency stubs are permitted only for invented roster tests."""
    fresh()
    expected, items = _roster(records)
    identity = historical_plan.identity()
    assert lc.strict_json(campaign_birth_raw) == {'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**identity}
    birth_sha = lc.digest(campaign_birth_raw)
    checked, diagnostics, selection_hashes = set(), {}, {}
    units = 0
    for key, task in expected.items():
        fresh()
        pool = pool_check(task)
        assert pool['binding'] == historical_plan.pool(task)
        model, predictions = _creation(historical_plan,task,items[key],birth_sha,pool['binding'])
        if task['phase'] == 'outer':
            selected, _ = _selection(historical_plan,task,pool,items,expected,checked)
            assert items[key]['birth']['source_only_selection'] == selected
            assert model['config'] == selected['selected_config']
            # Do not publish source metrics, predictions or configuration values.
            selection_hashes[key] = lc.hash_value(selected)
        result = numeric_check(pool,task,model,predictions)
        assert result['status'] == spec.NUMERICAL_STATUS and result['arm'] == task['arm']
        assert result['source_rows'] == pool['binding']['training_rows']
        assert result['source_pairs'] == pool['binding']['training_pairs']
        assert result['target_rows'] == pool['binding']['validation_rows']
        assert result['new_optimizer_calls'] == 0 and result['exact_canonical_scores_equal'] is True
        assert result['tolerance_strictly_below'] == spec.TOLERANCE
        assert result['outer_performance_computed'] is False
        assert result['old_campaign_closure_or_current_owner_certified'] is False
        assert result['recorded_optimizer_units_not_refitted'] == task['optimizer_units']
        assert all(math.isfinite(result[name]) and 0 <= result[name] < spec.TOLERANCE for name in ERROR_FIELDS)
        fresh()
        assert pool_check(task)['binding'] == pool['binding']
        diagnostics[key] = lc.strict_json(lc.canonical_bytes(result))
        checked.add(key)
        units += task['optimizer_units']
    assert len(checked) == spec.CHECKPOINTS and units == spec.RECORDED_UNITS
    assert len(selection_hashes) == spec.SOURCE_SELECTIONS
    fresh()
    return {'status':spec.SUPPLIED_STATUS,'saved_campaign_birth_sha256':birth_sha,
        'historical_prefit_sha256':historical_plan.prefit_sha256,
        'historical_runtime_binding_sha256':historical_plan.runtime_binding_sha256,
        'verified_checkpoints':63,'verified_inner_checkpoints':54,'verified_outer_checkpoints':9,
        'recorded_optimizer_units_not_refitted':84,'source_only_reselections_equal':9,
        'source_selection_declaration_sha256':selection_hashes,
        'checkpoint_numeric_diagnostics':diagnostics,
        'maximum_arithmetic_differences':{name:max(value[name] for value in diagnostics.values()) for name in ERROR_FIELDS},
        'biological_inputs_read':True,'new_optimizer_calls':0,'evaluation_or_gate_run':False,
        'outer_performance_computed_or_published':False,'independent_confirmation':False,
        'old_campaign_completion_missing':True,'old_supervisor_completion_missing':True,
        'original_formal_replay_still_ineligible':True,
        'historical_plan_is_not_a_current_owner_or_runtime_admission':True,
        'old_runtime_full_identity_established':False,'biological_or_generalization_claim':False}


def inspect_supplied(np, prepared, historical_plan, campaign_birth_raw, records, *, fresh):
    """Future new-stage caller must independently admit ALL actual objects.

    No campaign_complete argument exists and no lifecycle status is synthesized.
    This API cannot authorize reads, imports, a Job, current ownership, fitting,
    formal replay, evaluation or a gate. The deferred controller is pending.
    """
    fresh()
    contract = metadata.full_metadata_contract(prepared.metadata)
    document = lc.validate_prefit(historical_plan.document())
    assert prepared.prefit_document == document
    assert len(prepared.pools) == spec.POOLS and set(prepared.pools) == set(document['source_pools'])
    assert [row['intervention_id'] for row in prepared.metadata] == document['all_row_ids']
    assert [row['held_parent_fold'] for row in prepared.metadata] == document['all_row_folds']
    inputs = document['input_admission_bindings']
    assert contract['row_ids_sha256'] == inputs['input_row_ids_sha256']
    assert contract['metadata_sha256'] == inputs['input_metadata_sha256']
    by_id = {row['intervention_id']:row for row in prepared.metadata}
    def pool_check(task):
        fresh()
        pool = prepared.pools[lc.pool_key(task['outer_fold'],task['inner_fold'])]
        assert adapter.pool_binding(np,pool) == pool['binding'] == historical_plan.pool(task)
        assert pool['rows'] == [by_id[key] for key in pool['binding']['training_ids']]
        assert pool['validation_metadata'] == [by_id[key] for key in pool['binding']['validation_ids']]
        return pool
    def numeric_check(pool,task,model,predictions):
        return inspect_checkpoint(np,pool,task,model,predictions,fresh=fresh)
    return _inspect(np,prepared,historical_plan,campaign_birth_raw,records,
                    fresh=fresh,pool_check=pool_check,numeric_check=numeric_check)
