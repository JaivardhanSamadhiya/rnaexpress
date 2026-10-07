"""Separately frozen supervised namespace; old metadata analysis remains intact."""
from .common import ROOT,np,pd,sha256,clean,META as ORIGINAL_META,CORE,TASKS,FOLDS,NS,SRC,OUT,REP,ART,SEED,save,jsave,csvsave
from .common import load as original_load
from .splits import attach_groups
from src.generalization_crosscell_20261007.common import decisions,inner_regret,readj
from pathlib import Path
import hashlib,json,subprocess

TRACKS=['simple','base','raw','structure','lookup','bert','combined']
WIDTHS=dict(zip(TRACKS,[102,246,251,262,502,502,518]))
INFORMED=['structure','bert','combined']
FEATURE_ART=ROOT/'artifacts/generalization_crosscell_20261007'
UNPURGED_OUT=ROOT/'results/generalization_crosscell_20261007'
META=ORIGINAL_META+['similarity_component']

def load(outcomes=True):
    frame,_=original_load(outcomes)
    receipt=readj(OUT/'metadata_graph_receipt.json')
    assert receipt['cutoff']==30 and receipt['status']=='PASS'
    for name,digest in receipt['output_hashes'].items():assert sha256(ROOT/name)==digest
    groups=pd.read_csv(ART/'similarity_components.csv')
    # Group attachment is outcome-free; bind it by original IDs/order, then attach labels unchanged.
    meta=attach_groups(frame.drop(columns=['measured_delta'],errors='ignore'),groups)
    if outcomes:meta['measured_delta']=frame.measured_delta.to_numpy()
    return meta,None

def freeze_check(full=True):
    if full:
        from src.generalization_20261007.verify import preservation
        preservation()
    path=OUT/'prefit_manifest.json';manifest=readj(path)
    assert manifest['status']=='FROZEN_PREFIT' and manifest['checkpoint_adoption']==False
    names=manifest['files'] if full else manifest['critical_files']
    for name,digest in names.items():assert sha256(ROOT/name)==digest,name
    assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
    return manifest
