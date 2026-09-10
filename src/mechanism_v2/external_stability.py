"""Independent paired-stability predictor primitives; no automatic training run.

The complete outer driver must verify mapping, exclusions and committed protocol
before fitting real measurements. These primitives are tested on synthetic data.
"""
from __future__ import annotations
import itertools
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

KMERS=tuple(''.join(k) for size in range(1,5) for k in itertools.product('ACGT',repeat=size))
KMER_INDEX={k:i for i,k in enumerate(KMERS)}


def sequence_features(sequence):
    sequence=sequence.upper().replace('U','T')
    if not sequence or set(sequence)-set('ACGT'):raise ValueError('Invalid external sequence')
    vector=np.zeros(len(KMERS),float)
    for size in range(1,5):
        for i in range(len(sequence)-size+1):vector[KMER_INDEX[sequence[i:i+size]]]+=1
    return vector*100/len(sequence)


def paired_features(reference,mutant):
    a=sequence_features(reference);b=sequence_features(mutant)
    return np.r_[b-a,(a[:20]+b[:20])/2]


def reverse_features(x):
    x=np.asarray(x,float).copy()
    if x.ndim!=2 or x.shape[1]!=360 or not np.isfinite(x).all():raise ValueError('Invalid paired feature schema')
    x[:,:340]*=-1
    return x


class StabilityPredictor:
    def __init__(self,recipe):self.recipe=dict(recipe)

    def fit(self,x,y,groups):
        x=np.asarray(x,float);y=np.asarray(y,float);groups=np.asarray(groups)
        reverse=reverse_features(x)
        if len(x)!=len(y) or len(groups)!=len(y) or not np.isfinite(y).all():raise ValueError('Invalid stability training data')
        _,idx,counts=np.unique(groups,return_inverse=True,return_counts=True)
        weights=1/counts[idx];weights=weights/weights.sum()*len(weights)
        augmented=np.r_[x,reverse];target=np.r_[y,-y];weight=np.r_[weights,weights]*0.5
        self.scaler_=StandardScaler().fit(augmented,sample_weight=weight)
        transformed=self.scaler_.transform(augmented)
        if self.recipe['kind']=='ridge':
            self.model_=Ridge(alpha=self.recipe['alpha'],fit_intercept=False,solver='lsqr',tol=1e-8)
        elif self.recipe['kind']=='hgb':
            self.model_=HistGradientBoostingRegressor(**{k:v for k,v in self.recipe.items() if k not in {'id','kind'}},
                early_stopping=False,random_state=20260910)
        else:raise ValueError('Unregistered external model family')
        with threadpool_limits(limits=2):self.model_.fit(transformed,target,sample_weight=weight)
        self.training_groups_=sorted(set(groups.astype(str)))
        return self

    def predict(self,x):
        x=np.asarray(x,float);reverse=reverse_features(x)
        with threadpool_limits(limits=2):
            return (self.model_.predict(self.scaler_.transform(x))-
                    self.model_.predict(self.scaler_.transform(reverse)))/2
