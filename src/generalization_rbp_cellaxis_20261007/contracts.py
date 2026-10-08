"""Independent stdlib metadata contracts; neither feature nor label readers."""
from collections import Counter
from .spec import TASKS, KNOWN_TASKS, FOLDS, CONFIGS, GATE


def ids(rows, mask):
    return [r['intervention_id'] for r, keep in zip(rows, mask) if keep]


def purge(rows, train, target):
    held = [r for r, keep in zip(rows, target) if keep]
    components = {r['biological_component'] for r in held}
    alleles = {r[key] for r in held for key in ('parent_sequence', 'mutant_sequence')}
    genes = {str(r['gene_transcript']).strip().upper() for r in held}
    chosen = [bool(keep and r['biological_component'] not in components)
              for r, keep in zip(rows, train)]
    training = [r for r, keep in zip(rows, chosen) if keep]
    # Original purge removes components ONLY; contradiction stops, never adds
    # a new gene/allele filter or silently changes original source training.
    assert not {r[key] for r in training for key in ('parent_sequence', 'mutant_sequence')} & alleles
    assert not {str(r['gene_transcript']).strip().upper() for r in training} & genes
    return chosen


def outer(rows, task, fold):
    assert task in TASKS and fold in FOLDS
    source, target = TASKS[task]
    test = [r['cell_type'] == target and int(r['held_parent_fold']) == fold for r in rows]
    train = [r['cell_type'] == source and int(r['held_parent_fold']) != fold for r in rows]
    train = purge(rows, train, test)
    assert any(train) and any(test)
    return train, test


def inner(rows, fold):
    assert len({r['cell_type'] for r in rows}) == 1
    validation = [int(r['held_parent_fold']) == fold for r in rows]
    train = purge(rows, [not keep for keep in validation], validation)
    assert any(train) and any(validation)
    return train, validation


def known(rows, task, fold):
    assert task in KNOWN_TASKS and fold in FOLDS
    cell, source_task = KNOWN_TASKS[task]
    train, opposite = outer(rows, source_task, fold)
    target = [r['cell_type'] == cell and int(r['held_parent_fold']) == fold for r in rows]
    assert any(target) and not any(a and b for a, b in zip(train, target))
    assert purge(rows, train, target) == train, 'Same-cell overlap; STOP, no union-purge refit'
    all_sizes = Counter(r['parent_context_id'] for r in rows)
    target_sizes = Counter(r['parent_context_id'] for r, keep in zip(rows, target) if keep)
    assert all(all_sizes[key] == value for key, value in target_sizes.items()), 'Partial menu'
    assert {r['cell_type'] for r, keep in zip(rows, train) if keep} == {cell}
    return train, target, opposite


def source_choice(values):
    assert len(values) == len(CONFIGS)
    import math
    assert all(math.isfinite(value) for value in values)
    minimum = min(values)
    return next(c for c, value in zip(CONFIGS, values) if value <= minimum + 1e-12)


def comparison_checks(comparison):
    """Consumes verified summaries only; implements unchanged parallel gates."""
    assert len(comparison['per_cell_gain']) == len(comparison['wrong_direction_harm']) == 2
    return {
        'macro_gain': comparison['mean_gain'] >= GATE['baseline_macro_gain_min'],
        'each_cell_gain': min(comparison['per_cell_gain'].values()) >= GATE['baseline_each_cell_gain_min'],
        'bootstrap_lower': comparison['gain_ci'][0] > GATE['bootstrap_lower_strict_min'],
        'macro_wrong_harm': comparison['macro_wrong_direction_harm'] <= GATE['macro_wrong_harm_max'],
        'each_cell_wrong_harm': max(comparison['wrong_direction_harm'].values()) <= GATE['each_cell_wrong_harm_max'],
        'leave_best_positive': comparison['remaining_gain'] > GATE['leave_best_gain_strict_min'],
    }


def information_checks(comparison):
    return {'information_gain': comparison['mean_gain'] >= GATE['information_macro_gain_min'],
            'information_leave_best_positive': comparison['remaining_gain'] > GATE['information_leave_best_strict_min']}


def byte_equality(left, right, name):
    assert isinstance(left, bytes) and isinstance(right, bytes)
    assert left == right, 'Exact reused-control byte inequality: ' + name
