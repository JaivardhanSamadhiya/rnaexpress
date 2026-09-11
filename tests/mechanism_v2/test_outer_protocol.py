import numpy as np
import pandas as pd
import pytest

from src.mechanism_v2 import reporting
from src.mechanism_v2.gates import frozen_gates
from src.mechanism_v2.outer_evaluation import recipe_variants
from src.mechanism_v2.shortcut_probes import FORBIDDEN, grouped_nearest_mean_probe
from src.mechanism_v2.uncertainty import bootstrap_draw, percentile_rank
from tests.mechanism_v2.test_providers import StubStore


def test_recipe_variant_complexity_counts_nuisance_and_head_parameters():
    store = StubStore()
    store.design['recipes_per_family'] = [
        {'id': 'A', 'ridge': 0.01, 'nuisance': 'none', 'ranking_heads': False},
        {'id': 'D', 'ridge': 0.01, 'nuisance': 'source_size', 'ranking_heads': False},
        {'id': 'F', 'ridge': 0.01, 'nuisance': 'none', 'ranking_heads': True},
    ]
    variants = {v['variant']: v for v in recipe_variants(store, 100)}
    assert variants['A']['complexity'] == 100
    assert variants['D']['complexity'] == 110
    assert variants['F']['complexity'] == 103
    assert variants['A']['config']['seed'] == store.design['seed']
    assert variants['A']['config']['pairs_per_set'] == 8


def test_percentile_rank_is_within_decision_and_bounded():
    rows = pd.DataFrame({'decision_set_id': ['d0', 'd0', 'd0', 'd1', 'd1']})
    values = percentile_rank(rows, [1.0, 2.0, 3.0, 5.0, -5.0])
    assert values.tolist() == [0.0, 0.5, 1.0, 1.0, 0.0]
    single = percentile_rank(pd.DataFrame({'decision_set_id': ['d']}), [4.0])
    assert single.tolist() == [1.0]


def test_bootstrap_draw_relabels_repeated_components():
    store = StubStore()
    order, frame, audit = bootstrap_draw(store, np.arange(8), seed=5)
    assert len(order) == len(frame)
    assert audit['components_drawn'] == store.rows.iloc[:8].component.nunique()
    assert frame.decision_set_id.str.contains('#b').all()
    assert frame.component.equals(frame.biological_unit)
    # A component drawn twice must not collide with itself inside a decision set.
    assert frame.groupby(['decision_set_id', 'candidate_id']).size().max() == 1
    again = bootstrap_draw(store, np.arange(8), seed=5)
    assert np.array_equal(order, again[0]) and audit['draw_sha256'] == again[2]['draw_sha256']


def test_bootstrap_draw_requires_more_than_one_component():
    store = StubStore()
    with pytest.raises(ValueError, match='two components'):
        bootstrap_draw(store, np.array([0, 1]), seed=1)


def test_probe_reports_majority_baseline_and_refuses_thin_grouping():
    rng = np.random.default_rng(1)
    labels = np.array(['a'] * 60 + ['b'] * 60)
    groups = np.array([f'g{i}' for i in range(120)])
    informative = np.where(labels == 'a', 1.0, -1.0) + rng.normal(0, 0.1, 120)
    record = grouped_nearest_mean_probe(informative, labels, groups)
    assert record['eligible'] and record['accuracy'] > 0.9
    assert record['majority_class_accuracy'] == 0.5
    noise = grouped_nearest_mean_probe(rng.normal(size=120), labels, groups)
    assert noise['accuracy'] < 0.75
    assert grouped_nearest_mean_probe(informative[:3], labels[:3], groups[:3])['eligible'] is False


def test_forbidden_identity_substrings_cover_the_declared_channels():
    for part in ('source_id', 'parent_id', 'gene_id', 'reporter_id', 'localization_effect'):
        assert part in FORBIDDEN


def _table(statuses):
    return {name: {'status': status} for name, status in statuses.items()}


def test_verdict_is_no_go_when_any_gate_fails():
    config = frozen_gates()
    stages = {'development': {'primary_family': 'M4'},
              'transfer': {'gates': {'g5_cross_context': {'cross_cell': {'status': 'fail'}}}}}
    table = _table({'g1_useful_selection': 'pass', 'g2_distributed_benefit': 'fail'})
    verdict = reporting.determine_verdict(table, config, stages)
    assert verdict['verdict'] == reporting.ALLOWED[2]
    assert verdict['gates_failed'] == ['g2_distributed_benefit']
    assert verdict['development_gates_all_passed'] is False
    assert verdict['holdout_opened'] is False
    assert '98ffc02' in verdict['finalshot_historical_result']


def test_all_gates_passing_still_does_not_produce_a_go_verdict():
    config = frozen_gates()
    stages = {'development': {'primary_family': 'M4'},
              'transfer': {'gates': {'g5_cross_context': {'cross_cell': {'status': 'pass'}}}}}
    table = _table({f'g{i}': 'pass' for i in range(1, 11)})
    verdict = reporting.determine_verdict(table, config, stages)
    assert verdict['development_gates_all_passed'] is True
    assert verdict['verdict'] == reporting.ALLOWED[2]
    assert verdict['verdict'] in reporting.ALLOWED
    assert 'holdout' in verdict['astrocyte_holdout']


def test_ineligible_gate_is_not_a_pass():
    config = frozen_gates()
    stages = {'development': {'primary_family': 'M4'},
              'transfer': {'gates': {'g5_cross_context': {'cross_cell': {'status': 'ineligible'}}}}}
    table = _table({'g1_useful_selection': 'pass', 'g5_cross_context': 'ineligible'})
    verdict = reporting.determine_verdict(table, config, stages)
    assert verdict['gates_ineligible'] == ['g5_cross_context']
    assert verdict['development_gates_all_passed'] is False


def test_harm_points_collects_transfer_directions_and_small_bands():
    stages = {
        'transfer': {'tasks': {
            'leave_source_a': {'kind': 'leave_source', 'directions': {
                'increase': {'eligible': True, 'point': {'regret_gain': -0.03}},
                'decrease': {'eligible': False, 'reason': 'thin'}}},
            'within_a': {'kind': 'within_source', 'directions': {
                'increase': {'eligible': True, 'point': {'regret_gain': -0.9}}}}}},
        'development': {'edit_bands': {
            '2-5': {'eligible': True, 'point': {'regret_gain': 0.01}},
            '>50': {'eligible': True, 'point': {'regret_gain': -0.5}}}}}
    points = reporting.harm_points(stages)
    assert points == {'leave_source_a|increase': -0.03, 'band_2-5': 0.01}


def test_trans_clause_does_not_apply_unless_m7_is_selected():
    config = frozen_gates()
    stages = {'development': {'primary_family': 'M4'}, 'transfer': {'gates': {}}}
    assert reporting.trans_clause(stages, config)['applies'] is False
