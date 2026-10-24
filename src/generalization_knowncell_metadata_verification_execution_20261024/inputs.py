"""Bound corrected-acquisition JSON provenance, never a file reader."""
from . import common as c


def verify_acquisition(raw_inputs,admission):
    assert set(raw_inputs)==set(c.INPUT_PATHS)
    values={}
    for key,path in c.INPUT_PATHS.items():
        raw=raw_inputs[key];assert type(raw) is bytes
        assert c.sha(raw)==admission['input_pins'][path]
        values[key]=c.decode(raw)
    manifest=values['acquisition_generation_manifest']
    assert c.sha(raw_inputs['acquisition_generation_manifest'])==admission['acquisition_generation_manifest_sha256']==c.ACQ_GENERATION_SHA
    assert manifest['status']=='PROPOSED_ONE_CORRECTED_METADATA_ACQUISITION_AWAITING_ADDITIONAL_HUMAN_APPROVAL'
    assert manifest['stages']==manifest['implemented_entrypoints']==['metadata']
    assert manifest['original_resource_manifest_sha256']==c.POLICY_SHA
    assert manifest['original_resource_authorization_sha256']==c.AUTH_SHA
    assert manifest['original_resource_scope_sha256']==c.SCOPE_SHA
    assert manifest['resource_policy']==c.resource_policy()
    assert manifest['files']['src/'+c.ACQ_NS+'/worker.py']
    c.valid_sha(manifest['files']['src/'+c.ACQ_NS+'/worker.py'])
    retry_auth=values['acquisition_retry_authorization']
    retry_auth_sha=c.sha(raw_inputs['acquisition_retry_authorization'])
    assert retry_auth_sha==admission['acquisition_retry_authorization_sha256']
    assert retry_auth['status']=='EXACT_HUMAN_ONE_CORRECTED_METADATA_APPROVAL_RECORDED'
    assert retry_auth['answer']=='Approve one corrected metadata acquisition'
    assert retry_auth['execution_manifest_sha256']==admission['acquisition_generation_manifest_sha256']
    assert retry_auth['approved_stages']==['metadata'] and retry_auth['additional_owned_invocations']==1
    assert retry_auth['original_resource_execution_manifest_sha256']==c.POLICY_SHA
    assert retry_auth['original_resource_authorization_sha256']==c.AUTH_SHA
    assert retry_auth['original_resource_scope_sha256']==c.SCOPE_SHA
    assert retry_auth['resource_policy']==c.resource_policy()
    assert retry_auth['label_access_authorized'] is retry_auth['model_fitting_authorized'] is False
    assert retry_auth['scientific_protocol_changes_authorized'] is False
    assert retry_auth['scheduled_tasks_authorized'] is False
    assert retry_auth['failed_metadata_supervisor_receipt_sha256']==manifest['preserved_failed_attempt'][
        'results/generalization_knowncell_bounded_execution_20261023/metadata_supervisor_receipt.json']
    assert retry_auth['spending_authorized'] is False and retry_auth['automatic_retry_authorized'] is False
    supervisor=values['acquisition_supervisor'];completion=values['acquisition_completion'];birth=values['acquisition_birth']
    assert supervisor['status']=='PASS_CALIBRATED_METADATA_PENDING_INDEPENDENT_RECONSTRUCTION'
    assert supervisor['failure'] is None and supervisor['worker_started'] is True
    assert completion['status']=='PASS_CALIBRATED_METADATA_WORKER_CALLBACKS_RESTORED'
    assert completion['callbacks_restored'] is True and completion['scientific_packages_imported'] is False
    assert type(completion['fresh_calibrated_guard_calls']) is int and completion['fresh_calibrated_guard_calls']>0
    generation=admission['acquisition_generation_manifest_sha256']
    birth_sha=c.sha(raw_inputs['acquisition_birth']);completion_sha=c.sha(raw_inputs['acquisition_completion'])
    bundle_sha=c.sha(raw_inputs['bundle'])
    for value in (supervisor,completion,birth):
        assert value['execution_manifest_sha256']==generation
        assert value['resource_policy']==c.resource_policy()
    assert supervisor['authorization_sha256']==birth['authorization_sha256']==retry_auth_sha
    assert completion['original_resource_manifest_sha256']==c.POLICY_SHA
    assert completion['original_resource_authorization_sha256']==c.AUTH_SHA
    assert birth['stage']=='metadata' and birth['automatic_retry'] is False
    assert supervisor['birth_sha256']==completion['birth_sha256']==birth_sha
    assert supervisor['worker_completion_sha256']==completion_sha
    assert supervisor['metadata_bundle_sha256']==completion['metadata_bundle_sha256']==bundle_sha
    assert completion['metadata_admission_sha256']==c.METADATA_ADMISSION_SHA
    for value in (supervisor,completion):
        assert value['original_3GiB_resource_guard_unchanged'] is False
        assert value['actual_feature_reads']==value['model_fits']==0
    assert supervisor['numerical_labels_admitted']==completion['numerical_outcome_rows_admitted']==0
    metadata_admission=values['metadata_admission']
    assert metadata_admission['status']=='FROZEN_METADATA_ADMISSION_JOINT_KNOWNCELL'
    assert metadata_admission['data_pins'][c.CORE]==c.CORE_SHA
    assert metadata_admission['label_access_authorized'] is False and metadata_admission['model_fitting_authorized'] is False
    bundle=values['bundle']
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    assert bundle['metadata_admission_sha256']==c.METADATA_ADMISSION_SHA and bundle['core_sha256']==c.CORE_SHA
    assert bundle['numeric_outcome_rows_admitted']==bundle['actual_feature_reads']==bundle['models_fitted']==0
    assert bundle['every_payload_open_fresh_original_resource_gated'] is False
    calibration=bundle['resource_calibration']
    assert calibration['execution_manifest_sha256']==generation
    assert calibration['authorization_sha256']==retry_auth_sha
    assert calibration['scientific_metadata_and_contracts_unchanged'] is True
    assert calibration['birth_sha256']==birth_sha and calibration['stage']=='metadata'
    normalization=completion['metadata_serialization_normalization']
    assert normalization==bundle['metadata_serialization_normalization']
    assert normalization['status']=='PASS_EXACT_ORIGINAL_JSON_METADATA_SERIALIZATION_NORMALIZATION'
    assert normalization['before_canonical_sha256']==normalization['after_canonical_sha256']
    c.valid_sha(normalization['before_canonical_sha256'])
    assert normalization['only_original_JSON_tuple_to_array_semantics'] is True
    assert normalization['scientific_values_or_hashes_changed'] is False
    assert normalization['metadata_canonical_sha256']==c.sha(c.canonical(bundle['metadata']))
    assert normalization['contract_canonical_sha256']==c.sha(c.canonical(bundle['contract']))
    return bundle
