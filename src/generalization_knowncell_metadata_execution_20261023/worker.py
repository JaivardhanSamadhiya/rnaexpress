"""One bounded metadata-only worker; no numerical package is imported."""
import sys
import traceback
from .common import *


def run():
    manifest = verify_sources(json.loads(MANIFEST.read_bytes()))
    assert all(os.environ.get(key) == '1' for key in THREAD_KEYS)
    assert Path(sys.executable).resolve() == Path(manifest['python_executable']).resolve()
    for name, expected in manifest['python_native_files'].items():
        assert sha(Path(name).read_bytes()) == expected, name
    for path in (ROOT/BUNDLE, OUT/'worker_completion.json'):
        assert not path.exists(), 'Preserve prior outputs; no resume'
    from src.generalization_pum_process_probe_20261021 import headless
    assert resource_failure(headless.memory(), 0) is None
    from src.generalization_knowncell_joint_loader_20261022.loader import load_metadata
    bundle = load_metadata(root_start=True)
    assert bundle['numeric_outcome_rows_admitted'] == bundle['actual_feature_reads'] == bundle['models_fitted'] == 0
    assert not any(name.split('.')[0] in ('numpy', 'pandas', 'scipy') for name in sys.modules)
    verify_sources(manifest)
    assert resource_failure(headless.memory(), 0) is None
    bundle_sha = save_new(ROOT/BUNDLE, bundle)
    save_new(OUT/'worker_completion.json', {
        'status': 'PASS_ORIGINAL_FLOOR_METADATA_ONLY_WORKER',
        'execution_manifest_sha256': sha(MANIFEST.read_bytes()),
        'metadata_bundle_sha256': bundle_sha, 'row_ids_sha256': bundle['metadata']['row_ids_sha256'],
        'metadata_sha256': bundle['contract']['metadata_sha256'],
        'numeric_outcome_rows_admitted': 0, 'actual_feature_reads': 0, 'models_fitted': 0,
        'scientific_packages_imported': False, 'original_resource_guards_unchanged': True,
    })


if __name__ == '__main__':
    with (OUT/'worker.log').open('x', encoding='utf-8') as log:
        sys.stdout = sys.stderr = log
        try:
            run()
        except BaseException:
            traceback.print_exc()
            raise
