"""Scalar reference kernels supplied with in-memory inputs, never file paths.

No project loader, native dependency, sampler, optimizer or global mutable state.
The future numerical implementation must agree with these independently summed
gradients. None of these routines certifies that supplied inputs are admitted.
"""
import math
from .layout import require
from src.generalization_menu_loss_20261026.loss import menu_loss, TEMPERATURE


def _source_menus(catalog, count):
    catalog = tuple(catalog)
    require(bool(catalog), 'empty source menu catalog')
    indices = [i for menu in catalog for i in menu['indices']]
    require(len(indices) == len(set(indices)) == count and set(indices) == set(range(count)),
            'menus must partition every supplied source row; held/extra rows forbidden')
    require(len({menu['context'] for menu in catalog}) == len(catalog), 'duplicate menu key')
    require(all(len(m['indices']) >= 2 and math.isfinite(m['weight']) and m['weight'] > 0
                for m in catalog), 'bad source menu size or mass')
    require(abs(math.fsum(m['weight'] for m in catalog)-1.) <= 1e-12, 'invalid menu mass')
    return catalog


def matrix(values):
    rows = tuple(tuple(float(v) for v in row) for row in values)
    require(bool(rows) and bool(rows[0]), 'empty feature matrix')
    width = len(rows[0])
    require(all(len(row) == width and all(math.isfinite(v) for v in row) for row in rows),
            'ragged or nonfinite feature matrix')
    return rows


