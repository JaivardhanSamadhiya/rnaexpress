"""Prefit runtime software lineage, fixed caller and an acyclic request path."""
from src.generalization_knowncell_runtime_provider_20261023.spec import (
    ROOT,CACHE_PREFIX,SOFTWARE_STATUS,SOFTWARE_STATUS_SHA,PANDAS_ADMISSION,PANDAS_ADMISSION_SHA,
    PROFILE_OUT,PROFILE_MANIFEST,PROFILE_MANIFEST_SHA,PROFILE_ORIGIN,PROFILE_ORIGIN_SHA,BLOCKED)
NS='generalization_knowncell_prefit_runtime_20261024'
MODULE='src.'+NS+'.provider'
SOURCE='src/'+NS+'/provider.py'
PREPARATION='results/'+NS+'/preparation_manifest.json'
PREPARATION_STATUS='DEFERRED_PREFIT_CURRENT_RUNTIME_SOURCE_NOT_ACTUAL_ADMISSION'
REQUEST='results/generalization_knowncell_prefit_execution_20261024/prefit_runtime_request.json'
REQUEST_STATUS='FROZEN_PREFIT_RUNTIME_AND_ADMITTED_INPUT_RELOAD_REQUEST_NO_FIT'
PROVIDER_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_KNOWNCELL_STAGE'
CALLER='src.generalization_knowncell_prefit_execution_20261024.common'
CALLER_SOURCE=CALLER.replace('.','/')+'.py'
PHASES=('before_prefit','after_prefit')
FIELDS={'request_relative_path','request_sha256','provider_preparation_manifest_sha256',
        'software_status_sha256','pandas_admission_sha256'}
ORIGINAL_PROVIDER_PREPARATION='results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json'
ORIGINAL_PROVIDER_SHA='c10fd9e8f52095e2b8a5eae8b533ed4f66814090ab8844928af7c7392a18694f'


def static_allowed(name):
    from src.generalization_knowncell_runtime_provider_20261023.spec import static_allowed as original
    own=any(name.startswith(top+'/'+namespace+'/') for top in ('src','reports','results','artifacts')
        for namespace in (NS,'generalization_knowncell_prefit_execution_20261024'))
    return original(name) or own and name.endswith(('.py','.md','.json','/.gitattributes'))
