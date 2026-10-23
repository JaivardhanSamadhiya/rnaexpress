"""Deferred, explicit numerical functions. There is no runtime bootstrap here.

All scientific objects are supplied by a separately admitted caller. This file
has no project loader, sampler, selector, optimizer entrypoint, writer or guard
override. A mock check of these functions is not native numerical certification.
"""
import math
from .spec import (ARMS, CELLS, CELL_SIGNS, CONFIGS, DEVIATION_MULTIPLIER,
                   FEATURE_WIDTH, SUPPORTED_RMS, CANONICAL_MEAN, METHOD, OPTIONS,
                   SCORER)


def _float_array(np, value):
    return np.array(value, dtype=np.float64, order='C', copy=True)


def _matrix(np, value):
    matrix = _float_array(np, value)
    assert matrix.ndim == 2 and matrix.shape[0] > 0 and matrix.shape[1] == FEATURE_WIDTH
    assert np.isfinite(matrix).all()
    return matrix


def _vectors(np, z, y, w, signs):
    assert z.ndim == 2 and z.shape[0] > 0 and z.shape[1] == FEATURE_WIDTH
    assert y.shape == w.shape == signs.shape == (z.shape[0],)
    assert np.isfinite(z).all() and np.isfinite(y).all() and np.isfinite(w).all()
    assert np.isfinite(signs).all() and all(v in (-1., 1.) for v in y.tolist())
    assert all(v in (-1., 1.) for v in signs.tolist())
    assert all(v > 0. for v in w.tolist())
    assert abs(math.fsum(w.tolist()) - 1.) <= 1e-12
    for sign in (-1., 1.):
        assert abs(math.fsum(v for v, c in zip(w.tolist(), signs.tolist()) if c == sign) - .5) <= 1e-12


def prepare_training(np, x, left, right, labels, weights, cells):
    """Form ONE common source pair RMS, preserving the supplied original roster.

    Metadata/truth/roster provenance belongs to the separately reviewed loader
    and preference contract. This function neither samples nor filters pairs.
    """
    matrix = _matrix(np, x)
    left, right = np.asarray(left), np.asarray(right)
    assert left.ndim == right.ndim == 1 and left.shape == right.shape and left.shape[0] > 0
    assert left.dtype.kind in 'iu' and right.dtype.kind in 'iu'
    assert all(0 <= a < b < len(matrix) for a, b in zip(left.tolist(), right.tolist()))
    assert len(set(zip(left.tolist(), right.tolist()))) == left.shape[0]
    assert len(cells) == left.shape[0] and all(cell in CELLS for cell in cells)
    y, w = _float_array(np, labels), _float_array(np, weights)
    signs = _float_array(np, [CELL_SIGNS[cell] for cell in cells])
    differences = matrix[left] - matrix[right]
    _vectors(np, differences, y, w, signs)
    rms = np.sqrt(np.sum(w[:, None] * differences ** 2, axis=0))
    assert np.isfinite(rms).all()
    active = rms >= SUPPORTED_RMS
    scale = np.where(active, rms, 1.)
    z = differences / scale
    z[:, ~active] = 0.
    assert np.isfinite(z).all()
    return {'z': z, 'labels': y, 'weights': w, 'signs': signs,
            'scaling': {'pair_rms': rms.tolist(), 'scale': scale.tolist(),
                        'active': active.tolist(), 'mean': [0.] * FEATURE_WIDTH},
            'training_rows': len(matrix), 'training_pairs': left.shape[0]}


def _ordinary_value_gradient(np, expit, beta, z, y, w, penalty):
    """Ordinary logistic kernel; conditional heads deliberately use total mass1."""
    margin = y * (z @ beta)
    loss = float(w @ np.logaddexp(0., -margin) + penalty / 2. * (beta @ beta))
    q = -w * y * expit(-margin)
    gradient = z.T @ q + penalty * beta
    assert math.isfinite(loss) and np.isfinite(gradient).all()
    return loss, gradient


