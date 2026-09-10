"""Recompute FinalShot predictions in the new namespace; no retraining or old writes."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from .io import ROOT, git, load_development, sha256, write_json, write_once
from .primitives import edit_band

BASE='M0_geometry'
FULL='M1_M2_M3_nested_selected'
DEST='results/mechanism_v2/forensics'
METRICS=['directional_rank_percentile','normalized_regret','good_selection_at_3','good_selection_at_5']


def archived_functions():
    """Compile only unchanged metric/geometry definitions, without importing torch/training.

    This avoids executing old top-level module imports in a new environment.
    The full source digest is recorded and is in the preserved release inventory.
    """
    path=ROOT/'src/modeling/v4_decision_models.py'
    source=path.read_text(encoding='utf-8')
    tree=ast.parse(source)
    keep={'decision_set_metrics','geometry_features','source_set_weights'}
    constants={'INTERVENTION_CLASSES','EDIT_TIERS','GOOD_REGRET'}
    nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in keep) or (
        isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets))]
    if {n.name for n in nodes if isinstance(n,ast.FunctionDef)} != keep:
        raise ValueError('Archived function definitions missing')
    namespace={'np':np,'pd':pd,'math':math,'rankdata':rankdata,'spearmanr':spearmanr}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    return namespace


def csv(relative,frame):
    write_once(relative,frame.to_csv(index=False,lineterminator='\n').encode('utf-8'))


def summarize(sets):
    unit=sets.groupby(['model','dataset','requested_direction','biological_unit'],sort=True)[METRICS].mean().reset_index()
    source=unit.groupby(['model','dataset','requested_direction'],sort=True)[METRICS].mean().reset_index()
    return unit,source


def compare(summary,levels):
    base=summary[summary.model.eq(BASE)]
    full=summary[~summary.model.eq(BASE)]
    paired=full.merge(base,on=levels,suffixes=('','_base'),validate='many_to_one')
    paired['rank_gain']=paired.directional_rank_percentile-paired.directional_rank_percentile_base
    paired['regret_gain']=paired.normalized_regret_base-paired.normalized_regret
    return paired


def evaluate(rows,prediction,models,label):
    metric=archived_functions()['decision_set_metrics']
    pieces=[]
    for model in models:
        for direction,sign in [('increase',1),('decrease',-1)]:
            pieces.append(metric(rows,sign*prediction[model].to_numpy(float),model,direction,42017,label))
    return pd.concat(pieces,ignore_index=True)


def run_forensics():
    rows=load_development()
    prediction=pd.read_csv(ROOT/'results/finalshot/m0_m3_predictions.csv.gz')
    keys=['dataset','decision_set_id','candidate_id','biological_unit','biological_fold','feature_row']
    if not rows[keys].astype(str).equals(prediction[keys].astype(str)):
        raise ValueError('Archived prediction alignment differs')
    models=[BASE,'M1','M2','M3',FULL]
    sets=evaluate(rows,prediction,models,'mechanism_v2_archived_recomputation')
    unit,source=summarize(sets)
    context=compare(source,['dataset','requested_direction'])
    unit_context=compare(unit,['dataset','requested_direction','biological_unit'])
    csv(f'{DEST}/source_context.csv',context)
    csv(f'{DEST}/unit_context.csv',unit_context)
    selected=context[context.model.eq(FULL)]
    old=json.loads((ROOT/'results/finalshot/m0_m3_summary.json').read_text())
    agreement=[]
    for record in old['summary']:
        if record['model'] not in models:
            continue
        group=context[context.model.eq(record['model'])]
        rank=float(group.rank_gain.mean()); regret=float(group.regret_gain.mean())
        if not np.allclose([rank,regret], [record['rank_context_value'],record['regret_context_value']],rtol=0,atol=1e-10):
            raise ValueError(f'Archived numerical mismatch: {record["model"]}')
        agreement.append({'model':record['model'],'rank_gain':rank,'regret_gain':regret})
    print('Recomputed primary archived predictions: all 4 model summaries agree',flush=True)

    by_unit=unit_context[unit_context.model.eq(FULL)].groupby(['dataset','biological_unit'],sort=True)[['rank_gain','regret_gain']].mean().reset_index()
    rng=np.random.default_rng(42017)
    boot=np.zeros((10000,2))
    for _,g in by_unit.groupby('dataset',sort=True):
        values=g[['rank_gain','regret_gain']].to_numpy()
        boot+=values[rng.integers(0,len(values),(10000,len(values)))].mean(axis=1)/by_unit.dataset.nunique()
    distribution={'units':len(by_unit),'positive_unit_fraction':float(by_unit.regret_gain.gt(0).mean()),
        'median':float(by_unit.regret_gain.median()),'q25':float(by_unit.regret_gain.quantile(.25)),
        'q75':float(by_unit.regret_gain.quantile(.75)),'worst_decile':float(by_unit.regret_gain.quantile(.1)),
        'paired_direction_source_stratified_bootstrap_ci':np.quantile(boot,[.025,.975],axis=0).T.tolist()}
    csv(f'{DEST}/unit_bootstrap.csv',pd.DataFrame(boot,columns=['rank_gain','regret_gain']))

    subsets=[]
    bands=edit_band(rows.edit_cost)
    masks=[('size_'+b,bands==b) for b in ['1','2-5','6-10','11-25','26-50','>50']]
    masks += [('size_2-10',np.isin(bands,['2-5','6-10']))]
    masks += [('class_'+str(c),rows.intervention_class.eq(c).to_numpy()) for c in sorted(rows.intervention_class.unique())]
    for name,mask in masks:
        sub=rows.loc[mask].reset_index(drop=True)
        scores=prediction.loc[mask].reset_index(drop=True)
        metrics=evaluate(sub,scores,[BASE,FULL],name)
        if metrics.empty:
            subsets.append({'subset':name,'eligible_sets':0});continue
        u,s=summarize(metrics); p=compare(s,['dataset','requested_direction'])
        subsets.append({'subset':name,'rows':len(sub),'eligible_sets':metrics.decision_set_id.nunique(),
            'units':u.biological_unit.nunique(),'rank_gain':float(p.rank_gain.mean()),
            'regret_gain':float(p.regret_gain.mean()),'status':'exploratory subdivision of archived predictions'})
    csv(f'{DEST}/size_and_mutation_class.csv',pd.DataFrame(subsets))

    # Re-scope decision sets by literal parent ID, preserving candidate scores.
    parent_rows=rows.copy()
    parent_rows.decision_set_id=parent_rows[['decision_set_id','parent_id']].astype(str).agg('||'.join,axis=1)
    parent_metrics=evaluate(parent_rows,prediction,[BASE,FULL],'archived_parent_subsets')
    pu,ps=summarize(parent_metrics)
    csv(f'{DEST}/parent_subset_context.csv',compare(ps,['dataset','requested_direction']))

    # The original cap and minimum-four rule operate inside the same gene stratum:
    # after a global gene cap of two, no within-gene subset can have four entries.
    chronology={
        'protocol_history':git('log','--format=%h %aI %s','--','reports/finalshot_protocol.md'),
        'protocol_diff_since_freeze':git('diff','30c89a3', '98ffc02','--','reports/finalshot_protocol.md'),
        'head_history':git('log','--format=%h %aI %s','--','src/analysis/run_finalshot_head_randomization.py'),
        'cap_superseded':False,
        'literal_cap_maximum_per_gene_stratum':2,'required_within_gene_minimum':4,
        'literal_cap_eligible_subsets':0,
        'uncapped_reference':'results/finalshot/grouped_gate_summary.json',
        'interpretation':'Only sigmoid clarification changed protocol after initial freeze; cap not superseded. '
            'Literal cap yields an empty evaluable set, not a zero effect. Uncapped results remain qualified.'}
    write_json(f'{DEST}/protocol_chronology.json',chronology)
    result={'scope':'Prediction recomputation, not model retraining; exploratory forensic analyses',
        'rows':len(rows),'model_agreement':agreement,'unit_distribution':distribution,
        'metric_source_sha256':sha256(ROOT/'src/modeling/v4_decision_models.py'),
        'prediction_sha256':sha256(ROOT/'results/finalshot/m0_m3_predictions.csv.gz'),
        'literal_cap_evaluable':False,'astrocyte_data_accessed':False,'nzip_outcomes_accessed':False}
    write_json(f'{DEST}/recomputation_summary.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return result
