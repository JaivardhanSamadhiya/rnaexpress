"""Metadata, preference weighting and checkpoint contracts; no file readers."""
from collections import Counter, defaultdict
import hashlib
import json
import math
from .spec import ARMS, CELLS, FOLDS, CONFIGS, COUNTS, METADATA_COLUMNS


def ids_sha(rows):
    return hashlib.sha256('|'.join(r['intervention_id'] for r in rows).encode()).hexdigest()


def metadata_sha(rows):
    raw = [[row[key] for key in METADATA_COLUMNS] for row in rows]
    return hashlib.sha256(json.dumps(raw, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def validate_rows(rows):
    assert rows and len({r['intervention_id'] for r in rows}) == len(rows)
    assert all(set(r) == set(METADATA_COLUMNS) for r in rows), 'Metadata only: no label/score columns'
    assert {r['cell_type'] for r in rows} == set(CELLS)
    component_folds, contexts = defaultdict(set), defaultdict(list)
    for row in rows:
        assert row['dataset'] == 'mikl_gse173098' and row['endpoint_class'] == 'projection'
        assert not isinstance(row['held_parent_fold'], bool) and row['held_parent_fold'] in FOLDS
        for key in METADATA_COLUMNS:
            if key != 'held_parent_fold': assert isinstance(row[key], str) and row[key].strip()
        component_folds[row['biological_component']].add(row['held_parent_fold'])
        contexts[row['parent_context_id']].append(row)
    assert all(len(folds) == 1 for folds in component_folds.values()), 'Component spans inherited folds'
    for group in contexts.values():
        assert len(group) >= 2
        for key in ('cell_type', 'biological_component', 'held_parent_fold', 'parent_sequence'):
            assert len({r[key] for r in group}) == 1, 'Ambiguous context'
        assert len({r['mutant_sequence'] for r in group}) == len(group), 'Duplicate candidate sequence'
    by_cell = [{r['biological_component'] for r in rows if r['cell_type'] == c} for c in CELLS]
    assert by_cell[0] == by_cell[1], 'Different represented-cell component rosters'
    return contexts


def union_split(rows, held_fold):
    """Original component purge on BOTH target cells, then contradiction STOP."""
    validate_rows(rows); assert held_fold in FOLDS
    target = [i for i, row in enumerate(rows) if row['held_parent_fold'] == held_fold]
    assert target
    held = [rows[i] for i in target]
    components = {r['biological_component'] for r in held}
    train = [i for i, row in enumerate(rows) if row['held_parent_fold'] != held_fold
             and row['biological_component'] not in components]
    assert train and set(train).isdisjoint(target)
    source = [rows[i] for i in train]
    assert {r['cell_type'] for r in held} == {r['cell_type'] for r in source} == set(CELLS)
    genes = lambda group: {r['gene_transcript'].strip().upper() for r in group}
    alleles = lambda group: {r[key] for r in group for key in ('parent_sequence', 'mutant_sequence')}
    assert not genes(source) & genes(held), 'Gene contradiction: STOP; no extra purge'
    assert not alleles(source) & alleles(held), 'Allele contradiction: STOP; no extra purge'
    total = Counter(r['parent_context_id'] for r in rows)
    for group in (held, source):
        counts = Counter(r['parent_context_id'] for r in group)
        assert all(count == total[context] for context, count in counts.items()), 'Partial menu'
    return train, target


def exact_pairs(rows):
    contexts = validate_rows(rows); keyed = {}
    for context, group in sorted(contexts.items()):
        first = group[0]
        key = (first['biological_component'], first['parent_sequence'],
               tuple(sorted(row['mutant_sequence'] for row in group)))
        cells = keyed.setdefault(key, {}); assert first['cell_type'] not in cells
        cells[first['cell_type']] = (context, first['held_parent_fold'])
    pairs, unmatched = [], []
    for key, cells in sorted(keyed.items()):
        if set(cells) != set(CELLS):
            unmatched.extend(value[0] for value in cells.values()); continue
        assert len({value[1] for value in cells.values()}) == 1
        pairs.append({'biological_component': key[0], 'parent_sequence': key[1],
                      'mutant_sequences': key[2], 'gene_fold': cells[CELLS[0]][1],
                      'contexts': {cell: cells[cell][0] for cell in CELLS}})
    return pairs, sorted(unmatched)


def full_metadata_contract(rows):
    """Future in-memory admission; never reads a project file itself."""
    contexts = validate_rows(rows); pairs, unmatched = exact_pairs(rows)
    assert len(rows) == COUNTS['all_rows']
    assert Counter(row['cell_type'] for row in rows) == {CELLS[0]: COUNTS['CAD_rows'], CELLS[1]: COUNTS['Neuro-2a_rows']}
    assert len({r['biological_component'] for r in rows}) == COUNTS['components']
    assert {r['held_parent_fold'] for r in rows} == set(FOLDS)
    assert len(pairs) == COUNTS['paired_menus'] and len(unmatched) == COUNTS['unmatched_contexts']
    paired_contexts = {context for pair in pairs for context in pair['contexts'].values()}
    assert len(paired_contexts) == COUNTS['paired_contexts']
    assert sum(len(contexts[c]) for c in paired_contexts) == COUNTS['paired_rows']
    assert sum(len(contexts[c]) for c in unmatched) == COUNTS['unmatched_rows']
    assert {p['biological_component'] for p in pairs} == {r['biological_component'] for r in rows}
    coverage = Counter()
    splits = []
    for outer in FOLDS:
        train, target = union_split(rows, outer); coverage.update(target)
        source = [rows[i] for i in train]; inner = []
        for fold in FOLDS:
            if fold == outer: continue
            left, right = union_split(source, fold)
            inner.append({'validation_fold': fold, 'training_indices': [train[i] for i in left],
                          'validation_indices': [train[i] for i in right]})
        assert sorted(i for value in inner for i in value['validation_indices']) == sorted(train)
        splits.append({'outer_fold': outer, 'training_indices': train, 'target_indices': target, 'inner': inner})
    assert set(coverage) == set(range(len(rows))) and set(coverage.values()) == {1}
    return {'row_ids_sha256': ids_sha(rows), 'metadata_sha256': metadata_sha(rows),
            'splits': splits, 'pairs': pairs, 'unmatched_contexts': unmatched}


def hierarchical_weights(rows):
    """Equal cell/component/context/item mass, for candidate or valid-pair rows.

    For pair weighting, caller supplies one record for EACH valid ORIGINAL
    sampled pair and separately proves every original context is represented.
    This helper never silently drops ties, contexts or candidates.
    """
    assert rows and {row['cell_type'] for row in rows} == set(CELLS)
    components, contexts, counts = defaultdict(set), defaultdict(set), Counter()
    identities = {}
    for row in rows:
        c, g, context = (row[key] for key in ('cell_type', 'biological_component', 'parent_context_id'))
        assert c in CELLS
        assert context not in identities or identities[context] == (c, g)
        identities[context] = (c, g)
        components[c].add(g); contexts[c, g].add(context); counts[c, g, context] += 1
    assert components[CELLS[0]] == components[CELLS[1]]
    result = [1. / (2 * len(components[r['cell_type']]) *
                     len(contexts[r['cell_type'], r['biological_component']]) *
                     counts[r['cell_type'], r['biological_component'], r['parent_context_id']]) for r in rows]
    assert abs(math.fsum(result) - 1.) <= 1e-12
    for cell in CELLS:
        assert abs(math.fsum(w for w, row in zip(result, rows) if row['cell_type'] == cell) - .5) <= 1e-12
    return result


def preference_contract(rows, truths, left, right, labels):
    """Check an admitted original sampler output; does not replace its RNG."""
    contexts = validate_rows(rows)
    assert set(truths) == {row['intervention_id'] for row in rows}
    assert all(math.isfinite(v) for v in truths.values())
    assert len(left) == len(right) == len(labels) > 0
    records, seen, counts = [], set(), Counter()
    for a, b, label in zip(left, right, labels):
        assert isinstance(a, int) and isinstance(b, int) and 0 <= a < b < len(rows)
        one, two = rows[a], rows[b]
        assert one['parent_context_id'] == two['parent_context_id']
        assert (a, b) not in seen; seen.add((a, b))
        difference = truths[one['intervention_id']] - truths[two['intervention_id']]
        assert difference != 0 and label == (1 if difference > 0 else -1)
        counts[one['parent_context_id']] += 1; records.append(one)
    assert set(counts) == set(contexts), 'No-preference context: STOP; no cohort repair'
    assert all(count <= 256 for count in counts.values())
    # For all-pairs menus, prove the exact non-tied roster. Above the cap, the
    # ORIGINAL sampler's seed/RNG/output digest must additionally be bound.
    for context, group in contexts.items():
        indices = [i for i, row in enumerate(rows) if row['parent_context_id'] == context]
        total = len(indices) * (len(indices) - 1) // 2
        if total <= 256:
            expected = {(a, b) for k, a in enumerate(indices) for b in indices[k+1:]
                        if truths[rows[a]['intervention_id']] != truths[rows[b]['intervention_id']]}
            assert {(a, b) for a, b in seen if rows[a]['parent_context_id'] == context} == expected
    return hierarchical_weights(records)


def checkpoint_roster():
    records = []
    for arm in ARMS:
        for outer in FOLDS:
            for inner in FOLDS:
                if inner == outer: continue
                for config in CONFIGS:
                    records.append({'arm': arm, 'outer_fold': outer, 'inner_fold': inner,
                                    'configuration_id': config['id'], 'phase': 'inner',
                                    'optimizer_units': 2 if arm == 'independent' else 1})
            records.append({'arm': arm, 'outer_fold': outer, 'inner_fold': None,
                            'configuration_id': 'SOURCE_SELECTED', 'phase': 'outer',
                            'optimizer_units': 2 if arm == 'independent' else 1})
    assert len(records) == COUNTS['arm_checkpoints']
    assert sum(r['phase'] == 'inner' for r in records) == COUNTS['inner_arm_checkpoints']
    assert sum(r['optimizer_units'] for r in records) == COUNTS['optimizer_units']
    assert sum(r['optimizer_units'] for r in records if r['phase'] == 'inner') == COUNTS['inner_optimizer_units']
    return records
