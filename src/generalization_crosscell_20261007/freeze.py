"""Commit complete certified feature matrices and protocol before any fits."""
from .common import *


def run():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT/t/'fits').exists() for t in TRACKS)
    assert not (OUT/'prefit_manifest.json').exists()
    assert readj(OUT/'prepare_receipt.json')['status']=='PASS'
    assert readj(OUT/'tests_receipt.json')['status']=='PASS'
    paths=[p for directory in (SRC,REP,ART,OUT) for p in directory.glob('*') if p.is_file()]
    paths += [CORE,ROOT/'results/generalization_20261007/prefit_manifest.json',
        ROOT/'results/generalization_next_20261007/prefit_manifest.json',
        ROOT/'results/generalization_next_20261007/short_feature_receipt.json',
        ROOT/'src/generalization_20261007/route_scaling.py',ROOT/'src/generalization_20261007/common.py',
        ROOT/'src/generalization_20261007/verify.py',ROOT/'src/cross_assay_20260927/models.py',
        ROOT/'src/cross_assay_20260927/common.py',ROOT/'src/research_20260921/common.py']
    paths += [NEXT_ART/(track+'_model_features.npz') for track in TRACKS if track!='simple']
    jsave(OUT/'prefit_manifest.json',{'status':'FROZEN_PREFIT',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'tracks':TRACKS,'checkpoints':294,'numerical_threads':1,
        'project_fits_started':False,'independent_confirmation':False,'four_source_gate_unchanged':True})
    print('Prefit frozen; root review/commit required before fitting',flush=True)


if __name__=='__main__':run()
