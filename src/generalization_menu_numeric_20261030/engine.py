"""Three objectives on supplied source rows. NumPy/SciPy are injected explicitly.

No file opening, sampler, split selection, held-out evaluation or package import.
Full campaign admission and seeded historical sampler parity remain external.
"""
import math
from src.generalization_menu_comparison_core_20261026 import layout, scalar

OPTIONS = {'maxiter': 500, 'ftol': 1e-11, 'gtol': 1e-7}
TEMPERATURE = .25


class _Prepared:
    __slots__ = ('z', 'effects', 'menus', 'left', 'right', 'sign', 'weight',
                 'scale', 'mean', 'rms', 'active')


def prepare(np, *, features, effects, source_metadata, sampled_pairs):
    """Derive every menu, pair mass and scaler; accept no supplied weights.

    A read-only owned array prevents mutation through the original input.
    Source-only membership and archive provenance still require admission.
    """
    rows = layout.metadata(source_metadata)
    x = np.array(features, dtype=np.float64, order='C', copy=True)
    y = np.array(effects, dtype=np.float64, order='C', copy=True)
    layout.require(x.ndim == 2 and x.shape[0] == len(rows) and x.shape[1] > 0,
                   'source feature shape differs')
    layout.require(y.shape == (len(rows),) and np.isfinite(x).all() and np.isfinite(y).all(),
                   'source effects/features nonfinite or misaligned')
    menus = layout.menus(rows, range(len(rows)))
    pairs = scalar.pair_contract(y, menus, sampled_pairs)
    p = _Prepared()
    p.left = np.array([a for a,b,s,w in pairs], dtype=np.int64)
    p.right = np.array([b for a,b,s,w in pairs], dtype=np.int64)
    p.sign = np.array([s for a,b,s,w in pairs], dtype=np.float64)
    p.weight = np.array([w for a,b,s,w in pairs], dtype=np.float64)
    square = np.zeros(x.shape[1], dtype=np.float64)
    # Bound pair-difference scratch independently of the admitted pair count.
    for begin in range(0, len(pairs), 256):
        end = begin + 256
        difference = x[p.left[begin:end]] - x[p.right[begin:end]]
        square += np.sum(p.weight[begin:end, None] * difference**2, axis=0)
    p.rms = np.sqrt(square)
    p.active = p.rms >= 1e-8
    p.scale = np.where(p.active, p.rms, 1.)
    p.mean = np.zeros(x.shape[1], dtype=np.float64)
    for menu in menus:
        p.mean += menu['weight'] * np.mean(x[list(menu['indices'])], axis=0)
    layout.require(np.isfinite(p.rms).all() and np.isfinite(p.mean).all(), 'scaling overflow')
    x -= p.mean
    x /= p.scale
    x[:, ~p.active] = 0.
    p.z, p.effects = x, y
    p.menus = tuple((tuple(m['indices']), float(m['weight'])) for m in menus)
    for field in ('z','effects','left','right','sign','weight','rms','active','scale','mean'):
        getattr(p, field).flags.writeable = False
    return p