def objective_value_gradient(np, expit, arm, theta, z, y, w, signs, penalty):
    """Frozen global objectives, including the independent half-sum reference.

    The fit path validates inputs once rather than repeating full matrix scans
    inside every native optimizer callback. This public reference validates its
    supplied arrays; use only after runtime admission in future native profiles.
    """
    assert arm in ARMS and penalty in [config['penalty'] for config in CONFIGS]
    _vectors(np, z, y, w, signs)
    assert theta.shape == (FEATURE_WIDTH * (1 if arm == 'pooled' else 2),)
    assert np.isfinite(theta).all()
    return _objective(np, expit, arm, theta, z, y, w, signs, penalty)


def _objective(np, expit, arm, theta, z, y, w, signs, penalty):
    p = FEATURE_WIDTH
    if arm == 'pooled':
        return _ordinary_value_gradient(np, expit, theta, z, y, w, penalty)
    first, second = theta[:p], theta[p:]
    if arm == 'joint_shrink10':
        score = z @ first + signs * (z @ second)
        margin = y * score
        loss = float(w @ np.logaddexp(0., -margin) + penalty / 2. *
                     (first @ first + DEVIATION_MULTIPLIER * (second @ second)))
        q = -w * y * expit(-margin)
        gradient = np.concatenate((z.T @ q + penalty * first,
                                   z.T @ (signs * q) + penalty * DEVIATION_MULTIPLIER * second))
    else:
        # Global half-sum representation; fitter below solves two conditional
        # objectives with 2w and lambda/2 rather than changing their lambda.
        use_first = signs == 1.
        score = np.where(use_first, z @ first, z @ second)
        margin = y * score
        loss = float(w @ np.logaddexp(0., -margin) + penalty / 4. * (theta @ theta))
        q = -w * y * expit(-margin)
        gradient = np.concatenate((z.T @ np.where(use_first, q, 0.) + penalty / 2. * first,
                                   z.T @ np.where(use_first, 0., q) + penalty / 2. * second))
    assert math.isfinite(loss) and np.isfinite(gradient).all()
    return loss, gradient


def _scaling(np, scaling):
    assert set(scaling) == {'pair_rms', 'scale', 'active', 'mean'}
    assert scaling['mean'] == [0.] * FEATURE_WIDTH
    assert all(isinstance(v, bool) for v in scaling['active'])
    rms, scale = _float_array(np, scaling['pair_rms']), _float_array(np, scaling['scale'])
    active = np.asarray(scaling['active'])
    assert rms.shape == scale.shape == active.shape == (FEATURE_WIDTH,)
    assert np.isfinite(rms).all() and np.isfinite(scale).all()
    assert all(r >= 0. and s > 0. for r, s in zip(rms.tolist(), scale.tolist()))
    assert active.tolist() == (rms >= SUPPORTED_RMS).tolist()
    assert scale.tolist() == np.where(active, rms, 1.).tolist()
    return scale, active


def _optimize(np, minimize, fun, size, active):
    """Exact old options, zero initialization, no bounds/residual grouping."""
    result = minimize(fun, np.zeros(size, dtype=np.float64), jac=True,
                      method=METHOD, options=dict(OPTIONS))
    assert result.success, str(result.message)
    theta = _float_array(np, result.x)
    assert theta.shape == (size,) and np.isfinite(theta).all()
    support = np.concatenate((active, active)) if size == 2 * FEATURE_WIDTH else active
    assert all(use or value == 0. for value, use in zip(theta.tolist(), support.tolist())), 'Inactive coefficient drift'
    value, gradient = fun(theta)
    assert math.isfinite(float(result.fun)) and abs(float(result.fun) - value) <= 1e-10 * max(1., abs(value))
    assert np.isfinite(gradient).all()
    return theta, {'objective': value, 'success': True, 'message': str(result.message),
                   'iterations': int(result.nit),
                   'maximum_gradient_abs': max(abs(v) for v in gradient.tolist())}


