from src.cross_assay_20260927.common import ROOT,sha256,clean,readj,np,pd
from src.cross_assay_20260927.common import frozen as legacy_frozen
from pathlib import Path
import json,hashlib,itertools,gzip,io,subprocess
from scipy.special import expit,ndtr,log_ndtr,betainc
SRC=ROOT/'src/probabilistic_ranking_20260928';OUT=ROOT/'results/probabilistic_ranking_20260928';ART=ROOT/'artifacts/probabilistic_ranking_20260928';REP=ROOT/'reports/probabilistic_ranking_20260928'
OLD=ROOT/'results/cross_assay_20260927';OA=ROOT/'artifacts/cross_assay_20260927'
PRIMARY=['H0','P1','P2','P3'];SECONDARY=['Hraw','P2_weighted','Partial','H0_pairfree','P2_pairfree','P3_hetero'];STUDIES=['astrocyte_gse330741','mikl_gse173098','moffatt_gse334718','srle'];TOL=1e-12
def save(p,data):
    p=Path(p).resolve();assert any(p.is_relative_to(d) for d in (OUT,ART,REP,SRC))
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data,'Preserve '+str(p)
    else:p.write_bytes(data)
def jsave(p,obj):save(p,(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csvsave(p,f,compressed=False):
    data=f.to_csv(index=False,lineterminator='\n').encode();save(p,data)
    if compressed:save(str(p)+'.gz',gzip.compress(data,mtime=0))
def npzsave(p,**values):
    b=io.BytesIO();np.savez_compressed(b,**values);save(p,b.getvalue())
def load():
    f=pd.read_csv(OUT/'candidate_index.csv',low_memory=False)
    pairs=pd.read_csv(ART/'replicate_pairwise_evidence.csv',float_precision='round_trip')
    with np.load(ART/'data.npz') as a:x=a['features'].astype(float);r=a['replicates'].copy()
    return f,x,r,pairs
def frozen():
    legacy_frozen();m=readj(OUT/'prefit_manifest.json')
    for p,h in m['files'].items():assert sha256(ROOT/p)==h,p
    assert subprocess.check_output(['git','show','HEAD:results/probabilistic_ranking_20260928/prefit_manifest.json'],cwd=ROOT)==(OUT/'prefit_manifest.json').read_bytes()
    return m
def pair_stats(d):
    valid=np.isfinite(d);n=valid.sum(1);wins=(d>TOL).sum(1);loss=(d<-TOL).sum(1);ties=n-wins-loss
    mean=np.divide(np.nansum(d,axis=1),n,out=np.full(len(d),np.nan),where=n>0)
    ss=np.nansum((d-mean[:,None])**2,axis=1);var=np.divide(ss,n-1,out=np.full(len(d),np.nan),where=n>1)
    q1=np.divide(wins+.5*ties,n,out=np.full(len(d),np.nan),where=n>0);q2=(wins+.5*ties+.5)/(n+1)
    tail=1-betainc(wins+.5*ties+.5,loss+.5*ties+.5,.5)
    return {'n':n,'wins':wins,'losses':loss,'ties':ties,'mean':mean,'variance':var,'q1':q1,'q2':q2,'posterior_tail':tail}
def pair_weights(frame,pairs):
    u=frame[['dataset','biological_component','parent_context_id']].drop_duplicates();nc=u.groupby(['dataset','biological_component']).size();nu=u.groupby('dataset').biological_component.nunique();sizes=pairs.groupby('parent_context_id').size();nd=frame.dataset.nunique()
    w=np.array([1/(nd*nu[r.dataset]*nc[r.dataset,r.biological_component]*sizes[r.parent_context_id]) for r in pairs.itertuples()]);return w/w.sum()
def macro(frame,columns,keys=('stage','model','dataset')):
    return frame.groupby(list(keys)+['biological_component','parent_context_id'])[columns].mean().groupby(list(keys)+['biological_component']).mean().groupby(list(keys)).mean().reset_index()
def label(study):return {'astrocyte_gse330741':'Astrocyte','mikl_gse173098':'Mikl','moffatt_gse334718':'Moffatt','srle':'SRLE'}[study]
