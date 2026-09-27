from src.research_20260921.common import ROOT,sha256
from pathlib import Path
from functools import lru_cache
import json
import numpy as np
import pandas as pd

OLD=ROOT/'results/srle_prediction_20260926'
OLDART=ROOT/'artifacts/small_edit_20260925'
OUT=ROOT/'results/srle_synthesis_20260926'
ART=ROOT/'artifacts/srle_synthesis_20260926'
REPORT=ROOT/'reports/small_edit_20260925'
SEED=20260926
TOL=1e-12

def readj(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def save(path,payload):
    path=Path(path).resolve();assert any(path.is_relative_to(p) for p in (OUT,ART,REPORT))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==payload,'Preserving '+str(path)
    else:path.write_bytes(payload)
def jsave(path,obj):save(path,(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csvsave(path,frame):save(path,frame.to_csv(index=False,lineterminator='\n').encode())
def sign(x):return np.where(np.abs(x)<=TOL,0,np.sign(x))
@lru_cache(maxsize=150)
def draws(n):return np.random.default_rng(SEED).integers(0,n,(2000,n))
def interval(values):
    a=np.asarray(values,float);a=a[np.isfinite(a)]
    return (float(a.mean()),*np.quantile(a[draws(len(a))].mean(1),[.025,.975]).tolist()) if len(a) else (np.nan,)*3
def group_summary(frame,metrics,keys=()):
    records=[]
    groups=frame.groupby(list(keys),dropna=False) if keys else [((),frame)]
    for key,g in groups:
        key=key if isinstance(key,tuple) else (key,)
        row=dict(zip(keys,key));row.update(rows=len(g),statistical_groups=g.group.nunique(),biological_contexts=1)
        means=g.groupby('group')[metrics].mean()
        for metric in metrics:
            value,lo,hi=interval(means[metric]);row.update({metric:value,metric+'_ci_low':lo,metric+'_ci_high':hi})
        records.append(row)
    return pd.DataFrame(records)

def load():
    source=pd.read_csv(OLD/'sequence_inventory.csv',dtype={'group':str},float_precision='round_trip')
    effects=pd.read_csv(OLD/'edit_effect_predictions.csv',dtype={'group':str},float_precision='round_trip')
    choices=pd.read_csv(OLD/'decision_rows.csv',dtype={'group':str},float_precision='round_trip')
    fits=readj(OLD/'fitted_parameters.json')
    roster=pd.read_csv(OLDART/'srle_observation_inventory.csv',dtype={'group':str,'composition_before':str,'composition_after':str},float_precision='round_trip')
    return source,effects,choices,fits,roster
