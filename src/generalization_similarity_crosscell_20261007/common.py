"""Metadata-only loader and write-once files in a separate namespace."""
from src.generalization_crosscell_20261007.common import ROOT, np, pd, sha256, clean, META, CORE, TASKS, FOLDS, load
from pathlib import Path
import gzip,json,hashlib

NS='generalization_similarity_crosscell_20261007'
SRC,OUT,REP,ART=[ROOT/name/NS for name in ('src','results','reports','artifacts')]
LENGTH=150
CUTOFF=30
BLOCK=64
WORKERS=1
SEED=20261007

def save(path,payload):
    path=Path(path).resolve()
    assert any(path.is_relative_to(root) for root in (SRC,OUT,REP,ART))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): assert path.read_bytes()==payload,'Preserve '+str(path)
    else:path.write_bytes(payload)

def jsave(path,data):
    save(path,(json.dumps(clean(data),sort_keys=True,indent=2,allow_nan=False)+'\n').encode())

def csvsave(path,frame,compressed=False):
    payload=frame.to_csv(index=False,lineterminator='\n').encode()
    save(path,gzip.compress(payload,mtime=0) if compressed else payload)

def metadata_hash(frame):
    assert 'measured_delta' not in frame
    return hashlib.sha256(frame[META].to_csv(index=False,lineterminator='\n').encode()).hexdigest()
