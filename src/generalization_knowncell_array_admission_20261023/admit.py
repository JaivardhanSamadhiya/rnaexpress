"""Future guarded actual-array API; no bootstrap, writer or execution CLI.

The existing software-only invented profile is necessary evidence, not actual
biological/runtime acceptance. A separately frozen real provider is mandatory.
"""
import inspect
import json
import os
from pathlib import Path
import sys
from .spec import *
from src.generalization_knowncell_joint_loader_20261022 import loader
from src.generalization_knowncell_joint_loader_20261022.guard import fresh_gate,guarded_bytes,guarded_payload,live_resources
from src.generalization_knowncell_joint_implementation_20261022.contracts import ids_sha,metadata_sha
from src.generalization_knowncell_array_contract_20261022.validate import validate_supplied_array
from src.generalization_knowncell_joint_implementation_20261022.prepare import normalize_map


def sha(raw):return loader.digest(raw)


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def source_mode():
    assert sys.flags.no_site==1 and sys.dont_write_bytecode is True
    assert sys.pycache_prefix==str(CACHE_PREFIX) and not os.path.lexists(CACHE_PREFIX)


def fresh():
    source_mode()
    return fresh_gate() # Actual original Win32 probe and one-thread environment.


def hash_contract(value):
    assert isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    return value


def safe_relative(value,top=None):
    assert isinstance(value,str) and value==value.replace('\\','/')
    assert not value.startswith('/') and ':' not in value and all(part not in ('','..','.') for part in value.split('/'))
    if top:assert value.startswith(top+'/')
    path=ROOT/value;assert path.resolve().is_relative_to(ROOT.resolve())
    return path


def read_bound(relative,expected=None,*,committed=False,maximum=2*2**20):
    fresh();path=safe_relative(relative)
    raw=guarded_bytes(path,maximum=maximum)
    if expected is not None:assert sha(raw)==hash_contract(expected),relative
    if committed:
        fresh();loader._committed(relative,raw)
    return raw


def bounded_array_bytes(path,expected):
    fresh();assert Path(path).stat().st_size<=MAX_NPZ
    def bounded(stream):
        raw=stream.read(MAX_NPZ+1)
        assert len(raw)<=MAX_NPZ,'Compressed array exceeds fixed32MiB cap'
        return raw
    raw,receipt=guarded_payload(path,expected,bounded)
    assert len(raw)<=MAX_NPZ and receipt['actual_sha256']==expected
    return raw,receipt


def request_contract(request):
    assert request['status']==REQUEST_STATUS and request['namespace']==NS
    assert request['label_access_authorized'] is False and request['model_fitting_authorized'] is False
    assert request['runtime_import_authorized'] is True
    assert request['PUM_resource_exception_applies'] is False and request['PRELib_resource_exception_applies'] is False
    assert request['numerical_threads']==1
    assert request['data_pins']==DECLARED_PINS and request['expected_row_ids_sha256']==ROW_IDS_SHA
    assert request['array_contract_sha256']==ARRAY_CONTRACT_SHA and request['source_prefit_sha256']==SOURCE_PREFIT_SHA
    assert request['software_status_sha256']==SOFTWARE_STATUS_SHA and request['software_certificate_sha256']==SOFTWARE_CERT_SHA
    for name in ('metadata_bundle_sha256','source_readiness_sha256','provider_preparation_manifest_sha256'):hash_contract(request[name])
    provider=request['provider_binding']
    assert set(provider)=={'source_path','source_sha256','module','qualname','reviewed_deferred_only'}
    safe_relative(provider['source_path'],'src');hash_contract(provider['source_sha256'])
    assert provider['reviewed_deferred_only'] is True
    assert isinstance(provider['module'],str) and provider['module'].startswith('src.')
    assert isinstance(provider['qualname'],str) and provider['qualname'] and '<locals>' not in provider['qualname']
    return request


def software_contract(status,certificate):
    assert status['status']=='VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    assert status['project_rows_read']==status['biological_model_fits']==0
    assert status['metadata_array_label_and_fit_admissions_granted_here'] is False
    assert status['original_three_GiB_project_guards_unchanged'] is True
    assert status['future_loader_certificate_sha256']==SOFTWARE_CERT_SHA
    loader.pandas_certificate_contract(certificate)
    assert certificate['automatic_biological_admission'] is False
    assert certificate['actual_origin_receipt_sha256']==status['verified_files']['actual_origin_receipt.json']
    return True


