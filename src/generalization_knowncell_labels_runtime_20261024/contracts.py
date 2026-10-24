"""Pure labels request schemas; all runtime acceptance remains actual work."""
from src.generalization_knowncell_runtime_provider_20261023.contracts import (
    canonical,digest,decode,hash_contract,relative,software_contract,fresh_proof_contract)
from .spec import *


def binding_contract(binding):
    assert isinstance(binding,dict) and set(binding)==FIELDS
    assert binding['request_relative_path']==REQUEST
    for key in FIELDS-{'request_relative_path'}:hash_contract(binding[key])
    assert binding['software_status_sha256']==SOFTWARE_STATUS_SHA
    assert binding['pandas_admission_sha256']==PANDAS_ADMISSION_SHA
    return decode(canonical(binding))


def request_contract(value,binding,source_sha):
    assert value['namespace']=='generalization_knowncell_labels_execution_20261024'
    assert value['status']==REQUEST_STATUS and value['runtime_import_authorized'] is True
    assert value['label_access_authorized'] is True and value['model_fitting_authorized'] is False
    assert value['numerical_threads']==1
    assert value['software_status_sha256']==SOFTWARE_STATUS_SHA
    assert value['software_certificate_sha256']==PANDAS_ADMISSION_SHA
    assert value['provider_preparation_manifest_sha256']==binding['provider_preparation_manifest_sha256']
    assert value['provider_binding']=={'source_path':SOURCE,'source_sha256':hash_contract(source_sha),
        'module':MODULE,'qualname':'provide','reviewed_deferred_only':True}
    assert value['resource_policy_manifest_sha256']=='a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
    assert value['authorization_sha256']=='b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3'
    assert value['invocation']=='original_pandas_label_admission'
    for key in ('generation_manifest_sha256','metadata_bundle_sha256','array_certificate_sha256','array_supervisor_sha256'):
        hash_contract(value[key])
    return value
