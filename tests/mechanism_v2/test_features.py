import numpy as np
import pytest
from src.mechanism_v2.features import fold_sequence,native_fold_hash


def test_folding_known_hairpin_repeats():
    a=np.array(fold_sequence('GGGAAACCC'))
    assert np.array_equal(a,np.array(fold_sequence('GGGAAACCC')))
    assert a[0]<0 and a[1]<=a[0]
    assert 0<=a[2]<=1 and 0<=a[5]<=1
    assert a[3]>=0 and a[4]>=0
    assert len(native_fold_hash())==64


def test_unstructured_homopolymer():
    a=fold_sequence('AAAAAAAAAAAA')
    assert a[0]==0 and a[2]==1 and a[5]==0
    with pytest.raises(ValueError):fold_sequence('NNNN')
