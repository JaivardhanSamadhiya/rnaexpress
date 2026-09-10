"""Fixed exploratory shortcut diagnostics. No localization model selection."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.metrics import r2_score
from threadpoolctl import threadpool_limits
from .io import ROOT,load_development,write_json,sha256
from .forensics import archived_functions,csv,DEST,FULL
from .groups import component_groups


def run_probes():
    rows=load_development()
    yframe=pd.read_csv(ROOT/'results/finalshot/m0_m3_predictions.csv.gz')
    if not rows[['candidate_id','decision_set_id']].equals(yframe[['candidate_id','decision_set_id']]):
        raise ValueError('Prediction alignment mismatch')
    funcs=archived_functions()
    geometry=funcs['geometry_features'](rows)
    weights=funcs['source_set_weights'](rows)
    x=np.load(ROOT/'data/interim/finalshot_rbpnet_features.npy',mmap_mode='r')
    idx=rows.feature_row.to_numpy(int)
    delta_cols=np.array([g*9+j for g in range(103) for j in [0,1,2,3,4,5,8]])
    absolute_cols=np.array([g*9+j for g in range(103) for j in [6,7]])
    deltas=np.asarray(x[idx][:,delta_cols],dtype=np.float32)
    absolute=np.asarray(x[idx][:,absolute_cols],dtype=np.float32)
    blocks={'geometry':geometry,'size_class':geometry[:,np.r_[0:8,16:28]],
            'composition_location':geometry[:,8:16], 'absolute_parent_rbp':absolute,
            'delta_rbp':deltas,'geometry_delta_rbp':np.column_stack([geometry,deltas])}
    components,group_audit=component_groups(rows)
    write_json(f'{DEST}/exact_component_audit.json',group_audit)
    folds=rows.biological_fold.to_numpy(int)
    group_counts=pd.DataFrame({'component':components,'fold':folds}).groupby('component').fold.nunique()
    crossing=int(group_counts.gt(1).sum())
    if crossing:
        # These are diagnostic targets from archived folds, but no cross-component
        # mixing is allowed in a newly fit probe. Use group-purged old fold masks.
        print(f'Purging {crossing} components that cross archived folds in probe training',flush=True)
    targets=yframe[['M1','M2','M3',FULL]].to_numpy(float)
    records=[]
    for block,features in blocks.items():
        for kind in ['ridge','forest']:
            key=f'{DEST}/probe_{block}_{kind}.json'
            if (ROOT/key).exists():
                records.extend(json.loads((ROOT/key).read_text())['metrics']);continue
            pred=np.full_like(targets,np.nan)
            for fold in sorted(set(folds)):
                test=folds==fold
                train=(folds!=fold)&~np.isin(components,np.unique(components[test]))
                if train.sum()==0:raise ValueError('Component purge leaves empty training fold')
                scaler=StandardScaler().fit(features[train],sample_weight=weights[train])
                a=scaler.transform(features[train]);b=scaler.transform(features[test])
                if kind=='ridge':
                    model=Ridge(alpha=100,solver='lsqr',tol=1e-6)
                else:
                    model=RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=20,
                                                random_state=20260909,n_jobs=4)
                with threadpool_limits(limits=4):
                    model.fit(a,targets[train],sample_weight=weights[train])
                    pred[test]=model.predict(b)
            metrics=[]
            for j,target in enumerate(['M1','M2','M3',FULL]):
                for source in ['equal_source_pooled',*sorted(rows.dataset.unique())]:
                    mask=np.ones(len(rows),dtype=bool) if source=='equal_source_pooled' else rows.dataset.eq(source).to_numpy()
                    metrics.append({'block':block,'estimator':kind,'target':target,'source':source,
                        'weighted_oof_r2':float(r2_score(targets[mask,j],pred[mask,j],sample_weight=weights[mask])),
                        'rows':int(mask.sum()),'status':'exploratory prediction reconstruction, not causal attribution'})
            write_json(key,{'metrics':metrics,'old_fold_components_requiring_purge':crossing,
                'probe_target':'Archived fold-dependent score, not a single fitted teacher function',
                'feature_source_sha256':sha256(ROOT/'data/interim/finalshot_rbpnet_features.npy')})
            records.extend(metrics)
            print(f'Probe completed: {block}/{kind}',flush=True)
    csv(f'{DEST}/prediction_reconstruction_probes.csv',pd.DataFrame(records))
    return records
