"""Distinct committed design, fitting, and represented-evaluation freezes."""
from .common import *

def tests_check():
    receipt=readj(OUT/'synthetic_tests_receipt_v2.json')
    assert receipt['status']=='PASS' and receipt['numeric_imports']==receipt['models_fit']==receipt['project_reads']==0
    assert set(receipt['source_hashes'])=={p.relative_to(ROOT).as_posix() for p in SRC.glob('*.py')}
    hash_files(receipt['source_hashes']);hash_files(receipt['attribute_hashes'])
    assert receipt['protocol_sha256']==sha256(REP/'protocol.md')

def base_paths():
    paths=[p for folder in (SRC,REP,ART) for p in folder.glob('*') if p.is_file()]
    paths += [OUT/'.gitattributes',OUT/'synthetic_tests_receipt_v2.json',OUT/'source_readiness_receipt_v2.json']
    feature=ROOT/'results/generalization_conservation_feature_blocks_20261008/preparation_manifest.json'
    committed(feature);initial=readj(feature);hash_files(initial['files'])
    paths += [feature]+[ROOT/name for name in initial['files']]
    metadata=ROOT/'results/generalization_rbp_cellaxis_20261007/metadata_receipt.json'
    committed(metadata);oldmeta=readj(metadata);hash_files(oldmeta['files'])
    paths += [metadata]+[ROOT/name for name in oldmeta['files']]
    paths += [ROOT/name for name in (
        'src/generalization_campaign_20261007/crosscell_numeric_score_audit.py',
        'src/generalization_rbp_20261007/canonical_inner_replay.py','src/generalization_rbp_20261007/inner_replay.py',
        'src/generalization_knowncell_20261007/verify.py','src/generalization_knowncell_20261007/freeze.py',
        'src/generalization_20261007/common.py','src/cross_assay_20260927/common.py',
        'src/generalization_rbp_cellaxis_20261007/common.py','src/generalization_crosscell_20261007/common.py',
        'src/generalization_crosscell_20261007/splits.py','src/generalization_crosscell_20261007/bootstrap.py',
        'src/generalization_crosscell_20261007/verify.py','src/generalization_knowncell_20261007/splits.py',
        'src/generalization_knowncell_20261007/canonical_paired_contrast.py',
        'src/generalization_20261007/route_scaling.py','src/cross_assay_20260927/models.py',
        'src/generalization_20261007/verify.py')]
    return paths

def design():
    assert not DESIGN.exists() and not PREFIT.exists() and not (OUT/'control_reuse_receipt.json').exists()
    tests_check();ready=readj(OUT/'source_readiness_receipt_v2.json')
    assert ready['status']=='PASS_SOURCE_STATIC_READINESS' and ready['models_fit']==0
    paths=base_paths()
    own=[p for folder in (SRC,REP,ART) for p in folder.glob('*') if p.is_file()]
    own += [OUT/name for name in ('.gitattributes','synthetic_tests_receipt_v2.json','source_readiness_receipt_v2.json')]
    jsave(DESIGN,{'status':'FROZEN_CONSERVATION_CELLAXIS_DOWNSTREAM_DESIGN',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'own_committed_files':[p.relative_to(ROOT).as_posix() for p in own],
        'tracks':s.TRACKS,'widths':s.WIDTHS,'eligible':s.INFORMED,'source_only_configs':s.CONFIGS,
        'new_fit_tracks':s.NEW_FIT_TRACKS,'new_checkpoints':168,'known_extra_fits':0,
        'localization_outcomes_read_at_design':False,'scientific_arrays_read_at_design':False,
        'fits_exist':False,'allows_fitting':False,'separate_prefit_required':True,
        'root_commit_explicit_start_required_for_admission':True})

