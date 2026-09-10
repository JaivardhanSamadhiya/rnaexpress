"""Grouped independent-stability validation. No localization performance fitting.

Real fitting requires this file, predictor and design to match committed bytes.
Only uniquely recovered external pairs enter; all exclusions are inventoried.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import hashlib
import io
import json
import pickle
import subprocess
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold
from openpyxl import load_workbook
from .io import ROOT,load_development,write_json,write_once,sha256,git
from .stability_resources import validated_resource
from .external_stability import paired_features,StabilityPredictor
from .forensics import csv

DESIGN_PATH=ROOT/'configs/mechanism_v2/external_stability_design.json'
DEST='results/mechanism_v2/stability'


def joined_inputs():
    path=ROOT/f'{DEST}/sequence_mapping_full.csv'
    mapping=pd.read_csv(path)
    eligible=[];exclusions=[]
    for variant,group in mapping.groupby('variant',sort=True):
        pairs=group.loc[group.match_count.eq(1),['reference_sequence','mutant_sequence']].drop_duplicates()
        if group.match_count.gt(1).any() or len(pairs)>1:
            exclusions.append({'variant':variant,'reason':'ambiguous_assayed_pair'});continue
        if len(pairs)==0:
            exclusions.append({'variant':variant,'reason':'no_verified_pair'});continue
        eligible.append({'Mutant':variant,**pairs.iloc[0].to_dict()})
    if not eligible:raise ValueError('No uniquely sequence-verified external pairs')
    workbook_path,receipt=validated_resource('stability_supp1')
    book=load_workbook(io.BytesIO(workbook_path.read_bytes()),read_only=True,data_only=False)
    values=list(book['Sup_T2_metaTable'].values);table=pd.DataFrame(values[1:],columns=values[0])
    table=table[table.UTR_Group.eq("3'UTR")]
    if table.Mutant.duplicated().any():raise ValueError('Ambiguous external outcome key')
    joined=pd.DataFrame(eligible).merge(table,on='Mutant',validate='one_to_one')
    development=load_development()
    genes=set(development.gene_name.dropna().str.upper())
    seqs=set(development.parent_sequence.str.upper())|set(development.mutant_sequence.str.upper())
    # Conservatively also remove >=90% full-length global similarity, including
    # every developed mutant, with a cutoff-aware native implementation.
    from rapidfuzz.distance import Levenshtein
    by_length=defaultdict(list)
    for seq in seqs:by_length[len(seq)].append(seq)
    query_sequences=set(joined.reference_sequence)|set(joined.mutant_sequence)
    prefixes=defaultdict(list)
    for seq in query_sequences:prefixes[seq[:21]].append(seq)
    contained=set()
    for seq in seqs:
        for i in range(len(seq)-20):
            for query in prefixes.get(seq[i:i+21],()):
                if query in seq:contained.add(query)
    keep=[];near_cache={}
    def near_development(seq):
        if seq in near_cache:return near_cache[seq]
        if seq in seqs or seq in contained:near_cache[seq]=True;return True
        for length,candidates in by_length.items():
            cutoff=int(0.1*max(length,len(seq))+1e-9)
            if abs(length-len(seq))>cutoff:continue
            for candidate in candidates:
                if Levenshtein.distance(seq,candidate,score_cutoff=cutoff)<=cutoff:
                    near_cache[seq]=True;return True
        near_cache[seq]=False;return False
    for idx,row in joined.iterrows():
        reason=None
        if not isinstance(row.GeneSymbol,str) or row.GeneSymbol.upper() in genes:reason='missing_or_development_gene'
        elif near_development(row.reference_sequence) or near_development(row.mutant_sequence):reason='development_sequence_overlap_90pct'
        if reason:exclusions.append({'variant':row.Mutant,'reason':reason})
        else:keep.append(idx)
    joined=joined.loc[keep].sort_values('Mutant').reset_index(drop=True)
    # Connect external genes sharing any reference or mutant sequence; exact
    # reverse pair identities are thus grouped as well.
    parents={str(g).upper():str(g).upper() for g in joined.GeneSymbol}
    def find(g):
        while parents[g]!=g:parents[g]=parents[parents[g]];g=parents[g]
        return g
    seen={}
    for row in joined.itertuples(index=False):
        gene=str(row.GeneSymbol).upper()
        for seq in [row.reference_sequence,row.mutant_sequence]:
            if seq in seen:
                a,b=find(gene),find(seen[seq]);parents[max(a,b)]=min(a,b)
            else:seen[seq]=gene
    sequences=sorted(seen)
    for i,a in enumerate(sequences):
        for b in sequences[i+1:]:
            if find(seen[a])==find(seen[b]):continue
            cutoff=int(0.05*max(len(a),len(b))+1e-9)
            if abs(len(a)-len(b))>cutoff:continue
            if Levenshtein.distance(a,b,score_cutoff=cutoff)<=cutoff:
                left,right=find(seen[a]),find(seen[b]);parents[max(left,right)]=min(left,right)
    joined['external_group']=[find(str(g).upper()) for g in joined.GeneSymbol]
    output='data/interim/mechanism_v2/stability_verified_training_pairs.csv'
    csv(output,joined)
    csv(f'{DEST}/training_exclusions.csv',pd.DataFrame(exclusions,columns=['variant','reason']))
    record={'mapping_sha256':sha256(path),'supplement':receipt,'development_genes_excluded':True,
        'development_global_sequence_similarity_exclusion':0.90,'exact_containment_excluded':True,
        'external_gene_sequence_component_identity':0.95,'retained_pairs_before_cell_qc':len(joined),
        'independent_groups_before_cell_qc':joined.external_group.nunique(),
        'exclusions':pd.DataFrame(exclusions).reason.value_counts().to_dict() if exclusions else {},
        'training_pair_path':output,'training_pair_sha256':sha256(ROOT/output)}
    return joined,record


def group_mse(y,pred,groups):
    return float(pd.DataFrame({'group':groups,'error':(np.asarray(y)-pred)**2}).groupby('group').error.mean().mean())


def group_mean(y,groups):
    return float(pd.DataFrame({'group':groups,'y':y}).groupby('group').y.mean().mean())


def select_recipe(x,y,groups,recipes):
    if len(set(groups))<3:raise ValueError('Too few external inner groups')
    candidates=[]
    for order,recipe in enumerate(recipes):
        predictions=np.full(len(y),np.nan)
        for train,test in GroupKFold(3).split(x,y,groups):
            if set(groups[train])&set(groups[test]):raise AssertionError('External inner group leakage')
            model=StabilityPredictor(recipe).fit(x[train],y[train],groups[train])
            predictions[test]=model.predict(x[test])
        candidates.append({'recipe':recipe['id'],'gene_macro_mse':group_mse(y,predictions,groups),'order':order})
    minimum=min(c['gene_macro_mse'] for c in candidates)
    chosen=min((c for c in candidates if c['gene_macro_mse']<=minimum+1e-10),key=lambda c:c['order'])
    return recipes[chosen['order']],candidates


def committed_source_guard():
    relative=['src/mechanism_v2/stability_validation.py','src/mechanism_v2/external_stability.py',
              'configs/mechanism_v2/external_stability_design.json','src/mechanism_v2/stability_mapping.py']
    sources={}
    for name in relative:
        committed=subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=ROOT)
        if committed!=(ROOT/name).read_bytes():raise PermissionError(f'External validation code/design not committed: {name}')
        sources[name]=sha256(ROOT/name)
    return sources


def validate_external_stability():
    sources=committed_source_guard();design=json.loads(DESIGN_PATH.read_text())
    rows,input_record=joined_inputs()
    freeze={'git_commit':git('rev-parse','HEAD'),'sources':sources,'design':design,'input':input_record,
        'localization_model_fit':False,'astrocyte_accessed':False,'nzip_accessed':False}
    freeze_path=ROOT/f'{DEST}/external_training_freeze.json'
    if freeze_path.exists():
        prior=json.loads(freeze_path.read_text())
        if {k:v for k,v in prior.items() if k!='git_commit'}!={k:v for k,v in freeze.items() if k!='git_commit'}:
            raise ValueError('External training inputs/design/source changed; immutable run cannot resume')
    else:write_json(freeze_path,freeze)
    features=np.asarray([paired_features(r.reference_sequence,r.mutant_sequence) for r in rows.itertuples(index=False)])
    summaries={}
    for cell in design['cells']:
        half=rows[[f't05_WT_{cell}',f't05_mt_{cell}']].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        mask=np.isfinite(half).all(axis=1)&(half>0).all(axis=1)
        data=rows.loc[mask].reset_index(drop=True);x=features[mask]
        y=np.log2(half[mask,1]/half[mask,0]);groups=data.external_group.to_numpy(str)
        if len(set(groups))<5:raise ValueError(f'{cell}: insufficient groups for external CV')
        predictions=np.full(len(y),np.nan);mean_baseline=np.full(len(y),np.nan);folds=np.full(len(y),-1)
        selections=[]
        for fold,(train,test) in enumerate(GroupKFold(5).split(x,y,groups)):
            if set(groups[train])&set(groups[test]):raise AssertionError('External outer group leakage')
            path=ROOT/f'{DEST}/{cell}_outer_{fold}.json'
            if path.exists():
                saved=json.loads(path.read_text())
                if saved['input_sha256']!=input_record['training_pair_sha256'] or saved['test_indices']!=test.tolist():
                    raise ValueError('External resume input/partition changed')
                predictions[test]=saved['predictions'];mean_baseline[test]=saved['mean_baseline'];folds[test]=fold
                selections.append(saved['selection']);continue
            recipe,candidates=select_recipe(x[train],y[train],groups[train],design['models'])
            model=StabilityPredictor(recipe).fit(x[train],y[train],groups[train])
            predictions[test]=model.predict(x[test]);mean_baseline[test]=group_mean(y[train],groups[train]);folds[test]=fold
            selection={'outer_fold':fold,'selected':recipe['id'],'inner':candidates}
            selections.append(selection)
            write_json(path,{'input_sha256':input_record['training_pair_sha256'],'test_indices':test.tolist(),
                'predictions':predictions[test].tolist(),'mean_baseline':mean_baseline[test].tolist(),'selection':selection})
            print(f'External stability {cell} outer fold {fold+1}/5: {recipe["id"]}',flush=True)
        if not np.isfinite(predictions).all() or (folds<0).any():raise AssertionError('Incomplete external OOF prediction')
        mse=group_mse(y,predictions,groups);baseline_mse=group_mse(y,mean_baseline,groups)
        corr=float(spearmanr(y,predictions).statistic)
        group_ids=sorted(set(groups));indices={g:np.flatnonzero(groups==g) for g in group_ids}
        rng=np.random.default_rng(design['bootstrap']['seed']);boot=[]
        for _ in range(design['bootstrap']['resamples']):
            picked=rng.choice(group_ids,size=len(group_ids),replace=True)
            idx=np.concatenate([indices[g] for g in picked])
            value=float(spearmanr(y[idx],predictions[idx]).statistic)
            if np.isfinite(value):boot.append(value)
        if len(boot)<0.99*design['bootstrap']['resamples']:raise ValueError('Too many undefined external bootstrap correlations')
        interval=np.quantile(boot,[.025,.975]).tolist();improvement=1-mse/baseline_mse
        zero_mse=group_mse(y,np.zeros(len(y)),groups)
        zero_improvement=1-mse/zero_mse if zero_mse>0 else 0.
        gates=design['admission']
        admitted=(len(group_ids)>=gates['minimum_independent_groups'] and corr>=gates['minimum_oof_spearman']
            and interval[0]>gates['minimum_spearman_bootstrap_lower95']
            and improvement>=gates['minimum_relative_mse_improvement_over_training_mean']
            and zero_improvement>=gates['minimum_relative_mse_improvement_over_zero'])
        summary={'cell':cell,'pairs':len(y),'groups':len(group_ids),'oof_spearman':corr,
            'spearman_bootstrap95':interval,'group_macro_mse':mse,'training_mean_baseline_mse':baseline_mse,
            'zero_delta_baseline_mse':zero_mse,'relative_mse_improvement_over_zero':zero_improvement,
            'relative_mse_improvement':improvement,'admitted':bool(admitted),'selections':selections,
            'bootstrap_valid':len(boot),'scope':'independent external stability only'}
        data=data[['Mutant','external_group','reference_sequence','mutant_sequence']].assign(target=y,prediction=predictions,
            training_mean_baseline=mean_baseline,outer_fold=folds)
        csv(f'{DEST}/{cell}_oof_predictions.csv',data)
        write_json(f'{DEST}/{cell}_bootstrap_spearman.json',{'values':boot})
        if admitted:
            recipe,inner=select_recipe(x,y,groups,design['models'])
            model=StabilityPredictor(recipe).fit(x,y,groups)
            model_path=write_once(f'models/mechanism_v2/stability_{cell}.pkl',pickle.dumps(model,protocol=5))
            # Verify only our own freshly generated bytes, never external pickle.
            restored=pickle.loads(model_path.read_bytes())
            if not np.array_equal(model.predict(x),restored.predict(x)):raise ValueError('External model round-trip mismatch')
            summary['frozen_model']={'path':model_path.relative_to(ROOT).as_posix(),'sha256':sha256(model_path),
                'selected':recipe['id'],'selection_inner':inner}
        write_json(f'{DEST}/{cell}_validation_summary.json',summary);summaries[cell]=summary
        print(f'External stability {cell}: Spearman {corr:.4f}, relative MSE gain {improvement:.4f}, admitted={admitted}',flush=True)
    return summaries
