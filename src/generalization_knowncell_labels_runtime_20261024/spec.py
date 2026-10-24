"""Only software constants; no payloads or scientific imports."""
from src.generalization_knowncell_runtime_provider_20261023.spec import (
    ROOT,CACHE_PREFIX,SOFTWARE_STATUS,SOFTWARE_STATUS_SHA,PANDAS_ADMISSION,PANDAS_ADMISSION_SHA,
    PROFILE_OUT,PROFILE_MANIFEST,PROFILE_MANIFEST_SHA,PROFILE_ORIGIN,PROFILE_ORIGIN_SHA,BLOCKED)

NS='generalization_knowncell_labels_runtime_20261024'
MODULE='src.'+NS+'.provider'
SOURCE='src/'+NS+'/provider.py'
PREPARATION='results/'+NS+'/preparation_manifest.json'
PREPARATION_STATUS='DEFERRED_LABELS_CURRENT_RUNTIME_SOURCE_NOT_ACTUAL_ADMISSION'
REQUEST='results/generalization_knowncell_labels_execution_20261024/label_request_manifest.json'
REQUEST_STATUS='FROZEN_ORIGINAL_PANDAS_LABEL_ONLY_REQUEST_NO_FIT'
PROVIDER_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_LABEL_REQUEST'
PHASES=('before_labels','after_labels')
FIELDS={'request_relative_path','request_sha256','provider_preparation_manifest_sha256',
        'software_status_sha256','pandas_admission_sha256'}
ORIGINAL_PROVIDER_PREPARATION='results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json'
ORIGINAL_PROVIDER_SHA='c10fd9e8f52095e2b8a5eae8b533ed4f66814090ab8844928af7c7392a18694f'


def static_allowed(name):
    from src.generalization_knowncell_runtime_provider_20261023.spec import static_allowed as original
    return original(name) or any(name.startswith(top+'/'+NS+'/') for top in ('src','reports','results','artifacts')) and name.endswith(('.py','.md','.json','/.gitattributes'))
