"""Separate source-only selector arithmetic; exact saved scores and ID ties."""
from collections import defaultdict
import math
from src.generalization_knowncell_joint_design_20261009.spec import CELLS, CONFIGS, FOLDS
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata


def independent_metrics(rows,truths,scores):
    contexts = metadata.validate_rows(rows)
    identifiers = {row['intervention_id'] for row in rows}
    assert set(truths)==set(scores)==identifiers
    assert all(type(value) in (int,float) and math.isfinite(value) for value in truths.values())
    assert all(type(value) is float and math.isfinite(value) for value in scores.values())
    pairs,_ = metadata.exact_pairs(rows)
    paired = {context for pair in pairs for context in pair['contexts'].values()}
    assert paired
    by_component = defaultdict(list)
    count = 0
    for context in sorted(paired):
        group = contexts[context]
        values = [truths[row['intervention_id']] for row in group]
        low,high = min(values),max(values)
        assert high>low
        # Sorting establishes the original-ID rule even for a numerically exact
        # tie. No epsilon or scalar score substitute enters candidate choices.
        ordered = sorted(group,key=lambda row:row['intervention_id'])
        for direction in (-1,1):
            chosen = max(ordered,key=lambda row:direction*scores[row['intervention_id']])
            selected = direction*truths[chosen['intervention_id']]
            best = max(direction*value for value in values)
            regret = (best-selected)/(high-low)
            assert math.isfinite(regret) and 0<=regret<=1
            by_component[chosen['cell_type'],chosen['biological_component']].append(regret)
            count += 1
    components = [{gene for cell,gene in by_component if cell==actual} for actual in CELLS]
    assert components[0]==components[1] and components[0]
    means = {}
    for cell in CELLS:
        per_gene = [math.fsum(by_component[cell,gene])/len(by_component[cell,gene]) for gene in sorted(components[0])]
        means[cell] = math.fsum(per_gene)/len(components[0])
    assert count==4*len(pairs)
    return {'macro_regret':math.fsum(means.values())/2.,'per_cell_regret':means,
            'components':len(components[0]),'decisions':count}


def reselect(rows,effects,outer_fold,batches,held_ids):
    """Only source rows/effects and all two-fold OOF scores are accepted.

    Each configuration is evaluated on concatenated source predictions, with
    equal cell/component/menu/direction weighting. Unequal folds are not given
    equal mass. Unmatched predictions are mandatory but never gate selection.
    """
    assert type(outer_fold) is int and outer_fold in FOLDS
    identifiers = [row['intervention_id'] for row in rows]
    assert len(identifiers)==len(set(identifiers))==len(effects)>0
    assert not set(identifiers)&set(held_ids)
    assert all(row['held_parent_fold']!=outer_fold for row in rows)
    truths = dict(zip(identifiers,effects))
    inner_folds = set(FOLDS)-{outer_fold}
    assert {row['held_parent_fold'] for row in rows}==inner_folds
    assert set(batches)=={config['id'] for config in CONFIGS}
    metrics = {}
    for config in CONFIGS:
        by_fold = batches[config['id']]
        assert set(by_fold)==inner_folds
        scores = {}
        for fold in sorted(inner_folds):
            expected = [row['intervention_id'] for row in rows if row['held_parent_fold']==fold]
            predictions = by_fold[fold]
            assert predictions['row_ids']==expected,'Source OOF target order is incomplete or includes held genes'
            assert len(predictions['scores'])==len(expected)
            assert not set(scores)&set(expected)
            scores.update(zip(expected,predictions['scores']))
        assert set(scores)==set(identifiers)
        metrics[config['id']] = independent_metrics(rows,truths,scores)
    values = [metrics[config['id']]['macro_regret'] for config in CONFIGS]
    minimum = min(values)
    chosen = next(dict(config) for config,value in zip(CONFIGS,values) if value<=minimum+1e-12)
    return {'selected_config':chosen,'configuration_metrics':metrics,'source_row_count':len(rows),
            'source_only':True,'primary_paired_only':True,
            'canonical_ties':'exact_score_then_original_intervention_id'}
