"""Explicit scalar-reference objectives, not a NumPy fitter or optimizer.

The functions are usable on invented lists without importing a numerical
runtime. They define the arithmetic a future vectorized implementation must
match, and do not implement an alternative sampler or optimizer.
"""
import math
from .spec import CELLS, CELL_SIGNS, DEVIATION_MULTIPLIER, SUPPORTED_RMS


def dot(a, b):
    assert len(a) == len(b)
    return math.fsum(u * v for u, v in zip(a, b))


def validate(z, y, w, cells):
    assert len(z) == len(y) == len(w) == len(cells) > 0
    p = len(z[0]); assert p > 0
    assert all(len(row) == p and all(math.isfinite(x) for x in row) for row in z)
    assert all(value in (-1, 1) for value in y)
    assert all(cell in CELLS for cell in cells)
    assert all(math.isfinite(value) and value > 0 for value in w)
    assert abs(math.fsum(w) - 1.) <= 1e-12
    for cell in CELLS:
        assert abs(math.fsum(value for value, c in zip(w, cells) if c == cell) - .5) <= 1e-12
    return p


def residual(margin, label, weight):
    """Stable logistic loss and derivative with respect to the raw score."""
    assert math.isfinite(margin)
    loss = max(0., -margin) + math.log1p(math.exp(-abs(margin)))
    if margin >= 0:
        e = math.exp(-margin); derivative = -weight * label * e / (1. + e)
    else:
        derivative = -weight * label / (1. + math.exp(margin))
    return weight * loss, derivative


def joint_value_gradient(theta, z, y, w, cells, penalty):
    """Fixed shrink10 loss; theta=(beta,delta), no redundant per-cell residuals."""
    return shared_reference(theta, z, y, w, cells, penalty, DEVIATION_MULTIPLIER)


def shared_reference(theta, z, y, w, cells, penalty, multiplier):
    """Explicit reference also exposes multiplier1 for invented equivalence tests.

    Production is permitted to call joint_value_gradient only. This helper is
    not a multiplier grid, fitting entrypoint or extra experimental arm.
    """
    p = validate(z, y, w, cells)
    assert len(theta) == 2 * p and all(math.isfinite(x) for x in theta)
    assert math.isfinite(penalty) and penalty > 0
    assert math.isfinite(multiplier) and multiplier > 0
    beta, delta = theta[:p], theta[p:]
    gb = [penalty * b for b in beta]
    gd = [penalty * multiplier * d for d in delta]
    losses = []
    for row, label, weight, cell in zip(z, y, w, cells):
        sign = CELL_SIGNS[cell]
        loss, q = residual(label * (dot(row, beta) + sign * dot(row, delta)), label, weight)
        losses.append(loss)
        for j in range(p):
            gb[j] += row[j] * q
            gd[j] += sign * row[j] * q
    value = math.fsum(losses) + penalty / 2. * (dot(beta, beta) + multiplier * dot(delta, delta))
    assert math.isfinite(value) and all(math.isfinite(x) for x in gb + gd)
    return value, gb + gd


def pooled_value_gradient(beta, z, y, w, cells, penalty):
    p = validate(z, y, w, cells)
    assert len(beta) == p and all(math.isfinite(x) for x in beta)
    assert math.isfinite(penalty) and penalty > 0
    gradient = [penalty * x for x in beta]; losses = []
    for row, label, weight in zip(z, y, w):
        loss, q = residual(label * dot(row, beta), label, weight); losses.append(loss)
        for j in range(p): gradient[j] += row[j] * q
    return math.fsum(losses) + penalty / 2. * dot(beta, beta), gradient


def independent_value_gradient(theta, z, y, w, cells, penalty):
    """Global half-sum of conditional cell objectives; penalty=lambda/4 per head."""
    p = validate(z, y, w, cells)
    assert len(theta) == 2 * p and all(math.isfinite(x) for x in theta)
    assert math.isfinite(penalty) and penalty > 0
    gradient = [penalty / 2. * x for x in theta]; losses = []
    for row, label, weight, cell in zip(z, y, w, cells):
        offset = 0 if cell == CELLS[0] else p
        loss, q = residual(label * dot(row, theta[offset:offset+p]), label, weight); losses.append(loss)
        for j in range(p): gradient[offset+j] += row[j] * q
    return math.fsum(losses) + penalty / 4. * dot(theta, theta), gradient


def common_scale(differences, weights):
    assert differences and len(differences) == len(weights)
    p = len(differences[0]); assert p > 0
    assert all(len(row) == p and all(math.isfinite(x) for x in row) for row in differences)
    assert all(math.isfinite(w) and w > 0 for w in weights)
    assert abs(math.fsum(weights) - 1.) <= 1e-12
    rms = [math.sqrt(math.fsum(w * row[j] ** 2 for row, w in zip(differences, weights))) for j in range(p)]
    active = [value >= SUPPORTED_RMS for value in rms]
    scale = [value if use else 1. for value, use in zip(rms, active)]
    return {'pair_rms': rms, 'scale': scale, 'active': active, 'mean': [0.] * p}


def check_support(coefficients, scaling):
    active = scaling['active']
    assert len(coefficients) == len(active)
    assert all(math.isfinite(x) for x in coefficients)
    assert all(use or x == 0. for x, use in zip(coefficients, active))


def reference_scores(arm, rows, cells, model):
    """Independent scalar prediction reference, never a canonical NumPy scorer."""
    assert arm in ('pooled', 'independent', 'joint_shrink10')
    assert len(rows) == len(cells) and rows and all(cell in CELLS for cell in cells)
    scaling = model['scaling']; p = len(scaling['scale'])
    assert scaling['mean'] == [0.] * p
    assert all(math.isfinite(v) and v > 0 for v in scaling['scale'])
    assert all(len(row) == p and all(math.isfinite(v) for v in row) for row in rows)
    if arm == 'pooled':
        check_support(model['beta'], scaling)
        heads = {cell: model['beta'] for cell in CELLS}
    elif arm == 'independent':
        assert set(model['heads']) == set(CELLS)
        for head in model['heads'].values(): check_support(head, scaling)
        heads = model['heads']
    else:
        check_support(model['beta'], scaling); check_support(model['delta'], scaling)
        heads = {cell: [b + CELL_SIGNS[cell] * d for b, d in zip(model['beta'], model['delta'])] for cell in CELLS}
    return [dot([x / s for x, s in zip(row, scaling['scale'])], heads[cell])
            for row, cell in zip(rows, cells)]
