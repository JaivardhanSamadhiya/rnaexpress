from src.research_20260921.common import ROOT, sha256
from pathlib import Path
import gzip
import json
import numpy as np
import pandas as pd

OUT=ROOT/'results/small_edit_20260925'
REPORT=ROOT/'reports/small_edit_20260925'


def save(path, payload):
    path=Path(path).resolve()
    if not any(path.is_relative_to(p.resolve()) for p in (OUT,REPORT)):
        raise PermissionError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=payload:
            raise FileExistsError('Preserving '+str(path))
    else:
        path.write_bytes(payload)
    return path


def clean(obj):
    if isinstance(obj,dict): return {str(k):clean(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [clean(v) for v in obj]
    if isinstance(obj,np.ndarray): return clean(obj.tolist())
    if isinstance(obj,np.generic): return clean(obj.item())
    if isinstance(obj,float) and not np.isfinite(obj): return None
    return obj


def jsave(name,obj):
    return save(OUT/name,(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())


def csvsave(name,frame):
    payload=frame.to_csv(index=False,lineterminator='\n').encode()
    if name.endswith('.gz'): payload=gzip.compress(payload,mtime=0)
    return save(OUT/name,payload)


def readj(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def band(n):
    return str(n) if n<=3 else ('4-6' if n<=6 else '>6')
