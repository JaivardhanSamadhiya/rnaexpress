"""Separate committed design, fitting and postfit represented evaluation freezes."""
from .common import *


def tests_check():
    receipt=readj(OUT/'synthetic_tests_receipt_v3.json')
    assert receipt['status']=='PASS' and receipt['numeric_imports']==receipt['models_fit']==receipt['project_reads']==0
    assert set(receipt['source_hashes'])=={p.relative_to(ROOT).as_posix() for p in SRC.glob('*.py')}
    hash_files(receipt['source_hashes']);hash_files(receipt['attribute_hashes'])
    assert receipt['protocol_sha256']==sha256(REP/'protocol.md')


def base_paths():
    paths=[p for folder in (SRC,REP,ART) for p in folder.glob('*') if p.is_file()]
    paths+=[OUT/'.gitattributes',OUT/'synthetic_tests_receipt.json',OUT/'synthetic_tests_receipt_v2.json',
            OUT/'synthetic_tests_receipt_v3.json',OUT/'source_readiness_receipt.json',OUT/'source_readiness_receipt_v2.json',
            OUT/'source_readiness_receipt_v3.json',PREP_OUT/'preparation_manifest.json']
    initial=readj(PREP_OUT/'preparation_manifest.json')
    hash_files(initial['files']);paths += [ROOT/name for name in initial['files']]
    paths += [ROOT/name for name in ('src/generalization_campaign_20261007/crosscell_numeric_score_audit.py',
        'src/generalization_rbp_20261007/canonical_inner_replay.py','src/generalization_rbp_20261007/inner_replay.py',
        'src/generalization_knowncell_20261007/verify.py','src/generalization_knowncell_20261007/freeze.py',
        'src/generalization_20261007/common.py','src/cross_assay_20260927/common.py')]
    return paths


def design():
    assert not DESIGN.exists() and not PREFIT.exists() and not (OUT/'control_reuse_receipt.json').exists()
    tests_check();paths=base_paths()
    jsave(DESIGN,{'status':'FROZEN_RBP_CELLAXIS_DOWNSTREAM_DESIGN',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'own_committed_files':[p.relative_to(ROOT).as_posix() for folder in (SRC,REP,ART) for p in folder.glob('*') if p.is_file()]+[(OUT/name).relative_to(ROOT).as_posix() for name in
            ('synthetic_tests_receipt.json','synthetic_tests_receipt_v2.json','synthetic_tests_receipt_v3.json',
             'source_readiness_receipt.json','source_readiness_receipt_v2.json','source_readiness_receipt_v3.json','.gitattributes')],
        'tracks':s.TRACKS,'widths':s.WIDTHS,'eligible':s.INFORMED,'source_only_configs':s.CONFIGS,
        'new_fit_tracks':s.NEW_FIT_TRACKS,'new_checkpoints':168,'known_extra_fits':0,
        'project_reads_at_design':0,'fits_exist':False,'allows_fitting':False,
        'root_commit_explicit_start_required_for_admission':True,'separate_prefit_required':True})


def prefit(root_start=False):
    design_check(root_start);thread_check();resource_check();tests_check()
    assert not PREFIT.exists() and not (OUT/'crossed').exists()
    from .controls import check
    controls=check();inputs=input_check();frame=load()
    assert values_hash(frame.measured_delta)==controls['original_labels_sha256']
    assert rowhash(frame)==controls['row_ids_sha256'] and metadata_hash(frame)==controls['metadata_sha256']
    from .runtime_guard import make as runtime_make,check as runtime_check
    if not (OUT/'runtime_binding.json').exists():runtime_make()
    runtime_check()
    scientific=ROOT/'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
    committed(scientific);runtime_receipt=readj(scientific);assert runtime_receipt['status']=='PASS'
    science_root=ROOT/'data/interim/mechanism_v2/runtime'
    for name,expected in runtime_receipt['files'].items():assert sha256(science_root/name)==expected,name
    np,pd,*_=runtime();assert Path(np.__file__).resolve().is_relative_to(science_root.resolve())
    assert Path(pd.__file__).resolve().is_relative_to(science_root.resolve())
    paths=base_paths()+[DESIGN,CORE,scientific,OUT/'runtime_binding.json',OUT/'control_reuse_receipt.json',
        ROOT/'results/generalization_20261007/prefit_manifest.json',ROOT/'results/probabilistic_ranking_20260928/prefit_manifest.json',
        PREP_OUT/'metadata_receipt.json',PREP_OUT/'array_receipt.json']
    paths += [ROOT/name for name in controls['files']]
    paths += [ROOT/name for name in inputs['files']]+[ROOT/name for name in inputs['source_array_files']]
    paths += [ROOT/name for name in readj(PREP_OUT/'metadata_receipt.json')['files']]
    paths += [science_root/name for name in runtime_receipt['files']]
    paths += [ROOT/'results'/name/'prefit_manifest.json' for name in
              ('generalization_crosscell_20261007','generalization_rbp_20261007','generalization_joint_accessibility_20261007')]
    paths += [Path(np.__file__),Path(pd.__file__)]
    jsave(PREFIT,{'status':'FROZEN_RBP_CELLAXIS_PREFIT','files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'tracks':s.TRACKS,'widths':s.WIDTHS,'eligible':s.INFORMED,'new_fit_tracks':s.NEW_FIT_TRACKS,
        'new_checkpoints':168,'source_only_configs':s.CONFIGS,'original_labels_sha256':values_hash(frame.measured_delta),
        'original_metadata_sha256':metadata_hash(frame),'row_ids_sha256':rowhash(frame),
        'numerical_threads':1,'checkpoint_creation_sha_required':True,'controls_no_refit':True,
        'reused_control_observed_bytes_not_retroactive_birth':True,'all_new_inner_outer_replay_required':True,
        'original_full_shape_canonical_ID_ties':True,'known_extra_fits':0,'independent_confirmation':False,
        'root_commit_before_fitting':True})


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
    jsave(EVALUATION,{'status':'FROZEN_RBP_CELLAXIS_REPRESENTED_EVALUATION',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))},
        'tracks':s.TRACKS,'outer_predictors':36,'new_fits':0,'no_target_selection':True,
        'same_cell_complete_menu_allele_gene_component_safety':True,'source_checkpoints_unchanged':True,
        'separate_known_scope':True,'old_verdicts_unchanged':True,'independent_confirmation':False,
        'root_commit_before_known_outputs':True})


if __name__=='__main__':
    import sys
    command=sys.argv[1];assert command in ('design','prefit','evaluation')
    if command=='design':design()
    elif command=='prefit':prefit('--root-start' in sys.argv[2:])
    else:evaluation('--root-start' in sys.argv[2:])
