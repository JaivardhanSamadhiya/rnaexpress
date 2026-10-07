"""Separate root-reviewed prefit freeze; no estimator fitting."""
from .common import *


def run():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not (OUT/'prefit_manifest.json').exists()
    assert not any((OUT/track/'fits').exists() for track in TRACKS)
    assert readj(OUT/'feature_admission_receipt.json')['status'] == 'PASS'
    tests=readj(OUT/'tests_receipt_v3.json'); assert tests['status']=='PASS'
    for filename,expected in tests['source_hashes'].items(): assert sha256(SRC/filename)==expected,filename
    binding = readj(OUT/'runtime_binding.json')
    paths = [p for directory in (SRC,OUT,REP,ART) for p in directory.glob('*') if p.is_file()]
    paths += [CORE, LINEAR_OUT/'prefit_manifest.json',
              ROOT/'src/generalization_crosscell_20261007/splits.py',
              ROOT/'src/generalization_crosscell_20261007/verify.py',
              ROOT/'src/generalization_crosscell_20261007/common.py',
              ROOT/'src/generalization_20261007/common.py', ROOT/'src/generalization_20261007/verify.py',
              ROOT/'src/cross_assay_20260927/models.py', ROOT/'src/cross_assay_20260927/common.py',
              ROOT/'src/research_20260921/common.py', ROOT/'results/generalization_20261007/prefit_manifest.json']
    paths += [FEATURE_ART/(track+'_model_features.npz') for track in FEATURE_TRACKS]
    paths += [Path(path) for path in binding['files']]
    assert all(sha256(path) == expected for path,expected in binding['files'].items())
    jsave(OUT/'prefit_manifest.json', {'status': 'FROZEN_PREFIT',
        'files': {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p)
                  for p in sorted(set(paths))},
        'tracks': TRACKS, 'checkpoints': 588, 'max_boosting_iterations': 58800,
        'threads': 1, 'estimator_fits_started': False, 'independent_confirmation': False,
        'linear_crosscell_and_four_source_gates_unchanged': True})
    print('Nonlinear prefit manifest written; root review/commit required before fitting', flush=True)


if __name__ == '__main__': run()
