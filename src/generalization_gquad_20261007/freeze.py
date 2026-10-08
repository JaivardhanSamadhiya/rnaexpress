"""Separate admission stages; freezing never performs extraction or fitting."""
import sys
from .guards import *
from .spec import SPEC, TRACKS, SHAPES, ENDPOINT_SIGNS, INCREMENTAL

def paths():
    values = [p for folder in (SRC, REP) for p in folder.glob('*') if p.is_file()]
    values += [OUT / '.gitattributes', ART / '.gitattributes', OUT / 'synthetic_tests_receipt_final.json',
        OUT / 'preparation_receipt.json', OUT / 'row_index.csv.gz', ART / 'sequence_request_manifest.json',
        NEXT_OUT / 'prefit_manifest.json', NEXT_OUT / 'feature_production_manifest.json', NEXT_OUT / 'prepare_receipt.json',
        NEXT_OUT / 'short_feature_receipt.json', NEXT_ART / 'sequence_inventory.csv.gz', NEXT_ART / 'encoded_sequence_inventory.csv.gz',
        NEXT_ART / 'structure_postproduction_sha256_index.json', NEXT_OUT / 'structure_postproduction_audit_receipt.json',
        NEXT_OUT / 'structure_cache_production_receipt.json', NEXT_OUT / 'structure_config_v2.json',
        ROOT / 'artifacts/generalization_20261007/reporter_context_metadata.json',
        ROOT / 'src/generalization_20261007/common.py', ROOT / 'src/cross_assay_20260927/common.py',
        ROOT / 'src/research_20260921/common.py', ROOT / 'src/generalization_polarity_20261007/routes.py']
    values += list(source_control_paths().values())
    ready = readj(FEAS_OUT / 'readiness_receipt.json')
    values += [FEAS_OUT / 'readiness_receipt.json'] + [ROOT / name for field in ('files', 'prior_receipts') for name in canonical_map(ready[field])]
    backend = backend_check()
    values += [ROOT / name for field in ('source_files', 'source_code_and_declared_protocol') for name in canonical_map(backend[field])]
    values += [ROOT / name for name in canonical_map(backend['runtime']['files'])]
    return sorted(set(values))

def production():
    assert not (OUT / 'feature_production_manifest.json').exists() and not (ART / 'allele_cache').exists()
    assert not (OUT / 'features_receipt.json').exists() and not any((OUT / t / 'fits').exists() for t in TRACKS)
    tests_check(); backend_check(); source_control_paths(); structure_index_check(False)
    prep = readj(OUT / 'preparation_receipt.json'); assert prep['status'] == 'PASS' and prep['models_fit'] == prep['project_alleles_folded'] == 0
    assert not prep['labels_read'] and prep['rows'] == 26258 and prep['alleles'] == 18220
    assert prep['row_index_sha256'] == sha256(OUT / 'row_index.csv.gz')
    assert prep['sequence_request_manifest_sha256'] == sha256(ART / 'sequence_request_manifest.json')
    jsave(OUT / 'feature_production_manifest.json', {'status': 'FROZEN_GQUAD_FEATURE_PRODUCTION',
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths()}, 'spec': SPEC,
        'rows': 26258, 'alleles': 18220, 'shapes': SHAPES, 'production_threads': 1,
        'both_ensembles_fresh_required': True, 'ordinary_structure_actual_SHA_before_after_required': True,
        'immutable_first_creation_digests_required': True, 'root_commit_and_start_signal_required': True,
        'project_features_exist': False, 'project_outcomes_read': False, 'supervised_fits_authorized': False})
    print('GQ production freeze created; root commit/start required before production', flush=True)

def prefit():
    # Label admission occurs only here, after completed production/assembly.
    from .common import input_check, load, metadata_identity, label_hash
    from .routes import endpoint_sign
    from .common import np
    production_check(); tests_check(); backend_check(); source_control_paths(); receipt = input_check()
    assert not (OUT / 'prefit_manifest.json').exists() and not any((OUT / t / 'fits').exists() for t in TRACKS)
    frame = load(); assert metadata_identity(frame) == receipt['original_metadata_sha256']
    values = paths() + [OUT / 'feature_production_manifest.json', OUT / 'features_receipt.json', OUT / 'input_receipt.json',
        ART / 'cache_index.json', CORE, ROOT / 'results/generalization_20261007/prefit_manifest.json',
        ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json',
        ROOT / 'src/generalization_20261007/route_scaling.py', ROOT / 'src/cross_assay_20260927/models.py',
        ROOT / 'src/generalization_next_20261007/bootstrap.py',
        ROOT / 'artifacts/cross_assay_20260927/model_comparison.csv', ROOT / 'results/cross_assay_20260927/decision_metrics.csv',
        ROOT / 'src/generalization_splicebert_downstream_20261007/engine.py',
        ROOT / 'src/generalization_splicebert_downstream_20261007/verify.py',
        ROOT / 'src/generalization_splicebert_downstream_20261007/gate.py']
    values += [ROOT / name for name in receipt['files']]
    for entry in readj(ART / 'cache_index.json')['alleles']:
        values += [ROOT / entry['path'], ROOT / entry['birth_path']]
    # Pin the actual imported numerical package origin used by the frozen solver.
    values += [Path(np.__file__), ROOT / 'data/interim/mechanism_v2/runtime/numpy/core/_multiarray_umath.cp312-win_amd64.pyd']
    assert np.__version__ == '1.26.4' and Path(np.__file__).is_relative_to(ROOT / 'data/interim/mechanism_v2/runtime')
    jsave(OUT / 'prefit_manifest.json', {'status': 'FROZEN_GQUAD_PREFIT',
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(set(values))},
        'tracks': TRACKS, 'shapes': SHAPES, 'fits_per_track': 40, 'primary_fit_checkpoints': 200,
        'control_fitting_policy': 'STANDALONE_ALL_FIVE_NO_CHECKPOINT_REUSE',
        'original_labels_sha256': label_hash(frame.measured_delta),
        'aligned_labels_sha256': label_hash(frame.measured_delta.to_numpy(float) * endpoint_sign(frame)),
        'original_metadata_identity_sha256': metadata_identity(frame),
        'endpoint_signs': ENDPOINT_SIGNS, 'original_truths_unchanged': True,
        'source_only_three_penalties': [.005, .05, .5], 'numerical_threads': 1,
        'no_fits_exist': True, 'checkpoint_creation_SHA_sidecars_required': True,
        'all_inner_and_outer_replay_required': True, 'incremental_controls': INCREMENTAL,
        'independent_confirmation': False, 'subsequent_observed_data_followup': True, 'root_commits_before_fitting': True})
    print('GQ prefit freeze created; root commit/start required before 200 fits', flush=True)

if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('production', 'prefit')
    production() if sys.argv[1] == 'production' else prefit()
