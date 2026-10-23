"""Freeze loader sources and declared legacy pins; never open their payloads."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from src.generalization_knowncell_joint_implementation_20261022.prepare import normalize_map
from .spec import *


def sha(raw): return hashlib.sha256(raw).hexdigest()


def readj(path):
    path = Path(path); assert path.stat().st_size <= 4 * 2**20
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def declared_pins(design, source_prefit, known_evaluation):
    """Use immutable manifest declarations without following array/CSV paths."""
    assert design['status'] == 'FROZEN_STATIC_JOINT_KNOWNCELL_DESIGN_NOT_PROJECT_ADMISSION'
    assert known_evaluation['status'] == 'FROZEN_EVALUATION_KNOWN_CELL'
    source = normalize_map(source_prefit['files']); known = normalize_map(known_evaluation['files'])
    declared = design['declared_future_inputs_not_opened']
    core, feature = ALIASES['core'], ALIASES['feature']
    assert source[core] == known[core] == declared[core]['declared_sha256']
    assert source[feature] == known[feature] == declared[feature]['declared_sha256']
    assert all(value['actual_bytes_rehashed'] is False for value in declared.values())
    return {core: source[core], feature: source[feature],
            ALIASES['paired_menu_inventory']: known[ALIASES['paired_menu_inventory']],
            ALIASES['unmatched_inventory']: known[ALIASES['unmatched_inventory']]}


def run():
    # The only old result objects opened here are static/hash summary manifests.
    reference_path = ROOT / REFERENCE_READY; reference = readj(reference_path)
    assert reference['status'] == 'TESTED_REFERENCE_IMPLEMENTATION_NOT_METADATA_OR_FIT_ADMISSION'
    assert reference['project_dataset_reads'] == reference['project_feature_reads'] == reference['project_outcome_reads'] == 0
    assert reference['scientific_runtimes_imported'] is False
    source_files = normalize_map(reference['files'])
    for name, expected in source_files.items(): assert sha((ROOT / name).read_bytes()) == expected, name
    design = readj(ROOT / DESIGN_MANIFEST); design_files = normalize_map(design['files'])
    pref_raw = (ROOT / ALIASES['source_prefit']).read_bytes()
    assert sha(pref_raw) == design_files[ALIASES['source_prefit']]
    prefit = readj(ROOT / ALIASES['source_prefit'])
    known = readj(ROOT / KNOWN_EVALUATION)
    data_pins = declared_pins(design, prefit, known)
    extra = [REFERENCE_READY, KNOWN_EVALUATION, ALIASES['source_prefit'],
             'src/generalization_knowncell_20261007/common.py',
             'src/generalization_knowncell_20261007/splits.py']
    for name in extra:
        raw = (ROOT / name).read_bytes()
        if name in design_files: assert sha(raw) == design_files[name]
        source_files[name] = sha(raw)
    # Preserve and pin the first, overbroad provenance requirement as history.
    original_test_path = OUT / 'synthetic_tests_receipt.json'
    original_ready_path = ROOT / FIRST_READY_PATH
    assert sha(original_test_path.read_bytes()) == 'e8b1477cabf00d3609c53e2808d5087ab87de30946919829cbde27f2c3d47727'
    assert sha(original_ready_path.read_bytes()) == '5f92c8c74235cc2c8281f94b1daa9fae7d1bc0de6e7b1b012c3ee42ecb16a4cb'
    receipt_path = OUT / 'synthetic_tests_receipt_reviewed.json'; receipt = readj(receipt_path)
    assert receipt['status'] == 'PASS_INVENTED_STDLIB_SELECTIVE_LOADER_CHECKS'
    assert receipt['project_dataset_reads'] == receipt['project_feature_reads'] == receipt['project_outcome_reads'] == 0
    assert receipt['scientific_runtimes_imported'] is False
    sources = sorted(SRC.glob('*.py'))
    assert receipt['source_files'] == {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources}
    for path in sources: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    own = sources + [SRC / '.gitattributes', REP / '.gitattributes', REP / 'protocol.md',
                     REP / 'provenance_correction.md', OUT / '.gitattributes', receipt_path,
                     original_test_path, original_ready_path]
    files = {**source_files, **{p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in own}}
    payload = {'status': 'SOURCE_FROZEN_SELECTIVE_LOADER_NOT_PROJECT_ADMISSION',
               'generated_utc': datetime.now(timezone.utc).isoformat(), 'files': files,
               'declared_data_pins': data_pins,
               'expected_mikl_row_ids_sha256': design['metadata_summary_row_ids_sha256'],
               'metadata_admission_path': METADATA_ADMISSION, 'FIT_label_admission_path': FIT_ADMISSION,
               'metadata_bundle_path': METADATA_BUNDLE, 'pandas_admission_path': PANDAS_ADMISSION,
               'array_admission_path': ARRAY_ADMISSION,
               'metadata_loader_code_implemented_not_run': True, 'FIT_label_loader_code_implemented_not_run': True,
               'project_dataset_reads': 0, 'project_feature_reads': 0, 'project_outcome_reads': 0,
               'models_fitted': 0, 'scientific_runtimes_imported': False, 'full_trainer_implemented': False,
               'future_each_payload_read_RAM_floor': 3 * 2**30, 'future_each_payload_read_disk_floor': 2**30,
               'numerical_threads': 1, 'PUM_resource_exception_applies': False,
               'metadata_whole_CSV_bytes_and_tokens_traversed_no_numeric_effect_parsing': True,
               'label_parser': 'original_deferred_pandas_read_csv_options_and_to_numpy_float',
               'NumPy_only_bridge_does_not_certify_pandas': True,
               'separate_pinned_pandas_currentPython_origins_and_invented_original_parser_tests_REQUIRED': True,
               'pandas_certificate_status_required': PANDAS_STATUS,
               'pandas_invented_test_status_required': PANDAS_TEST_STATUS,
               'old_interpreter_bitwise_parity_established': False,
               'historical_interpreter_output_parity_is_not_an_admission_requirement': True,
               'first18_test_receipt_and_readiness_preserved_and_pinned': True,
               'actual_array_validation_not_implemented_or_run_here': True,
               'new_metadata_and_FIT_manifests_root_commit_REQUIRED': True,
               'git_helper_expected_sha256': DIRECT_GIT_SHA256,
               'git_helper_actual_current_bytes_not_rehashed_during_preparation': True}
    target = ROOT / READY_PATH
    with target.open('xb') as handle:
        handle.write((json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())
    print('SOURCE_ONLY_LOADER_READY', len(files), sha(target.read_bytes()), flush=True)


if __name__ == '__main__': run()
