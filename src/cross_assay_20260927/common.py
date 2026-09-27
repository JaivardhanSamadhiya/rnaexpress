from src.research_20260921.common import ROOT,sha256
from pathlib import Path
import json,itertools,hashlib
import numpy as np
import pandas as pd
OUT=ROOT/'results/cross_assay_20260927'
ART=ROOT/'artifacts/cross_assay_20260927'
REPORT=ROOT/'reports/cross_assay_20260927'
SRC=ROOT/'src/cross_assay_20260927'
SEED=20260927
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,np.ndarray)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x
def save(p,data):
    p=Path(p).resolve();assert any(p.is_relative_to(r) for r in (OUT,ART,REPORT,SRC))
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data,'Preserve '+str(p)
    else:p.write_bytes(data)
def jsave(p,obj):save(p,(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csvsave(p,df):save(p,df.to_csv(index=False,lineterminator='\n').encode())
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def config():return readj(OUT/'config.json')
def frozen():
    import subprocess
    f=readj(OUT/'development_freeze.json')
    for p,h in f['files'].items():assert sha256(ROOT/p)==h,p
    rel=(OUT/'development_freeze.json').relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)==(OUT/'development_freeze.json').read_bytes()
    return f
