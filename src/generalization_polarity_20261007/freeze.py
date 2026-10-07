"""Hash all fixed source, inputs, protocol and tests before comparative fitting."""
from .common import *


def run():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT / track / 'fits').exists() for track in TRACKS)
    assert not (OUT/'prefit_manifest.json').exists(), 'Preserve existing freeze'
    assert readj(OUT/'prepare_receipt.json')['status'] == 'PASS'
    assert readj(OUT/'tests_receipt.json')['status'] == 'PASS'
    dependencies = [
        CORE, BASE, ROOT/'results/generalization_next_20261007/short_feature_receipt.json',
        ROOT/'results/generalization_20261007/prefit_manifest.json',
        ROOT/'artifacts/generalization_20261007/delivery_receipt.json',
        ROOT/'artifacts/generalization_20261007/reporter_context_metadata.json',
        ROOT/'src/generalization_20261007/common.py',
        ROOT/'src/generalization_20261007/route_scaling.py',
        ROOT/'src/generalization_20261007/verify.py',
        ROOT/'src/cross_assay_20260927/models.py',
        ROOT/'src/cross_assay_20260927/common.py',
        ROOT/'src/research_20260921/common.py',
        ROOT/'artifacts/cross_assay_20260927/model_comparison.csv',
        ROOT/'results/cross_assay_20260927/decision_metrics.csv',
    ]
    paths = dependencies + [p for directory in (SRC,REP,ART,OUT)
                            for p in directory.glob('*') if p.is_file()]
    paths = sorted(set(paths))
    jsave(OUT/'prefit_manifest.json', {'status':'FROZEN_PREFIT',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'tracks':TRACKS,'comparative_fits':80,'numerical_threads':1,
        'no_comparative_fits_exist':True,'protected_outcomes_opened':False,
        'independent_confirmation':False})
    print('Frozen',len(paths),'files; commit before any fitting',flush=True)


if __name__ == '__main__': run()
