from src.research_20260921.common import ROOT, sha256
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

OUT=ROOT/'results/srle_prediction_20260926'
ART=ROOT/'artifacts/small_edit_20260925'
REPORT=ROOT/'reports/small_edit_20260925'
OLD=ROOT/'results/research_20260921'
MODELS=('composition','1mer','2mer','3mer','kmer123','position_additive','position_pair')
SCHEMES=('sequence_holdout','composition_holdout','purged_composition_holdout')
SEED=20260926
TOL=1e-12


def save(path,payload):
    path=Path(path).resolve()
    assert any(path.is_relative_to(p) for p in (OUT,ART,REPORT))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        assert path.read_bytes()==payload, 'Preserving '+str(path)
    else: path.write_bytes(payload)


def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v


def jsave(path,v):save(path,(json.dumps(clean(v),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csvsave(path,v):save(path,v.to_csv(index=False,lineterminator='\n').encode())
def readj(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def counts(seqs):return np.array([[s.count(b) for b in 'ACGT'] for s in seqs],int)
def keys(seqs):return [''.join(map(str,row)) for row in counts(seqs)]


def training_mask(frame,scheme,key=None):
    mask=~frame.test.to_numpy(bool)
    if scheme=='sequence_holdout':return mask
    comp=counts(frame.kmer)
    target=np.array(list(map(int,key)))
    distance=np.abs(comp-target).sum(1)
    return mask & (distance>(4 if scheme=='purged_composition_holdout' else 0))


def bootstrap_counts(n):
    draws=np.random.default_rng(SEED).integers(0,n,(2000,n))
    return np.array([np.bincount(row,minlength=n) for row in draws])
