"""Original allele identities, fixed inherited folds and immutable namespace."""
from src.generalization_20261007.common import (
    ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret,
)
from pathlib import Path
import gzip, hashlib, io, json, subprocess

NS='generalization_crosscell_20261007'
SRC,OUT,REP,ART=[ROOT/name/NS for name in ('src','results','reports','artifacts')]
TRACKS=['simple','base','raw','structure','lookup','bert','combined']
WIDTHS=dict(zip(TRACKS,[102,246,251,262,502,502,518]))
INFORMED=['structure','bert','combined']
TASKS={'CAD_to_N2A':('CAD','Neuro-2a'),'N2A_to_CAD':('Neuro-2a','CAD')}
FOLDS=[0,1,2]
SEED=20261007
CORE=ROOT/'results/probabilistic_ranking_20260928/candidate_index.csv'
NEXT_ART=ROOT/'artifacts/generalization_next_20261007'
META=['intervention_id','dataset','cell_type','endpoint_class','parent_context_id',
      'biological_component','gene_transcript','held_parent_fold','parent_sequence','mutant_sequence']


def save(path,payload):
    path=Path(path).resolve()
    assert any(path.is_relative_to(root) for root in (SRC,OUT,REP,ART))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): assert path.read_bytes()==payload,'Preserve '+str(path)
    else: path.write_bytes(payload)


def jsave(path,data):
    save(path,(json.dumps(clean(data),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())


def csvsave(path,frame,compressed=False):
    data=frame.to_csv(index=False,lineterminator='\n').encode()
    save(path,gzip.compress(data,mtime=0) if compressed else data)


def matrixsave(path,matrix):
    assert np.isfinite(matrix).all()
    buffer=io.BytesIO();np.savez_compressed(buffer,features=np.asarray(matrix))
    save(path,buffer.getvalue())


def load(outcomes=True):
    fields=META+(['measured_delta'] if outcomes else [])
    core=pd.read_csv(CORE,usecols=fields,low_memory=False)
    assert len(core)==26258 and core.intervention_id.is_unique
    core['original_core_row']=np.arange(len(core))
    frame=core[core.dataset.eq('mikl_gse173098')].reset_index(drop=True)
    assert len(frame)==13781 and set(frame.cell_type)=={'CAD','Neuro-2a'}
    assert set(frame.endpoint_class)=={'projection'} and set(frame.held_parent_fold)==set(FOLDS)
    assert frame.groupby('biological_component').held_parent_fold.nunique().eq(1).all()
    assert frame.biological_component.nunique()==187
    return frame,None


def freeze_check():
    from src.generalization_20261007.verify import preservation
    preservation()
    path=OUT/'prefit_manifest.json';manifest=readj(path)
    for name,checksum in manifest['files'].items(): assert sha256(ROOT/name)==checksum,name
    assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
    return manifest
