"""Record the initial state and build only sequence-derived features before fits."""
from .common import *
from .engine import module
from scipy import sparse
import io

def run():
    from src.probabilistic_ranking_20260928.common import frozen as previous_frozen
    previous_frozen()
    initial_path=OUT/'initial_state.json'
    if not initial_path.exists():
        changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
        receipts=[ROOT/'artifacts'/ns/'delivery_receipt.json' for ns in ('cross_assay_20260927','failure_audit_20260928','probabilistic_ranking_20260928')]
        jsave(initial_path,{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'unchanged_user_files':{p:sha256(ROOT/p) for p in changed},
            'previous_receipts':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha256(p)} for p in receipts],
            'new_authorization':'2026-10-07: reassess old correctness, research and work on distinct generalization routes in parallel',
            'no_spending':True,'reserved_outcomes_remain_closed':True})
    frame,base=load()
    for track in TRACKS:
        m=module(track)
        if hasattr(m,'prepare_auxiliary'):
            m.prepare_auxiliary()
        if (ART/(track+'_features.npz')).exists():
            receipt=readj(OUT/(track+'_feature_receipt.json'))
            assert sha256(ART/(track+'_features.npz'))==receipt['sha256']
            assert receipt['configurations']==m.CONFIGS
            print('Preserved prepared',track,receipt['shape'],flush=True)
            continue
        x=m.build_features(frame,base)
        b=io.BytesIO()
        if sparse.issparse(x):
            assert np.isfinite(x.data).all()
            sparse.save_npz(b,x)
        else:
            assert np.isfinite(x).all()
            np.savez_compressed(b,features=x)
        save(ART/(track+'_features.npz'),b.getvalue())
        jsave(OUT/(track+'_feature_receipt.json'),{'shape':list(x.shape),'sparse':bool(sparse.issparse(x)),
            'sha256':sha256(ART/(track+'_features.npz')),'configurations':m.CONFIGS,'built_before_fitting':True})
        print('Prepared',track,x.shape,flush=True)
    csvsave(OUT/'row_index.csv.gz',frame[['intervention_id','dataset','parent_context_id','biological_component']],True)
    jsave(OUT/'prepare_receipt.json',{'status':'PASS','rows':len(frame),'studies':STUDIES,
        'features_use':'admitted sequences and original feature rows only; no held-assay fitting','new_outcomes_opened':False})

if __name__=='__main__':run()
