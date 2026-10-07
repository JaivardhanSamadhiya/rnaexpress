"""Reconstruct every inner training roster from original metadata."""
from .common import *
from .routes import module
from src.cross_assay_20260927.models import purge

def run():
    freeze_check()
    frame,_=load(); checked=0
    for track in TRACKS:
        for held in STUDIES:
            test=frame.dataset.eq(held).to_numpy()
            source=frame.loc[purge(frame,~test,test)].reset_index(drop=True)
            for inner in sorted(source.dataset.unique()):
                validation=source.dataset.eq(inner).to_numpy()
                training=source.loc[purge(source,~validation,validation)].reset_index(drop=True)
                checksum=hashlib.sha256('|'.join(training.intervention_id).encode()).hexdigest()
                for config in module(track).CONFIGS:
                    fit=readj(OUT/track/'fits'/(held+'__inner__'+inner+'_'+config['id']+'.json'))
                    assert fit['_config']==config and fit['_training_ids_sha256']==checksum
                    assert fit['_training_studies']==sorted(training.dataset.unique())
                    assert fit['_training_components']==sorted(training.biological_component.unique())
                    assert not {held,inner}&set(fit['_training_studies'])
                    assert fit['training_rows']==len(training)
                    checked+=1
    assert checked==216
    jsave(OUT/'inner_roster_audit.json', {'status':'PASS','checkpoints_checked':checked,
        'global_component_and_original_exact_allele_purge_reconstructed':True,
        'code_sha256':sha256(Path(__file__))})

if __name__=='__main__': run()