def pair_contract(effects, menu_catalog, supplied_pairs):
    """Bind a supplied historical sampler result, omit exact target ties only.

    This cannot establish NumPy-generator equivalence: that remains a separate
    actual-input/native admission. Never substitute a Python random sampler.
    """
    effects = tuple(float(v) for v in effects)
    require(all(math.isfinite(v) for v in effects), 'nonfinite effect')
    menu_catalog = _source_menus(menu_catalog, len(effects))
    require(set(supplied_pairs) == {m['context'] for m in menu_catalog}, 'pair/context roster differs')
    result = []; covered = set()
    for menu in menu_catalog:
        indices = menu['indices']; allowed = set(indices)
        require(not (covered & allowed), 'overlapping menus'); covered |= allowed
        require(all(0 <= i < len(effects) for i in indices), 'bad effect index')
        require(max(effects[i] for i in indices) > min(effects[i] for i in indices),
                'uninformative menu cannot be dropped')
        pairs = tuple(tuple(pair) for pair in supplied_pairs[menu['context']])
        expected_count = min(256, len(indices)*(len(indices)-1)//2)
        require(len(pairs) == len(set(pairs)) == expected_count, 'incomplete or duplicated sampled roster')
        require(all(len(pair) == 2 and pair[0] < pair[1] and
                    pair[0] in allowed and pair[1] in allowed for pair in pairs),
                'invalid or cross-context pair')
        valid = tuple((a,b) for a,b in pairs if effects[a] != effects[b])
        require(bool(valid), 'sampler left no preference; no silent context deletion')
        for a,b in valid:
            result.append((a,b,1. if effects[a] > effects[b] else -1.,menu['weight']/len(valid)))
    require(abs(math.fsum(row[3] for row in result)-1.) <= 1e-12, 'pair weights do not sum to one')
    return tuple(result)


def scaling(features, pair_rows, menu_catalog):
    x = matrix(features); width = len(x[0])
    menu_catalog = _source_menus(menu_catalog, len(x))
    require(bool(pair_rows) and abs(math.fsum(row[3] for row in pair_rows)-1.) <= 1e-12,
            'invalid pair mass')
    require(all(0 <= a < b < len(x) and w > 0 and math.isfinite(w)
                and y in (-1.,1.) for a,b,y,w in pair_rows), 'bad pair data')
    rms = tuple(math.sqrt(math.fsum(w*(x[a][j]-x[b][j])**2
                                   for a,b,_,w in pair_rows)) for j in range(width))
    active = tuple(v >= 1e-8 for v in rms)
    scale = tuple(v if flag else 1. for v,flag in zip(rms,active))
    require(abs(math.fsum(m['weight'] for m in menu_catalog)-1.) <= 1e-12, 'invalid menu mass')
    mean = tuple(math.fsum(m['weight']/len(m['indices'])*x[i][j]
                           for m in menu_catalog for i in m['indices']) for j in range(width))
    require(all(math.isfinite(v) for v in rms+mean), 'scaling overflow')
    return {'pair_rms': rms, 'active': active, 'scale': scale, 'mean': mean}


def objective(beta, features, effects, menu_catalog, pair_rows, scale, *, arm, penalty):
    """Independent full-vector objective/gradient, preserving source-only scale."""
    require(arm in ('pairwise','margin_pair','menu_cost'), 'unknown comparison arm')
    penalty = float(penalty)
    require(math.isfinite(penalty) and penalty > 0, 'positive finite penalty required')
    x = matrix(features); beta = tuple(float(v) for v in beta); width = len(x[0])
    menu_catalog = _source_menus(menu_catalog, len(x))
    require(len(beta) == width and all(math.isfinite(v) for v in beta), 'bad coefficient vector')
    require(len(effects) == len(x) and all(math.isfinite(v) for v in effects), 'bad effects')
    require(all(len(scale[k]) == width for k in ('active','scale','mean')), 'bad scaling width')
    require(all(math.isfinite(v) and v > 0 for v in scale['scale']), 'bad scale')
    require(all(math.isfinite(v) for v in scale['mean']), 'bad center')
    require(all(active or beta[j] == 0. for j,active in enumerate(scale['active'])),
            'unsupported coefficient is nonzero')
    owner = {i:m['context'] for m in menu_catalog for i in m['indices']}
    require(bool(pair_rows) and abs(math.fsum(w for _,_,_,w in pair_rows)-1.) <= 1e-12,
            'invalid pair mass')
    require(all(0 <= a < b < len(x) and owner[a] == owner[b] and w > 0 and math.isfinite(w)
                and effects[a] != effects[b] and y == (1. if effects[a] > effects[b] else -1.)
                for a,b,y,w in pair_rows), 'invalid source pair')
    z = tuple(tuple((v-scale['mean'][j])/scale['scale'][j] if scale['active'][j] else 0.
                    for j,v in enumerate(row)) for row in x)
    scores = tuple(math.fsum(a*b for a,b in zip(row,beta)) for row in z)
    terms = []; residuals = [[] for _ in x]
    if arm in ('pairwise','margin_pair'):
        temperature, target_margin = ((1.,0.) if arm == 'pairwise' else (TEMPERATURE,1.))
        for a,b,y,w in pair_rows:
            margin = y*(scores[a]-scores[b])
            t = (target_margin-margin)/temperature
            terms.append(w*temperature*(max(0.,t)+math.log1p(math.exp(-abs(t)))))
            if t >= 0:
                residual = -w*y/(1.+math.exp(-t))
            else:
                e = math.exp(t); residual = -w*y*e/(1.+e)
            residuals[a].append(residual); residuals[b].append(-residual)
    else:
        for menu in menu_catalog:
            idx = menu['indices']; w = menu['weight']
            loss,gradient = menu_loss([scores[i] for i in idx],[effects[i] for i in idx])
            terms.append(w*loss)
            for i,g in zip(idx,gradient):residuals[i].append(w*g)
    residual = tuple(math.fsum(parts) for parts in residuals)
    loss = math.fsum(terms)+penalty/2*math.fsum(v*v for v in beta)
    gradient = tuple(math.fsum(r*row[j] for r,row in zip(residual,z))+penalty*beta[j]
                     if scale['active'][j] else 0. for j in range(width))
    require(math.isfinite(loss) and all(math.isfinite(v) for v in gradient), 'nonfinite objective')
    return loss, gradient