def prefit(root_start=False):
    design_check(root_start);thread_check();resource_check();tests_check()
    assert not PREFIT.exists() and not (OUT/'crossed').exists()
    from .controls import check
    controls=check();inputs=input_check();frame=load()
    assert values_hash(frame.measured_delta)==controls['original_labels_sha256']
    assert rowhash(frame)==controls['row_ids_sha256'] and metadata_hash(frame)==controls['metadata_sha256']
    from .runtime_guard import make as runtime_make,check as runtime_check,SCIENTIFIC,PREFIX
    if not (OUT/'runtime_binding.json').exists():runtime_make()
    runtime_check();committed(SCIENTIFIC);runtime_receipt=readj(SCIENTIFIC);assert runtime_receipt['status']=='PASS'
    for name,expected in runtime_receipt['files'].items():assert sha256(PREFIX/name)==expected,name
    np,pd,*_=runtime();assert Path(np.__file__).resolve().is_relative_to(PREFIX.resolve())
    assert Path(pd.__file__).resolve().is_relative_to(PREFIX.resolve())
    paths=base_paths()+[DESIGN,CORE,SCIENTIFIC,OUT/'runtime_binding.json',OUT/'control_reuse_receipt.json',
        ROOT/'results/generalization_20261007/prefit_manifest.json',ROOT/'results/probabilistic_ranking_20260928/prefit_manifest.json',
        PREP_OUT/'metadata_receipt.json',PREP_OUT/'array_receipt.json']
    paths += [ROOT/name for name in controls['files']]
    paths += [ROOT/name for name in inputs['files']]+[ROOT/name for name in inputs['source_array_files']]
    paths += [ROOT/name for name in readj(PREP_OUT/'metadata_receipt.json')['files']]
    paths += [PREFIX/name for name in runtime_receipt['files']]+[Path(np.__file__),Path(pd.__file__),OLD_OUT/'prefit_manifest.json']
    jsave(PREFIT,{'status':'FROZEN_CONSERVATION_CELLAXIS_PREFIT','files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'tracks':s.TRACKS,'widths':s.WIDTHS,'eligible':s.INFORMED,'new_fit_tracks':s.NEW_FIT_TRACKS,
        'new_checkpoints':168,'source_only_configs':s.CONFIGS,'original_labels_sha256':values_hash(frame.measured_delta),
        'original_metadata_sha256':metadata_hash(frame),'row_ids_sha256':rowhash(frame),'numerical_threads':1,
        'checkpoint_creation_sha_required':True,'controls_no_refit':True,'reused_control_observed_bytes_not_retroactive_birth':True,
        'all_new_inner_outer_replay_required':True,'original_full_shape_canonical_ID_ties':True,
        'known_extra_fits':0,'independent_confirmation':False,'root_commit_before_fitting':True})

def evaluation(root_start=False):
    assert root_start;prefit_check();tests_check()
    assert not EVALUATION.exists() and not (OUT/'represented').exists()
    receipt=readj(OUT/'crossed_verification_receipt.json')
    assert receipt['status']=='PASS' and receipt['prefit_sha256']==sha256(PREFIT)
    assert receipt['new_inner_replayed']==144 and receipt['new_outer_replayed']==24
    assert receipt['source_configs_independently_reselected'] and receipt['canonical_exact_ID_ties_preserved']
    hash_files(receipt['files']);frame=load()
    from src.generalization_knowncell_20261007.splits import masks
    for task in s.KNOWN_TASKS:
        for fold in s.FOLDS:masks(frame,task,fold)
    paths=base_paths()+[PREFIT,OUT/'crossed_verification_receipt.json']+[ROOT/name for name in receipt['files']]
    paths += [ROOT/name for name in readj(OUT/'control_reuse_receipt.json')['files']]
    paths += [ROOT/name for name in input_check()['files']]
    jsave(EVALUATION,{'status':'FROZEN_CONSERVATION_CELLAXIS_REPRESENTED_EVALUATION',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},'tracks':s.TRACKS,
        'outer_predictors':36,'new_fits':0,'no_target_selection':True,
        'same_cell_complete_menu_allele_gene_component_safety':True,'source_checkpoints_unchanged':True,
        'separate_known_scope':True,'old_verdicts_unchanged':True,'independent_confirmation':False,'root_commit_before_known_outputs':True})

if __name__=='__main__':
    import sys
    command=sys.argv[1];assert command in ('design','prefit','evaluation')
    if command=='design':design()
    elif command=='prefit':prefit('--root-start' in sys.argv[2:])
    else:evaluation('--root-start' in sys.argv[2:])
