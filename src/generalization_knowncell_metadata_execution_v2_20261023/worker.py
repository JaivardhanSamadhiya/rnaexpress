"""Bound-hash metadata worker. Never admits labels, arrays or native packages."""
import argparse
import sys
import traceback
from .common import *


def admit(expected_sha):
    manifest=verify_sources(expected_sha)
    assert all(os.environ.get(key)=='1' for key in THREAD_KEYS)
    interpreter(manifest)
    return manifest


def run(expected_sha):
    admit(expected_sha)
    for path in (ROOT/BUNDLE,OUT/'worker_completion.json'):
        assert not path.exists(),'Preserve existing/partial outputs; no resume'
    from src.generalization_pum_process_probe_20261021 import headless
    assert resource_failure(headless.memory(),0) is None
    from src.generalization_knowncell_joint_loader_20261022.loader import load_metadata
    bundle=load_metadata(root_start=True)
    assert bundle['numeric_outcome_rows_admitted']==bundle['actual_feature_reads']==bundle['models_fitted']==0
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    verify_sources(expected_sha)
    assert resource_failure(headless.memory(),0) is None
    bundle_sha=save_new(ROOT/BUNDLE,bundle)
    verify_sources(expected_sha)
    assert resource_failure(headless.memory(),0) is None
    save_new(OUT/'worker_completion.json',{
        'status':'PASS_SOURCE_BOUND_ORIGINAL_FLOOR_METADATA_V2_WORKER',
        'initial_committed_execution_manifest_sha256':expected_sha,
        'metadata_bundle_sha256':bundle_sha,'row_ids_sha256':bundle['metadata']['row_ids_sha256'],
        'metadata_sha256':bundle['contract']['metadata_sha256'],
        'metadata_admission_sha256':bundle['metadata_admission_sha256'],
        'numeric_outcome_rows_admitted':0,'actual_feature_reads':0,'models_fitted':0,
        'scientific_packages_imported':False,'source_mode':source_mode(),
        'original_resource_guards_unchanged':True})
    verify_sources(expected_sha)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha',required=True)
    expected=parser.parse_args().manifest_sha
    # Validate the inherited creation identity BEFORE even creating worker.log.
    admit(expected)
    with (OUT/'worker.log').open('x',encoding='utf-8') as log:
        sys.stdout=sys.stderr=log
        try:run(expected)
        except BaseException:
            traceback.print_exc();raise


if __name__=='__main__':main()
