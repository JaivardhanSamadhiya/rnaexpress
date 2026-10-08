"""Late scientific imports, admitted Mikl labels and immutable companion IO."""
from pathlib import Path
from functools import lru_cache
import ctypes
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from src.generalization_conservation_cellaxis_20261008 import spec as s
from src.generalization_rbp_cellaxis_20261007.common import sha256, readj, committed

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_conservation_cellaxis_20261008'
SRC, OUT, REP, ART = [ROOT / name / NS for name in ('src','results','reports','artifacts')]
PREP_OUT = ROOT / 'results/generalization_conservation_cellaxis_20261008'
OLD_OUT = ROOT / 'results/generalization_crosscell_20261007'
OLD_KNOWN = ROOT / 'results/generalization_knowncell_20261007'
NUMERIC_AUDIT = ROOT / 'results/generalization_campaign_20261007/crosscell_numeric_score_audit_01.json'
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'
DESIGN = OUT / 'design_manifest_v2.json'
PREFIT = OUT / 'prefit_manifest.json'
EVALUATION = OUT / 'evaluation_manifest.json'


@lru_cache(maxsize=1)
def runtime():
    from .runtime_guard import python_contract,SCIENTIFIC
    committed(SCIENTIFIC);python_contract(readj(SCIENTIFIC))
    from src.research_20260921 import common as bootstrap
    from src.generalization_crosscell_20261007 import common as old
    from src.generalization_20261007.route_scaling import fit_model, predict_model
    return old.np, old.pd, old, fit_model, predict_model


def clean(value):
    if isinstance(value,dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [clean(v) for v in value]
    if isinstance(value,Path): return str(value)
    if hasattr(value,'item'): return clean(value.item())
    return value


def save(path, payload):
    path=Path(path).resolve()
    assert any(path.is_relative_to(p.resolve()) for p in (SRC,OUT,REP,ART))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(payload)


def jsave(path,value):
    save(path,(json.dumps(clean(value),sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


def csvsave(path,frame,compressed=False):
    raw=frame.to_csv(index=False,lineterminator='\n').encode()
    save(path,gzip.compress(raw,mtime=0) if compressed else raw)


def hash_files(files):
    aliases=set()
    for name,expected in files.items():
        name=name.replace('\\','/')
        assert ':' not in name and not name.startswith('/') and all(k not in ('','.','..') for k in name.split('/'))
        assert name.casefold() not in aliases,'Hash path aliases';aliases.add(name.casefold())
        path=(ROOT/name).resolve();assert path.is_relative_to(ROOT.resolve()) and sha256(path)==expected,name


def manifest_check(path,status):
    committed(path);value=readj(path);assert value['status']==status
    hash_files(value['files'])
    for name in value.get('own_committed_files',[]):committed(ROOT/name)
    return value


def design_check(root_start=False):
    assert root_start,'Root explicit start after source-only companion commit required'
    return manifest_check(DESIGN,'FROZEN_CONSERVATION_CELLAXIS_DOWNSTREAM_DESIGN')


def thread_check():
    assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
    for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS'):assert os.environ.get(name)=='1'


def resource_check(min_ram=3.,min_disk=1.):
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in
            ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
    info=Memory();info.length=ctypes.sizeof(info)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info))
    ram,disk=info.available/2**30,shutil.disk_usage(ROOT).free/2**30
    assert ram>=min_ram and disk>=min_disk,'Resource floor: '+str((ram,disk))
    return {'available_RAM_GiB':ram,'free_disk_GiB':disk}


def certified_core():
    foundation=ROOT/'results/generalization_20261007/prefit_manifest.json'
    admission=ROOT/'results/probabilistic_ranking_20260928/prefit_manifest.json'
    committed(foundation);committed(admission)
    assert sha256(admission)==readj(foundation)['files'][admission.relative_to(ROOT).as_posix()]
    assert sha256(CORE)==readj(admission)['files'][CORE.relative_to(ROOT).as_posix()]
    return CORE


def load():
    np,pd,old,_,_=runtime()
    certified_core();frame,_=old.load(False)
    permitted=set(frame.original_core_row.astype(int)+1)
    truth=pd.read_csv(CORE,usecols=['intervention_id','measured_delta'],low_memory=False,
        skiprows=lambda row:row>0 and row not in permitted)
    assert list(truth.intervention_id)==list(frame.intervention_id)
    frame['measured_delta']=truth.measured_delta.to_numpy(float)
    assert np.isfinite(frame.measured_delta).all()
    admitted=readj(PREP_OUT/'metadata_receipt.json');assert admitted['status']=='PASS'
    assert sha256(CORE)==admitted['core_sha256']
    pd.testing.assert_frame_equal(frame.drop(columns='measured_delta'),pd.read_csv(PREP_OUT/'row_index.csv.gz',low_memory=False))
    return frame


def rowhash(frame):return hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
def metadata_hash(frame):return hashlib.sha256(frame[s.META].to_csv(index=False,lineterminator='\n').encode()).hexdigest()
def values_hash(value):
    np,*_=runtime();return hashlib.sha256(np.ascontiguousarray(value,dtype='<f8').tobytes()).hexdigest()


def input_check():
    receipt=readj(PREP_OUT/'array_receipt.json')
    assert receipt['status']=='PASS' and receipt['widths']==s.WIDTHS and receipt['rows']==s.ROWS
    hash_files(receipt['files']);hash_files(receipt['source_array_files'])
    assert receipt['base_simple_exact_bytes'] and receipt['every_new_track_has_exact_original_base_prefix']
    return receipt


def features(track):
    assert track in s.TRACKS
    np,*_=runtime();receipt=input_check();path=ROOT/receipt['feature_paths'][track]
    with np.load(path,allow_pickle=False) as data:
        assert data.files==['features'];x=np.asarray(data['features'],dtype=float)
    assert x.shape==(s.ROWS,s.WIDTHS[track]) and np.isfinite(x).all()
    assert values_hash(x)==receipt['parsed_float64_matrix_sha256'][track]
    return x


def prefit_check():
    thread_check();value=manifest_check(PREFIT,'FROZEN_CONSERVATION_CELLAXIS_PREFIT')
    from src.generalization_20261007.verify import preservation
    preservation();input_check()
    from .controls import check as controls_check
    controls_check()
    from .runtime_guard import check as runtime_check
    runtime_check();return value


def evaluation_check():
    prefit_check();return manifest_check(EVALUATION,'FROZEN_CONSERVATION_CELLAXIS_REPRESENTED_EVALUATION')
