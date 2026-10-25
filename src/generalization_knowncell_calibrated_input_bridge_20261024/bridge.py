"""Validate supplied exact admitted objects; no reader/bootstrap/pool/fit CLI."""
import math
import struct
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from .spec import *
from . import contracts as c


def bridge_inputs(np,metadata_bundle_bytes,matrix,array_certificate_bytes,label_certificate_bytes,
                  root_binding_bytes,current_stage_origin_proof,*,root_start=False):
    """Return original engine arguments, never runtime/input/FIT permission.

    A reviewed actually owned caller must first verify its real parent Job,
    birth, source/admission closure and current process native origins. This
    library verifies committed supplied identities and schemas, not that
    caller's execution. No caller-supplied resource/probe callback exists.
    """
    assert root_start is True
    c.fresh()
    binding=c.binding_contract(c.decode(root_binding_bytes))
    c.committed_bytes(binding_path(binding['stage']),root_binding_bytes)
    c.committed_bytes(METADATA_PATH,metadata_bundle_bytes,binding['metadata_bundle_sha256'])
    c.committed_bytes(ARRAY_PATH,array_certificate_bytes,binding['array_certificate_sha256'])
    c.committed_bytes(LABEL_PATH,label_certificate_bytes,binding['label_certificate_sha256'])
    c.current_stage_contract(np,current_stage_origin_proof,binding)
    bundle=c.decode(metadata_bundle_bytes);array=c.decode(array_certificate_bytes);labels=c.decode(label_certificate_bytes)
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    assert bundle['numeric_outcome_rows_admitted']==bundle['actual_feature_reads']==bundle['models_fitted']==0
    assert bundle['core_sha256']==CORE_SHA and bundle['declared_simple102_sha256_not_loaded']==NPZ_SHA
    rows=bundle['metadata']['rows'];ids=[row['intervention_id'] for row in rows]
    c.fresh();contract=reference.full_metadata_contract(rows)
    assert c.canonical(contract)==c.canonical(bundle['contract'])
    assert reference.ids_sha(rows)==bundle['metadata']['row_ids_sha256']==ROW_IDS_SHA
    assert array['status']==ARRAY_STATUS and array['actual_npz_sha256']==NPZ_SHA
    c.calibrated_certificate(array,'array','array_admission')
    assert array['metadata_bundle_sha256']==binding['metadata_bundle_sha256']
    assert array['rows']==COUNTS['rows'] and array['columns']==COUNTS['columns']
    assert array['same_allele_feature_bytes_equal'] is True and array['original_row_ids_sha256']==ROW_IDS_SHA
    assert array['underlying_report']['creation_identity']['supplied_metadata_sha256']==contract['metadata_sha256']
    assert array['numeric_labels_admitted'] is array['FIT_admission_granted'] is False and array['models_fitted']==0
    assert array['software_status_sha256']==SOFTWARE_STATUS_SHA and array['software_certificate_sha256']==PANDAS_SHA
    stable_proof=array['runtime_acceptance_after_array']
    c.fresh();stable_runtime_sha=c.runtime_contract(np,stable_proof)
    assert stable_runtime_sha==binding['runtime_binding_sha256']
    assert stable_proof['request_binding']['request_sha256']==array['array_request_sha256']
    assert labels['status']==LABEL_STATUS
    c.calibrated_certificate(labels,'labels','original_pandas_label_admission')
    for key in ('metadata_bundle_sha256','array_certificate_sha256','array_supervisor_sha256'):
        assert labels[key]==binding[key],key
    assert labels['rows']==len(ids)==COUNTS['rows'] and labels['original_row_ids_sha256']==ROW_IDS_SHA
    assert labels['metadata_sha256']==contract['metadata_sha256']
    assert labels['pandas_admission_sha256']==PANDAS_SHA and labels['software_status_sha256']==SOFTWARE_STATUS_SHA
    assert labels['actual_origin_receipt_sha256']==V4_ORIGIN_SHA
    c.valid_hash(labels['label_request_sha256'])
    assert labels['models_fitted']==labels['actual_feature_reads']==0
    assert labels['label_access_does_not_authorize_fitting'] is True
    source=labels['source_core_read']
    assert source['actual_sha256']==CORE_SHA and type(source['raw_bytes_traversed']) is int and source['raw_bytes_traversed']>0
    assert source['fresh_original_resource_gate_before_open'] is False
    c.protected_label_proofs(labels)
    original=labels['labels_result'];assert isinstance(original,dict) and set(original)==LABEL_KEYS
    assert original['intervention_ids']==ids,'Original label IDs/order changed'
    assert original['numeric_outcome_rows_admitted']==len(ids)
    assert original['parser']==PARSER and original['original_truth_orientation'] is True
    assert original['old_interpreter_bitwise_parity_established'] is False
    assert original['pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'] is True
    values=original['measured_delta']
    assert type(values) is list and len(values)==len(ids)
    assert all(type(value) is float and math.isfinite(value) for value in values),'Finite JSON float list required'
    original_label_bytes=b''.join(struct.pack('<d',value) for value in values)
    assert c.digest(original_label_bytes)==original['parsed_effects_float64_sha256'],'Original parsed label scalar bits changed'
    assert type(matrix) is np.ndarray and matrix.shape==(COUNTS['rows'],COUNTS['columns'])
    assert matrix.dtype.kind=='f' and matrix.dtype.itemsize==8 and matrix.dtype.isnative and not matrix.dtype.hasobject
    c.fresh();matrix_bytes=matrix.tobytes(order='C')
    assert type(matrix_bytes) is bytes and len(matrix_bytes)==8*len(ids)*COUNTS['columns']
    assert all(math.isfinite(value) for (value,) in struct.iter_unpack('<d',matrix_bytes))
    assert c.digest(matrix_bytes)==array['underlying_report']['post_original_astype_float_C_bytes_sha256'],'Supplied matrix scalar bits changed'
    effects=dict(zip(ids,values));assert len(effects)==len(ids)
    admissions={'status':'ADMITTED_MIKL_METADATA_SIMPLE102_ORIGINAL_EFFECTS',
        'runtime_binding_sha256':stable_runtime_sha,'metadata_admission_sha256':bundle['metadata_admission_sha256'],
        'feature_admission_sha256':binding['array_certificate_sha256'],'label_admission_sha256':binding['label_certificate_sha256'],
        'fit_source_manifest_sha256':binding['fit_source_manifest_sha256'],
        'native_profile_receipt_sha256':binding['native_profile_receipt_sha256'],
        'original_sampler_source_sha256':MODEL_SHA,'numeric_source_manifest_sha256':binding['numeric_source_manifest_sha256'],
        'lifecycle_v2_manifest_sha256':binding['lifecycle_v2_manifest_sha256'],
        'input_row_ids_sha256':reference.ids_sha(rows),'input_metadata_sha256':reference.metadata_sha(rows),
        'input_features_sha256':c.bits_hash(matrix_bytes,matrix.shape),
        'input_effects_sha256':c.bits_hash(original_label_bytes,(len(ids),))}
    for name,value in admissions.items():
        if name.endswith('_sha256'):c.valid_hash(value)
    c.fresh()
    return {'metadata':rows,'features':matrix,'effects':effects,'admissions':admissions,
        'bridge_report':{'status':'BRIDGED_SUPPLIED_CALIBRATED_INPUTS_NOT_PREFIT_RUNTIME_OR_FIT_AUTHORITY',
            'rows':len(ids),'columns':COUNTS['columns'],'row_order_preserved':True,
            'matrix_object_returned_unchanged':True,'array_scalar_bits_rechecked':True,
            'persisted_original_parser_label_bits_rechecked':True,'label_reparse_recast_or_recomputation':False,
            'root_binding_sha256':c.digest(root_binding_bytes),'stage':binding['stage'],
            'stable_admitted_runtime_binding_sha256':stable_runtime_sha,
            'current_stage_origin_proof_sha256':binding['current_stage_origin_proof_sha256'],
            'current_stage_origin_proof_schema_and_hash_checked':True,
            'actual_native_origin_verification_performed_here':False,
            'actual_parent_Job_or_reviewed_caller_execution_certified_here':False,
            'reviewed_owned_caller_admission_and_fresh_origin_verification_required':True,
            'committed_prefit_created':False,'runtime_or_input_or_FIT_authority_granted_here':False,
            'CORE_or_NPZ_payload_opened_here':False,'sampler_or_pool_preparation_run':False,
            'optimizer_calls':0,'evaluation_or_gate_run':False}}
