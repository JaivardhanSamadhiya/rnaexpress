"""Pure request, software and fresh-proof checks; no native calls or imports."""
import hashlib
import json
import math
from pathlib import Path
from .spec import *


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('utf-8')


def digest(raw):
    assert isinstance(raw,bytes)
    return hashlib.sha256(raw).hexdigest()


def hash_contract(value):
    assert isinstance(value,str) and len(value)==64 and all(character in '0123456789abcdef' for character in value)
    return value


def decode(raw):
    def unique(pairs):
        value = {}
        for key,item in pairs:
            assert key not in value,'Duplicate JSON field'
            value[key] = item
        return value
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(AssertionError('Nonfinite JSON token')))


def relative(name):
    assert isinstance(name,str) and name==name.replace('\\','/') and ':' not in name
    assert not name.startswith('/') and all(part not in ('','.','..') for part in name.split('/'))
    path = ROOT/name
    assert not path.is_symlink() and path.resolve().is_relative_to(ROOT.resolve())
    return path


def binding_contract(binding):
    assert isinstance(binding,dict) and set(binding)==BINDING_FIELDS
    for name in BINDING_FIELDS-{'request_relative_path'}:
        hash_contract(binding[name])
    assert binding['request_relative_path']==REQUEST,'Only the frozen array stage is supported'
    assert binding['software_status_sha256']==SOFTWARE_STATUS_SHA
    assert binding['pandas_admission_sha256']==PANDAS_ADMISSION_SHA
    return decode(canonical(binding))


def request_contract(request,binding,source_sha):
    assert request['namespace']=='generalization_knowncell_array_admission_20261023'
    assert request['status']==REQUEST_STATUS and request['runtime_import_authorized'] is True
    assert request['label_access_authorized'] is request['model_fitting_authorized'] is False
    assert request['PUM_resource_exception_applies'] is request['PRELib_resource_exception_applies'] is False
    assert request['numerical_threads']==1
    assert request['software_status_sha256']==SOFTWARE_STATUS_SHA
    assert request['software_certificate_sha256']==PANDAS_ADMISSION_SHA
    assert request['provider_preparation_manifest_sha256']==binding['provider_preparation_manifest_sha256']
    provider = request['provider_binding']
    assert set(provider)=={'source_path','source_sha256','module','qualname','reviewed_deferred_only'}
    assert provider=={'source_path':SOURCE,'source_sha256':source_sha,'module':MODULE,
                      'qualname':'provide','reviewed_deferred_only':True}
    return True


def software_contract(status,certificate,origin,profile):
    assert status['status']=='VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    assert status['initial_manifest_sha256']==PROFILE_MANIFEST_SHA
    assert status['project_rows_read']==status['biological_model_fits']==0
    assert status['metadata_array_label_and_fit_admissions_granted_here'] is False
    assert status['original_three_GiB_project_guards_unchanged'] is True
    assert status['future_loader_certificate_sha256']==PANDAS_ADMISSION_SHA
    assert status['future_loader_software_certificate']==PANDAS_ADMISSION
    assert status['verified_files']['preparation_manifest.json']==PROFILE_MANIFEST_SHA
    assert status['verified_files']['actual_origin_receipt.json']==PROFILE_ORIGIN_SHA
    assert certificate['status']=='PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER'
    assert certificate['pandas_version']==certificate['original_pandas_version']=='2.2.3'
    assert certificate['original_pandas_package_and_native_bytes_unchanged'] is True
    assert certificate['invented_original_parser_options_and_results']=='PASS_PINNED_PANDAS_DEFAULT_CSV_OPTIONS_RESULTS'
    assert certificate['old_interpreter_bitwise_parity_established'] is False
    assert certificate['automatic_biological_admission'] is False
    assert certificate['actual_origin_receipt_sha256']==PROFILE_ORIGIN_SHA
    assert certificate['preparation_manifest_sha256']==PROFILE_MANIFEST_SHA
    assert certificate['biological_rows_read']==certificate['model_fits']==0
    assert origin['status']=='PASS_ACTUAL_LOADED_PANDAS_NUMPY_SCIPY_ONE_THREAD_CURRENT_PYTHON_V4'
    assert origin['preparation_manifest_sha256']==PROFILE_MANIFEST_SHA
    assert origin['biological_rows_read']==origin['biological_model_fits']==0
    assert profile['status']=='FROZEN_INVENTED_ONE_THREAD_PROFILE_INITIAL_MANIFEST_BINDING_V4'
    return True


def fresh_proof_contract(proof,accepted_origin,inventory):
    expected = accepted_origin['final']
    assert proof['current_python_inventory_sha256']==expected['current_python_inventory_sha256']
    assert proof['v3_payload_inventory_sha256']==expected['v3_payload_inventory_sha256']
    assert proof['python_version']==expected['python_version']
    assert proof['actually_loaded_Python_DLLs']==expected['actually_loaded_Python_DLLs']
    assert proof['old_interpreter_bitwise_parity_established'] is False
    assert proof['old_exact_runtime_identity_passes'] is False
    assert proof['fresh_full_NumPy_payload_check'] is True
    assert proof['unused_pandas_SciPy_files_freshly_rehashed_in_worker'] is False
    assert proof['possible_bytecode_payload_proof']['status']=='PASS_EXISTING_POSSIBLE_BYTECODE_PAYLOADS_BOUND'
    assert proof['possible_bytecode_payload_proof']['possible_existing_bytecode_payloads']=={},'Fresh absent cache prefix is required'
    assert proof['two_explicit_root_cache_admissions']==expected['two_explicit_root_cache_admissions']
    modules = proof['actually_loaded_scientific_modules']
    for package in ('numpy','pandas','scipy'):
        name = package+'/__init__.py'
        assert modules[name]==inventory['files'][name]
    for name,sha in modules.items():
        assert inventory['files'].get(name)==sha
    observed = proof['actually_loaded_scientific_native_files']
    assert observed
    prefix = SCIENTIFIC_PREFIX.resolve()
    for name,sha in observed.items():
        path = Path(name).resolve()
        assert path.is_relative_to(prefix) and inventory['native_files'][path.relative_to(prefix).as_posix()]==sha
    for name,sha in proof['actually_loaded_current_python_native_files'].items():
        assert inventory['current_python_native_files'].get(name)==sha
    pools = proof['actually_loaded_threadpools']
    assert pools and all(pool['num_threads']==1 and pool['user_api'] in ('blas','openmp') for pool in pools)
    assert {str(Path(pool['filepath']).resolve()) for pool in pools} == {
        str(Path(pool['filepath']).resolve()) for pool in expected['actually_loaded_threadpools']}
    canonical(proof)
    return True
