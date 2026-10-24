"""Bind already supplied admitted inputs, without reading labels or arrays."""
import math
import struct
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from .spec import *
from . import contracts as c


def root_bindings(expected):
    """Prospective root declaration, not an existing loader certificate schema."""
    assert isinstance(expected,dict) and set(expected)==set(BINDING_HASHES)
    for value in expected.values():c.valid_hash(value)
    assert expected['native_profile_receipt_sha256']==V4_ORIGIN_SHA
    return expected


def bridge_inputs(np,metadata_bundle_bytes,matrix,array_certificate_bytes,labels_result,fit_admission_bytes,*,
                  expected_bindings,root_start=False):
    """Return exact engine arguments/declaration; no prefit or fitting authority.

    expected_bindings must come from a future separately verified root input
    admission. It is NOT supplied by readiness or invented tests. Existing
    loader results gain no invented array/runtime fields in this function.
    """
    assert root_start is True
    c.fresh();expected=root_bindings(expected_bindings)
    c.committed_bytes(METADATA_PATH,metadata_bundle_bytes,expected['metadata_bundle_sha256'])
    c.committed_bytes(ARRAY_PATH,array_certificate_bytes,expected['array_certificate_sha256'])
    c.committed_bytes(FIT_PATH,fit_admission_bytes,expected['fit_label_admission_sha256'])
    bundle=c.decode(metadata_bundle_bytes);array=c.decode(array_certificate_bytes);fit=c.decode(fit_admission_bytes)
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    assert bundle['numeric_outcome_rows_admitted']==bundle['actual_feature_reads']==bundle['models_fitted']==0
    assert bundle['core_sha256']==CORE_SHA and bundle['declared_simple102_sha256_not_loaded']==NPZ_SHA
    rows=bundle['metadata']['rows'];ids=[row['intervention_id'] for row in rows]
    c.fresh();contract=reference.full_metadata_contract(rows)
    assert c.canonical(contract)==c.canonical(bundle['contract'])
    assert reference.ids_sha(rows)==bundle['metadata']['row_ids_sha256']==ROW_IDS_SHA
    assert array['status']==ARRAY_STATUS and array['actual_npz_sha256']==NPZ_SHA
    assert array['metadata_bundle_sha256']==expected['metadata_bundle_sha256']
    assert array['rows']==COUNTS['rows'] and array['columns']==COUNTS['columns']
    assert array['same_allele_feature_bytes_equal'] is True
    assert array['original_row_ids_sha256']==ROW_IDS_SHA
    assert array['underlying_report']['creation_identity']['supplied_metadata_sha256']==contract['metadata_sha256']
    assert array['numeric_labels_admitted'] is False and array['FIT_admission_granted'] is False and array['models_fitted']==0
    assert array['software_status_sha256']==SOFTWARE_STATUS_SHA and array['software_certificate_sha256']==PANDAS_SHA
    proof=array['runtime_acceptance_after_array']
    c.fresh();runtime_sha=c.runtime_contract(np,proof)
    assert runtime_sha==expected['runtime_binding_sha256']
    assert proof['request_binding']['request_sha256']==array['array_request_sha256']
    assert fit['namespace']=='generalization_knowncell_joint_loader_20261022' and fit['mode']=='fit_labels'
    assert fit['status']=='FROZEN_MIKL_MEAN_EFFECT_ADMISSION_JOINT_KNOWNCELL'
    assert fit['label_access_authorized'] is True and fit['model_fitting_authorized'] is False
    assert fit['PUM_resource_exception_applies'] is False and fit['numerical_threads']==1
    assert fit['metadata_bundle_sha256']==expected['metadata_bundle_sha256']
    assert fit['array_admission_sha256']==expected['array_certificate_sha256'] and fit['pandas_admission_sha256']==PANDAS_SHA
    assert fit['data_pins'][CORE_PATH]==CORE_SHA
    assert labels_result['fit_label_admission_sha256']==expected['fit_label_admission_sha256']
    assert labels_result['metadata_bundle_sha256']==expected['metadata_bundle_sha256'] and labels_result['pandas_admission_sha256']==PANDAS_SHA
    assert labels_result['source_core_read']['actual_sha256']==CORE_SHA
    assert labels_result['source_core_read']['fresh_original_resource_gate_before_open'] is True
    assert labels_result['source_core_read']['raw_bytes_traversed']>0
    assert labels_result['intervention_ids']==ids,'Original parsed labels must retain exact full ID/order'
    assert labels_result['numeric_outcome_rows_admitted']==len(ids)==COUNTS['rows']
    assert labels_result['parser']=='original_pandas_default_read_csv_low_memory_False_then_to_numpy_float'
    assert labels_result['original_truth_orientation'] is True and labels_result['old_interpreter_bitwise_parity_established'] is False
    assert labels_result['pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'] is True
    assert labels_result['actual_feature_reads']==labels_result['models_fitted']==0
    assert labels_result['label_access_does_not_authorize_fitting'] is True
    vector=labels_result['measured_delta']
    # No array() cast and no label reparsing. These must be actual admitted
    # ordinary native float64 ndarrays from the unchanged original parser/load.
    assert type(matrix) is np.ndarray and type(vector) is np.ndarray
    assert matrix.shape==(COUNTS['rows'],COUNTS['columns']) and vector.shape==(COUNTS['rows'],)
    for value in (matrix,vector):
        assert value.dtype.kind=='f' and value.dtype.itemsize==8 and value.dtype.isnative and not value.dtype.hasobject
    c.fresh();assert np.isfinite(matrix).all()
    c.fresh();matrix_bytes=matrix.tobytes(order='C')
    assert c.digest(matrix_bytes)==array['underlying_report']['post_original_astype_float_C_bytes_sha256'],'Supplied array scalar bits changed'
    c.fresh();values=vector.tolist() # This is the ONLY label conversion.
    assert isinstance(values,list) and len(values)==len(ids) and all(type(value) is float and math.isfinite(value) for value in values)
    original_label_bytes=b''.join(struct.pack('<d',value) for value in values)
    assert c.digest(original_label_bytes)==labels_result['parsed_effects_float64_sha256'],'Original parsed label bits changed'
    effects=dict(zip(ids,values));assert len(effects)==len(ids) and set(effects)==set(ids)
    admissions={'status':'ADMITTED_MIKL_METADATA_SIMPLE102_ORIGINAL_EFFECTS',
        'runtime_binding_sha256':runtime_sha,'metadata_admission_sha256':bundle['metadata_admission_sha256'],
        'feature_admission_sha256':expected['array_certificate_sha256'],'label_admission_sha256':expected['fit_label_admission_sha256'],
        'fit_source_manifest_sha256':expected['fit_source_manifest_sha256'],
        'native_profile_receipt_sha256':expected['native_profile_receipt_sha256'],
        'original_sampler_source_sha256':MODEL_SHA,'numeric_source_manifest_sha256':expected['numeric_source_manifest_sha256'],
        'lifecycle_v2_manifest_sha256':expected['lifecycle_v2_manifest_sha256'],
        'input_row_ids_sha256':reference.ids_sha(rows),'input_metadata_sha256':reference.metadata_sha(rows),
        'input_features_sha256':c.bits_hash(matrix_bytes,matrix.shape),'input_effects_sha256':c.bits_hash(original_label_bytes,vector.shape)}
    for name,value in admissions.items():
        if name.endswith('_sha256'):c.valid_hash(value)
    c.fresh()
    return {'metadata':rows,'features':matrix,'effects':effects,'admissions':admissions,
        'bridge_report':{'status':'BRIDGED_SUPPLIED_ADMITTED_INPUTS_NOT_COMMITTED_PREFIT_OR_FIT_PERMISSION',
            'rows':len(ids),'columns':COUNTS['columns'],'row_order_preserved':True,
            'array_bits_rechecked':True,'original_parser_effect_bits_rechecked':True,'original_vector_tolist_only':True,
            'metadata_bundle_sha256':expected['metadata_bundle_sha256'],'array_certificate_sha256':expected['array_certificate_sha256'],
            'future_root_binding_declaration_verified_by_caller_required':True,
            'committed_prefit_created':False,'input_admission_certificate_persisted':False,
            'source_pool_preparation_run':False,'sampler_called':False,'optimizer_calls':0,
            'independent_replay_complete':False,'gate_evaluated':False,'training_authorized_here':False}}
