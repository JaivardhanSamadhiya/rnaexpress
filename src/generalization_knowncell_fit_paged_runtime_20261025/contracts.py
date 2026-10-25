"""Prospective FIT request; runtime declarations never grant actual authority."""
from src.generalization_knowncell_runtime_provider_20261023.contracts import (
    canonical,digest,decode,hash_contract,relative,software_contract,fresh_proof_contract)
from .spec import *


def binding_contract(value):
    assert isinstance(value,dict) and set(value)==FIELDS and value['request_relative_path']==REQUEST
    for key in FIELDS-{'request_relative_path'}:hash_contract(value[key])
    assert value['software_status_sha256']==SOFTWARE_STATUS_SHA and value['pandas_admission_sha256']==PANDAS_ADMISSION_SHA
    return decode(canonical(value))


def request_contract(value,binding,source_sha):
    assert value['namespace']=='generalization_knowncell_fit_paged_execution_20261025' and value['status']==REQUEST_STATUS
    assert value['stage']=='fit' and value['invocation']=='fixed_63_checkpoint_84_optimizer_unit_fit' and value['numerical_threads']==1
    for key in ('runtime_import_authorized','array_reload_authorized','saved_label_read_authorized',
                'pool_preparation_authorized','model_fitting_authorized'):assert value[key] is True
    assert value['CORE_read_authorized'] is False
    assert value['checkpoint_refresh_keys']==list(CHECKPOINT_KEYS) and value['optimizer_units']==84
    assert value['software_status_sha256']==SOFTWARE_STATUS_SHA and value['software_certificate_sha256']==PANDAS_ADMISSION_SHA
    assert value['provider_preparation_manifest_sha256']==binding['provider_preparation_manifest_sha256']
    assert value['provider_binding']=={'source_path':SOURCE,'source_sha256':hash_contract(source_sha),
        'module':MODULE,'qualname':'provide','reviewed_deferred_only':True}
    assert value['approved_policy_manifest_sha256']=='a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
    assert value['authorization_sha256']=='b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3'
    for key in ('generation_manifest_sha256','static_root_binding_sha256','controller_source_admission_sha256',
                'stable_admitted_runtime_binding_sha256','actual_prefit_sha256','projection_root_admission_sha256'):
        hash_contract(value[key])
    assert not {'caller_birth_sha256','current_stage_origin_proof_sha256','run_admission_sha256'} & set(value)
    return value
