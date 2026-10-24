"""Metadata-only child; proposed policy cannot authorize other stages here."""
import argparse
import os
import sys
import traceback
from . import common as c


def normalize_metadata_bundle(bundle):
    """Original JSON semantics only; unchanged annotator remains tuple-strict."""
    before = c.canonical(bundle)
    normalized = c.decode(before)
    after = c.canonical(normalized)
    assert before==after,'Original JSON serialization semantics changed'
    assert c.canonical(bundle['metadata'])==c.canonical(normalized['metadata'])
    assert c.canonical(bundle['contract'])==c.canonical(normalized['contract'])
    return normalized,{'status':'PASS_EXACT_ORIGINAL_JSON_METADATA_SERIALIZATION_NORMALIZATION',
        'before_canonical_sha256':c.sha(before),'after_canonical_sha256':c.sha(after),
        'metadata_canonical_sha256':c.sha(c.canonical(bundle['metadata'])),
        'contract_canonical_sha256':c.sha(c.canonical(bundle['contract'])),
        'only_original_JSON_tuple_to_array_semantics':True,'scientific_values_or_hashes_changed':False}


def run(stage, parent_pid, expected_sha, birth_sha):
    assert stage in c.IMPLEMENTED_STAGES
    evidence = {'parent_pid': parent_pid, 'birth_sha256': birth_sha}
    c.admit_authorization(expected_sha)
    c.verify_owner(stage, expected_sha, evidence)
    assert not c.METADATA_BUNDLE.exists()
    assert not (c.OUT / (stage + '_worker_completion.json')).exists()
    from src.generalization_pum_process_probe_20261021 import headless
    assert c.resource_failure(headless.memory(), 0) is None
    from .calibration import calibrated
    with calibrated(stage, expected_sha, evidence) as session:
        from src.generalization_knowncell_joint_loader_20261022.loader import load_metadata
        bundle = load_metadata(root_start=True)
        assert bundle['numeric_outcome_rows_admitted'] == bundle['actual_feature_reads'] == bundle['models_fitted'] == 0
        assert not any(name.split('.')[0] in ('numpy', 'pandas', 'scipy', 'torch', 'openvino', 'sklearn') for name in sys.modules)
        bundle,normalization = normalize_metadata_bundle(bundle)
        bundle = session.annotate(bundle)
        assert c.sha(c.canonical(bundle['metadata']))==normalization['metadata_canonical_sha256']
        assert c.sha(c.canonical(bundle['contract']))==normalization['contract_canonical_sha256']
        bundle['metadata_serialization_normalization'] = normalization
        assert bundle['every_payload_open_fresh_original_resource_gated'] is False
        for value in bundle['payload_reads'].values():
            assert value['fresh_original_resource_gate_before_open'] is False
        c.verify_sources(expected_sha)
        assert c.resource_failure(headless.memory(), 0) is None
        bundle_sha = c.save_new(c.METADATA_BUNDLE, bundle)
    assert session.restored is True and session.calls > 0
    c.verify_sources(expected_sha)
    c.verify_owner(stage, expected_sha, evidence)
    assert c.resource_failure(headless.memory(), 0) is None
    c.save_new(c.OUT / (stage + '_worker_completion.json'), {
        'status': 'PASS_CALIBRATED_METADATA_WORKER_CALLBACKS_RESTORED',
        'execution_manifest_sha256': expected_sha, 'birth_sha256': birth_sha,
        'metadata_bundle_sha256': bundle_sha, 'metadata_admission_sha256': bundle['metadata_admission_sha256'],
        'row_ids_sha256': bundle['metadata']['row_ids_sha256'], 'metadata_sha256': bundle['contract']['metadata_sha256'],
        'numerical_outcome_rows_admitted': 0, 'actual_feature_reads': 0, 'model_fits': 0,
        'scientific_packages_imported': False, 'callbacks_restored': True, 'fresh_calibrated_guard_calls': session.calls,
        'metadata_serialization_normalization':normalization,
        'original_resource_manifest_sha256':c.ORIGINAL_MANIFEST_SHA,
        'original_resource_authorization_sha256':c.ORIGINAL_AUTH_SHA,
        'resource_policy': c.resource_policy(), 'original_3GiB_resource_guard_unchanged': False,
        'scientific_protocol_settings_changed': False, 'source_mode': c.source_mode()})
    c.verify_sources(expected_sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=c.IMPLEMENTED_STAGES)
    parser.add_argument('parent_pid', type=int)
    parser.add_argument('manifest_sha')
    parser.add_argument('birth_sha')
    args = parser.parse_args()
    assert os.getppid() == args.parent_pid
    c.admit_authorization(args.manifest_sha)
    c.verify_owner(args.stage, args.manifest_sha, {'parent_pid': args.parent_pid, 'birth_sha256': args.birth_sha})
    with (c.OUT / (args.stage + '_worker.log')).open('x', encoding='utf-8') as log:
        sys.stdout = sys.stderr = log
        try:
            run(args.stage, args.parent_pid, args.manifest_sha, args.birth_sha)
        except BaseException:
            traceback.print_exc()
            raise


if __name__ == '__main__':
    main()
