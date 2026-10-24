"""Fixed original parser; current request/provenance and truthful calibration."""
import math
from pathlib import Path
import struct
from . import common as c
from src.generalization_knowncell_joint_loader_20261022 import guard,loader,parsers
from src.generalization_knowncell_array_admission_20261023 import admit as original_array
from src.generalization_knowncell_labels_runtime_20261024 import provider,contracts as runtime_contracts


def read_bound(name,want,*,maximum=64*2**20):
    raw=guard.guarded_bytes(c.relative(name),maximum=maximum)
    assert c.sha(raw)==c.valid_sha(want),name
    guard.fresh_gate();loader._committed(name,raw)
    return raw


def request_contract(request,admission,generation):
    assert request['provider_preparation_manifest_sha256']==c.RUNTIME_PREPARATION_SHA
    binding={'request_relative_path':c.REQUEST,'request_sha256':admission['input_pins'][c.REQUEST],
        'provider_preparation_manifest_sha256':request['provider_preparation_manifest_sha256'],
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA}
    runtime_contracts.binding_contract(binding)
    runtime_contracts.request_contract(request,binding,request['provider_binding']['source_sha256'])
    assert request['generation_manifest_sha256']==generation
    assert request['metadata_bundle_sha256']==admission['input_pins'][c.METADATA_BUNDLE]
    assert request['array_certificate_sha256']==admission['input_pins'][c.ARRAY_CERTIFICATE]
    assert request['array_supervisor_sha256']==admission['input_pins'][c.ARRAY_SUPERVISOR]
    assert request['core_sha256']==c.CORE_SHA and request['expected_row_ids_sha256']==c.ROW_IDS_SHA
    assert request['source_loader_readiness_sha256']==request['source_pins'][c.LOADER_READY]
    assert request['source_pins']['src/generalization_knowncell_joint_loader_20261022/parsers.py']
    assert request['source_pins']['src/generalization_knowncell_joint_loader_20261022/loader.py']
    return binding


def metadata_prerequisite(bundle,report,supervisor):
    rows=original_array.metadata_contract(bundle)
    guard.fresh_gate()
    contract=loader.full_metadata_contract(rows)
    assert c.canonical(contract)==c.canonical(bundle['contract'])
    assert report['status']=='PASS_INDEPENDENT_METADATA_DERIVATION_AND_CONTRACT_WITH_OWNED_RAW_READ_PROOF'
    assert supervisor['status']=='PASS_SECOND_METADATA_EXECUTION_REQUIRES_REVIEW_AND_COMMIT' and supervisor['failure'] is None
    assert supervisor['independent_report_sha256']==c.INDEPENDENT_REPORT_SHA
    assert report['generation_manifest_sha256']==supervisor['generation_manifest_sha256']
    for field in ('run_admission_sha256','birth_sha256'):assert report[field]==supervisor[field]
    assert report['acquisition_input_hashes'][c.METADATA_BUNDLE]==c.METADATA_SHA
    assert report['outer_raw_CORE_SHA_verified_against_frozen_admission'] is True
    assert report['each_acquisition_input_committed_bytes_checked'] is True
    assert report['array_label_or_FIT_permission_granted'] is False
    assert report['numerical_outcomes_admitted']==report['actual_feature_reads']==report['model_fits']==0
    independent=report['independent_verification']
    assert independent['status']==c.prior.HELPER_STATUS and independent['counts']==c.prior.HELPER_COUNTS
    assert independent['row_ids_sha256']==c.ROW_IDS_SHA
    for field in ('source_CSV_metadata_derivation_independently_verified','original_core_position_alignment_independently_verified',
                  'nonMikl_full_core_ID_roster_independently_verified','both_cells_used_for_every_purge',
                  'source_and_target_full_menus_preserved','original_row_order_preserved'):
        assert independent[field] is True
    return rows


