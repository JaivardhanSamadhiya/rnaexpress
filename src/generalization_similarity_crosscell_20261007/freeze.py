"""A new complete supervised prefit manifest; root commits before fitting."""
from .experiment_common import *

def run():
    from src.generalization_20261007.verify import preservation
    preservation();assert not (OUT/'prefit_manifest.json').exists()
    assert not any((OUT/track/'fits').exists() for track in TRACKS)
    admission=readj(OUT/'feature_admission_receipt.json');assert admission['status']=='PASS'
    tests=readj(OUT/'experiment_tests_receipt_v2.json');assert tests['status']=='PASS'
    for name,digest in tests['source_hashes'].items():assert sha256(ROOT/name)==digest
    graph=readj(OUT/'metadata_graph_receipt.json')
    for name,digest in graph['source_hashes'].items():assert sha256(ROOT/name)==digest
    preanalysis=readj(OUT/'preanalysis_manifest.json')
    assert sha256(REP/'protocol.md')==preanalysis['protocol_sha256']
    paths=[path for directory in (SRC,OUT,ART,REP) for path in directory.glob('*') if path.is_file()]
    paths += [ROOT/name for name in admission['feature_files']]
    paths += [ROOT/name for name in graph['runtime']['files']]
    paths += [ROOT/name for name in readj(OUT/'numerical_runtime_binding.json')['files']]
    paths += [CORE,UNPURGED_OUT/'prefit_manifest.json',ROOT/'results/generalization_next_20261007/prefit_manifest.json']
    for name in ['generalization_20261007/route_scaling.py','generalization_20261007/common.py','generalization_20261007/verify.py',
                 'generalization_crosscell_20261007/common.py','generalization_crosscell_20261007/splits.py',
                 'generalization_crosscell_20261007/bootstrap.py','cross_assay_20260927/models.py','cross_assay_20260927/common.py','research_20260921/common.py']:
        paths.append(ROOT/'src'/name)
    # Pin already-certified numerical runtime files used by the matched original solver.
    numerical=readj(UNPURGED_OUT/'prefit_manifest.json')
    paths += [ROOT/name for name in numerical['files'] if name.startswith('data/interim/mechanism_v2/runtime/')]
    critical=[path for path in paths if path.is_relative_to(SRC) or path.is_relative_to(REP) or path.is_relative_to(ART) or path.is_relative_to(OUT)]
    critical += [ROOT/name for name in graph['runtime']['files']]
    critical += [ROOT/name for name in readj(OUT/'numerical_runtime_binding.json')['files']]
    critical += [path for path in paths if path.is_relative_to(ROOT/'src')]
    jsave(OUT/'prefit_manifest.json',{'status':'FROZEN_PREFIT','tracks':TRACKS,'checkpoints':294,
        'files':{path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(set(paths))},
        'critical_files':{path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(set(critical))},
        'numerical_threads':1,'checkpoint_adoption':False,'primary_distance_cutoff':30,
        'global_similarity_family_exclusion':True,'bootstrap_gate_unit':'original gene',
        'family_cluster_bootstrap':'additional required lowerbound>0, same equal-gene point estimand',
        'full_preservation_checks':'run start/end, verification and gate; small critical hashes at each checkpoint',
        'project_fits_started':False,'independent_confirmation':False,'four_source_gate_unchanged':True})
    print('Similarity supervised prefit manifest ready for root commit; no fit',flush=True)

if __name__=='__main__':run()
