import json

import numpy as np
import pandas as pd
import pytest

from src.mechanism_v2 import gates
from src.mechanism_v2.io import ROOT


def cohort(components=30, candidates=4, gain=0.5, sources=('a', 'b')):
    """Synthetic decision sets whose outcomes are known, so gains are checkable."""
    records = []
    rng = np.random.default_rng(7)
    for source in sources:
        for unit in range(components):
            for candidate in range(candidates):
                records.append({
                    'dataset': source, 'component': f'c{unit}', 'biological_unit': f'c{unit}',
                    'decision_set_id': f'{source}_d{unit}', 'candidate_id': f'k{candidate}',
                    'localization_effect': float(rng.normal()),
                    'edit_cost': 3 + candidate, 'edit_fraction': 0.01 * (candidate + 1),
                    'intervention_class': 'random_substitution' if candidate % 2 else 'regional_shuffle',
                    'gene_name': f'g{unit}', 'motif_family': 'not_applicable',
                    'reporter': 'GFP', 'cell_type': 'CAD', 'direction': 'increase',
                })
    rows = gates.with_strata(pd.DataFrame(records))
    truth = rows.localization_effect.to_numpy(float)
    good = gain * truth + (1 - gain) * rng.normal(size=len(truth))
    return rows, good, rng.normal(size=len(truth))


def test_frozen_gate_config_is_readable_and_versioned():
    record = gates.frozen_gates()
    assert record['version'] == 'mechanism_v2_frozen_gates_v1'
    assert record['gates']['g1_useful_selection']['rank_gain_minimum'] == 0.020
    assert record['gates']['g1_useful_selection']['regret_gain_minimum'] == 0.010
    assert record['gates']['g2_distributed_benefit']['fraction_components_improved_minimum'] == 0.55
    assert record['verdicts']['development_only_result_cannot_be_a_go'] is True


def test_perfect_score_passes_and_noise_fails_useful_selection():
    rows, good, noise = cohort()
    truth = rows.localization_effect.to_numpy(float)
    config = gates.frozen_gates()
    strong = gates.paired_evidence(rows, truth, noise, bootstrap=200, label='oracle')
    assert strong['eligible'] and strong['point']['rank_gain'] > 0.2
    assert gates.gate_useful_selection(strong, config)['status'] == 'pass'
    weak = gates.paired_evidence(rows, noise, noise * -1.0, bootstrap=200, label='noise')
    assert gates.gate_useful_selection(weak, config)['status'] in {'fail', 'pass'}
    identical = gates.paired_evidence(rows, noise, noise, bootstrap=200, label='identical')
    assert identical['point']['rank_gain'] == 0.0 and identical['point']['regret_gain'] == 0.0
    assert gates.gate_useful_selection(identical, config)['status'] == 'fail'


def test_restriction_splits_decision_sets_without_merging_them():
    rows, good, noise = cohort(components=3, candidates=4)
    restricted = gates.restrict_decisions(rows, ('edit_band', 'intervention_class'))
    assert restricted.decision_set_id.nunique() > rows.decision_set_id.nunique()
    for value in restricted.decision_set_id:
        assert value.count('||') == 1
    original = set(rows.decision_set_id)
    assert all(v.split('||')[0] in original for v in restricted.decision_set_id)


def test_matched_gate_is_ineligible_below_the_component_minimum():
    rows, good, noise = cohort(components=5)
    truth = rows.localization_effect.to_numpy(float)
    config = gates.frozen_gates()
    evidence = gates.paired_evidence(rows, truth, noise, bootstrap=200)
    record = gates.gate_matched_edits(evidence, config)
    assert record['status'] == 'ineligible' and 'components' in record['reason']


def test_cap_two_per_gene_leaves_at_most_two_candidates():
    rows, _, _ = cohort(components=4, candidates=6)
    capped = gates.cap_two_per_gene(rows)
    sizes = capped.groupby(['decision_set_id', 'gene_label']).size()
    assert sizes.max() <= 2


def test_direction_filter_yields_single_direction_evidence():
    rows, good, noise = cohort(components=25)
    truth = rows.localization_effect.to_numpy(float)
    increase = gates.paired_evidence(rows, truth, noise, direction='increase', bootstrap=200)
    decrease = gates.paired_evidence(rows, truth, noise, direction='decrease', bootstrap=200)
    assert increase['direction'] == 'increase' and decrease['direction'] == 'decrease'
    assert increase['point']['rank_gain'] != decrease['point']['rank_gain']
    with pytest.raises(ValueError):
        gates.paired_evidence(rows, truth, noise, direction='sideways')