def array_prerequisite(raw,certificate,supervisor,admission):
    assert c.sha(raw)==admission['input_pins'][c.ARRAY_CERTIFICATE]
    assert certificate['status']=='PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY'
    assert certificate['invocation']=='array_admission'
    assert certificate['generation_manifest_sha256']==c.ARRAY_GENERATION_SHA
    assert certificate['metadata_bundle_sha256']==c.METADATA_SHA and certificate['actual_npz_sha256']==c.NPZ_SHA
    assert certificate['original_row_ids_sha256']==c.ROW_IDS_SHA
    assert certificate['rows']==c.COUNT and certificate['columns']==102 and certificate['same_allele_feature_bytes_equal'] is True
    assert certificate['underlying_report']['post_original_astype_float_C_bytes_sha256']==c.ARRAY_CAST_SHA
    assert certificate['original_resource_guards_unchanged'] is False and certificate['resource_exception_applies'] is True
    assert certificate['numeric_labels_admitted'] is certificate['FIT_admission_granted'] is False and certificate['models_fitted']==0
    assert certificate['approved_policy_manifest_sha256']==c.POLICY_SHA and certificate['authorization_sha256']==c.AUTH_SHA
    assert certificate['approval_scope_sha256']==c.SCOPE_SHA
    assert certificate['independent_metadata_report_sha256']==c.INDEPENDENT_REPORT_SHA
    assert supervisor['status']=='PASS_EXACT_ARRAY_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT'
    assert supervisor['failure'] is None and supervisor['invocation']=='array_admission'
    assert supervisor['certificate_sha256']==c.sha(raw)
    for field in ('generation_manifest_sha256','run_admission_sha256','birth_sha256','approved_policy_manifest_sha256',
                  'authorization_sha256','approval_scope_sha256'):
        assert supervisor[field]==certificate[field]
    assert supervisor['resource_policy']==c.resource_policy() and supervisor['automatic_retry'] is False
    assert supervisor['numerical_outcomes_admitted']==supervisor['model_fits']==0
    protected={key:certificate[key] for key in ('runtime_acceptance','runtime_acceptance_after_array')}
    assert c.sha(c.canonical(protected))==certificate['protected_runtime_payloads_sha256']
    for key,phase in (('runtime_acceptance','before_array'),('runtime_acceptance_after_array','after_array')):
        proof=protected[key]
        assert proof['status']=='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_ARRAY_REQUEST' and proof['phase']==phase
        assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA and proof['model_fits']==0
    return certificate


def accepted_runtime(binding,phase):
    guard.fresh_gate()
    result=provider.provide(binding,phase=phase,root_start=True)
    assert set(result)=={'np','pd','minimize','expit','actual_origin_receipt_sha256','fresh_origin_proof','fresh_origin_proof_sha256'}
    proof=result['fresh_origin_proof']
    assert runtime_contracts.digest(runtime_contracts.canonical(proof))==result['fresh_origin_proof_sha256']
    assert proof['status']==c.runtime.PROVIDER_STATUS and proof['phase']==phase and proof['request_binding']==binding
    assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
    assert proof['provider_opened_project_array'] is proof['provider_opened_labels_or_fit_inputs'] is False
    assert result['actual_origin_receipt_sha256']==proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
    np,pd=result['np'],result['pd']
    for module,name,version in ((np,'numpy','1.26.4'),(pd,'pandas','2.2.3')):
        assert module.__name__==name and module.__version__==version
        path=Path(module.__file__).resolve()
        assert path==(c.ROOT/'data/interim/mechanism_v2/runtime'/name/'__init__.py').resolve()
        assert proof[name+'_module_path']==str(path)
        assert c.sha(guard.guarded_bytes(path))==proof[name+'_module_sha256']
    return result


def serialize_original_result(result,np,expected_ids):
    """Only the original parser ndarray.tolist, then exact little-endian bits."""
    assert result['intervention_ids']==expected_ids
    assert result['parser']==c.PARSER and result['original_truth_orientation'] is True
    assert result['old_interpreter_bitwise_parity_established'] is False
    assert result['pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'] is True
    vector=result['measured_delta']
    assert type(vector) is np.ndarray and vector.shape==(len(expected_ids),)
    assert vector.dtype.kind=='f' and vector.dtype.itemsize==8 and vector.dtype.isnative and not vector.dtype.hasobject
    guard.fresh_gate();values=vector.tolist()
    assert isinstance(values,list) and len(values)==len(expected_ids)
    assert all(type(value) is float and math.isfinite(value) for value in values)
    assert c.sha(b''.join(struct.pack('<d',value) for value in values))==result['parsed_effects_float64_sha256']
    assert result['numeric_outcome_rows_admitted']==len(expected_ids)
    serialized=dict(result);serialized['measured_delta']=values
    assert serialized.keys()==result.keys()
    return serialized