def fit_prepared(np, minimize, expit, prepared, arm, config):
    """Deferred single-arm kernel, not an admitted project training campaign.

    Caller supplies the SAME prepared object for all three arms. Common scaler
    identity and source/checkpoint provenance must be independently bound later.
    """
    assert arm in ARMS and config in CONFIGS
    z, y, w, signs = [prepared[key] for key in ('z', 'labels', 'weights', 'signs')]
    _vectors(np, z, y, w, signs)
    _, active = _scaling(np, prepared['scaling'])
    assert np.all(z[:, ~active] == 0.)
    penalty = config['penalty']; summaries = {}
    model = {'arm': arm, 'config': dict(config), 'scaling': {key: list(value) for key, value in prepared['scaling'].items()},
             'training_rows': prepared['training_rows'], 'training_pairs': prepared['training_pairs'],
             'canonical_mean': CANONICAL_MEAN, 'canonical_scorer': SCORER,
             'optimizer_method': METHOD, 'optimizer_options': dict(OPTIONS),
             'feature_width': FEATURE_WIDTH}
    if arm == 'independent':
        heads = {}
        for cell in CELLS:
            mask = signs == CELL_SIGNS[cell]
            cell_z, cell_y, conditional_w = z[mask], y[mask], 2. * w[mask]
            assert abs(math.fsum(conditional_w.tolist()) - 1.) <= 1e-12
            fun = lambda theta: _ordinary_value_gradient(np, expit, theta, cell_z, cell_y, conditional_w, penalty)
            head, summary = _optimize(np, minimize, fun, FEATURE_WIDTH, active)
            heads[cell] = head.tolist(); summaries[cell] = summary
        model['heads'] = heads
        model['objective'] = .5 * math.fsum(summary['objective'] for summary in summaries.values())
    else:
        fun = lambda theta: _objective(np, expit, arm, theta, z, y, w, signs, penalty)
        theta, summary = _optimize(np, minimize, fun, FEATURE_WIDTH * (2 if arm == 'joint_shrink10' else 1), active)
        model['beta'] = theta[:FEATURE_WIDTH].tolist()
        if arm == 'joint_shrink10': model['delta'] = theta[FEATURE_WIDTH:].tolist()
        summaries['joint' if arm == 'joint_shrink10' else 'pooled'] = summary
        model['objective'] = summary['objective']
    model['optimizer_summaries'] = summaries
    model['optimizer_units'] = 2 if arm == 'independent' else 1
    return model


def canonical_scores(np, model, x, cells):
    """ONE full validation shape, including both complete cell heads.

    The future caller binds exact full target IDs/order/shape; this function
    cannot infer whether a caller has improperly prefiltered that matrix.
    Exact choices use these returned values, not independent rounded sums.
    """
    assert model['arm'] in ARMS and model['config'] in CONFIGS
    assert model['feature_width'] == FEATURE_WIDTH and model['canonical_scorer'] == SCORER
    assert model['canonical_mean'] == CANONICAL_MEAN
    matrix = _matrix(np, x)
    assert len(cells) == len(matrix) and all(cell in CELLS for cell in cells)
    scale, active = _scaling(np, model['scaling'])
    # Keep this exact arithmetic/shape convention frozen; no row/cell subsets,
    # BLAS chunks, active-column compression or alternative mean convention.
    z = (matrix - np.zeros(FEATURE_WIDTH, dtype=np.float64)) / scale
    def coefficient(values):
        result = _float_array(np, values)
        assert result.shape == (FEATURE_WIDTH,) and np.isfinite(result).all()
        assert all(use or value == 0. for value, use in zip(result.tolist(), active.tolist()))
        return result
    arm = model['arm']
    if arm == 'pooled':
        scores = z @ coefficient(model['beta'])
    else:
        if arm == 'independent':
            assert set(model['heads']) == set(CELLS)
            heads = [coefficient(model['heads'][cell]) for cell in CELLS]
        else:
            beta, delta = coefficient(model['beta']), coefficient(model['delta'])
            heads = [beta + CELL_SIGNS[cell] * delta for cell in CELLS]
        first, second = z @ heads[0], z @ heads[1]
        scores = np.where(np.asarray([cell == CELLS[0] for cell in cells]), first, second)
    assert scores.shape == (len(matrix),) and np.isfinite(scores).all()
    return scores
