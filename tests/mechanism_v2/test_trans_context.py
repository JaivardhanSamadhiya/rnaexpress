import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.trans_context import aligned_interactions


def test_aligned_context_and_unsupported_cell_guard():
    expression=pd.DataFrame({'human_rbp':['A','A','B','B','C','C'],
        'cell_line':['CAD','N2A']*3,'context_eligible':[True]*4+[False]*2,
        'compartment_balanced_expression_proxy':[1.,3.,3.,1.,np.nan,np.nan]})
    delta=np.zeros((2,3,4));delta[:,0]=1;delta[:,1]=2;delta[:,2]=999
    value,audit=aligned_interactions(delta,['A','B','C'],expression,['CAD','N2A'])
    np.testing.assert_allclose(value,[[1.75]*4,[1.25]*4])
    assert audit['eligible_proteins']==['A','B'] and len(audit['excluded'])==1
    with pytest.raises(PermissionError):aligned_interactions(delta,['A','B','C'],expression,['CAD','unsupported'])