def objective(np, expit, prepared, beta, *, arm, penalty):
    layout.require(type(prepared) is _Prepared, 'derived source preparation required')
    p = prepared
    layout.require(arm in layout.ARMS, 'unknown comparison arm')
    layout.require(math.isfinite(penalty) and penalty > 0, 'positive finite penalty required')
    beta = np.asarray(beta, dtype=np.float64)
    layout.require(beta.shape == p.scale.shape and np.isfinite(beta).all(), 'bad coefficient vector')
    layout.require(np.all(beta[~p.active] == 0.), 'unsupported coefficient is nonzero')
    scores = p.z @ beta
    residual = np.zeros(len(scores), dtype=np.float64)
    if arm in ('pairwise', 'margin_pair'):
        temperature, margin = (1., 0.) if arm == 'pairwise' else (TEMPERATURE, 1.)
        logits = (margin - p.sign * (scores[p.left] - scores[p.right])) / temperature
        value = float(np.dot(p.weight, temperature * np.logaddexp(0., logits)))
        pair_residual = -p.weight * p.sign * expit(logits)
        np.add.at(residual, p.left, pair_residual)
        np.add.at(residual, p.right, -pair_residual)
    else:
        terms = []
        for indices, weight in p.menus:
            idx = np.asarray(indices, dtype=np.int64)
            y, s = p.effects[idx], scores[idx]
            # Match the scalar reference's stable offset and exact best ties.
            s = s - s[0]
            low, high = float(np.min(y)), float(np.max(y))
            span = high - low
            layout.require(math.isfinite(span) and span > 0, 'uninformative/overflowing menu')
            for direction, best in ((1., high), (-1., low)):
                chosen = y == best
                reference = float(np.mean(s[chosen]))
                cost = (high-y)/span if direction == 1. else (y-low)/span
                logits = cost + direction*(s-reference)
                layout.require(np.isfinite(logits).all(), 'augmented score overflow')
                peak = float(np.max(logits))
                exponential = np.exp((logits-peak)/TEMPERATURE)
                total = float(np.sum(exponential))
                terms.append(weight/2 * (peak+TEMPERATURE*math.log(total)))
                local = direction*(exponential/total-chosen/np.sum(chosen))
                residual[idx] += weight/2 * local
        value = math.fsum(terms)
    value += penalty/2 * float(np.dot(beta,beta))
    gradient = p.z.T @ residual + penalty*beta
    gradient[~p.active] = 0.
    layout.require(math.isfinite(value) and np.isfinite(gradient).all(), 'nonfinite objective')
    return value, gradient


def fit(np, minimize, expit, prepared, *, arm, penalty):
    """Zero-start fixed solver. This function grants no biological fit authority."""
    fun = lambda beta: objective(np,expit,prepared,beta,arm=arm,penalty=penalty)
    result = minimize(fun, np.zeros(len(prepared.scale)), jac=True,
                      method='L-BFGS-B', options=dict(OPTIONS))
    layout.require(bool(result.success), 'optimizer did not converge: '+str(result.message))
    value, gradient = fun(result.x)
    layout.require(np.all(result.x[~prepared.active] == 0.), 'unsupported fitted coefficient')
    return {'arm':arm, 'penalty':penalty, 'beta':result.x.tolist(),
            'scale':prepared.scale.tolist(), 'mean':prepared.mean.tolist(),
            'active':prepared.active.tolist(), 'pair_rms':prepared.rms.tolist(),
            'objective':value, 'gradient_max_abs':float(np.max(np.abs(gradient))),
            'optimizer_iterations':int(result.nit), 'optimizer_success':True,
            'optimizer_options':dict(OPTIONS)}


def scores(np, model, features):
    """Stable row-by-row full-vector float64 scoring; no target scaler fitting."""
    layout.require(isinstance(model['active'],(list,tuple)) and
                   all(type(value) is bool for value in model['active']),
                   'scoring support must contain actual booleans')
    beta = np.asarray(model['beta'], dtype=np.float64)
    scale = np.asarray(model['scale'], dtype=np.float64)
    mean = np.asarray(model['mean'], dtype=np.float64)
    active = np.asarray(model['active'], dtype=np.bool_)
    x = np.asarray(features, dtype=np.float64)
    layout.require(beta.ndim == 1 and len(beta) > 0 and x.ndim == 2
                   and x.shape[1:] == beta.shape and scale.shape == beta.shape
                   and mean.shape == beta.shape and active.shape == beta.shape, 'score shape differs')
    layout.require(np.isfinite(x).all() and np.isfinite(beta).all() and np.isfinite(mean).all()
                   and np.isfinite(scale).all() and np.all(scale > 0)
                   and np.all(beta[~active] == 0.), 'invalid scoring model/input')
    output = np.empty(len(x), dtype=np.float64)
    for i, row in enumerate(x):
        z = np.where(active, (row-mean)/scale, 0.)
        output[i] = np.sum(z*beta, dtype=np.float64)
    layout.require(np.isfinite(output).all(), 'score overflow')
    return output
