"""Validate any diagnostic checkpoint before resuming the frozen permutation runner."""
from .common import *
from .permutation import permute_training
from src.cross_assay_20260927.models import purge

def run():
    freeze_check()
    frame,_=load()
    for held in STUDIES:
        path=OUT/'permutation'/(held+'.json')
        if not path.exists(): continue
        test=frame.dataset.eq(held).to_numpy()
        train=purge(frame,~test,test)
        source=permute_training(frame.loc[train].reset_index(drop=True))
        fit=readj(path)
        assert fit['training_ids_sha256']==hashlib.sha256('|'.join(source.intervention_id).encode()).hexdigest()
        assert fit['permuted_labels_sha256']==hashlib.sha256(source.measured_delta.to_numpy().tobytes()).hexdigest()
        assert fit['config']=={'id':'fixed_permuted_05','penalty':.05,'scaling':'pair'}
    from .permutation import run as diagnostic
    diagnostic()

if __name__=='__main__': run()
