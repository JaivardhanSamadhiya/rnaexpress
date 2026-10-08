"""Prepare separate byte/hash chain only; never invoke the original freeze."""
from . import common as c


def run():
    assert not c.MANIFEST.exists(), 'Preserve existing compatibility preparation'
    c.no_original_outputs()
    paths, normalized = c.original_byte_check()
    original = c.readj(c.OLD_FEAS)
    c.jsave(c.NORMALIZATION, {'status': 'READY_SEPARATOR_ONLY_NORMALIZATION',
        'original_receipt': c.OLD_FEAS.relative_to(c.ROOT).as_posix(),
        'original_receipt_sha256': c.sha256(c.OLD_FEAS),
        'original_keys_in_order': list(original['source_sha256']),
        'normalized_source_sha256': normalized['source_sha256'],
        'keys_with_changed_separators': [name for name in original['source_sha256'] if '\\' in name],
        'hash_values_changed': False, 'other_receipt_fields_changed': False,
        'collision_rejection': 'exact normalized key and Windows case-insensitive alias',
        'original_file_modified': False, 'original_freeze_invoked': False})
    tests_path = c.OUT / 'synthetic_tests_receipt.json'
    tests = c.readj(tests_path)
    source_hashes = {path.relative_to(c.ROOT).as_posix(): c.sha256(path) for path in sorted(c.SRC.glob('*.py'))}
    assert tests['status'] == 'PASS' and tests['source_hashes'] == source_hashes
    assert tests['actual_original_freeze_calls'] == 0 and tests['project_outcomes_read'] is False
    assert tests['plan_sha256'] == c.sha256(c.PLAN)
    for folder in (c.SRC, c.OUT, c.REP, c.ART):
        paths += [path for path in folder.rglob('*') if path.is_file()]
    # No original model/outcome/feature values are opened here; original production
    # still performs all runtime/source-control admission checks when root starts.
    c.jsave(c.MANIFEST, {'status': 'FROZEN_ADDITIVE_JOINT_SEPARATOR_COMPATIBILITY',
        'files': {path.relative_to(c.ROOT).as_posix(): c.sha256(path) for path in sorted(set(paths))},
        'original_joint_source_modules': 17, 'original_joint_scoped_tests': 22,
        'normalization_scope': 'one exact feasibility receipt source_sha256 key map, separators only',
        'original_source_report_receipt_bytes_unchanged': True,
        'original_checks_delegated_once_before_first_manifest_write': True,
        'supplemental_chain_must_be_added_to_original_manifest_files': True,
        'preparation_and_tests_actual_original_freeze_calls': 0,
        'project_outcomes_read': False, 'project_feature_values_read': False,
        'project_production_run': False, 'models_fit': 0,
        'root_review_commit_and_explicit_start_required': True})
    print('Additive joint freeze compatibility preparation ready; root review/commit/start required', c.sha256(c.MANIFEST), flush=True)


if __name__ == '__main__':
    run()
