"""Smooth cost-sensitive menu loss, using only Python's math module.

This is a structured margin surrogate, not a novel learning algorithm or SPO+.
It upper-bounds the observed two-direction hard selection regret of one menu.
It makes no statistical consistency or transfer claim. No data/optimizer imports.
"""
import math

TEMPERATURE = 0.25


def _vector(values, name):
    result = tuple(float(value) for value in values)
    if len(result) < 2 or not all(math.isfinite(value) for value in result):
        raise ValueError(name + ' requires at least two finite values')
    return result


def menu_loss(scores, effects, *, temperature=TEMPERATURE):
    """Return mean two-direction loss and its gradient in candidate-score order.

    For each direction d, r_i is observed normalized regret and B is the exact
    set of best-effect candidates. L_d = tau log sum_i exp((r_i + d(s_i -
    mean_{b in B} s_b))/tau). The gradient is d(p_i - 1[i in B]/|B|).

    Full menus and informative finite spans are required. Tied best effects
    share reference mass equally. No outcome-dependent row deletion, target
    smoothing, feature scaling, menu weighting or fitting occurs here.
    """
    scores, effects = _vector(scores, 'scores'), _vector(effects, 'effects')
    if len(scores) != len(effects):
        raise ValueError('score/effect lengths differ')
    temperature = float(temperature)
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError('temperature must be finite and positive')
    low, high = min(effects), max(effects)
    span = high - low
    if not math.isfinite(span) or span <= 0:
        raise ValueError('menu has no finite informative effect span')
    centered = tuple(value - scores[0] for value in scores)
    if not all(math.isfinite(value) for value in centered):
        raise ValueError('score differences overflow')
    losses, gradients = [], []
    for direction, best in ((1., high), (-1., low)):
        indices = tuple(i for i, value in enumerate(effects) if value == best)
        mass = 1. / len(indices)
        reference = math.fsum(centered[i] * mass for i in indices)
        costs = tuple((high - value) / span if direction == 1. else
                      (value - low) / span for value in effects)
        logits = tuple(cost + direction * (score - reference)
                       for cost, score in zip(costs, centered))
        if not all(math.isfinite(value) for value in logits):
            raise ValueError('augmented score differences overflow')
        peak = max(logits)
        exponentials = tuple(math.exp((value - peak) / temperature)
                             for value in logits)
        total = math.fsum(exponentials)
        losses.append(peak + temperature * math.log(total))
        gradients.append(tuple(direction * (value / total -
                              (mass if effects[i] == best else 0.))
                               for i, value in enumerate(exponentials)))
    loss = math.fsum(losses) / 2.
    gradient = tuple(math.fsum(pair) / 2. for pair in zip(*gradients))
    if not math.isfinite(loss) or not all(math.isfinite(v) for v in gradient):
        raise ValueError('loss or gradient is nonfinite')
    return loss, gradient
