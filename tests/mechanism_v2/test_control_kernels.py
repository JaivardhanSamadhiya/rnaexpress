import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.control_kernels import intervention_permutation,permute_rbp_identities,random_projection,random_sequence_delta


def rows_for_permutation():
    return pd.DataFrame({'feature_row':[0,0,1,2,3,3,4,5],
        'dataset':['a']*8,'biological_unit':['u','u','v','w','x','x','y','z'],
        'component':['u','u','v','w','x','x','y','z'],'edit_cost':[2]*8,
        'parent_sequence':['ACGT']*8})


def test_permutation_replicates_once_per_unique_intervention():
    rows=rows_for_permutation();partition=[0,0,0,0,1,1,1,1]
    donors,eligible,audit=intervention_permutation(rows,partition,['dataset','edit_band'],seed=12,cross_component=True)
    assert donors[0]==donors[1] and donors[4]==donors[5]
    assert eligible.all() and audit['unique_interventions']==6
    np.testing.assert_array_equal(sorted(donors[[0,2,3]]),[0,1,2])
    np.testing.assert_array_equal(sorted(donors[[4,6,7]]),[3,4,5])
    assert (donors!=rows.feature_row.to_numpy()).all()


def test_repeated_intervention_cannot_cross_null_partitions():
    with pytest.raises(ValueError):intervention_permutation(rows_for_permutation(),[0,1,0,0,1,1,1,1])


def test_identity_null_preserves_summary_roles_and_replicated_rows():
    x=np.tile(np.arange(40).reshape(1,10,4),(3,1,1))
    altered,_=permute_rbp_identities(x,['same','same','different'])
    np.testing.assert_array_equal(altered[0],altered[1])
    assert not np.array_equal(altered[0],altered[2])
    for row in altered:
        np.testing.assert_array_equal(np.sort(row[:,0]),x[0,:,0])
        np.testing.assert_array_equal(np.diff(row,axis=1),np.ones((10,3)))


def test_random_embedding_is_a_frozen_sequence_function():
    projection=random_projection(output_dimensions=8)
    a='ACGTACGT';b='ACTTACGT'
    forward=random_sequence_delta(a,b,projection)
    np.testing.assert_array_equal(forward,-random_sequence_delta(b,a,projection))
    np.testing.assert_array_equal(random_sequence_delta(a,a,projection),np.zeros(8))
    np.testing.assert_array_equal(projection,random_projection(output_dimensions=8))
