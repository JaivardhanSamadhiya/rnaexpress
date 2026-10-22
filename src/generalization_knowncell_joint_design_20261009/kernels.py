"""Invented scalar logistic arithmetic, not an optimizer or project fitter."""
import math


def dot(a, b):
    assert len(a) == len(b)
    return math.fsum(x * y for x, y in zip(a, b))


def _validate(differences, labels, weights, cells, width):
    assert len(differences) == len(labels) == len(weights) == len(cells) > 0
    assert all(len(row) == width for row in differences)
    assert all(math.isfinite(x) for row in differences for x in row)
    assert all(y in (-1, 1) for y in labels)
    assert all(c in (-1, 1) for c in cells)
    assert all(math.isfinite(w) and w > 0 for w in weights)
    assert abs(math.fsum(weights) - 1.) <= 1e-12
    for cell in (-1, 1):
        assert abs(math.fsum(w for c, w in zip(cells, weights) if c == cell) - .5) <= 1e-12


def _logloss_residual(margin, weight, label):
    # Stable at large positive/negative finite margins.
    loss = max(-margin, 0.) + math.log1p(math.exp(-abs(margin)))
    if margin >= 0:
        e = math.exp(-margin)
        residual = -weight * label * e / (1. + e)
    else:
        residual = -weight * label / (1. + math.exp(margin))
    return weight * loss, residual


def shared_value_gradient(differences, labels, weights, cells, beta, delta,
                          penalty, multiplier=10.):
    """L=sum(w*logistic)+lambda/2*(||beta||2+gamma*||delta||2)."""
    assert len(beta) == len(delta) > 0
    assert all(math.isfinite(x) for x in list(beta) + list(delta))
    assert math.isfinite(penalty) and penalty > 0
    assert math.isfinite(multiplier) and multiplier > 0
    p = len(beta)
    _validate(differences, labels, weights, cells, p)
    losses, gb, gd = [], [penalty * x for x in beta], [penalty * multiplier * x for x in delta]
    for row, y, w, cell in zip(differences, labels, weights, cells):
        loss, residual = _logloss_residual(y * (dot(row, beta) + cell * dot(row, delta)), w, y)
        losses.append(loss)
        for j, x in enumerate(row):
            gb[j] += residual * x
            gd[j] += residual * cell * x
    value = math.fsum(losses) + penalty / 2. * (dot(beta, beta) + multiplier * dot(delta, delta))
    return value, gb, gd


def independent_value_gradient(differences, labels, weights, cells, cad, n2a, penalty):
    """Global objective=.5*(L_CAD+lambda/2||u||2)+.5*(L_N2A+lambda/2||v||2)."""
    assert len(cad) == len(n2a) > 0 and math.isfinite(penalty) and penalty > 0
    assert all(math.isfinite(x) for x in list(cad) + list(n2a))
    p = len(cad)
    _validate(differences, labels, weights, cells, p)
    losses = []
    gu, gv = [penalty / 2. * x for x in cad], [penalty / 2. * x for x in n2a]
    for row, y, w, cell in zip(differences, labels, weights, cells):
        coefficient, gradient = (cad, gu) if cell == 1 else (n2a, gv)
        loss, residual = _logloss_residual(y * dot(row, coefficient), w, y)
        losses.append(loss)
        for j, x in enumerate(row):
            gradient[j] += residual * x
    return math.fsum(losses) + penalty / 4. * (dot(cad, cad) + dot(n2a, n2a)), gu, gv


def pair_rms(differences, weights):
    assert differences and len(differences) == len(weights)
    width = len(differences[0])
    assert width > 0 and all(len(row) == width for row in differences)
    assert all(math.isfinite(w) and w > 0 for w in weights)
    assert all(math.isfinite(v) for row in differences for v in row)
    total = math.fsum(weights)
    return [math.sqrt(math.fsum(w * row[j] ** 2 for row, w in zip(differences, weights)) / total)
            for j in range(width)]
