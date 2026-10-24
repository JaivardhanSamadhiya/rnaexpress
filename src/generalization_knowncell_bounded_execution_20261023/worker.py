"""Metadata-only child; proposed policy cannot authorize other stages here."""
import argparse
import os
import sys
import traceback
from . import common as c


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
        bundle = session.annotate(bundle)
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