def load_labels(session,generation,run_sha,birth_sha):
    """Owned worker only; no alternate provider, parser, file or source aliases."""
    admission=c.read_run(generation,run_sha,check_commit=True)
    captured={name:read_bound(name,want) for name,want in admission['input_pins'].items()}
    objects={name:c.decode(raw) for name,raw in captured.items()}
    request=objects[c.REQUEST];binding=request_contract(request,admission,generation)
    closure=c.verify_sources(generation)['files']
    for name,want in request['source_pins'].items():
        assert name in closure and closure[name]==c.valid_sha(want)
        assert name==c.LOADER_READY or name.startswith('src/') and name.endswith('.py')
        read_bound(name,want)
    ready=objects.get(c.LOADER_READY)
    if ready is None:ready=c.decode(read_bound(c.LOADER_READY,request['source_loader_readiness_sha256']))
    assert ready['status']=='SOURCE_FROZEN_SELECTIVE_LOADER_NOT_PROJECT_ADMISSION'
    assert ready['declared_data_pins'][c.CORE]==c.CORE_SHA
    assert ready['expected_mikl_row_ids_sha256']==c.ROW_IDS_SHA
    bundle=objects[c.METADATA_BUNDLE]
    metadata_prerequisite(bundle,objects[c.INDEPENDENT_REPORT],objects[c.INDEPENDENT_SUPERVISOR])
    array_prerequisite(captured[c.ARRAY_CERTIFICATE],objects[c.ARRAY_CERTIFICATE],objects[c.ARRAY_SUPERVISOR],admission)
    pandas_raw=read_bound(c.runtime.PANDAS_ADMISSION,c.runtime.PANDAS_ADMISSION_SHA)
    pandas_certificate=c.decode(pandas_raw);loader.pandas_certificate_contract(pandas_certificate)
    loader._python_before_pandas(pandas_certificate)
    before=accepted_runtime(binding,'before_labels');pd=before['pd'];np=before['np']
    assert pd.__version__==pandas_certificate['pandas_version']
    assert str(Path(pd.__file__).resolve())==str(Path(pandas_certificate['pandas_module_path']).resolve())
    assert c.sha(guard.guarded_bytes(Path(pd.__file__).resolve()))==pandas_certificate['pandas_module_sha256']
    # EXACT frozen read_csv usecols/low_memory/skiprows/to_numpy(float), unchanged.
    result,source_read=guard.guarded_payload(c.ROOT/c.CORE,c.CORE_SHA,
        lambda stream:parsers.pandas_effects(stream,pd,bundle['metadata']))
    ids=[row['intervention_id'] for row in bundle['metadata']['rows']]
    labels=serialize_original_result(result,np,ids)
    after=accepted_runtime(binding,'after_labels')
    assert after['np'] is np and after['pd'] is pd
    protected={'runtime_acceptance':before['fresh_origin_proof'],'runtime_acceptance_after_labels':after['fresh_origin_proof']}
    payload={'status':c.LABEL_STATUS,'invocation':c.INVOCATION,'generation_manifest_sha256':generation,
        'run_admission_sha256':run_sha,'birth_sha256':birth_sha,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'metadata_bundle_sha256':c.METADATA_SHA,'array_certificate_sha256':admission['input_pins'][c.ARRAY_CERTIFICATE],
        'array_supervisor_sha256':admission['input_pins'][c.ARRAY_SUPERVISOR],
        'label_request_sha256':admission['input_pins'][c.REQUEST],
        'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA,'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,
        'actual_origin_receipt_sha256':c.runtime.PROFILE_ORIGIN_SHA,'rows':len(ids),'original_row_ids_sha256':c.ROW_IDS_SHA,
        'metadata_sha256':bundle['contract']['metadata_sha256'],'labels_result':labels,'source_core_read':source_read,
        'actual_feature_reads':0,'models_fitted':0,'label_access_does_not_authorize_fitting':True,
        'runtime_imports_accepted_not_historical_bitwise_parity':True,'resource_exception_applies':True,
        'parent_pid':__import__('os').getppid(),'worker_pid':__import__('os').getpid()}
    annotated=session.annotate(payload)
    assert annotated['source_core_read']['fresh_original_resource_gate_before_open'] is False
    assert c.canonical(annotated['labels_result'])==c.canonical(labels)
    annotated.update(protected)
    annotated['protected_runtime_payloads_sha256']=c.sha(c.canonical(protected))
    return annotated


