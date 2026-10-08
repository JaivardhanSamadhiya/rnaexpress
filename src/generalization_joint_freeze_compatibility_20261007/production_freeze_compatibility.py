"""Root-start-only original freeze delegation with temporary separator adapter."""
from contextlib import contextmanager
import importlib
from pathlib import Path
import sys
from . import common as c


def make_reader(original_readj, expected_hash, target=c.OLD_FEAS, hasher=c.sha256):
    target = Path(target).resolve()

    def reader(path):
        if Path(path).resolve() != target:
            return original_readj(path)
        assert hasher(target) == expected_hash, 'Original feasibility bytes changed'
        original = original_readj(path)
        return c.normalized_receipt(original)

    return reader


def make_saver(original_jsave, extra_files, provenance, target=c.OLD_MANIFEST,
               exists=None, hasher=c.sha256):
    target = Path(target).resolve()
    exists = (lambda path: Path(path).exists()) if exists is None else exists
    called = []

    def saver(path, value):
        assert not called, 'Original manifest save may occur exactly once'
        assert Path(path).resolve() == target, 'Unexpected original freeze write destination'
        assert not exists(target), 'Preserve existing original production manifest'
        assert value['status'] == 'FROZEN_JOINT_ACCESSIBILITY_PRODUCTION'
        assert value['alleles'] == 18220 and value['rows'] == 26258
        assert value['tracks'] == ['duplicate_marginal', 'joint']
        assert value['shapes'] == {'base': 246, 'raw': 502, 'access': 758, 'duplicate_marginal': 1014, 'joint': 1014}
        assert value['production_threads'] == 1 and value['immutable_creation_digests_required'] is True
        assert value['synthetic_equivalence_atol'] == 1e-6 and value['synthetic_equivalence_rtol'] == 1e-5
        assert value['project_features_exist'] is False and value['fits_exist'] is False and value['project_outcomes_read'] is False
        assert 'path_compatibility' not in value and isinstance(value['files'], dict)
        enhanced = dict(value)
        enhanced['files'] = dict(value['files'])
        existing = c.normalize_path_keys(enhanced['files'])
        assert existing == enhanced['files'], 'Original new production files must remain canonical'
        normalized_extra = c.normalize_path_keys(extra_files)
        assert normalized_extra == extra_files
        for name, expected in extra_files.items():
            assert hasher(c.ROOT / name) == expected, 'Supplemental preparation changed: ' + name
            if name in enhanced['files']:
                assert enhanced['files'][name] == expected, 'Reject changed existing manifest entry'
            enhanced['files'][name] = expected
        enhanced['path_compatibility'] = dict(provenance)
        called.append(True)
        return original_jsave(path, enhanced)

    saver.calls = called
    return saver


@contextmanager
def temporary_bindings(module, reader, saver):
    original_readj, original_jsave = module.readj, module.jsave
    module.readj, module.jsave = reader, saver
    try:
        yield
    finally:
        module.readj, module.jsave = original_readj, original_jsave


def delegate_once(module, reader, saver):
    before = module.readj, module.jsave
    with temporary_bindings(module, reader, saver):
        module.production()
    assert module.readj is before[0] and module.jsave is before[1]
    assert len(saver.calls) == 1, 'Original production must perform its one immutable manifest write'


def run(root_start=False):
    assert root_start, 'Explicit root start required after independent review/commit'
    c.environment()
    manifest = c.check_preparation()
    c.no_original_outputs()
    assert not (c.OUT / 'execution_receipt.json').exists() and not (c.OUT / 'execution_failure_receipt.json').exists()
    original = importlib.import_module('src.generalization_joint_accessibility_20261007.freeze')
    assert Path(original.__file__).resolve() == (c.OLD_SRC / 'freeze.py').resolve()
    original_readj, original_jsave = original.readj, original.jsave
    extra = dict(manifest['files'])
    extra[c.MANIFEST.relative_to(c.ROOT).as_posix()] = c.sha256(c.MANIFEST)
    provenance = {'status': 'ADDITIVE_SEPARATOR_ONLY_COMPATIBILITY',
        'preparation_manifest': c.MANIFEST.relative_to(c.ROOT).as_posix(),
        'preparation_manifest_sha256': c.sha256(c.MANIFEST),
        'normalization_plan_sha256': c.sha256(c.NORMALIZATION),
        'original_feasibility_receipt_sha256': c.sha256(c.OLD_FEAS),
        'original_failure_log_sha256': c.sha256(c.FAILURE_LOG),
        'adapted_read': 'only synthetic_feasibility_receipt.source_sha256 keys, backslash to slash, collision rejection',
        'original_production_function_calls': 1, 'original_sources_modified': False,
        'original_admission_checks_delegated_unchanged': True,
        'supplemental_chain_rechecked_by_original_production_and_prefit': True}
    reader = make_reader(original_readj, c.sha256(c.OLD_FEAS))
    saver = make_saver(original_jsave, extra, provenance)
    try:
        delegate_once(original, reader, saver)
    except Exception as error:
        assert original.readj is original_readj and original.jsave is original_jsave
        c.jsave(c.OUT / 'execution_failure_receipt.json', {'status': 'PRESERVED_TECHNICAL_FREEZE_FAILURE',
            'error_type': type(error).__name__, 'error': str(error),
            'original_bindings_restored': True, 'original_manifest_exists': c.OLD_MANIFEST.exists(),
            'preparation_manifest_sha256': c.sha256(c.MANIFEST),
            'project_production_run': False, 'outcomes_read': False, 'models_fit': 0})
        raise
    assert original.readj is original_readj and original.jsave is original_jsave
    # Check all supplemental original/new bytes again; no model/data-value reads.
    c.check_preparation()
    result = c.readj(c.OLD_MANIFEST)
    assert result['path_compatibility'] == provenance
    assert all(result['files'][name] == digest for name, digest in extra.items())
    c.jsave(c.OUT / 'execution_receipt.json', {'status': 'PASS_ORIGINAL_FREEZE_WITH_ADDITIVE_SEPARATOR_CHAIN',
        'original_manifest': c.OLD_MANIFEST.relative_to(c.ROOT).as_posix(),
        'original_manifest_sha256': c.sha256(c.OLD_MANIFEST),
        'preparation_manifest_sha256': c.sha256(c.MANIFEST),
        'original_production_function_calls': 1, 'original_manifest_save_calls': len(saver.calls),
        'original_bindings_restored': True, 'original_source_bytes_unchanged': True,
        'supplemental_files_count': len(extra), 'root_commits_original_manifest_before_producer': True,
        'project_production_run': False, 'outcomes_read': False, 'models_fit': 0})
    print('Original production freeze PASS with additive separator-only chain; root commit before producer', flush=True)


if __name__ == '__main__':
    assert sys.argv[1:] == ['--root-start']
    run(root_start=True)
