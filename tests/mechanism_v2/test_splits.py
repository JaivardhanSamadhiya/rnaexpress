import numpy as np
import pandas as pd
from src.mechanism_v2.splits import balanced_group_folds


def test_fold_assignment_is_outcome_blind_and_group_disjoint():
    rows=pd.DataFrame({'dataset':np.repeat(['s1','s2','s3'],12),
        'biological_unit':[f'u{i}' for i in range(36)],'feature_row':np.arange(36),
        'localization_effect':np.arange(36)})
    groups=np.array([f'g{i}' for i in range(36)]);groups[12]=groups[0]
    first=balanced_group_folds(rows,groups)
    rows['localization_effect']=-rows.localization_effect*200
    np.testing.assert_array_equal(first,balanced_group_folds(rows,groups))
    assert first[0]==first[12]
    assert len(set(first))==5
    perm=np.random.default_rng(20).permutation(len(rows))
    moved=balanced_group_folds(rows.iloc[perm],groups[perm])
    np.testing.assert_array_equal(first[perm],moved)
