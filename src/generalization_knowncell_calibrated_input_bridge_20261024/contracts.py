"""Supplied schemas plus original actual guard/committed-byte helpers.

No current parent/Job admission or runtime-origin verifier is manufactured here.
Those are mandatory preconditions of the separately reviewed owned caller.
"""
import os
from src.generalization_knowncell_joint_input_bridge_20261023 import contracts as original
from src.generalization_knowncell_bounded_execution_20261023.common import canonical as operational_canonical
from .spec import *

canonical=original.canonical
decode=original.decode
digest=original.digest
valid_hash=original.valid_hash
fresh=original.fresh
committed_bytes=original.committed_bytes
bits_hash=original.bits_hash
runtime_contract=original.runtime_contract


def binding_contract(value):
    fields={'status','namespace','stage','reviewed_controller_source',
        'reviewed_owned_caller_required','runtime_and_FIT_authority_granted_here',
        'approved_policy_manifest_sha256','authorization_sha256','approval_scope_sha256',*HASH_FIELDS}
    assert isinstance(value,dict) and set(value)==fields
    assert value['status']==BINDING_STATUS and value['namespace']==NS and value['stage'] in STAGES
    assert value['reviewed_owned_caller_required'] is True
    assert value['runtime_and_FIT_authority_granted_here'] is False
    for key in HASH_FIELDS:valid_hash(value[key])
    name=value['reviewed_controller_source']
    assert isinstance(name,str) and name.startswith('src/generalization_knowncell_') and name.endswith('.py')
    assert name==name.replace('\\','/') and ':' not in name and all(p not in ('','.','..') for p in name.split('/'))
    assert value['array_certificate_sha256']==ARRAY_SHA
    assert value['native_profile_receipt_sha256']==V4_ORIGIN_SHA
    assert value['approved_policy_manifest_sha256']==POLICY_SHA
    assert value['authorization_sha256']==AUTH_SHA and value['approval_scope_sha256']==SCOPE_SHA
    return value


def current_stage_contract(np,proof,binding):
    """Check supplied proof identity/schema, NOT actually inspect loaded DLLs.

    The genuine owned controller must run its separately reviewed current-origin
    verifier and owner checks before this bridge. A matching dictionary is not
    independently a runtime/Job certificate; the output expressly says so.
    """
    assert digest(canonical(proof))==binding['current_stage_origin_proof_sha256']
    assert proof['status']==STAGE_PROOF_STATUS and proof['stage']==binding['stage']
    assert proof['phase']=='before_supplied_input_bridge'
    assert proof['current_pid']==os.getpid() and proof['parent_pid']==os.getppid()
    assert proof['caller_birth_sha256']==binding['caller_birth_sha256']
    assert proof['reviewed_controller_admission_sha256']==binding['reviewed_controller_admission_sha256']
    assert proof['stable_admitted_runtime_binding_sha256']==binding['runtime_binding_sha256']
    assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
    assert proof['software_status_sha256']==SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==PANDAS_SHA
    assert proof['actual_origin_receipt_sha256']==V4_ORIGIN_SHA
    assert proof['numpy_module_path']==str(NUMPY_PATH) and proof['numpy_module_sha256']==NUMPY_SHA
    assert proof['numpy_version']=='1.26.4' and proof['pandas_version']=='2.2.3' and proof['scipy_version']=='1.14.1'
    assert proof['numerical_threads']==1 and proof['source_cache_remained_absent'] is True
    assert proof['old_interpreter_bitwise_parity_established'] is False
    assert proof['runtime_and_FIT_authority_granted_here'] is False
    assert isinstance(proof['UTC'],str) and proof['UTC']
    assert np.__name__=='numpy' and np.__version__=='1.26.4'
    from pathlib import Path
    assert Path(np.__file__).resolve()==NUMPY_PATH.resolve()


def calibrated_certificate(value,stage,invocation):
    assert value['approved_policy_manifest_sha256']==POLICY_SHA
    assert value['authorization_sha256']==AUTH_SHA and value['approval_scope_sha256']==SCOPE_SHA
    for name in ('generation_manifest_sha256','run_admission_sha256','birth_sha256'):valid_hash(value[name])
    assert value['invocation']==invocation
    assert value['resource_exception_applies'] is True and value['original_resource_guards_unchanged'] is False
    calibration=value['resource_calibration']
    assert calibration['status']=='EXPLICITLY_AUTHORIZED_BOUNDED_KNOWNCELL_RESOURCE_CALIBRATION'
    assert calibration['stage']==stage and calibration['invocation']==invocation
    assert calibration['execution_manifest_sha256']==value['generation_manifest_sha256']
    assert calibration['authorization_sha256']==AUTH_SHA and calibration['birth_sha256']==value['birth_sha256']
    assert calibration['scientific_protocol_settings_changed'] is False
    assert calibration['scientific_metadata_and_contracts_unchanged'] is True
    assert calibration['startup_physical_floor']==512*2**20 and calibration['live_physical_floor']==256*2**20
    assert calibration['disk_floor']==calibration['live_global_commit_reserve']==2**30
    assert calibration['callbacks_restored_at_annotation'] is False
    assert type(calibration['fresh_calibrated_guard_calls']) is int and calibration['fresh_calibrated_guard_calls']>0
    assert calibration['hard_job_caps_and_continuous_monitoring_owned_by_controller'] is True
    for name in ('worker_pid','parent_pid'):assert type(value[name]) is int and value[name]>0
    assert calibration['current_pid']==value['worker_pid'] and calibration['parent_pid']==value['parent_pid']


def protected_label_proofs(value):
    protected={key:value[key] for key in ('runtime_acceptance','runtime_acceptance_after_labels')}
    assert digest(operational_canonical(protected))==value['protected_runtime_payloads_sha256']
    before=protected['runtime_acceptance'];after=protected['runtime_acceptance_after_labels']
    assert before['request_binding']==after['request_binding']
    for key,phase in (('runtime_acceptance','before_labels'),('runtime_acceptance_after_labels','after_labels')):
        proof=protected[key]
        assert proof['status']==LABEL_PROVIDER_STATUS and proof['phase']==phase
        assert proof['request_binding']['request_relative_path']==LABEL_REQUEST
        assert proof['request_binding']['request_sha256']==value['label_request_sha256']
        assert proof['request_binding']['software_status_sha256']==SOFTWARE_STATUS_SHA
        assert proof['request_binding']['pandas_admission_sha256']==PANDAS_SHA
        valid_hash(proof['request_binding']['provider_preparation_manifest_sha256'])
        assert proof['actual_origin_receipt_sha256']==V4_ORIGIN_SHA
        assert proof['software_status_sha256']==SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==PANDAS_SHA
        assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
        assert proof['same_owned_software_objects_retained'] is True and proof['source_cache_remained_absent'] is True
        assert proof['numpy_version']=='1.26.4' and proof['pandas_version']=='2.2.3'
        assert proof['old_interpreter_bitwise_parity_established'] is False and proof['model_fits']==0
