from src.research_20260921.common import ROOT,sha256
from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd

OUT=ROOT/'results/generalization_20260926'
ART=ROOT/'artifacts/generalization_20260926'
REPORT=ROOT/'reports/generalization_20260926'
SOURCE=ROOT/'data/raw/astrocyte_gse330741'
WORKBOOK=SOURCE/'supplementary/media-1.xlsx'
SEED=20260926
EXCLUDED='slc1a2.1_2621_2681'
VOCAB={k:[''.join(s) for s in itertools.product('ACGT',repeat=k)] for k in (1,2,3)}
WORDS=sum(VOCAB.values(),[])
TOL=1e-12

def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list,np.ndarray)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x
def save(path,payload):
    path=Path(path).resolve();assert any(path.is_relative_to(p) for p in (OUT,ART,REPORT))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==payload,'Preserving '+str(path)
    else:path.write_bytes(payload)
def readj(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def jsave(path,obj):save(path,(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csvsave(path,frame):save(path,frame.to_csv(index=False,lineterminator='\n').encode())
def count(sequence):
    return np.array([sum(sequence[i:i+len(w)]==w for i in range(len(sequence)-len(w)+1)) for w in WORDS],float)
def delta_features(frame):
    parents={s:count(s) for s in frame.parent_sequence.unique()}
    return np.array([count(m)-parents[p] for p,m in zip(frame.parent_sequence,frame.mutant_sequence)])
def sign(a):return np.where(np.abs(a)<=TOL,0,np.sign(a))
def config():return readj(OUT/'evaluation_config.json')

def assert_frozen():
    import subprocess,re
    f=readj(OUT/'prefit_freeze.json')
    for path,h in f['files'].items():assert sha256(ROOT/path)==h,path
    rel=(OUT/'prefit_freeze.json').relative_to(ROOT).as_posix()
    record=REPORT/'GSE330741_PREFIT_FREEZE.md'
    assert record.exists() and 'OUTCOMES MAY NOW BE OPENED' in record.read_text(encoding='utf-8')
    commit=re.search(r'Protocol commit: `([a-f0-9]+)`',record.read_text(encoding='utf-8')).group(1)
    assert subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT)==(OUT/'prefit_freeze.json').read_bytes()
    assert subprocess.check_output(['git','show','HEAD:'+record.relative_to(ROOT).as_posix()],cwd=ROOT)==record.read_bytes()
    return f
