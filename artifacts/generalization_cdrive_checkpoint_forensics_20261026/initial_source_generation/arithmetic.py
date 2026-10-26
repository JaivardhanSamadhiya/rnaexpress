"""New forensic orchestration of unchanged original pure reference functions.

The public historical replay wrapper retains its original 3 GiB admission.
This file does not invoke or modify it. A future new owned forensic controller
must admit its own inputs/runtime/resources before supplying these objects.
"""
import math
from src.generalization_knowncell_joint_implementation_20261022 import kernels as scalar
from src.generalization_knowncell_joint_implementation_20261022.contracts import preference_contract
from src.generalization_knowncell_joint_implementation_20261022.spec import CELLS, CONFIGS
from src.generalization_knowncell_joint_campaign_20261023.writer import check_model, check_predictions
from src.generalization_knowncell_joint_replay_20261023.arithmetic import (
    bound_difference, conditional_objective, independent_canonical,
)
from . import spec

ERROR_FIELDS = ('maximum_scaling_difference','maximum_objective_difference',
                'maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference')


def inspect_checkpoint(np, pool, task, model, predictions, *, fresh):
    """Return consistency diagnostics only; never publish predictions/utility.

    `fresh` is a mandatory callback from a future fixed reviewed controller,
    not an alternative implementation of any historical resource function.
    No optimizer, model writer, evaluator or gate is accepted by this API.
    """
    assert callable(fresh)
    fresh()
    binding = pool['binding']
    config = model['config']
    assert config in CONFIGS
    check_model(model, task, config, binding)
    check_predictions(predictions, binding)
    rows = pool['rows']
    assert len(rows) == len(pool['effects'])
    truths = dict(zip([row['intervention_id'] for row in rows], pool['effects']))
    assert len(truths) == len(rows)
    left, right, labels = pool['left'], pool['right'], pool['labels']
    weights = preference_contract(rows, truths, left, right, labels)
    assert weights == pool['prepared']['weights'].tolist()
    cells = [rows[index]['cell_type'] for index in left]
    training = pool['features'].tolist()
    assert len(training) == len(rows) and all(len(row) == 102 for row in training)
    differences = [[a-b for a,b in zip(training[one],training[two])] for one,two in zip(left,right)]
    fresh()
    scaling = scalar.common_scale(differences, weights)
    assert scaling['active'] == model['scaling']['active']
    scale_difference = max(bound_difference(a,b) for key in ('pair_rms','scale')
                           for a,b in zip(scaling[key],model['scaling'][key]))
    # Retain the saved, birth-bound scaler after checking independent agreement.
    actual_scale, active = model['scaling']['scale'], model['scaling']['active']
    z = [[value/scale if use else 0. for value,scale,use in zip(row,actual_scale,active)]
         for row in differences]
    arm, penalty = task['arm'], config['penalty']
    objective_errors, gradient_errors = [], []
    if arm == 'independent':
        theta = model['heads'][CELLS[0]] + model['heads'][CELLS[1]]
        global_value, _ = scalar.independent_value_gradient(theta,z,labels,weights,cells,penalty)
        for cell in CELLS:
            fresh()
            value, gradient = conditional_objective(model['heads'][cell],z,labels,weights,cells,cell,penalty)
            saved = model['optimizer_summaries'][cell]
            objective_errors.append(bound_difference(value,saved['objective']))
            gradient_errors.append(bound_difference(max(abs(v) for v in gradient),saved['maximum_gradient_abs']))
    else:
        theta = model['beta'] + (model['delta'] if arm == 'joint_shrink10' else [])
        function = scalar.joint_value_gradient if arm == 'joint_shrink10' else scalar.pooled_value_gradient
        fresh()
        global_value, gradient = function(theta,z,labels,weights,cells,penalty)
        saved = model['optimizer_summaries']['joint' if arm == 'joint_shrink10' else 'pooled']
        objective_errors.append(bound_difference(global_value,saved['objective']))
        gradient_errors.append(bound_difference(max(abs(v) for v in gradient),saved['maximum_gradient_abs']))
    objective_errors.append(bound_difference(global_value,model['objective']))
    fresh()
    target_cells = [row['cell_type'] for row in pool['validation_metadata']]
    canonical = independent_canonical(np,model,pool['validation_features'],target_cells).tolist()
    assert predictions['scores'] == canonical, 'Exact canonical full-shape score replay failed'
    scalar_scores = scalar.reference_scores(arm,pool['validation_features'].tolist(),target_cells,model)
    score_error = max(bound_difference(a,b) for a,b in zip(canonical,scalar_scores))
    fresh()
    result = {'status':spec.NUMERICAL_STATUS,'arm':arm,
        'source_rows':len(rows),'source_pairs':len(left),'target_rows':len(canonical),
        'maximum_scaling_difference':scale_difference,
        'maximum_objective_difference':max(objective_errors),
        'maximum_recorded_gradient_norm_difference':max(gradient_errors),
        'maximum_scalar_score_difference':score_error,
        'exact_canonical_scores_equal':True,'tolerance_strictly_below':spec.TOLERANCE,
        'recorded_optimizer_units_not_refitted':task['optimizer_units'],
        'new_optimizer_calls':0,'outer_performance_computed':False,
        'old_campaign_closure_or_current_owner_certified':False,
        'optimizer_optimality_or_execution_history_certified':False}
    assert all(math.isfinite(result[name]) and 0 <= result[name] < spec.TOLERANCE for name in ERROR_FIELDS)
    return result
