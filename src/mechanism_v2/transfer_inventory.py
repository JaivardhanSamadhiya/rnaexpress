"""Outcome-blind purged transfer tasks, independent of any model predictions."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from .io import ROOT,load_development,sha256,write_json
from .splits import balanced_group_folds
from .feature_store import validate_split_alignment


def purged_partition(rows,train_mask,test_mask,group_column='component'):
    train=np.asarray(train_mask,bool);test=np.asarray(test_mask,bool)
    if train.shape!=(len(rows),) or test.shape!=(len(rows),):raise ValueError('Mask shape mismatch')
    if np.any(train&test):raise ValueError('Raw transfer train/test overlap')
    held=set(rows.loc[test,group_column])
    purged=train & rows[group_column].isin(held).to_numpy()
    train=train & ~purged
    a=np.flatnonzero(train);b=np.flatnonzero(test)
    if set(rows.iloc[a][group_column])&set(rows.iloc[b][group_column]):raise AssertionError('Group purge failed')
    if set(rows.iloc[a].feature_row)&set(rows.iloc[b].feature_row):raise AssertionError('Intervention purge failed')
    return a,b,int(purged.sum())


def task_record(rows,name,kind,train_mask,test_mask,seed=20260913):
    train,test,purged=purged_partition(rows,train_mask,test_mask)
    groups=rows.iloc[train].component.to_numpy()
    eligible=len(set(groups))>=3 and len(test)>0
    inner={}
    if eligible:
        assignments=balanced_group_folds(rows.iloc[train],groups,3,seed)
        inner=dict(zip(groups,map(int,assignments)))
    return {'name':name,'kind':kind,'train_row_ids':train.tolist(),'test_row_ids':test.tolist(),
        'purged_train_rows':purged,'train_components':len(set(groups)),
        'test_components':int(rows.iloc[test].component.nunique()),
        'test_decisions':int(rows.iloc[test].decision_set_id.nunique()),
        'inner_component_folds':inner,'eligible_for_fitting':bool(eligible),
        'ineligible_reason':None if eligible else 'fewer_than_three_training_components_or_empty_test',
        'outcomes_used':False,'inference':'shared latent, no target-context labels or calibration',
        'inner_seed':seed}


def build_transfer_tasks(rows):
    tasks=[]
    for source in sorted(rows.dataset.unique()):
        test=rows.dataset.eq(source)
        tasks.append(task_record(rows,'leave_source_'+source,'leave_source',~test,test))
        for fold in range(5):
            tasks.append(task_record(rows,f'within_{source}_{fold}','within_source',
                test&rows.outer_fold.ne(fold),test&rows.outer_fold.eq(fold)))
    mikl=rows.dataset.eq('mikl_gse173098')
    moffatt=rows.dataset.eq('moffatt_gse334718')
    for kind,source_mask,field,contexts in [
        ('cross_cell',mikl,'cell_type',['CAD','Neuro-2a']),
        ('cross_reporter',moffatt,'reporter',['GFP','Firefly'])]:
        for train_context,test_context in [contexts,contexts[::-1]]:
            for fold in range(5):
                tasks.append(task_record(rows,f'{kind}_{train_context}_to_{test_context}_{fold}',kind,
                    source_mask&rows[field].eq(train_context)&rows.outer_fold.ne(fold),
                    source_mask&rows[field].eq(test_context)&rows.outer_fold.eq(fold)))
    for fold in range(5):
        tasks.append(task_record(rows,f'large_to_small_{fold}','large_to_small',
            rows.edit_cost.gt(10)&rows.outer_fold.ne(fold),
            rows.edit_cost.between(2,10)&rows.outer_fold.eq(fold)))
    if len({t['name'] for t in tasks})!=len(tasks):raise ValueError('Duplicate transfer task name')
    return tasks


def build_transfer_inventory():
    rows=load_development()
    manifest_path=ROOT/'results/mechanism_v2/manifests/splits_all_alleles95.json'
    manifest=json.loads(manifest_path.read_text())
    if sha256(ROOT/manifest['outer'])!=manifest['outer_sha256']:raise ValueError('Changed primary split')
    inventory=pd.read_csv(ROOT/manifest['outer']);validate_split_alignment(rows,inventory)
    rows['component']=inventory.component;rows['outer_fold']=inventory.outer_fold
    # Exclude outcomes from the interface used to generate tasks.
    fields=['dataset','biological_unit','component','outer_fold','feature_row','decision_set_id',
        'cell_type','reporter','edit_cost']
    tasks=build_transfer_tasks(rows[fields])
    result={'primary_split_manifest_sha256':sha256(manifest_path),'code_sha256':sha256(ROOT/'src/mechanism_v2/transfer_inventory.py'),
        'tasks':tasks,'outcomes_used':False,'models_fit':False,
        'scope':'3 leave-source, 15 within-source, 10 cell, 10 reporter and 5 large-to-small held-group tasks',
        'unit':'primary all-allele95 connected component; source-overlapping groups purged from training',
        'selection':'same six recipes in each M0-M7 family, inner-only; never borrow primary-fold choices for a different training domain',
        'aggregation':'concatenate five held-group folds per directed context transfer, then score both directions'}
    write_json('results/mechanism_v2/manifests/transfer_inventory.json',result)
    print(json.dumps({'tasks':len(tasks),'fitting_eligible':sum(t['eligible_for_fitting'] for t in tasks),
        'purged_train_rows_total':sum(t['purged_train_rows'] for t in tasks),
        'kind_counts':pd.Series([t['kind'] for t in tasks]).value_counts().to_dict()}),flush=True)


if __name__=='__main__':build_transfer_inventory()
