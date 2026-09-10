"""Resumable inner-only localization fitting, with a committed-input barrier.

Outer-fold outcomes are never passed to fit, selection or metric routines here.
The complete outer evaluator and holdout remain separate, unavailable stages.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from contextlib import contextmanager
import hashlib
import json
import os
import subprocess
import numpy as np
import pandas as pd
from .io import ROOT,canonical_json,git,sha256,write_json,output_path
from .feature_store import FeatureStore,BLOCK_MANIFESTS,DIMENSIONS
from .ranking import RankConfig,PairedRanker
from .evaluation import decision_metrics
from .features import array_file
from .primitives import choose_recipe
from .preservation import preserve

FREEZE='results/mechanism_v2/manifests/development_training_freeze.json'
CODE=['src/mechanism_v2/'+x+'.py' for x in ['io','groups','splits','ranking','primitives',
    'feature_store','development_training','evaluation','forensics','features']]
CODE+=['src/modeling/v4_decision_models.py']
DESIGN=['configs/mechanism_v2/localization_design.json','reports/mechanism_v2/model_selection.md',
    'reports/mechanism_v2/prospective_gate_design.md','configs/mechanism_v2/environment.lock.txt']


def recipes(design):
    records=[]
    for family,blocks in design['families'].items():
        for variant in design['recipes_per_family']:
            cfg={k:v for k,v in variant.items() if k!='id'}
            cfg.update(design['ranker_constants']);cfg['seed']=design['seed']
            nuisance_dims={'none':0,'source':3,'size':7,'source_size':10}[cfg['nuisance']]
            records.append({'recipe_id':family+'_'+variant['id'],'family':family,'config':cfg,
                'complexity':sum(DIMENSIONS[b] for b in blocks)+nuisance_dims+3*int(cfg['ranking_heads'])})
    return records


def committed_hash(path):
    raw=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=ROOT)
    digest=sha256(ROOT/path)
    if hashlib.sha256(raw).hexdigest()!=digest:
        raise PermissionError(f'Commit the exact dependency before fitting: {path}')
    return digest


def prepare_training():
    preserve();store=FeatureStore()
    paths=CODE+DESIGN+[store.design['split_manifest'],store.split['outer'],
        'results/mechanism_v2/manifests/environment.json',
        'results/mechanism_v2/stability/SH_validation_summary.json',
        'results/mechanism_v2/stability/HEK_validation_summary.json']
    paths+=['results/mechanism_v2/features/'+p for p in BLOCK_MANIFESTS.values()]
    hashes={p:committed_hash(p) for p in paths}
    record={'format':'mechanism_v2_inner_training_freeze_v1','git_commit':git('rev-parse','HEAD'),
        'dependencies':hashes,'recipes':recipes(store.design),'candidate_rows':len(store.rows),
        'components':int(store.rows.component.nunique()),'feature_arrays':{
            b:{k:r[k] for k in ['path','sha256','shape','dtype']} for b,r in store.records.items()},
        'outer_evaluation_authorized':False,'holdout_authorized':False,
        'selection_only':'For each outer fold, fit and score only its three inner partitions.'}
    if (ROOT/FREEZE).exists():
        previous=json.loads((ROOT/FREEZE).read_text())
        # Subsequent documentation commits need not invalidate a byte-identical recipe.
        record['git_commit']=previous['git_commit']
    write_json(FREEZE,record)
    print(f'Inner training freeze verified: {len(record["recipes"])} recipes, outer/holdout disabled',flush=True)
    return record


def verify_freeze():
    record=json.loads((ROOT/FREEZE).read_text())
    if record['format']!='mechanism_v2_inner_training_freeze_v1':raise ValueError('Unknown training freeze')
    for path,digest in record['dependencies'].items():
        if sha256(ROOT/path)!=digest:raise PermissionError(f'Frozen training dependency changed: {path}')
    return record


@contextmanager
def training_lock():
    path=output_path('results/mechanism_v2/training/inner_training.lock')
    path.parent.mkdir(parents=True,exist_ok=True)
    # Stale locks are intentionally NOT auto-deleted. Inspect PID/logs first.
    with path.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps({'pid':os.getpid(),'freeze_sha256':sha256(ROOT/FREEZE)}))
    try:yield
    finally:path.unlink()


def assert_inner_boundary(rows,outer,train_idx,valid_idx):
    train_idx=np.asarray(train_idx,int);valid_idx=np.asarray(valid_idx,int)
    if not len(train_idx) or not len(valid_idx):raise ValueError('Empty inner partition')
    if (train_idx<0).any() or (valid_idx<0).any() or (train_idx>=len(rows)).any() or (valid_idx>=len(rows)).any():
        raise ValueError('Inner row index outside certified inventory')
    if len(set(train_idx))!=len(train_idx) or len(set(valid_idx))!=len(valid_idx):raise ValueError('Duplicate row index')
    if np.intersect1d(train_idx,valid_idx).size:raise ValueError('Train/validation row overlap')
    train=rows.iloc[train_idx];valid=rows.iloc[valid_idx]
    if train.outer_fold.eq(outer).any() or valid.outer_fold.eq(outer).any():
        raise PermissionError('Outer test rows reached inner development')
    if set(train.component)&set(valid.component):raise ValueError('Biological component leakage')
    if set(train.feature_row)&set(valid.feature_row):raise ValueError('Repeated intervention leakage')


def metric_summary(metrics):
    if metrics.empty:raise ValueError('No eligible inner decision sets')
    means=metrics.groupby(['dataset','component','direction'])[['regret','rank']].mean()
    contexts=means.groupby(['dataset','direction']).mean()
    return {k:float(contexts[k].mean()) for k in ['regret','rank']}


def checked_checkpoint(path,identity):
    record=json.loads(path.read_text())
    if record['identity']!=identity:raise ValueError('Checkpoint identity mismatch')
    for field in ['model','predictions']:
        if sha256(ROOT/record[field]['path'])!=record[field]['sha256']:
            raise ValueError('Checkpoint artifact hash mismatch')
    value=np.load(ROOT/record['predictions']['path'],allow_pickle=False)
    if value.ndim!=2 or value.shape[1]!=2 or not np.isfinite(value).all():raise ValueError('Invalid cached predictions')
    if not np.array_equal(value[:,0],identity['valid_row_ids']):raise ValueError('Prediction row identity mismatch')
    PairedRanker.from_record(json.loads((ROOT/record['model']['path']).read_text()))
    return record,value[:,1]


def fit_inner_checkpoint(store,x,columns,recipe,outer,inner,train_idx,valid_idx):
    assert_inner_boundary(store.rows,outer,train_idx,valid_idx)
    label=f'outer_{outer}/{recipe["recipe_id"]}/inner_{inner}'
    identity={'freeze_sha256':sha256(ROOT/FREEZE),'recipe':recipe,'outer':int(outer),'inner':int(inner),
        'train_row_ids':list(map(int,train_idx)),'valid_row_ids':list(map(int,valid_idx))}
    path=ROOT/f'results/mechanism_v2/training/{label}.json'
    if path.exists():return checked_checkpoint(path,identity)[1]
    model=PairedRanker(RankConfig(**recipe['config'])).fit(x[train_idx],store.train_frame(train_idx),columns)
    prediction=model.predict(x[valid_idx])
    restored=PairedRanker.from_record(model.to_record()).predict(x[valid_idx])
    if not np.allclose(restored,prediction,rtol=0,atol=1e-12):raise ValueError('Model serialization changes prediction')
    model_path=f'models/mechanism_v2/inner/{label}.json'
    write_json(model_path,model.to_record())
    pred_record=array_file(f'data/interim/mechanism_v2/inner_predictions/{label}.npy',
        np.column_stack([valid_idx,prediction]))
    metric,excluded=decision_metrics(store.rows.iloc[valid_idx],prediction)
    record={'identity':identity,'model':{'path':model_path,'sha256':sha256(ROOT/model_path)},
        'predictions':pred_record,'inner_metrics':metric_summary(metric),
        'excluded_decisions':excluded.to_dict('records'),'fit_audit':model.fit_audit_}
    write_json(path,record)
    return prediction


def run_inner_training():
    frozen=verify_freeze();store=FeatureStore();all_recipes=recipes(store.design)
    if all_recipes!=frozen['recipes']:raise ValueError('Recipe list changed')
    with training_lock():
        for outer in range(store.design['outer_folds']):
            pool=np.flatnonzero(store.rows.outer_fold.to_numpy()!=outer)
            assignments=store.rows.component.map(store.split['inner_component_folds'][str(outer)])
            if assignments.iloc[pool].isna().any():raise ValueError('Missing inner fold')
            summary=[]
            for family in store.design['families']:
                x,columns=store.matrix(family)
                for recipe in [r for r in all_recipes if r['family']==family]:
                    prediction=np.full(len(store.rows),np.nan)
                    for inner in range(store.design['inner_folds']):
                        valid=pool[assignments.iloc[pool].to_numpy()==inner]
                        train=pool[assignments.iloc[pool].to_numpy()!=inner]
                        prediction[valid]=fit_inner_checkpoint(store,x,columns,recipe,outer,inner,train,valid)
                        print(f'Inner fit verified: outer={outer} recipe={recipe["recipe_id"]} inner={inner}',flush=True)
                    if not np.isfinite(prediction[pool]).all():raise ValueError('Incomplete inner OOF predictions')
                    if np.isfinite(prediction[store.rows.outer_fold.eq(outer)]).any():
                        raise PermissionError('Outer predictions produced by inner runner')
                    metrics,_=decision_metrics(store.rows.iloc[pool],prediction[pool])
                    summary.append({**recipe,**metric_summary(metrics)})
                del x
            chosen={family:choose_recipe([r for r in summary if r['family']==family],
                store.design['selection']['regret_tolerance']) for family in store.design['families']}
            primary=choose_recipe([r for r in summary if r['family'] in store.design['selection']['primary_pool']],
                store.design['selection']['regret_tolerance'])
            write_json(f'results/mechanism_v2/training/outer_{outer}/selection.json',{
                'freeze_sha256':sha256(ROOT/FREEZE),'inner_summaries':summary,
                'family_selections':chosen,'primary_selection':primary,'outer_outcomes_used':False})
            print(f'Outer fold {outer}: inner selection complete; outer outcomes not evaluated',flush=True)
        write_json('results/mechanism_v2/training/inner_complete.json',{
            'freeze_sha256':sha256(ROOT/FREEZE),'outer_folds':5,'recipes_per_fold':len(all_recipes),
            'inner_fits':len(all_recipes)*5*3,'outer_evaluation_complete':False})
