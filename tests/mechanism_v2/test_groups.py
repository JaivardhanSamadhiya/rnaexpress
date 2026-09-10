import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.groups import component_groups,assert_partition_disjoint


def fixture():
    return pd.DataFrame({'biological_unit':['a','b','c','d'],'parent_sequence':['AAAA','CCCC','GGGG','GGGA'],
        'mutant_sequence':['AAAT','AAAT','GGGT','GGGC'],'gene_id':[None]*4,'gene_name':['one','two','three','four'],
        'feature_row':[0,1,2,3]})


def test_derived_sequence_connects_units():
    groups,audit=component_groups(fixture())
    assert audit['components']==3 and groups[0]==groups[1]
    assert groups[2]!=groups[3]


def test_near_parent_sensitive_grouping():
    _,audit=component_groups(fixture(),near_identity=.75)
    assert audit['components']==2


def test_parent_gene_and_partition_guard():
    f=fixture();f.loc[3,'gene_name']='three'
    groups,audit=component_groups(f)
    assert audit['components']==2
    with pytest.raises(ValueError):
        assert_partition_disjoint(f,[0,1,0,0],groups)
    assert_partition_disjoint(f,[0,0,1,1],groups)
