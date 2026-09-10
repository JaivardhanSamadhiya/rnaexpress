import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.transfer_inventory import purged_partition,build_transfer_tasks


def test_cross_source_shared_gene_is_purged():
    rows=pd.DataFrame({'component':['a','b','a','c'],'feature_row':[0,1,2,3]})
    train,test,n=purged_partition(rows,[1,1,0,0],[0,0,1,1])
    assert train.tolist()==[1] and test.tolist()==[2,3] and n==1
    with pytest.raises(ValueError):purged_partition(rows,[1,1,0,0],[1,0,0,1])


def test_transfer_inventory_never_reuses_parent_across_contexts():
    records=[]
    for source,field,contexts in [('mikl_gse173098','cell_type',['CAD','Neuro-2a']),
        ('moffatt_gse334718','reporter',['GFP','Firefly']),('tdp43_gse288185','reporter',['MPRA reporter'])]:
        for unit in range(10):
            for context in contexts:
                record={'dataset':source,'biological_unit':source+str(unit),'component':source+str(unit),
                    'outer_fold':unit%5,'feature_row':1000*len(records)+unit,'decision_set_id':f'{source}_{unit}_{context}',
                    'cell_type':'CAD','reporter':'GFP','edit_cost':2 if unit%2 else 20}
                record[field]=context;records.append(record)
    rows=pd.DataFrame(records);tasks=build_transfer_tasks(rows)
    assert len(tasks)==43
    for task in tasks:
        train=rows.iloc[task['train_row_ids']];test=rows.iloc[task['test_row_ids']]
        assert not set(train.component)&set(test.component)
        assert task['outcomes_used'] is False
        if task['kind']=='cross_cell':
            assert train.cell_type.nunique()==test.cell_type.nunique()==1
            assert train.cell_type.iloc[0]!=test.cell_type.iloc[0]
