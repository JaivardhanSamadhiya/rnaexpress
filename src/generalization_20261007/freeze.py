from .common import *

def run():
    assert not (OUT/'prefit_manifest.json').exists()
    assert not any((OUT/track/'fits').exists() for track in TRACKS),'No comparative fits before freeze'
    assert readj(OUT/'prepare_receipt.json')['status']=='PASS'
    assert readj(OUT/'tests_receipt_final.json')['status']=='PASS'
    paths=sorted(p for root in (SRC,REP) for p in root.glob('*') if p.is_file())
    paths+=sorted(ART.glob('*_features.npz'))
    paths+=sorted(ART.glob('endpoint_auxiliary*'))
    paths+=sorted(OUT.glob('endpoint_auxiliary*'))
    paths+=sorted(OUT.glob('*_feature_receipt.json'))
    paths += [OUT/'prepare_receipt.json',OUT/'row_index.csv.gz',OUT/'initial_state.json',OUT/'tests_receipt_final.json']
    paths += [ROOT/'results/probabilistic_ranking_20260928/prefit_manifest.json',
              ROOT/'results/cross_assay_20260927/development_freeze.json']
    jsave(OUT/'prefit_manifest.json',{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'status':'PREFIT_FROZEN','no_fits_exist':True,'no_new_independent_validation':True})
    print('Frozen',len(paths),'files. Commit this manifest before running tracks.',flush=True)

if __name__=='__main__':run()
