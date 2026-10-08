"""Array API supplied after admission; importing this module is stdlib-only."""
from collections import Counter
import hashlib
import itertools
import math
import random
from . import spec as s

def cap_edges(n, context, np=None):
    assert n >= 2
    if n * (n - 1) // 2 <= s.CAP: return list(itertools.combinations(range(n), 2))
    seed = int(hashlib.sha256((str(s.CAP_SEED) + context).encode()).hexdigest()[:8], 16)
    # Native benchmark uses exactly the old NumPy default_rng/choice policy.
    # The stdlib mock substitutes Random ONLY for outcome-free preparation tests.
    rng = np.random.default_rng(seed) if np is not None else random.Random(seed)
    pairs = set()
    while len(pairs) < s.CAP:
        a, b = rng.choice(n, 2, replace=False).tolist() if np is not None else rng.sample(range(n), 2)
        pairs.add((min(a, b), max(a, b)))
    return sorted(pairs)

def blocks(n):
    assert n >= 2
    return [(start, min(n, start + s.BLOCK)) for start in range(0, n, s.BLOCK)]

def non_tied_count(y):
    count = Counter(y); n = len(y)
    return n * (n - 1) // 2 - sum(k * (k - 1) // 2 for k in count.values())

def prepare_contexts(y, contexts, np=None):
    """Inputs are invented list-valued labels; cap-positive cohort/mass frozen."""
    all_ids = [i for row in contexts for i in row['indices']]
    assert len(all_ids) == len(set(all_ids)) == len(y) and set(all_ids) == set(range(len(y)))
    rows = []
    for row in contexts:
        ids = row['indices']; local_y = [y[i] for i in ids]
        edges = cap_edges(len(ids), row['name'], np=np)
        valid = [(ids[a], ids[b]) for a, b in edges if local_y[a] != local_y[b]]
        assert row['mass'] > 0 and math.isfinite(row['mass'])
        if valid: rows.append({'name': row['name'], 'indices': ids, 'cap': valid,
                               'mass': row['mass'], 'all_count': non_tied_count(local_y)})
    total = math.fsum(row['mass'] for row in rows); assert total > 0
    for row in rows: row['mass'] /= total
    return rows

def invented(n, p, tag):
    rng = random.Random(s.SEED + n * 4099 + p * 37 + tag)
    x = [[rng.uniform(-1., 1.) for _ in range(p - 1)] + [7.] for _ in range(n)]
    y = [float((i * 7 + i // 11) % 13) for i in range(n)]
    beta = [rng.uniform(-.08, .08) for _ in range(p - 1)] + [0.]
    return x, y, beta

def transformed(np, x, prepared, original_contexts=None):
    """One original-cap scale and candidate-weighted mean shared by both arms."""
    x = np.asarray(x, dtype=np.float64); scale2 = np.zeros(x.shape[1]); mean = np.zeros(x.shape[1])
    mean_contexts = original_contexts if original_contexts is not None else prepared
    mean_mass = math.fsum(c['mass'] for c in mean_contexts)
    for c in mean_contexts:
        ids = np.asarray(c['indices'], dtype=int)
        mean += c['mass'] / mean_mass * x[ids].mean(axis=0)
    for c in prepared:
        pairs = np.asarray(c['cap'], dtype=int)
        delta = x[pairs[:, 0]] - x[pairs[:, 1]]
        scale2 += c['mass'] * (delta * delta).mean(axis=0)
    scale = np.sqrt(scale2); active = scale >= 1e-8
    scale[~active] = 1.
    return (x[:, active] - mean[active]) / scale[active], mean, scale, active

def objective(np, z, beta, y, prepared, mode):
    """Blocked utilities -> candidate residuals -> Z.T@g; no pair-feature array."""
    assert mode in ('cap', 'all')
    u = z @ beta; g = np.zeros(len(y)); loss = .5 * s.PENALTY * float(beta @ beta)
    y = np.asarray(y, dtype=np.float64)
    for c in prepared:
        if mode == 'cap':
            pair = np.asarray(c['cap'], dtype=int); a, b = pair[:, 0], pair[:, 1]
            t = np.where(y[a] > y[b], 1., -1.); margin = t * (u[a] - u[b]); weight = c['mass'] / len(pair)
            loss += weight * float(np.logaddexp(0., -margin).sum())
            r = -weight * t * np.exp(-np.logaddexp(0., margin))
            np.add.at(g, a, r); np.add.at(g, b, -r)
        else:
            ids = np.asarray(c['indices'], dtype=int); cy, cu = y[ids], u[ids]
            cols = np.arange(len(ids)); weight = c['mass'] / c['all_count']
            for start, stop in blocks(len(ids)):
                rows = np.arange(start, stop)
                t = (cy[rows, None] > cy[None, :]).astype(float) - (cy[rows, None] < cy[None, :])
                valid = (cols[None, :] > rows[:, None]) & (t != 0.)
                margin = t * (cu[rows, None] - cu[None, :])
                loss += weight * float(np.logaddexp(0., -margin)[valid].sum())
                r = -weight * t * np.exp(-np.logaddexp(0., margin)); r[~valid] = 0.
                g[ids[rows]] += r.sum(axis=1); g[ids] -= r.sum(axis=0)
    gradient = z.T @ g + s.PENALTY * beta
    assert np.isfinite(loss) and np.isfinite(gradient).all()
    return loss, gradient

def materialized(np, z, beta, y, prepared, mode):
    """Independent tiny pair-feature reference, explicitly NOT for large cases."""
    pieces = []; targets = []; weights = []
    for c in prepared:
        pairs = c['cap'] if mode == 'cap' else [(a, b) for a, b in itertools.combinations(c['indices'], 2) if y[a] != y[b]]
        for a, b in pairs:
            pieces.append(z[a] - z[b]); targets.append(1. if y[a] > y[b] else -1.); weights.append(c['mass'] / len(pairs))
    d, t, w = np.asarray(pieces), np.asarray(targets), np.asarray(weights)
    margin = t * (d @ beta)
    loss = float(w @ np.logaddexp(0., -margin)) + .5 * s.PENALTY * float(beta @ beta)
    negative = margin < 0.; probability = np.empty(len(margin))
    probability[negative] = 1. / (1. + np.exp(margin[negative]))
    e = np.exp(-margin[~negative]); probability[~negative] = e / (1. + e)
    residual = -w * t * probability
    return loss, d.T @ residual + s.PENALTY * beta