def metadata_contract(bundle):
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    assert bundle['numeric_outcome_rows_admitted']==bundle['actual_feature_reads']==bundle['models_fitted']==0
    assert bundle['metadata_admission_sha256']==METADATA_ADMISSION_SHA and bundle['core_sha256']==CORE_SHA
    assert bundle['declared_simple102_sha256_not_loaded']==NPZ_SHA
    rows=bundle['metadata']['rows']
    assert len(rows)==13781 and ids_sha(rows)==bundle['metadata']['row_ids_sha256']==ROW_IDS_SHA
    assert metadata_sha(rows)==bundle['contract']['metadata_sha256']
    return rows


def accepted_runtime(runtime_provider,request,request_sha,status,certificate,phase):
    assert phase in ('before_array','after_array')
    binding=request['provider_binding']
    source=read_bound(binding['source_path'],binding['source_sha256'],committed=True)
    assert source # Root reviews this provider as deferred-only; no import here.
    assert inspect.isfunction(runtime_provider)
    assert runtime_provider.__module__==binding['module'] and runtime_provider.__qualname__==binding['qualname']
    assert Path(runtime_provider.__code__.co_filename).resolve()==safe_relative(binding['source_path']).resolve()
    fresh() # Immediately before the externally implemented native provider.
    request_binding={'request_relative_path':REQUEST,'request_sha256':request_sha,
        'provider_preparation_manifest_sha256':request['provider_preparation_manifest_sha256'],
        'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':SOFTWARE_CERT_SHA}
    result=runtime_provider(request_binding,phase=phase,root_start=True)
    assert isinstance(result,dict) and set(result)=={'np','pd','minimize','expit','actual_origin_receipt_sha256','fresh_origin_proof','fresh_origin_proof_sha256'}
    assert result['actual_origin_receipt_sha256']==V4_ORIGIN_SHA
    proof=result['fresh_origin_proof'];np=result['np']
    assert sha(canonical(proof))==result['fresh_origin_proof_sha256']
    assert proof['status']==PROVIDER_STATUS and proof['request_binding']==request_binding
    assert proof['phase']==phase
    assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True
    assert proof['invented_only'] is False and proof['provider_opened_project_array'] is False
    assert proof['numpy_module_path']==str(NUMPY_PATH) and proof['numpy_module_sha256']==NUMPY_SHA
    assert proof['numpy_version']=='1.26.4'
    assert getattr(np,'__name__',None)=='numpy' and np.__version__=='1.26.4'
    assert Path(np.__file__).resolve()==NUMPY_PATH.resolve()
    fresh();assert sha(guarded_bytes(NUMPY_PATH))==NUMPY_SHA
    canonical(proof) # Finite, JSON-persistable actual acceptance evidence.
    return np,proof


def validate_report(report,runtime_sha,metadata_payload_sha):
    assert report['status']=='VALIDATED_SUPPLIED_ARRAY_BYTES_NOT_PROJECT_ADMISSION'
    assert report['rows']==13781 and report['columns']==102 and report['all_columns_finite'] is True
    assert report['supplied_npz_sha256']==NPZ_SHA
    assert report['external_runtime_receipt_sha256']==runtime_sha
    assert report['exact_astype_value_bits_replayed'] is True
    assert report['supplied_metadata_full_counts_and_split_contract_checked'] is True
    identity=report['creation_identity']
    assert identity['supplied_creation_receipt_sha256']==CREATION_SHA and identity['supplied_metadata_receipt_sha256']==METADATA_SHA
    assert identity['row_ids_sha256']==ROW_IDS_SHA and identity['creation_order_matches_supplied_metadata'] is True
    assert identity['supplied_metadata_sha256']==metadata_payload_sha
    for field in ('original_storage_parity','native_astype_parity'):
        assert report[field]['all_crosscell_matching_allele_bytes_equal'] is True
        assert report[field]['crosscell_allele_groups']>0
        assert report[field]['tolerance_or_zero_filling_used'] is False
    return True


def static_pin_allowed(name):
    if name.startswith('src/'):return name.endswith(('.py','/.gitattributes'))
    if name.startswith('reports/'):return name.endswith(('.md','/.gitattributes'))
    if name in (ARRAY_CONTRACT,SOURCE_PREFIT,SOFTWARE_STATUS,SOFTWARE_CERT):return True
    for namespace in (NS,'generalization_knowncell_array_contract_20261022'):
        if name.startswith('results/'+namespace+'/'):
            return name.rsplit('/',1)[-1] in ('.gitattributes','synthetic_tests_receipt.json')
    return False


