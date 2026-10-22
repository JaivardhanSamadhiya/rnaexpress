"""Pure metadata contracts used only on invented records in this preparation."""
from collections import Counter, defaultdict
import math
from .spec import CELLS, FOLDS, CONFIGS


def union_masks(rows, held_fold):
    """Both cells' held-fold union; old component removal, then contradiction STOP."""
    assert held_fold in FOLDS and rows
    assert len({r['intervention_id'] for r in rows}) == len(rows)
    assert {r['cell_type'] for r in rows} == set(CELLS)
    assert all(int(r['held_parent_fold']) in FOLDS for r in rows)
    target = [int(r['held_parent_fold']) == held_fold for r in rows]
    held = [r for r, use in zip(rows, target) if use]
    assert held and {r['cell_type'] for r in held} == set(CELLS)
    components = {r['biological_component'] for r in held}
    training = [not use and r['biological_component'] not in components for r, use in zip(rows, target)]
    selected = [r for r, use in zip(rows, training) if use]
    assert selected and {r['cell_type'] for r in selected} == set(CELLS)
    genes = lambda rs: {str(r['gene_transcript']).strip().upper() for r in rs}
    alleles = lambda rs: {r[k] for r in rs for k in ('parent_sequence', 'mutant_sequence')}
    assert not genes(selected) & genes(held), 'Gene contradiction: STOP, do not add filter'
    assert not alleles(selected) & alleles(held), 'Allele contradiction: STOP, do not add filter'
    all_sizes = Counter(r['parent_context_id'] for r in rows)
    for mask in (training, target):
        sizes = Counter(r['parent_context_id'] for r, use in zip(rows, mask) if use)
        assert all(all_sizes[key] == n for key, n in sizes.items()), 'Partial menu'
    return training, target


def exact_pairs(rows):
    contexts = defaultdict(list)
    for r in rows:
        assert r['cell_type'] in CELLS
        contexts[r['parent_context_id']].append(r)
    menus = {}
    for context, group in sorted(contexts.items()):
        for key in ('cell_type', 'parent_sequence', 'biological_component', 'held_parent_fold'):
            assert len({r[key] for r in group}) == 1
        assert len({r['mutant_sequence'] for r in group}) == len(group), 'Ambiguous duplicate allele'
        first = group[0]
        key = (first['biological_component'], first['parent_sequence'],
               tuple(sorted(r['mutant_sequence'] for r in group)))
        cellmap = menus.setdefault(key, {})
        assert first['cell_type'] not in cellmap
        cellmap[first['cell_type']] = (context, group)
    paired, unmatched = [], []
    for key, cellmap in sorted(menus.items()):
        if set(cellmap) != set(CELLS):
            unmatched.extend(context for context, _ in cellmap.values())
            continue
        assert len({group[0]['held_parent_fold'] for _, group in cellmap.values()}) == 1
        paired.append({'component': key[0], 'contexts': {c: cellmap[c][0] for c in CELLS},
                       'alleles': list(key[2])})
    return paired, unmatched


def preference_weights(records):
    """Equal cell, component within cell, context within component/cell, valid pair."""
    assert records and {r['cell_type'] for r in records} == set(CELLS)
    components, contexts = defaultdict(set), defaultdict(set)
    counts = Counter()
    for r in records:
        c, g, context = r['cell_type'], r['biological_component'], r['parent_context_id']
        components[c].add(g)
        contexts[c, g].add(context)
        counts[c, g, context] += 1
    assert components[CELLS[0]] == components[CELLS[1]], 'Missing represented-cell components'
    w = [1. / (2 * len(components[r['cell_type']]) *
               len(contexts[r['cell_type'], r['biological_component']]) *
               counts[r['cell_type'], r['biological_component'], r['parent_context_id']])
         for r in records]
    assert abs(math.fsum(w) - 1.) < 1e-12
    return w


def choose_config(values):
    assert len(values) == len(CONFIGS) and all(math.isfinite(v) for v in values)
    minimum = min(values)
    return next(c for c, value in zip(CONFIGS, values) if value <= minimum + 1e-12)


def paired_macro_regret(records):
    """Invented decision summaries: direction/menu within gene, then genes/cells."""
    assert records and {r['cell_type'] for r in records} == set(CELLS)
    decisions, values = set(), defaultdict(list)
    roster = defaultdict(set)
    for r in records:
        assert r['direction'] in (-1, 1) and math.isfinite(r['regret'])
        assert 0 <= r['regret'] <= 1
        key = (r['cell_type'], r['biological_component'], r['parent_context_id'], r['direction'])
        assert key not in decisions
        decisions.add(key)
        values[r['cell_type'], r['biological_component']].append(r['regret'])
        roster[r['cell_type']].add(r['biological_component'])
    assert roster[CELLS[0]] == roster[CELLS[1]]
    for c, g, context, direction in decisions:
        assert (c, g, context, -direction) in decisions
    per_cell = [math.fsum(math.fsum(values[c, g]) / len(values[c, g])
                         for g in sorted(roster[c])) / len(roster[c]) for c in CELLS]
    return math.fsum(per_cell) / 2.
