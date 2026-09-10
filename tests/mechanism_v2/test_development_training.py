import json
import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.io import ROOT
from src.mechanism_v2.development_training import recipes,assert_inner_boundary,metric_summary
from src.mechanism_v2.feature_store import validate_split_alignment
from src.mechanism_v2 import development_training as training
from src.mechanism_v2 import io as guarded_io


def test_recipe_inventory_and_primary_identity_exclusion():
    design=json.loads((ROOT/'configs/mechanism_v2/localization_design.json').read_text())
    recipe=recipes(design)
    assert len(recipe)==48 and len({r['recipe_id'] for r in recipe})==48
    assert {r['config']['nuisance'] for r in recipe}=={'none','source','size','source_size'}
    for family,blocks in design['families'].items():
        if family!='M0':assert 'geometry' not in blocks
        assert not any('absolute' in b or 'source' in b or 'stability' in b for b in blocks)
    assert design['families']['M7'][:-1]==design['families']['M6']


def test_outer_labels_cannot_reach_inner_partitions():
    rows=pd.DataFrame({'outer_fold':[0,0,1,1,2,2],'component':['a','a','b','b','c','c'],
        'feature_row':np.arange(6)})
    assert_inner_boundary(rows,0,[2,3],[4,5])
    with pytest.raises(PermissionError):assert_inner_boundary(rows,0,[0,1],[4,5])
    with pytest.raises(ValueError):assert_inner_boundary(rows,0,[2],[3])
    with pytest.raises(ValueError):assert_inner_boundary(rows,0,[2,2],[4,5])
    rows.loc[4,'feature_row']=2
    with pytest.raises(ValueError):assert_inner_boundary(rows,0,[2,3],[4,5])


def test_metric_selection_balances_components_and_contexts():
    rows=pd.DataFrame({'dataset':['a']*10+['b'],'component':['x']*9+['y','z'],
        'direction':['increase']*11,'regret':[1.]*9+[0.,0.],'rank':[0.]*9+[1.,1.]})
    summary=metric_summary(rows)
    assert summary=={'regret':.25,'rank':.75}


def test_row_inventory_misalignment_rejected():
    rows=pd.DataFrame({'dataset':['a','a'],'biological_unit':['u','v'],
        'decision_set_id':['d1','d2'],'candidate_id':['c1','c2'],'feature_row':[0,1]})
    inventory=rows.assign(component=['u','v'],outer_fold=[0,1])
    validate_split_alignment(rows,inventory)
    with pytest.raises(ValueError):validate_split_alignment(rows,inventory.iloc[::-1])


def test_inner_checkpoint_roundtrip_and_hash_corruption(tmp_path,monkeypatch):
    monkeypatch.setattr(training,'ROOT',tmp_path)
    monkeypatch.setattr(guarded_io,'ROOT',tmp_path)
    monkeypatch.setattr(guarded_io,'OUTPUT_ROOTS',(tmp_path/'results/mechanism_v2',
        tmp_path/'models/mechanism_v2',tmp_path/'data/interim/mechanism_v2'))
    guarded_io.write_json(training.FREEZE,{'synthetic_test':True})
    rng=np.random.default_rng(17);x=rng.normal(size=(30,2))
    rows=pd.DataFrame({'dataset':np.repeat(['a','b']*3,5),
        'component':np.repeat([f'u{i}' for i in range(6)],5),
        'decision_set_id':np.repeat([f'd{i}' for i in range(6)],5),
        'candidate_id':[f'c{i}' for i in range(30)],'edit_cost':np.ones(30),
        'localization_effect':x[:,0]-x[:,1],'feature_row':np.arange(30),
        'outer_fold':np.repeat([0,0,1,1,2,2],5)})
    class SyntheticStore:
        def __init__(self):self.rows=rows
        def train_frame(self,indices):
            part=rows.iloc[indices].copy().reset_index(drop=True)
            part['biological_unit']=part.component
            return part
    store=SyntheticStore();train=np.arange(10,20);valid=np.arange(20,30)
    recipe={'recipe_id':'synthetic','family':'test','config':{},'complexity':2}
    p=training.fit_inner_checkpoint(store,x,['delta:0','delta:1'],recipe,0,0,train,valid)
    second=training.fit_inner_checkpoint(store,x,['delta:0','delta:1'],recipe,0,0,train,valid)
    np.testing.assert_array_equal(p,second)
    receipt=json.loads((tmp_path/'results/mechanism_v2/training/outer_0/synthetic/inner_0.json').read_text())
    (tmp_path/receipt['predictions']['path']).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash mismatch'):
        training.fit_inner_checkpoint(store,x,['delta:0','delta:1'],recipe,0,0,train,valid)


def test_duplicate_training_process_is_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(training,'ROOT',tmp_path)
    monkeypatch.setattr(guarded_io,'ROOT',tmp_path)
    monkeypatch.setattr(guarded_io,'OUTPUT_ROOTS',(tmp_path/'results/mechanism_v2',))
    guarded_io.write_json(training.FREEZE,{'synthetic_test':True})
    with training.training_lock():
        with pytest.raises(FileExistsError):
            with training.training_lock():pass
    assert not (tmp_path/'results/mechanism_v2/training/inner_training.lock').exists()
