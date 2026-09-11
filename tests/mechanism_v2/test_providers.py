import numpy as np
import pandas as pd
import pytest

from src.mechanism_v2 import providers
from src.mechanism_v2.controls import decision_complete_mask
from src.mechanism_v2.reporting import ALLOWED


class StubStore:
    """Minimal stand-in with the exact interface the providers rely on."""

    def __init__(self, n_rows=12, n_interventions=11):
        rng = np.random.default_rng(3)
        # Six two-candidate components; component c0 repeats one intervention twice, so the
        # replicated-context rules are genuinely exercised without violating them.
        self.rows = pd.DataFrame({
            'dataset': ['mikl_gse173098'] * 6 + ['moffatt_gse334718'] * 6,
            'biological_unit': [f'u{i // 2}' for i in range(n_rows)],
            'component': [f'c{i // 2}' for i in range(n_rows)],
            'decision_set_id': [f'd{i // 2}' for i in range(n_rows)],
            'candidate_id': [f'k{i}' for i in range(n_rows)],
            'feature_row': [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'edit_cost': [3, 3, 7, 20, 40, 300, 1, 3, 7, 20, 40, 300],
            'edit_fraction': np.linspace(0.01, 0.5, n_rows),
            'intervention_class': ['random_substitution'] * n_rows,
            'parent_sequence': ['ACGT' * 25] * n_rows,
            'outer_fold': [0] * 8 + [1] * 4,
        })
        self.feature_rows = self.rows.feature_row.to_numpy(int)
        self.design = {'families': {'M0': ['geometry'], 'M4': ['rbp_delta', 'structure_delta']},
                       'recipes_per_family': [{'id': 'A', 'ridge': 0.01, 'nuisance': 'none',
                                               'ranking_heads': False}],
                       'ranker_constants': {'nuisance_strength': 0.1, 'head_shrinkage': 0.1,
                                            'pairs_per_set': 8, 'max_iterations': 20,
                                            'tolerance': 1e-8},
                       'seed': 20260909, 'outer_folds': 2, 'inner_folds': 2,
                       'selection': {'regret_tolerance': 0.002}}
        self.blocks = {'geometry': rng.normal(size=(n_rows, 3)),
                       'rbp_delta': rng.normal(size=(n_interventions, 4)),
                       'structure_delta': rng.normal(size=(n_interventions, 2))}
        self.records = {}

    def matrix(self, family):
        names = self.design['families'][family]
        blocks = [self.blocks[n] if n == 'geometry' else self.blocks[n][self.feature_rows]
                  for n in names]
        columns = [f'{n}:{j:03d}' for n in names for j in range(self.blocks[n].shape[1])]
        return np.column_stack(blocks).astype(np.float32), columns


def test_edit_descriptor_columns_are_declared_not_data_derived():
    store = StubStore()
    provider = providers.EditDescriptorProvider()
    x, columns, audit = provider.build(store, np.arange(8), np.arange(8, 12), 'inner_0_0')
    assert len(columns) == len(providers.EDIT_BANDS) + len(providers.INTERVENTION_CLASSES) + 3
    assert x.shape == (len(store.rows), len(columns))
    assert np.isfinite(x).all()
    store.rows.loc[0, 'intervention_class'] = 'invented_class'
    with pytest.raises(ValueError, match='Undeclared mutation class'):
        providers.EditDescriptorProvider().build(store, np.arange(8), np.arange(8, 12), 'inner_0_0')


def test_static_provider_is_memoized_and_releasable():
    store = StubStore()
    provider = providers.FamilyProvider('M0')
    first = provider.build(store, np.arange(8), np.arange(8, 12), 'outer_0')
    assert provider.build(store, np.arange(8), np.arange(8, 12), 'outer_0') is first
    provider.release()
    assert provider.build(store, np.arange(8), np.arange(8, 12), 'outer_0') is not first


def test_block_removal_keeps_the_other_blocks_only():
    store = StubStore()
    provider = providers.BlockRemovalProvider('M4', 'structure_delta')
    x, columns, audit = provider.build(store, np.arange(8), np.arange(8, 12), 'outer_0')
    assert all(c.startswith('rbp_delta:') for c in columns)
    assert audit['removed_block'] == 'structure_delta'
    with pytest.raises(ValueError, match='not part of'):
        providers.BlockRemovalProvider('M4', 'motif_delta').build(
            store, np.arange(8), np.arange(8, 12), 'outer_0')


def test_bijection_permutes_only_named_blocks_and_stays_inside_the_partition():
    store = StubStore()
    provider = providers.BijectionProvider('M4', blocks=('structure_delta',), strata=())
    train, held = np.arange(8), np.arange(8, 12)
    x, columns, audit = provider.build(store, train, held, 'outer_0')
    truth, _ = store.matrix('M4')
    assert np.allclose(x[:, :4], truth[:, :4])
    assert audit['permuted_blocks'] == ['structure_delta']
    assert audit['preserved_blocks'] == ['rbp_delta']
    assert audit['unique_interventions'] >= 2
    mask = provider.eligibility(store, train, held, 'outer_0')
    assert mask[np.concatenate([train, held])].any()


def test_bijection_donors_never_cross_the_train_evaluation_boundary():
    store = StubStore()
    provider = providers.BijectionProvider('M4', strata=())
    train, held = np.arange(8), np.arange(8, 12)
    idx, donor, eligible, audit = provider._plan(store, train, held)
    partition = np.where(np.arange(len(idx)) < len(train), 'train', 'evaluation')
    donor_partition = {}
    for row, group in zip(store.feature_rows[idx], partition):
        donor_partition.setdefault(int(row), group)
    for received, group in zip(donor, partition):
        assert donor_partition[int(received)] == group


def test_parent_identity_control_is_ineligible_and_explains_itself():
    provider = providers.ParentIdentityProvider()
    assert provider.eligible is False
    assert 'unseen' in provider.ineligible_reason
    with pytest.raises(PermissionError):
        provider.build(StubStore(), np.arange(8), np.arange(8, 12), 'outer_0')


def test_decision_complete_mask_drops_partially_eligible_decisions():
    rows = pd.DataFrame({'decision_set_id': ['d0', 'd0', 'd1', 'd1']})
    mask = decision_complete_mask(rows, [True, False, True, True])
    assert mask.tolist() == [False, False, True, True]


def test_only_three_verdicts_exist():
    assert len(ALLOWED) == 3
    assert ALLOWED[2] == 'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS'
    assert all('ZERO-SHOT' in v for v in ALLOWED)
