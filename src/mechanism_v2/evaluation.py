"""Intervention selection metrics and paired connected-unit uncertainty.

Functions are independent of fitting and accept already-frozen predictions.
The bootstrap resamples a biological component once, retaining both directions
and any cross-source occurrences together. Rows are never bootstrap units.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata


def decision_metrics(rows,score,minimum_candidates=2):
    scores=np.asarray(score,float)
    if scores.shape!=(len(rows),) or not np.isfinite(scores).all():raise ValueError('Invalid predictions')
    needed=['dataset','component','decision_set_id','candidate_id','localization_effect']
    if rows[needed].isna().any().any():raise ValueError('Missing evaluation fields')
    if not np.isfinite(rows.localization_effect.to_numpy(float)).all():raise ValueError('Invalid evaluation outcomes')
    if minimum_candidates<2:raise ValueError('At least two candidates required for a ranking metric')
    work=rows[needed].copy();work['score']=scores
    output=[];excluded=[]
    for decision,group in work.groupby('decision_set_id',sort=True):
        if group.component.nunique()!=1 or group.dataset.nunique()!=1:
            raise ValueError('Decision set crosses biological component/source')
        if group.candidate_id.duplicated().any():raise ValueError('Duplicate decision candidate')
        if len(group)<minimum_candidates:
            excluded.append({'decision_set_id':decision,'reason':'insufficient_candidates'});continue
        if group.localization_effect.nunique()<2:
            excluded.append({'decision_set_id':decision,'reason':'zero_outcome_range'});continue
        cohort=hashlib.sha256(json.dumps(sorted(zip(group.candidate_id.astype(str),
            group.localization_effect.astype(float))),allow_nan=False,separators=(',',':')).encode()).hexdigest()
        for direction,sign in [('increase',1.),('decrease',-1.)]:
            utility=sign*group.localization_effect.to_numpy(float)
            prediction=sign*group.score.to_numpy(float)
            order=np.lexsort((group.candidate_id.astype(str).to_numpy(),-prediction))
            regret=(utility.max()-utility)/(utility.max()-utility.min())
            rank=1-(rankdata(-utility,method='average')-1)/(len(group)-1)
            chosen=order[0]
            output.append({'dataset':group.dataset.iloc[0],'component':group.component.iloc[0],
                'decision_set_id':decision,'direction':direction,'candidates':len(group),
                'candidate_outcome_sha256':cohort,
                'selected_candidate':str(group.candidate_id.iloc[chosen]),
                'rank':float(rank[chosen]),'regret':float(regret[chosen]),
                'good_at_3':float((regret[order[:3]]<=0.1).any()),
                'good_at_5':float((regret[order[:5]]<=0.1).any()),
                'random_expected_regret':float(regret.mean())})
    return pd.DataFrame(output),pd.DataFrame(excluded,columns=['decision_set_id','reason'])


def pair_comparison(full,baseline):
    keys=['dataset','component','decision_set_id','direction']
    if full[keys].duplicated().any() or baseline[keys].duplicated().any():raise ValueError('Duplicate metric key')
    paired=full.merge(baseline,on=keys,suffixes=('','_baseline'),validate='one_to_one',how='outer',indicator=True)
    if not paired['_merge'].eq('both').all():raise ValueError('Comparisons must use identical eligible decision sets')
    if not np.array_equal(paired.candidates,paired.candidates_baseline):raise ValueError('Candidate sets differ in size')
    if not np.array_equal(paired.candidate_outcome_sha256,paired.candidate_outcome_sha256_baseline):
        raise ValueError('Candidate identities or outcomes differ')
    paired['rank_gain']=paired['rank']-paired.rank_baseline
    paired['regret_gain']=paired.regret_baseline-paired.regret
    return paired.drop(columns='_merge')


def context_values(paired):
    units=paired.groupby(['dataset','component','direction'])[['rank_gain','regret_gain']].mean().reset_index()
    contexts=units.groupby(['dataset','direction'])[['rank_gain','regret_gain']].mean().reset_index()
    values={key:float(contexts[key].mean()) for key in ['rank_gain','regret_gain']}
    return values,units,contexts


def paired_component_bootstrap(paired,resamples=10000,seed=20260909):
    """Global component resampling; equal context means within every replicate.

    Missing-source replicates are recorded and omitted, not filled with zero.
    More than 1% omitted makes the interval ineligible, rather than silently
    changing the bootstrap design. Every component's directions travel together.
    """
    if resamples<100:raise ValueError('At least 100 bootstrap replicates required')
    point,units,contexts=context_values(paired)
    groups=sorted(units.component.unique());context_keys=sorted(set(zip(units.dataset,units.direction)))
    if len(groups)<2:raise ValueError('At least two independent components required')
    columns=pd.MultiIndex.from_tuples(context_keys,names=['dataset','direction'])
    matrices=[]
    for metric in ['rank_gain','regret_gain']:
        pivot=units.pivot(index='component',columns=['dataset','direction'],values=metric).reindex(index=groups,columns=columns)
        matrices.append(pivot.to_numpy(float))
    present=np.isfinite(matrices[0]).astype(float)
    if not np.array_equal(present,np.isfinite(matrices[1])):raise ValueError('Metric availability differs')
    rng=np.random.default_rng(seed)
    multiplicities=rng.multinomial(len(groups),np.repeat(1/len(groups),len(groups)),size=resamples)
    denominators=multiplicities@present;valid=(denominators>0).all(axis=1)
    samples={}
    for metric,matrix in zip(['rank_gain','regret_gain'],matrices):
        values=(multiplicities[valid]@np.nan_to_num(matrix))/denominators[valid]
        samples[metric]=values.mean(axis=1)
    eligible=bool(valid.mean()>=0.99)
    result={'point':point,'components':len(groups),'resamples_requested':resamples,
        'resamples_valid':int(valid.sum()),'eligible':eligible,'seed':seed,
        'unit':'connected biological component; all directions and cross-source occurrences together',
        'confidence95':{k:np.quantile(v,[.025,.975]).tolist() for k,v in samples.items()},
        'missing_context_replicates':int((~valid).sum())}
    return result,samples


def distributed_benefit(paired):
    _,units,contexts=context_values(paired)
    component=units.groupby('component')[['rank_gain','regret_gain']].mean()
    gain=component.regret_gain.to_numpy(float)
    if not len(gain):raise ValueError('No independent units')
    source=units.groupby(['dataset','component']).regret_gain.mean().reset_index()
    direction=units.groupby(['direction','component']).regret_gain.mean().reset_index()
    return {'components':len(gain),'fraction_improved':float((gain>0).mean()),'median':float(np.median(gain)),
        'quartiles':np.quantile(gain,[.25,.75]).tolist(),'worst_decile_quantile':float(np.quantile(gain,.1)),
        'worst_decile_mean':float(np.sort(gain)[:max(1,int(np.ceil(.1*len(gain))))].mean()),
        'leave_best_one_out_mean':float((gain.sum()-gain.max())/(len(gain)-1)) if len(gain)>1 else None,
        'source_fractions':source.assign(improved=source.regret_gain>0).groupby('dataset').improved.mean().to_dict(),
        'direction_fractions':direction.assign(improved=direction.regret_gain>0).groupby('direction').improved.mean().to_dict()}


def holm_adjust(pvalues):
    """Familywise correction for prospectively enumerated formal mechanism tests."""
    p=np.asarray(pvalues,float)
    if p.ndim!=1 or not np.isfinite(p).all() or (p<0).any() or (p>1).any():raise ValueError('Invalid p-values')
    order=np.argsort(p,kind='stable');out=np.empty_like(p)
    out[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return out
