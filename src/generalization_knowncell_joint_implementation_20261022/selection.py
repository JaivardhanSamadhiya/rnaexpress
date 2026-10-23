"""Exact-ID choices and concatenated source-only OOF selection on in-memory lists.

Inputs named scores must be the future canonical scorer's outputs. An
independent arithmetic tolerance never defines a replacement choice/tie band.
No output is a project prediction or a substitute for independent replay.
"""
from collections import defaultdict
import math
from .spec import CELLS, FOLDS, CONFIGS
from .contracts import validate_rows, union_split, exact_pairs


def decisions(rows, scores, truths):
    contexts = validate_rows(rows)
    ids = {row['intervention_id'] for row in rows}
    assert set(scores) == set(truths) == ids
    assert all(math.isfinite(v) for v in list(scores.values()) + list(truths.values()))
    result = []
    for context, group in sorted(contexts.items()):
        effects = [truths[row['intervention_id']] for row in group]
        low, high = min(effects), max(effects); assert high > low
        for direction in (-1, 1):
            # Exact canonical score, THEN original ID. No near-tie tolerance.
            chosen = min(group, key=lambda r: (-direction * scores[r['intervention_id']], r['intervention_id']))
            selected = direction * truths[chosen['intervention_id']]
            oriented = [direction * value for value in effects]
            wrong = selected < -1e-12
            feasible = any(value > 1e-12 for value in oriented)
            unavoidable = all(value < -1e-12 for value in oriented)
            result.append({'cell_type': chosen['cell_type'],
                           'biological_component': chosen['biological_component'],
                           'parent_context_id': context, 'gene_fold': chosen['held_parent_fold'],
                           'direction': direction, 'selected_id': chosen['intervention_id'],
                           'selected_mutant_sequence': chosen['mutant_sequence'],
                           'selected_score': scores[chosen['intervention_id']],
                           'selected_effect': truths[chosen['intervention_id']], 'candidates': len(group),
                           'regret': (max(oriented) - selected) / (high - low),
                           'wrong_direction': float(wrong), 'avoidable_wrong': float(wrong and feasible),
                           'no_feasible_candidate': float(not feasible),
                           'unavoidable_wrong': float(wrong and unavoidable),
                           'neutral_only_alternative_wrong': float(wrong and not feasible and not unavoidable)})
    return result


def primary_metrics(records, pairs):
    """Require exactly the full paired decision roster, not an intersection."""
    expected = {(cell, context, direction): (pair['biological_component'], pair['gene_fold'], len(pair['mutant_sequences']))
                for pair in pairs for cell, context in pair['contexts'].items() for direction in (-1, 1)}
    assert len(expected) == 4 * len(pairs) > 0
    actual = {}
    for row in records:
        key = (row['cell_type'], row['parent_context_id'], row['direction'])
        assert key not in actual and key in expected
        assert (row['biological_component'], row['gene_fold'], row['candidates']) == expected[key]
        assert math.isfinite(row['regret']) and 0 <= row['regret'] <= 1
        actual[key] = row
    assert set(actual) == set(expected)
    grouped = defaultdict(list)
    for row in records: grouped[row['cell_type'], row['biological_component']].append(row['regret'])
    components = [{g for c, g in grouped if c == cell} for cell in CELLS]
    assert components[0] == components[1] and components[0]
    means = {cell: math.fsum(math.fsum(grouped[cell, gene]) / len(grouped[cell, gene])
                             for gene in sorted(components[0])) / len(components[0]) for cell in CELLS}
    return {'macro_regret': math.fsum(means.values()) / 2., 'per_cell_regret': means,
            'components': len(components[0]), 'decisions': len(records)}


def choose_config(values):
    assert len(values) == len(CONFIGS) and all(math.isfinite(value) for value in values)
    minimum = min(values)
    return next(dict(config) for config, value in zip(CONFIGS, values) if value <= minimum + 1e-12)


def select_source_config(rows, outer_fold, source_truths, batches):
    """One setting from all two-fold OOF decisions, excluding every outer ID.

    batches[configuration_id][inner_validation_fold] is an exact ID->canonical
    score mapping. Unmatched source menus must also have predictions, but do
    not enter the primary selector. There is one shared setting for both
    independent heads. Source provenance/checkpoint replay is a later layer.
    """
    outer_train, _ = union_split(rows, outer_fold)
    source = [rows[i] for i in outer_train]
    source_ids = {row['intervention_id'] for row in source}
    assert set(source_truths) == source_ids, 'Outer/unused truth admission to selector'
    assert all(math.isfinite(value) for value in source_truths.values())
    inner_folds = set(FOLDS) - {outer_fold}
    expected = {}
    for fold in inner_folds:
        _, target = union_split(source, fold)
        expected[fold] = {source[i]['intervention_id'] for i in target}
    assert set().union(*expected.values()) == source_ids
    assert sum(len(value) for value in expected.values()) == len(source_ids)
    assert set(batches) == {config['id'] for config in CONFIGS}
    pairs, _ = exact_pairs(source)
    paired_contexts = {context for pair in pairs for context in pair['contexts'].values()}
    values = []; metrics = {}
    for config in CONFIGS:
        by_fold = batches[config['id']]; assert set(by_fold) == inner_folds
        scores = {}
        for fold in sorted(inner_folds):
            assert set(by_fold[fold]) == expected[fold], 'Incomplete/outer/wrong-fold OOF scores'
            assert not set(scores) & set(by_fold[fold])
            scores.update(by_fold[fold])
        all_decisions = decisions(source, scores, source_truths)
        primary = [row for row in all_decisions if row['parent_context_id'] in paired_contexts]
        value = primary_metrics(primary, pairs)
        metrics[config['id']] = value; values.append(value['macro_regret'])
    return {'selected_config': choose_config(values), 'configuration_metrics': metrics,
            'outer_fold': outer_fold, 'source_row_count': len(source),
            'source_only': True, 'primary_paired_only': True,
            'canonical_ties': 'exact_score_then_original_intervention_id'}


def bound_reference(canonical, independent, tolerance=1e-9):
    """Return CANONICAL values unchanged after independent arithmetic bound."""
    assert tolerance == 1e-9 and set(canonical) == set(independent) and canonical
    assert all(math.isfinite(v) for v in list(canonical.values()) + list(independent.values()))
    maximum = max(abs(canonical[key] - independent[key]) for key in canonical)
    assert maximum < tolerance
    return canonical, maximum
