"""Separate scalar objective/scaling and full-shape canonical score replay.

All inputs and numerical objects must come from a future admitted controller.
This layer opens no file, imports no scientific package and fits no model.
It does not certify the supplied pools' provenance or a whole campaign.
"""
import math
from src.generalization_knowncell_joint_implementation_20261022 import kernels as scalar
from src.generalization_knowncell_joint_implementation_20261022.contracts import preference_contract
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
from src.generalization_knowncell_joint_implementation_20261022.spec import CELLS, CONFIGS
from src.generalization_knowncell_joint_campaign_20261023.writer import check_model, check_predictions

TOLERANCE = 1e-9


def fresh(probe, environment):
    return require_resources(probe(), environment)


def bound_difference(actual, expected):
    assert math.isfinite(actual) and math.isfinite(expected)
    difference = abs(actual-expected)
    assert difference < TOLERANCE, 'Independent arithmetic difference exceeds the original bound'
    return difference


def independent_canonical(np, model, features, cells):
    """Reconstruct the exact full-102 C/float64 convention independently.

    No call to the production numerical scorer is made. The complete matrix is
    used for both cell heads. Scalar tolerances never replace these exact ties.
    """
    matrix = np.array(features, dtype=np.float64, order='C', copy=True)
    assert matrix.shape == (len(cells), 102) and len(cells) > 0
    assert np.isfinite(matrix).all() and all(cell in CELLS for cell in cells)
    scale = np.array(model['scaling']['scale'], dtype=np.float64, order='C', copy=True)
    assert scale.shape == (102,) and np.isfinite(scale).all()
    assert all(value > 0 for value in scale.tolist())
    assert model['scaling']['mean'] == [0.]*102
    normalized = (matrix-np.zeros(102, dtype=np.float64))/scale
    def coefficient(values):
        array = np.array(values, dtype=np.float64, order='C', copy=True)
        assert array.shape == (102,) and np.isfinite(array).all()
        return array
    arm = model['arm']
    if arm == 'pooled':
        result = normalized @ coefficient(model['beta'])
    else:
        assert arm in ('independent', 'joint_shrink10')
        if arm == 'independent':
            one, two = [coefficient(model['heads'][cell]) for cell in CELLS]
        else:
            beta, delta = coefficient(model['beta']), coefficient(model['delta'])
            one, two = beta+delta, beta-delta
        first, second = normalized @ one, normalized @ two
        result = np.where(np.asarray([cell == CELLS[0] for cell in cells]), first, second)
    assert result.shape == (len(cells),) and np.isfinite(result).all()
    return result


def conditional_objective(theta, z, labels, weights, cells, cell, penalty):
    """Independent head's conditional loss uses 2w and lambda/2."""
    gradient = [penalty*value for value in theta]
    losses = []
    for row, label, weight, actual_cell in zip(z, labels, weights, cells):
        if actual_cell != cell:
            continue
        loss, residual = scalar.residual(label*scalar.dot(row, theta), label, 2.*weight)
        losses.append(loss)
        for j in range(102):
            gradient[j] += row[j]*residual
    return math.fsum(losses)+penalty/2.*scalar.dot(theta, theta), gradient


def replay_checkpoint(np, pool, task, model, predictions, *, probe, environment):
    """Verify supplied checkpoint arithmetic; no optimizer or result selection.

    The future caller must first bind the pool/birth/completion to the immutable
    committed prefit. These independent computations supplement that proof.
    """
    fresh(probe, environment)
    binding = pool['binding']
    config = model['config']
    assert config in CONFIGS
    check_model(model, task, config, binding)
    check_predictions(predictions, binding)
    rows = pool['rows']
    truths = {row['intervention_id']:value for row,value in zip(rows, pool['effects'])}
    assert len(rows) == len(pool['effects']) and len(truths) == len(rows)
    left, right, labels = pool['left'], pool['right'], pool['labels']
    weights = preference_contract(rows, truths, left, right, labels)
    assert weights == pool['prepared']['weights'].tolist()
    cells = [rows[index]['cell_type'] for index in left]
    training = pool['features'].tolist()
    assert len(training) == len(rows) and all(len(row) == 102 for row in training)
    differences = [[a-b for a,b in zip(training[one], training[two])] for one,two in zip(left,right)]
    scaling = scalar.common_scale(differences, weights)
    assert scaling['active'] == model['scaling']['active'], 'Independent support differs; do not repair'
    scale_difference = max(bound_difference(a,b) for key in ('pair_rms', 'scale')
                           for a,b in zip(scaling[key], model['scaling'][key]))
    # Use the birth-bound actual scaler for objective/scoring replay, after its
    # independent bound. Do not redefine saved coefficients or canonical scores.
    actual_scale = model['scaling']['scale']
    active = model['scaling']['active']
    z = [[value/scale if use else 0. for value,scale,use in zip(row,actual_scale,active)]
         for row in differences]
    arm, penalty = task['arm'], config['penalty']
    objective_differences, gradient_differences = [], []
    if arm == 'independent':
        theta = model['heads'][CELLS[0]]+model['heads'][CELLS[1]]
        global_value, _ = scalar.independent_value_gradient(theta, z, labels, weights, cells, penalty)
        for cell in CELLS:
            value, gradient = conditional_objective(model['heads'][cell], z, labels, weights, cells, cell, penalty)
            saved = model['optimizer_summaries'][cell]
            objective_differences.append(bound_difference(value, saved['objective']))
            gradient_differences.append(bound_difference(max(abs(v) for v in gradient), saved['maximum_gradient_abs']))
    else:
        theta = model['beta']+(model['delta'] if arm == 'joint_shrink10' else [])
        function = scalar.joint_value_gradient if arm == 'joint_shrink10' else scalar.pooled_value_gradient
        global_value, gradient = function(theta, z, labels, weights, cells, penalty)
        saved = model['optimizer_summaries']['joint' if arm == 'joint_shrink10' else 'pooled']
        objective_differences.append(bound_difference(global_value, saved['objective']))
        gradient_differences.append(bound_difference(max(abs(v) for v in gradient), saved['maximum_gradient_abs']))
    objective_differences.append(bound_difference(global_value, model['objective']))
    fresh(probe, environment)
    target_cells = [row['cell_type'] for row in pool['validation_metadata']]
    replay = independent_canonical(np, model, pool['validation_features'], target_cells).tolist()
    assert predictions['scores'] == replay, 'Exact canonical full-shape score replay failed'
    scalar_prediction = scalar.reference_scores(arm, pool['validation_features'].tolist(), target_cells, model)
    score_difference = max(bound_difference(a,b) for a,b in zip(replay, scalar_prediction))
    fresh(probe, environment)
    return {'status':'PASS_SUPPLIED_CHECKPOINT_SCALAR_AND_CANONICAL_ARITHMETIC_ONLY',
            'arm':arm, 'optimizer_units_not_refitted':task['optimizer_units'],
            'source_rows':len(rows), 'source_pairs':len(left), 'target_rows':len(replay),
            'maximum_scaling_difference':scale_difference,
            'maximum_objective_difference':max(objective_differences),
            'maximum_recorded_gradient_norm_difference':max(gradient_differences),
            'maximum_scalar_score_difference':score_difference,
            'exact_canonical_scores_equal':True, 'tolerance':TOLERANCE,
            'new_optimizer_calls':0, 'whole_campaign_or_gate_verified':False,
            'input_provenance_or_optimizer_optimality_certified_here':False}
