"""Prospective, outcome-blind nested split inventories; no model evaluation."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd
from .groups import component_groups,assert_partition_disjoint
from .io import load_development,write_json,sha256,ROOT
from .forensics import csv


def balanced_group_folds(rows,groups,n_splits=5,seed=20260909):
    """Balance independent units per source without dividing any component.

    Greedy allocation minimizes squared per-source unit counts, followed by
    component count. Hashed tie order is deterministic, label/outcome blind.
    """
    if n_splits<2:raise ValueError('At least two folds required')
    table=rows[['dataset','biological_unit']].assign(component=np.asarray(groups)).drop_duplicates()
    counts=pd.crosstab(table.component,table.dataset).sort_index()
    if len(counts)<n_splits:raise ValueError('Too few independent groups for requested folds')
    loads=np.zeros((n_splits,len(counts.columns)),float);number=np.zeros(n_splits,int)
    mapping={}
    def tie(value):return hashlib.sha256(f'{seed}:{value}'.encode()).hexdigest()
    order=sorted(counts.index,key=lambda g:(-int((counts.loc[g]>0).sum()),-int(counts.loc[g].sum()),tie(g)))
    scales=np.maximum(counts.sum(axis=0).to_numpy(float)/n_splits,1)
    for group in order:
        vector=counts.loc[group].to_numpy(float)
        candidates=[]
        for fold in range(n_splits):
            proposed=loads.copy();proposed[fold]+=vector
            objective=float(((proposed/scales)**2).sum())
            candidates.append((objective,number[fold],tie(f'{group}:{fold}'),fold))
        fold=min(candidates)[-1];loads[fold]+=vector;number[fold]+=1;mapping[group]=fold
    folds=np.array([mapping[g] for g in groups],int)
    assert_partition_disjoint(rows,folds,groups)
    return folds


def build_splits():
    rows=load_development()
    for identity,label in [(0.95,'primary95'),(0.90,'sensitivity90')]:
        groups,audit=component_groups(rows,near_identity=identity)
        folds=balanced_group_folds(rows,groups)
        frame=rows[['dataset','biological_unit','decision_set_id','candidate_id','feature_row']].copy()
        frame['component']=groups;frame['outer_fold']=folds
        inner={}
        for fold in sorted(set(folds)):
            mask=folds!=fold
            inner_folds=balanced_group_folds(rows.loc[mask],groups[mask],3,20260909+fold+1)
            component_map=pd.DataFrame({'component':groups[mask],'fold':inner_folds}).drop_duplicates()
            inner[str(fold)]={str(r.component):int(r.fold) for r in component_map.itertuples(index=False)}
        path=f'results/mechanism_v2/splits/{label}.csv'
        csv(path,frame)
        record={'group_audit':audit,'primary_outer_folds':5,'inner_folds':3,
            'split_seed':20260909,'outcomes_used_for_assignment':False,'rows':len(rows),
            'outer':path,'outer_sha256':sha256(ROOT/path),'inner_component_folds':inner,
            'source_by_fold_units':frame.groupby(['dataset','outer_fold']).biological_unit.nunique().rename('units').reset_index().to_dict('records'),
            'limitations':['Near-identity sensitivity uses parent sequences; exact grouping includes all mutants.',
                'Gene-symbol/ID grouping is not a validated gene-family ontology; family sensitivity remains pending.',
                'These are repeatedly reused development datasets, not a new external confirmation.']}
        write_json(f'results/mechanism_v2/manifests/splits_{label}.json',record)
        print(f'{label}: {audit["original_units"]} original units -> {audit["components"]} connected groups; nested split checks passed',flush=True)