def validate_certificate(value,generation,run_sha,birth_sha):
    assert value['status']==c.LABEL_STATUS and value['invocation']==c.INVOCATION
    assert value['generation_manifest_sha256']==generation and value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA and value['authorization_sha256']==c.AUTH_SHA
    assert value['approval_scope_sha256']==c.SCOPE_SHA
    admission=c.read_run(generation,run_sha)
    for key,path in (('array_certificate_sha256',c.ARRAY_CERTIFICATE),('array_supervisor_sha256',c.ARRAY_SUPERVISOR),('label_request_sha256',c.REQUEST)):
        assert value[key]==admission['input_pins'][path]
    assert value['metadata_bundle_sha256']==c.METADATA_SHA and value['rows']==c.COUNT
    assert value['original_row_ids_sha256']==c.ROW_IDS_SHA
    assert value['metadata_sha256']==c.METADATA_CONTENT_SHA
    labels=value['labels_result'];ids=labels['intervention_ids'];effects=labels['measured_delta']
    assert len(ids)==len(set(ids))==len(effects)==c.COUNT
    assert c.sha('|'.join(ids).encode())==c.ROW_IDS_SHA
    assert all(type(effect) is float and math.isfinite(effect) for effect in effects)
    assert c.sha(b''.join(struct.pack('<d',effect) for effect in effects))==labels['parsed_effects_float64_sha256']
    assert labels['numeric_outcome_rows_admitted']==c.COUNT and labels['parser']==c.PARSER
    assert labels['original_truth_orientation'] is True and labels['old_interpreter_bitwise_parity_established'] is False
    assert labels['pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'] is True
    assert value['models_fitted']==value['actual_feature_reads']==0 and value['label_access_does_not_authorize_fitting'] is True
    assert value['source_core_read']['actual_sha256']==c.CORE_SHA and value['source_core_read']['raw_bytes_traversed']>0
    assert value['source_core_read']['fresh_original_resource_gate_before_open'] is False
    assert value['original_resource_guards_unchanged'] is False and value['resource_exception_applies'] is True
    protected={name:value[name] for name in ('runtime_acceptance','runtime_acceptance_after_labels')}
    assert c.sha(c.canonical(protected))==value['protected_runtime_payloads_sha256']
    for phase,name in (('before_labels','runtime_acceptance'),('after_labels','runtime_acceptance_after_labels')):
        proof=protected[name]
        assert proof['status']==c.runtime.PROVIDER_STATUS and proof['phase']==phase
        assert proof['request_binding']['request_sha256']==value['label_request_sha256']
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
        assert proof['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA
        assert proof['software_certificate_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['request_binding']['request_relative_path']==c.REQUEST
        assert proof['request_binding']['provider_preparation_manifest_sha256']==c.RUNTIME_PREPARATION_SHA
        assert proof['request_binding']['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA
        assert proof['request_binding']['pandas_admission_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['same_owned_software_objects_retained'] is True and proof['source_cache_remained_absent'] is True
        assert proof['numpy_version']=='1.26.4' and proof['pandas_version']=='2.2.3'
        assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
        assert proof['old_interpreter_bitwise_parity_established'] is False and proof['model_fits']==0
    assert protected['runtime_acceptance']['request_binding']==protected['runtime_acceptance_after_labels']['request_binding']
    calibration=value['resource_calibration']
    assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['birth_sha256']==birth_sha and calibration['authorization_sha256']==c.AUTH_SHA
    assert calibration['invocation']==c.INVOCATION and calibration['scientific_protocol_settings_changed'] is False
    assert calibration['approved_policy_manifest_sha256']==c.POLICY_SHA and calibration['approval_scope_sha256']==c.SCOPE_SHA
    assert type(value['parent_pid']) is type(value['worker_pid']) is int
    assert value['parent_pid']>0 and value['worker_pid']>0
    assert calibration['current_pid']==value['worker_pid'] and calibration['parent_pid']==value['parent_pid']
    return value
