import numpy as np
import pandas as pd
import pytest

from src.mechanism_v2.fitting import assert_outer_boundary, partition_audit, row_identity


def inventory():
    return pd.DataFrame({
        'component': ['a', 'a', 'b', 'b', 'c', 'c'],
        'feature_row': [0, 1, 2, 3, 4, 5],
        'decision_set_id': ['d0', 'd0', 'd1', 'd1', 'd2', 'd2'],
        'outer_fold': [0, 0, 1, 1, 1, 1],
    })


def test_row_identity_is_order_sensitive_and_compact():
    assert row_identity([0, 1, 2]) != row_identity([2, 1, 0])
    assert row_identity([0, 1, 2])['count'] == 3
    with pytest.raises(ValueError):
        row_identity([])


def test_partition_audit_rejects_component_and_intervention_leakage():
    rows = inventory()
    with pytest.raises(PermissionError):
        partition_audit(rows, [0], [1])
    audit = partition_audit(rows, [0, 1], [2, 3])
    assert audit['shared_components'] == [] and audit['group_purged']
    assert audit['train_components'] == 1 and audit['evaluation_components'] == 1


def test_partition_audit_rejects_overlap_and_duplicates():
    rows = inventory()
    with pytest.raises(ValueError, match='overlap'):
        partition_audit(rows, [0, 1], [1, 2], purge_groups=False)
    with pytest.raises(ValueError, match='Duplicate'):
        partition_audit(rows, [0, 0], [2], purge_groups=False)
    with pytest.raises(ValueError, match='outside'):
        partition_audit(rows, [0], [99], purge_groups=False)


def test_outer_boundary_requires_the_whole_untouched_fold_exactly_once():
    rows = inventory()
    audit = assert_outer_boundary(rows, 1, [0, 1], [2, 3, 4, 5])
    assert audit['evaluation_components'] == 2
    with pytest.raises(PermissionError, match='whole untouched fold'):
        assert_outer_boundary(rows, 1, [0, 1], [2, 3])
    with pytest.raises(PermissionError, match='reached outer training'):
        assert_outer_boundary(rows, 1, [0, 1, 2], [3, 4, 5])
    with pytest.raises(PermissionError, match='another fold'):
        assert_outer_boundary(rows, 0, [2, 3, 4, 5], [0, 1, 2])
