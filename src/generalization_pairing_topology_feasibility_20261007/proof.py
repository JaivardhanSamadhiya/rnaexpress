"""Invented ordinary single-pair ensembles; NOT Turner/Boltzmann folds.

The example proves that the stored summary map is not invertible. It does
not assert two physical ensembles for one fixed RNA under one energy model.
"""
import math

SEQUENCE = 'GGGGAAACUUCAAAA'
ALLOWED = {'AU', 'UA', 'GC', 'CG', 'GU', 'UG'}


def matrices():
    n = len(SEQUENCE)
    results = []
    for partners in ({0: (7, 10), 3: (7, 10), 1: (8, 9), 2: (8, 9)},
                     {0: (8, 9), 3: (8, 9), 1: (7, 10), 2: (7, 10)}):
        edges = [(i, j) for i, js in partners.items() for j in js]
        assert len(edges) == 8
        p = [[0.0] * n for _ in range(n)]
        for i, j in edges:
            assert j - i >= 4 and SEQUENCE[i] + SEQUENCE[j] in ALLOWED
            p[i][j] = p[j][i] = 1 / 8
        # Each of eight legal, noncrossing single-pair structures has mass1/8.
        results.append(p)
    return results


def summaries(p):
    n = len(p)
    unpaired, entropy, distance = [], [], []
    for i, row in enumerate(p):
        u = 1 - sum(row)
        unpaired.append(u)
        entropy.append(-sum(x * math.log2(x) for x in row if x > 0)
                       - (u * math.log2(u) if u > 0 else 0))
        distance.append(sum(x * abs(i - j) for j, x in enumerate(row)) / (n - 1))
    return unpaired, entropy, distance


def partner_mass(p, index, base):
    return sum(value for j, value in enumerate(p[index]) if SEQUENCE[j] == base)