def admit_simple102(runtime_provider,*,root_start=False):
    """Return matrix+certificate; root alone later persists/commits exclusively.

    No provider, array request or metadata bundle currently exists by inference
    from preparation. This API cannot bootstrap or manufacture those approvals.
    """
    assert root_start is True,'Explicit root array-only start is required'
    fresh()
    request_raw=read_bound(REQUEST,committed=True);request=request_contract(loader.json_bytes(request_raw));request_sha=sha(request_raw)
    ready_raw=read_bound(READY,request['source_readiness_sha256'],committed=True)
    ready=loader.json_bytes(ready_raw)
    assert ready['status']=='SOURCE_ONLY_GUARDED_ARRAY_API_NOT_PROJECT_ADMISSION'
    for name,want in ready['files'].items():
        # Readiness pins only source/static summaries; it never includes NPZ/CSV.
        assert static_pin_allowed(name)
        read_bound(name,want,maximum=64*2**20)
    contract_raw=read_bound(ARRAY_CONTRACT,ARRAY_CONTRACT_SHA,committed=True)
    assert loader.json_bytes(contract_raw)['status']=='SOURCE_ONLY_SUPPLIED_ARRAY_CONTRACT_NOT_PROJECT_ADMISSION'
    prefit=loader.json_bytes(read_bound(SOURCE_PREFIT,SOURCE_PREFIT_SHA,committed=True))
    assert prefit['status']=='FROZEN_PREFIT'
    prefit_files=normalize_map(prefit['files']) # Original map is never mutated; aliases/collisions fail.
    for path,want in DECLARED_PINS.items():assert prefit_files[path]==want
    status=loader.json_bytes(read_bound(SOFTWARE_STATUS,SOFTWARE_STATUS_SHA,committed=True))
    certificate=loader.json_bytes(read_bound(SOFTWARE_CERT,SOFTWARE_CERT_SHA,committed=True))
    software_contract(status,certificate)
    bundle=loader.json_bytes(read_bound(METADATA_BUNDLE,request['metadata_bundle_sha256'],committed=True,maximum=64*2**20))
    rows=metadata_contract(bundle)
    creation=read_bound(CREATION,CREATION_SHA,committed=True)
    metadata=read_bound(METADATA,METADATA_SHA,committed=True)
    np,acceptance=accepted_runtime(runtime_provider,request,request_sha,status,certificate,'before_array')
    raw,acquisition=bounded_array_bytes(ROOT/NPZ,NPZ_SHA)
    fresh()
    runtime_sha=sha(canonical(acceptance))
    matrix,report=validate_supplied_array(raw,rows,creation,metadata,
        expected_npz_sha256=NPZ_SHA,expected_creation_sha256=CREATION_SHA,expected_metadata_sha256=METADATA_SHA,
        expected_row_ids_sha256=ROW_IDS_SHA,np=np,external_runtime_accepted=True,
        external_runtime_receipt_sha256=runtime_sha,resource_probe=live_resources,environment=os.environ)
    validate_report(report,runtime_sha,bundle['contract']['metadata_sha256'])
    post_np,post_acceptance=accepted_runtime(runtime_provider,request,request_sha,status,certificate,'after_array')
    assert post_np is np,'Runtime provider changed NumPy module after validation'
    fresh()
    # Recheck immutable request/source/metadata identities before returning.
    assert read_bound(REQUEST,request_sha,committed=True)==request_raw
    read_bound(METADATA_BUNDLE,request['metadata_bundle_sha256'],committed=True,maximum=64*2**20)
    result={'status':STATUS,'actual_npz_sha256':NPZ_SHA,'metadata_bundle_sha256':request['metadata_bundle_sha256'],
            'rows':13781,'columns':102,'same_allele_feature_bytes_equal':True,
            'array_request_sha256':request_sha,'source_readiness_sha256':request['source_readiness_sha256'],
            'original_creation_receipt_sha256':CREATION_SHA,'original_metadata_receipt_sha256':METADATA_SHA,
            'original_row_ids_sha256':ROW_IDS_SHA,'array_contract_sha256':ARRAY_CONTRACT_SHA,
            'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':SOFTWARE_CERT_SHA,
            'runtime_acceptance':acceptance,'runtime_acceptance_after_array':post_acceptance,
            'array_acquisition':acquisition,'underlying_report':report,
            'numeric_labels_admitted':False,'FIT_admission_granted':False,'models_fitted':0,
            'certificate_persisted_here':False,'requires_exclusive_root_save_and_commit':True,
            'original_resource_guards_unchanged':True,'resource_exception_applies':False}
    return matrix,result
