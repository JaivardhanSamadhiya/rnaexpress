"""Describe the actual menu sizes relevant to the proposed loss hypothesis.

Only already exposed saved decision records are accepted. No candidate search,
training, original labels/features, protected outcomes or threshold changes.
"""
from collections import Counter, defaultdict
import math

ARMS = ('pooled', 'independent', 'joint_shrink10')


def require(value, message):
    if not value:raise ValueError(message)


def size_bin(size):
    return str(size) if size <= 4 else ('5-9' if size < 10 else '10+')


def analyze(result):
    decisions = result['primary_decisions']
    require(set(decisions) == set(ARMS), 'expected all three frozen arms')
    grouped = {}
    for arm in ARMS:
        groups = defaultdict(dict)
        for row in decisions[arm]:
            key = (row['cell_type'], row['biological_component'], row['parent_context_id'])
            d = row['direction']
            require(d in (-1,1) and d not in groups[key], 'duplicate or invalid direction')
            require(isinstance(row['candidates'],int) and row['candidates'] >= 2, 'invalid menu size')
            require(math.isfinite(row['regret']) and -1e-12 <= row['regret'] <= 1+1e-12,
                    'invalid saved regret')
            require(math.isfinite(row['selected_score']), 'nonfinite saved extremum')
            groups[key][d] = row
        require(bool(groups), 'empty decisions')
        for directions in groups.values():
            require(set(directions) == {-1,1}, 'missing direction')
            require(directions[-1]['candidates'] == directions[1]['candidates'], 'inconsistent candidate count')
        grouped[arm] = dict(groups)
    ref = grouped[ARMS[0]]
    require(all(set(groups) == set(ref) for groups in grouped.values()), 'arm context rosters differ')
    components = defaultdict(set); counts = Counter((cell,component) for cell,component,_ in ref)
    for cell,component,_ in ref:components[cell].add(component)
    weights = {key:1./(len(components)*len(components[key[0]])*counts[key[:2]]) for key in ref}
    require(abs(math.fsum(weights.values())-1.) <= 1e-12, 'invalid hierarchical decision mass')
    sizes = {key:ref[key][1]['candidates'] for key in ref}
    for groups in grouped.values():
        require(all(groups[key][1]['candidates'] == sizes[key] for key in ref), 'arm menu sizes differ')
    bins = {}
    for name in ('2','3','4','5-9','10+'):
        keys = [key for key,size in sizes.items() if size_bin(size) == name]
        bins[name] = {'menus':len(keys),'primary_weight':math.fsum(weights[key] for key in keys)}
    arms = {}
    for arm,groups in grouped.items():
        regrets = {key:math.fsum(row['regret'] for row in dirs.values())/2.
                   for key,dirs in groups.items()}
        constants = []
        for key,dirs in groups.items():
            low, high = dirs[-1], dirs[1]
            require(high['selected_score'] >= low['selected_score'], 'saved extrema scores reversed')
            zero_span = high['selected_score'] == low['selected_score']
            same_id = high['selected_id'] == low['selected_id']
            require(zero_span == same_id, 'canonical score/ID extrema inconsistency')
            if zero_span:
                require(abs(regrets[key]-.5) <= 1e-12, 'constant-score menu must average to regret0.5')
                constants.append(key)
        binary = [key for key,size in sizes.items() if size == 2]
        multi = [key for key,size in sizes.items() if size > 2]
        binary_mass = math.fsum(weights[key] for key in binary)
        multi_contribution = math.fsum(weights[key]*regrets[key] for key in multi)
        conditional = {}
        for name in bins:
            keys = [key for key,size in sizes.items() if size_bin(size) == name]
            mass = bins[name]['primary_weight']
            conditional[name] = math.fsum(weights[key]*regrets[key] for key in keys)/mass if mass else None
        macro = math.fsum(weights[key]*value for key,value in regrets.items())
        arms[arm] = {'macro_regret_recomputed':macro,'conditional_regret_by_menu_size':conditional,
                     'binary_implied_tie_aware_pair_accuracy':1.-conditional['2'] if binary_mass else None,
                     'exact_constant_score_menus':len(constants),
                     'exact_constant_score_primary_weight':math.fsum(weights[key] for key in constants),
                     'multicandidate_current_regret_contribution':multi_contribution,
                     'restricted_best_possible_regret_if_only_multicandidate_choices_change':macro-multi_contribution}
    return {'status':'POST_GATE_SAVED_MENU_FEASIBILITY_NOT_NEW_PRIMARY',
            'menus_per_arm':len(ref),'cells':sorted(components),
            'components_per_cell':{cell:len(values) for cell,values in components.items()},
            'menu_size_bins':bins,'maximum_menu_size':max(sizes.values()),'arms':arms,
            'fits_or_refits':0,'original_feature_or_label_inputs_reopened':False,
            'frozen_primary_verdict_unchanged':result['status'],
            'restricted_bound_scope':'Only changes to choices in menus with more than two candidates; binary choices held fixed. Not a bound on other predictors or biology.',
            'constant_score_cause_identified':False,
            'note':'Two-candidate menu regret is one minus tie-aware ordering accuracy. The proposed menu loss then changes margin/temperature, not relative cost weighting among multiple alternatives.'}
