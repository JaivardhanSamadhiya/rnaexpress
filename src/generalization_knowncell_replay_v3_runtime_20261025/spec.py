"""Fixed FIT software lineage and exactly63 source-bound refresh positions."""
from src.generalization_knowncell_runtime_provider_20261023.spec import (
    ROOT,CACHE_PREFIX,SOFTWARE_STATUS,SOFTWARE_STATUS_SHA,PANDAS_ADMISSION,PANDAS_ADMISSION_SHA,
    PROFILE_OUT,PROFILE_MANIFEST,PROFILE_MANIFEST_SHA,PROFILE_ORIGIN,PROFILE_ORIGIN_SHA,BLOCKED)
from src.generalization_knowncell_joint_campaign_20261023.contracts import task_roster,task_key
NS='generalization_knowncell_replay_v3_runtime_20261025'
MODULE='src.'+NS+'.provider'
SOURCE='src/'+NS+'/provider.py'
PREPARATION='results/'+NS+'/preparation_manifest.json'
PREPARATION_STATUS='DEFERRED_INDEPENDENT_REPLAY_RUNTIME_SOURCE_NOT_ACTUAL_ADMISSION'
REQUEST='results/generalization_knowncell_replay_v3_execution_20261025/replay_runtime_request.json'
REQUEST_STATUS='FROZEN_INDEPENDENT63_CHECKPOINT_REPLAY_RUNTIME_REQUEST'
PROVIDER_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_KNOWNCELL_STAGE'
CALLER='src.generalization_knowncell_replay_v3_execution_20261025.common'
CALLER_SOURCE=CALLER.replace('.','/')+'.py'
FIELDS={'request_relative_path','request_sha256','provider_preparation_manifest_sha256',
        'software_status_sha256','pandas_admission_sha256'}
CHECKPOINT_KEYS=()
PHASES=('before_replay','after_replay')
ORIGINAL_PROVIDER_PREPARATION='results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json'
ORIGINAL_PROVIDER_SHA='c10fd9e8f52095e2b8a5eae8b533ed4f66814090ab8844928af7c7392a18694f'


def static_allowed(name):
    from src.generalization_knowncell_runtime_provider_20261023.spec import static_allowed as original
    if name.startswith('src/'):return name.endswith(('.py','/.gitattributes'))
    if name.startswith('reports/'):return name.endswith(('.md','/.gitattributes'))
    own=any(name.startswith(top+'/'+namespace+'/') for top in ('results','artifacts') for namespace in
        (NS,'generalization_knowncell_replay_v3_execution_20261025','generalization_knowncell_calibrated_input_bridge_20261024',
         'generalization_knowncell_prefit_projection_20261024','generalization_knowncell_prefit_projection_v2_20261024',
         'generalization_knowncell_joint_runner_20261023','generalization_knowncell_joint_input_bridge_20261023'))
    return original(name) or own and name.endswith(('.json','.log','/.gitattributes'))
