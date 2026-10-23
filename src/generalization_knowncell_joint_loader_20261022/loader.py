"""Future guarded project APIs, deliberately without an execution CLI.

No function is run on project payloads during preparation. Separate committed
metadata and FIT-label manifests are required; neither exists by default.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from src.generalization_knowncell_joint_implementation_20261022.contracts import full_metadata_contract
from src.generalization_knowncell_joint_implementation_20261022.prepare import normalize_map
from . import parsers
from .guard import fresh_gate, guarded_bytes, guarded_payload
from .spec import *


def digest(raw): return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def json_bytes(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate JSON field'
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)


def _small(rel):
    path = ROOT / rel
    assert path.resolve().is_relative_to(ROOT.resolve())
    return guarded_bytes(path)


def _committed(rel, actual):
    assert rel.replace('\\', '/') == rel and '..' not in rel.split('/') and not rel.startswith('/')
    assert digest(guarded_bytes(DIRECT_GIT)) == DIRECT_GIT_SHA256, 'Changed direct Git helper; no fallback'
    fresh_gate()
    blob = subprocess.check_output([str(DIRECT_GIT), 'show', 'HEAD:' + rel], cwd=ROOT,
                                   creationflags=0x00000008 if os.name == 'nt' else 0)
    assert blob == actual, 'Admission/source summary is not exact current committed bytes'


def _admission(mode, root_start):
    assert root_start is True, 'Explicit root-start required; readiness alone grants no project read'
    assert mode in ('metadata', 'fit_labels')
    rel = METADATA_ADMISSION if mode == 'metadata' else FIT_ADMISSION
    raw = _small(rel); manifest = json_bytes(raw); _committed(rel, raw)
    assert manifest['namespace'] == NS and manifest['mode'] == mode
    assert manifest['status'] == (METADATA_STATUS if mode == 'metadata' else FIT_STATUS)
    assert manifest['label_access_authorized'] is (mode == 'fit_labels')
    assert manifest['model_fitting_authorized'] is False, 'This admission never authorizes training'
    assert manifest['PUM_resource_exception_applies'] is False and manifest['numerical_threads'] == 1
    ready_raw = _small(READY_PATH); ready = json_bytes(ready_raw); _committed(READY_PATH, ready_raw)
    assert ready['status'] == 'SOURCE_FROZEN_SELECTIVE_LOADER_NOT_PROJECT_ADMISSION'
    assert manifest['source_readiness_sha256'] == digest(ready_raw)
    assert manifest['data_pins'] == ready['declared_data_pins']
    # Preparation pins ONLY source/report/static summary objects, never arrays
    # or the CORE CSV. A forged path list cannot turn this into broad loading.
    allowed_summaries = {DESIGN_MANIFEST, REFERENCE_READY, KNOWN_EVALUATION, FIRST_READY_PATH,
                         ALIASES['source_prefit']}
    for name, expected in normalize_map(ready['files']).items():
        source = name.startswith('src/') and (name.endswith('.py') or name.endswith('/.gitattributes'))
        report = name.startswith('reports/') and (name.endswith('.md') or name.endswith('/.gitattributes'))
        assert source or report or name in allowed_summaries or (
            name.startswith('results/generalization_knowncell_joint_') and
            name.rsplit('/', 1)[-1] in ('.gitattributes', 'synthetic_tests_receipt.json', 'synthetic_tests_receipt_reviewed.json'))
        assert digest(_small(name)) == expected, name
    return manifest, ready, digest(raw)


def load_metadata(*, root_start=False):
    """Future metadata-only admission: no array or numerical label parser."""
    manifest, ready, admission_sha = _admission('metadata', root_start)
    pins = ready['declared_data_pins']
    parsed, core_read = guarded_payload(ROOT / ALIASES['core'], pins[ALIASES['core']], parsers.metadata_csv, text=True)
    assert parsed['all_core_rows'] == ALL_CORE_ROWS
    assert parsed['row_ids_sha256'] == ready['expected_mikl_row_ids_sha256']
    contract = full_metadata_contract(parsed['rows'])
    saved_pairs, pairs_read = guarded_payload(ROOT / ALIASES['paired_menu_inventory'],
        pins[ALIASES['paired_menu_inventory']], parsers.metadata_inventory_csv, text=True)
    saved_unmatched, unmatched_read = guarded_payload(ROOT / ALIASES['unmatched_inventory'],
        pins[ALIASES['unmatched_inventory']], parsers.metadata_inventory_csv, text=True)
    parsers.inventory_contract(parsed['rows'], contract['pairs'], contract['unmatched_contexts'], saved_pairs, saved_unmatched)
    return {'status': 'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION',
            'metadata_admission_sha256': admission_sha, 'core_sha256': core_read['actual_sha256'],
            'declared_simple102_sha256_not_loaded': pins[ALIASES['feature']],
            'metadata': parsed, 'contract': contract,
            'payload_reads': {'core': core_read, 'paired_inventory': pairs_read, 'unmatched_inventory': unmatched_read},
            'actual_feature_reads': 0, 'numeric_outcome_rows_admitted': 0, 'models_fitted': 0,
            'every_payload_open_fresh_original_resource_gated': True,
            'whole_core_bytes_traversed_not_annotation_only_IO': True,
            'preserves_all_rows_and_unmatched_menus': True,
            'requires_root_immutable_save_and_commit_before_FIT': True}


def _python_before_pandas(record):
    """Current executable/DLL bytes before invoking a future pandas provider."""
    assert sys.version_info[:2] == (3, 12) and sys.implementation.cache_tag == record['python_cache_tag'] == 'cpython-312'
    executable = Path(sys.executable).resolve()
    assert executable == Path(record['python_executable']).resolve()
    expected_paths = {executable, executable.parent / 'python3.dll', executable.parent / 'python312.dll'}
    actual = {Path(name).resolve(): value for name, value in record['python_native_files'].items()}
    assert len(actual) == len(record['python_native_files']) and set(actual) == expected_paths
    for path, expected in actual.items(): assert digest(guarded_bytes(path)) == expected


def pandas_certificate_contract(record):
    """Narrow actual package/current-interpreter evidence, no historical parity."""
    assert record['status'] == PANDAS_STATUS
    assert record['pandas_version'] == record['original_pandas_version'] == '2.2.3'
    assert record['original_pandas_package_and_native_bytes_unchanged'] is True
    assert record['invented_original_parser_options_and_results'] == PANDAS_TEST_STATUS
    assert record['old_interpreter_bitwise_parity_established'] is False
    assert record['biological_rows_read'] == record['model_fits'] == 0
    return True


def load_fit_labels(runtime_provider, *, root_start=False):
    """Future Mikl-only ORIGINAL pandas labels, never fit or load an array.

    runtime_provider is root-owned, separately frozen and independently
    origin-checked. A NumPy-only compatibility receipt cannot admit pandas.
    """
    manifest, ready, admission_sha = _admission('fit_labels', root_start)
    assert callable(runtime_provider)
    metadata_raw = _small(METADATA_BUNDLE)
    assert digest(metadata_raw) == manifest['metadata_bundle_sha256']; _committed(METADATA_BUNDLE, metadata_raw)
    bundle = json_bytes(metadata_raw)
    assert bundle['status'] == 'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    assert bundle['core_sha256'] == ready['declared_data_pins'][ALIASES['core']]
    metadata = bundle['metadata']
    assert metadata['row_ids_sha256'] == ready['expected_mikl_row_ids_sha256']
    contract = full_metadata_contract(metadata['rows'])
    assert canonical_bytes(contract) == canonical_bytes(bundle['contract'])
    array_raw = _small(ARRAY_ADMISSION)
    assert digest(array_raw) == manifest['array_admission_sha256']; _committed(ARRAY_ADMISSION, array_raw)
    array = json_bytes(array_raw)
    assert array['status'] == ARRAY_STATUS
    assert array['actual_npz_sha256'] == ready['declared_data_pins'][ALIASES['feature']]
    assert array['metadata_bundle_sha256'] == digest(metadata_raw)
    assert array['rows'] == COUNTS['all_rows'] and array['columns'] == 102 and array['same_allele_feature_bytes_equal'] is True
    pandas_raw = _small(PANDAS_ADMISSION)
    assert digest(pandas_raw) == manifest['pandas_admission_sha256']; _committed(PANDAS_ADMISSION, pandas_raw)
    record = json_bytes(pandas_raw)
    pandas_certificate_contract(record)
    _python_before_pandas(record)
    fresh_gate()  # Before a provider may import ANY scientific runtime.
    supplied = runtime_provider()
    assert supplied['pandas_admission_sha256'] == digest(pandas_raw)
    assert supplied['actual_origin_receipt_sha256'] == record['actual_origin_receipt_sha256']
    pd = supplied['pandas']
    assert pd.__name__ == 'pandas' and pd.__version__ == record['pandas_version']
    actual_path = Path(pd.__file__).resolve()
    assert actual_path == Path(record['pandas_module_path']).resolve()
    assert actual_path.is_relative_to((ROOT / 'data/interim/mechanism_v2/runtime').resolve())
    assert digest(guarded_bytes(actual_path)) == record['pandas_module_sha256']
    result, core_read = guarded_payload(ROOT / ALIASES['core'], ready['declared_data_pins'][ALIASES['core']],
                                      lambda binary: parsers.pandas_effects(binary, pd, metadata))
    result.update({'fit_label_admission_sha256': admission_sha,
                   'metadata_bundle_sha256': digest(metadata_raw),
                   'pandas_admission_sha256': digest(pandas_raw), 'source_core_read': core_read,
                   'actual_feature_reads': 0, 'models_fitted': 0,
                   'label_access_does_not_authorize_fitting': True})
    return result
