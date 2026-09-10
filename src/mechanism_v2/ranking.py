"""Compact paired-ranking model with a source-free biological prediction API.

No real localization evaluation is launched by this module. Nuisance handling is
a closed-form linear predictability penalty, not an unrestricted neural domain
adversary. Source-conditioned ranking temperatures are optional training heads;
unseen sources always use the shared latent score. No per-source feature blocks.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from threadpoolctl import threadpool_limits
from .primitives import edit_band


@dataclass(frozen=True)
class RankConfig:
    ridge:float=0.01
    nuisance:str='none'
    nuisance_strength:float=0.1
    ranking_heads:bool=False
    head_shrinkage:float=0.1
    pairs_per_set:int=128
    seed:int=20260909
    max_iterations:int=400
    tolerance:float=1e-8


def row_weights(frame):
    """Equal sources -> connected biological units -> decision sets -> rows."""
    keys=['dataset','biological_unit','decision_set_id']
    if frame[keys].isna().any().any():raise ValueError('Missing training grouping')
    table=frame[keys].drop_duplicates()
    if table.decision_set_id.duplicated().any():raise ValueError('A decision set belongs to multiple units')
    n_sources=table.dataset.nunique()
    units=table.groupby('dataset').biological_unit.nunique()
    sets=table.groupby(['dataset','biological_unit']).decision_set_id.nunique()
    counts=frame.groupby('decision_set_id').size()
    weights=np.array([1/(n_sources*units[r.dataset]*sets.loc[(r.dataset,r.biological_unit)]*counts[r.decision_set_id])
        for r in frame[keys].itertuples(index=False)])
    return weights/weights.sum()


def pair_design(frame,config):
    """Outcome-independent pair sampling; only exact target ties are omitted."""
    if not frame.index.equals(pd.RangeIndex(len(frame))):raise ValueError('Require positional row index')
    y=frame.localization_effect.to_numpy(float)
    if not np.isfinite(y).all():raise ValueError('Non-finite training outcomes')
    if config.pairs_per_set<1:raise ValueError('Positive pair cap required')
    rw=row_weights(frame); records=[]
    sources=sorted(frame.dataset.astype(str).unique());lookup={v:i for i,v in enumerate(sources)}
    for decision,indices in frame.groupby('decision_set_id',sort=True).indices.items():
        idx=np.array(sorted(indices,key=lambda j:str(frame.candidate_id.iloc[j])),dtype=int)
        if frame.candidate_id.iloc[idx].duplicated().any():raise ValueError('Duplicate candidate in training set')
        n=len(idx);total=n*(n-1)//2
        if total==0:continue
        seed=(int(hashlib.sha256(str(decision).encode()).hexdigest()[:16],16)+config.seed)%2**64
        rng=np.random.default_rng(seed)
        if total<=config.pairs_per_set:
            chosen=list(itertools.combinations(range(n),2))
        else:
            # Uniform rejection sampling over unordered pairs, no outcome use.
            chosen=set()
            while len(chosen)<config.pairs_per_set:
                a,b=map(int,rng.integers(0,n,size=2))
                if a!=b:chosen.add(tuple(sorted((a,b))))
            chosen=sorted(chosen)
        local=[(int(idx[a]),int(idx[b])) for a,b in chosen if y[idx[a]]!=y[idx[b]]]
        if not local:continue
        weight=float(rw[idx].sum())/len(local)
        source=lookup[str(frame.dataset.iloc[idx[0]])]
        records.extend((a,b,float(np.sign(y[a]-y[b])),weight,source) for a,b in local)
    if not records:raise ValueError('No non-tied within-set training pairs')
    p=np.asarray(records,float);p[:,3]/=p[:,3].sum()
    return {'left':p[:,0].astype(int),'right':p[:,1].astype(int),'sign':p[:,2],
            'weight':p[:,3],'source':p[:,4].astype(int),'source_names':sources}


def nuisance_matrix(x,frame,weights,mode):
    """Training-only linear predictability of z from centered nuisance indicators.

    P = X' W D (D' W D + 1e-6 I)^-1 D' W X is positive semidefinite.
    beta' P beta is the ridge-regularized variational maximum over a linear
    nuisance predictor of z. This controls linear associations only. It must not
    be reported as proof of nuisance independence or causal disentanglement.
    """
    if mode not in {'none','source','size','source_size'}:raise ValueError('Unknown nuisance mode')
    if mode=='none':return np.zeros((x.shape[1],x.shape[1]))
    fields=[]
    if 'source' in mode:fields.append(pd.get_dummies(frame.dataset.astype(str),dtype=float).to_numpy())
    if 'size' in mode:fields.append(pd.get_dummies(edit_band(frame.edit_cost.to_numpy()),dtype=float).to_numpy())
    d=np.column_stack(fields);d-=weights@d
    gram=d.T@(weights[:,None]*d)+1e-6*np.eye(d.shape[1])
    cross=d.T@(weights[:,None]*x)
    return cross.T@np.linalg.solve(gram,cross)


def ranking_objective(parameters,differences,sign,weight,source,nuisance,config,n_sources):
    p=differences.shape[1];beta=parameters[:p]
    theta=parameters[p:] if config.ranking_heads else np.zeros(n_sources)
    scales=np.exp(theta);latent=differences@beta
    margin=sign*scales[source]*latent
    loss=float(weight@np.logaddexp(0,-margin)+0.5*config.ridge*(beta@beta))
    slope=-weight*sign*scales[source]*expit(-margin)
    gradient_beta=differences.T@slope+config.ridge*beta
    if config.nuisance!='none':
        penalty=nuisance@beta
        loss+=config.nuisance_strength*float(beta@penalty)
        gradient_beta+=2*config.nuisance_strength*penalty
    if config.ranking_heads:
        loss+=0.5*config.head_shrinkage*float(theta@theta)
        gradient_theta=np.bincount(source,weights=slope*latent,minlength=n_sources)+config.head_shrinkage*theta
        gradient=np.r_[gradient_beta,gradient_theta]
    else:gradient=gradient_beta
    return loss,gradient


class PairedRanker:
    """Score = standardized mechanistic deltas dot shared beta; identity-free API."""
    def __init__(self,config=RankConfig()):
        self.config=config

    def fit(self,features,frame,feature_names):
        frame=frame.reset_index(drop=True)
        x=np.asarray(features,dtype=np.float64)
        if x.ndim!=2 or x.shape[0]!=len(frame) or x.shape[1]!=len(feature_names):
            raise ValueError('Training feature shape mismatch')
        if not np.isfinite(x).all():raise ValueError('Non-finite features')
        if len(set(feature_names))!=len(feature_names):raise ValueError('Duplicate feature names')
        forbidden=('source_id','dataset_id','parent_id','gene_id','reporter_id','localization_effect','requested_direction')
        if any(any(part in name.lower() for part in forbidden) for name in feature_names):
            raise PermissionError('Identity/outcome feature in latent representation')
        if self.config.ridge<=0 or self.config.head_shrinkage<=0 or self.config.nuisance_strength<0:
            raise ValueError('Invalid regularization')
        weights=row_weights(frame)
        self.mean_=weights@x
        variance=weights@((x-self.mean_)**2)
        self.scale_=np.sqrt(np.maximum(variance,1e-12))
        x=(x-self.mean_)/self.scale_
        pairs=pair_design(frame,self.config)
        differences=x[pairs['left']]-x[pairs['right']]
        nuisance=nuisance_matrix(x,frame,weights,self.config.nuisance)
        p=x.shape[1];n_sources=len(pairs['source_names'])
        initial=np.zeros(p+(n_sources if self.config.ranking_heads else 0))
        bounds=[(None,None)]*p+([(-1,1)]*n_sources if self.config.ranking_heads else [])
        with threadpool_limits(limits=2):
            result=minimize(ranking_objective,initial,args=(differences,pairs['sign'],pairs['weight'],
                pairs['source'],nuisance,self.config,n_sources),jac=True,method='L-BFGS-B',bounds=bounds,
                options={'maxiter':self.config.max_iterations,'ftol':self.config.tolerance,'gtol':1e-6})
        if not result.success or not np.isfinite(result.x).all():
            raise RuntimeError(f'Ranking optimization failed: {result.message}')
        self.beta_=result.x[:p];self.feature_names_=list(feature_names)
        self.ranking_temperatures_=dict(zip(pairs['source_names'],
            np.exp(result.x[p:]).tolist() if self.config.ranking_heads else [1.]*n_sources))
        self.fit_audit_={'pairs':len(pairs['left']),'rows':len(frame),'source_names':pairs['source_names'],
            'objective':float(result.fun),'iterations':int(result.nit),'converged':bool(result.success),
            'gradient_max_abs':float(np.abs(result.jac).max()),
            'latent_receives_source_identity':False,'nuisance_penalty':'linear predictability only'}
        return self

    def predict(self,features):
        x=np.asarray(features,dtype=np.float64)
        if x.ndim!=2 or x.shape[1]!=len(self.beta_) or not np.isfinite(x).all():
            raise ValueError('Prediction shape/non-finite feature error')
        return ((x-self.mean_)/self.scale_)@self.beta_

    def predict_ranking_head(self,features,sources):
        score=self.predict(features)
        if len(sources)!=len(score):raise ValueError('Head/source shape mismatch')
        return score*np.array([self.ranking_temperatures_.get(str(s),1.) for s in sources])

    def to_record(self):
        return {'format':'mechanism_v2_paired_ranker_v1','configuration':asdict(self.config),
            'mean':self.mean_.tolist(),'scale':self.scale_.tolist(),'beta':self.beta_.tolist(),
            'feature_names':self.feature_names_,'ranking_temperatures':self.ranking_temperatures_,
            'fit_audit':self.fit_audit_}

    @classmethod
    def from_record(cls,record):
        if record['format']!='mechanism_v2_paired_ranker_v1':raise ValueError('Unknown model format')
        model=cls(RankConfig(**record['configuration']))
        for name in ['mean','scale','beta']:
            value=np.asarray(record[name],float)
            if value.ndim!=1 or not np.isfinite(value).all():raise ValueError('Corrupt model array')
            setattr(model,name+'_',value)
        model.feature_names_=record['feature_names']
        if not len(model.mean_)==len(model.scale_)==len(model.beta_)==len(model.feature_names_):
            raise ValueError('Corrupt model dimensions')
        if (model.scale_<=0).any():raise ValueError('Corrupt scaler')
        model.ranking_temperatures_=record['ranking_temperatures'];model.fit_audit_=record['fit_audit']
        if any(not np.isfinite(v) or v<=0 for v in model.ranking_temperatures_.values()):
            raise ValueError('Corrupt source head')
        return model
