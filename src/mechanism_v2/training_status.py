"""Audit completed inner fits without printing or selecting scientific results."""
from __future__ import annotations
import json
from .io import ROOT,sha256,write_json


def audit_inner_progress():
    # This utility is separate from, and does not alter, the frozen fitting code.
    from .development_training import verify_freeze,checked_checkpoint,FREEZE
    from .feature_store import FeatureStore
    import numpy as np
    freeze=verify_freeze();store=FeatureStore();digest=sha256(ROOT/FREEZE)
    complete=[];per_fold={};checked=[]
    for outer in range(5):
        pool=np.flatnonzero(store.rows.outer_fold.to_numpy()!=outer)
        assignment=store.rows.component.map(store.split['inner_component_folds'][str(outer)])
        count=0
        for recipe in freeze['recipes']:
            for inner in range(3):
                path=ROOT/f'results/mechanism_v2/training/outer_{outer}/{recipe["recipe_id"]}/inner_{inner}.json'
                if not path.exists():continue
                valid=pool[assignment.iloc[pool].to_numpy()==inner]
                train=pool[assignment.iloc[pool].to_numpy()!=inner]
                identity={'freeze_sha256':digest,'recipe':recipe,'outer':outer,'inner':inner,
                    'train_row_ids':list(map(int,train)),'valid_row_ids':list(map(int,valid))}
                checked_checkpoint(path,identity)
                count+=1;checked.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha256(path)})
        per_fold[str(outer)]=count
        selection=ROOT/f'results/mechanism_v2/training/outer_{outer}/selection.json'
        if selection.exists():
            record=json.loads(selection.read_text())
            if count!=144 or record['freeze_sha256']!=digest or record['outer_outcomes_used']:
                raise ValueError('Invalid completed inner selection')
            if len(record['inner_summaries'])!=48:raise ValueError('Incomplete recipe selection')
            # Only audit inventory; deliberately do not display chosen scores/families.
            complete.append(outer)
    result={'freeze_sha256':digest,'verified_completed_fits':sum(per_fold.values()),
        'required_fits':720,'per_outer_fold':per_fold,'completed_inner_selection_cycles':complete,
        'outer_evaluation_complete':False,'checkpoints':checked}
    path=f'results/mechanism_v2/training/status/verified_{sum(per_fold.values()):04d}_fits.json'
    write_json(path,result)
    print(json.dumps({k:v for k,v in result.items() if k!='checkpoints'},indent=2),flush=True)
    return result


if __name__=='__main__':
    from . import run_pipeline  # initialize the isolated runtime before numerical imports
    audit_inner_progress()
