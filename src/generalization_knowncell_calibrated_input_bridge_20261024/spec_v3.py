"""Precommittable static bindings; live owner/origin evidence stays separate."""
from .spec_v2 import *

READY='results/'+NS+'/preparation_manifest_v3.json'
BINDING_STATUS='FROZEN_STATIC_ROOT_CALIBRATED_INPUT_BINDINGS_V3_NOT_FIT_PERMISSION'
HASH_FIELDS=tuple(name for name in HASH_FIELDS if name not in ('caller_birth_sha256','current_stage_origin_proof_sha256'))
OWNER_STATUS='SUPPLIED_CURRENT_OWNER_CONTEXT_REQUIRES_ACTUAL_FIXED_CALLER_VERIFICATION'
OWNER_FIELDS={'status','stage','current_pid','parent_pid','caller_birth_sha256',
    'current_stage_origin_proof_sha256','static_root_binding_sha256','reviewed_controller_admission_sha256',
    'actual_parent_Job_and_native_origins_checked_by_fixed_caller','runtime_and_FIT_authority_granted_here'}


def binding_path(stage):
    assert stage in STAGES
    return 'results/'+NS+'/root_bindings_v3_'+stage+'.json'