def test_minimum_decisions_makes_thin_evidence_ineligible():
    rows, good, noise = cohort(components=2)
    truth = rows.localization_effect.to_numpy(float)
    record = gates.paired_evidence(rows, truth, noise, minimum_decisions=1000)
    assert record['eligible'] is False and 'below the required' in record['reason']


def test_retained_fraction_is_undefined_for_nonpositive_full_gain():
    assert gates.retained_fraction({'regret_gain': 0.0}, {'regret_gain': 0.5}, 'regret_gain') is None
    assert gates.retained_fraction({'regret_gain': -0.1}, {'regret_gain': 0.5}, 'regret_gain') is None
    assert gates.retained_fraction({'regret_gain': 0.2}, {'regret_gain': 0.1}, 'regret_gain') == 0.5


def test_sign_test_is_bounded_and_never_exactly_zero():
    record = gates.paired_sign_test(np.full(40, 0.5), resamples=500, seed=1)
    assert 0 < record['p_value'] <= 1
    null = gates.paired_sign_test(np.array([0.1, -0.1, 0.2, -0.2]), resamples=500, seed=1)
    assert null['p_value'] > 0.1
    with pytest.raises(ValueError):
        gates.paired_sign_test([1.0])


def test_necessity_gate_fails_when_a_null_reproduces_the_gain():
    config = gates.frozen_gates()
    full = {'eligible': True, 'point': {'rank_gain': 0.10, 'regret_gain': 0.05},
            'components': 40, 'decisions': 100}
    identical = {'eligible': True, 'point': {'rank_gain': 0.10, 'regret_gain': 0.05},
                 'components': 40, 'decisions': 100}
    destroyed = {'eligible': True, 'point': {'rank_gain': 0.00, 'regret_gain': 0.00},
                 'components': 40, 'decisions': 100}
    nulls = {'n5_bijection_global': identical, 'n8_bijection_source_edit_band': identical}
    record = gates.gate_necessity(full, nulls, {}, config)
    assert record['status'] == 'fail'
    assert record['nulls']['n5_bijection_global']['null_meets_both_useful_selection_thresholds']
    nulls = {'n5_bijection_global': destroyed, 'n8_bijection_source_edit_band': destroyed}
    removals = {'rbp_delta': {'eligible': True, 'harm': {'rank_gain': 0.05, 'regret_gain': 0.02},
                              'p_value': 0.0001, 'components': 40}}
    record = gates.gate_necessity(full, nulls, removals, config)
    assert record['status'] == 'pass'
    assert record['block_removals']['rbp_delta']['claim'] is True
    assert record['block_removals']['trans_aligned']['p_value'] == 1.0
    assert record['block_removals']['trans_aligned']['claim'] is False


def test_hard_harm_flags_a_single_bad_task():
    config = gates.frozen_gates()
    distributed = {'worst_decile_mean': -0.01}
    good = gates.gate_hard_harm({'a': 0.01, 'b': -0.001}, distributed, config)
    assert good['status'] == 'pass'
    bad = gates.gate_hard_harm({'a': 0.01, 'b': -0.05}, distributed, config)
    assert bad['status'] == 'fail' and 'b' in bad['violations']
    catastrophic = gates.gate_hard_harm({'a': 0.01}, {'worst_decile_mean': -0.5}, config)
    assert catastrophic['status'] == 'fail'


def test_leave_source_gate_requires_all_six_tasks():
    config = gates.frozen_gates()
    tasks = {}
    for source in ('s1', 's2', 's3'):
        for direction in ('increase', 'decrease'):
            tasks[f'leave_source_{source}|{direction}'] = {
                'eligible': True, 'point': {'rank_gain': 0.05, 'regret_gain': 0.03}}
    assert gates.gate_leave_source(tasks, config)['status'] == 'pass'
    tasks.pop('leave_source_s3|decrease')
    assert gates.gate_leave_source(tasks, config)['status'] == 'ineligible'


def test_small_edit_gate_requires_both_subbands():
    config = gates.frozen_gates()
    bands = {'2-10': {'eligible': True, 'point': {'rank_gain': 0.05, 'regret_gain': 0.03},
                      'components': 40},
             '2-5': {'eligible': True, 'point': {'rank_gain': 0.04, 'regret_gain': 0.02}},
             '6-10': {'eligible': True, 'point': {'rank_gain': 0.04, 'regret_gain': 0.02}}}
    assert gates.gate_small_edits(bands, config)['status'] == 'pass'
    bands['6-10'] = {'eligible': True, 'point': {'rank_gain': 0.0, 'regret_gain': -0.02}}
    assert gates.gate_small_edits(bands, config)['status'] == 'fail'
    bands['6-10'] = {'eligible': False, 'reason': 'no rows'}
    assert gates.gate_small_edits(bands, config)['status'] == 'ineligible'
