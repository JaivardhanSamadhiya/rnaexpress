"""Separate prospective static bindings from mandatory supplied current context."""
import os
from . import contracts as original
from .contracts import (canonical,decode,digest,valid_hash,fresh,committed_bytes,bits_hash,
    runtime_contract,operational_canonical,calibrated_certificate,protected_label_proofs)
from .spec_v3 import *


def binding_contract(value):
    fields={'status','namespace','stage','reviewed_controller_source',
        'reviewed_owned_caller_required','runtime_and_FIT_authority_granted_here',
        'approved_policy_manifest_sha256','authorization_sha256','approval_scope_sha256',*HASH_FIELDS}
    assert isinstance(value,dict) and set(value)==fields,'Static binding must not contain live birth/origin evidence'
    assert value['status']==BINDING_STATUS and value['namespace']==NS and value['stage'] in STAGES
    assert value['reviewed_owned_caller_required'] is True and value['runtime_and_FIT_authority_granted_here'] is False
    for key in HASH_FIELDS:valid_hash(value[key])
    name=value['reviewed_controller_source']
    assert isinstance(name,str) and name.startswith('src/generalization_knowncell_') and name.endswith('.py')
    assert name==name.replace('\\','/') and ':' not in name and all(p not in ('','.','..') for p in name.split('/'))
    assert value['array_certificate_sha256']==ARRAY_SHA and value['native_profile_receipt_sha256']==V4_ORIGIN_SHA
    assert value['approved_policy_manifest_sha256']==POLICY_SHA
    assert value['authorization_sha256']==AUTH_SHA and value['approval_scope_sha256']==SCOPE_SHA
    return value


def current_stage_contract(np,proof,binding,owner,static_binding_raw):
    """Check supplied live cross-bindings, not prove actual Job/native execution.

    The fixed owned caller must genuinely verify its owner and loaded origins.
    This function never supplies a fake common, probe or owner-verification call.
    """
    assert isinstance(owner,dict) and set(owner)==OWNER_FIELDS
    assert owner['status']==OWNER_STATUS and owner['stage']==binding['stage']
    assert owner['actual_parent_Job_and_native_origins_checked_by_fixed_caller'] is True
    assert owner['runtime_and_FIT_authority_granted_here'] is False
    for key in ('caller_birth_sha256','current_stage_origin_proof_sha256','static_root_binding_sha256',
                'reviewed_controller_admission_sha256'):valid_hash(owner[key])
    for key,actual in (('current_pid',os.getpid()),('parent_pid',os.getppid())):
        assert type(owner[key]) is int and owner[key]==actual
        assert type(proof[key]) is int and proof[key]==actual
    assert owner['static_root_binding_sha256']==digest(static_binding_raw)
    assert owner['reviewed_controller_admission_sha256']==binding['reviewed_controller_admission_sha256']
    assert owner['current_stage_origin_proof_sha256']==digest(canonical(proof))
    assert proof['static_root_binding_sha256']==owner['static_root_binding_sha256']
    assert proof['caller_birth_sha256']==owner['caller_birth_sha256']
    # Reuse the frozen pure proof checker with explicit live-only arguments.
    # This transient checker input is never committed or treated as root binding.
    checker_binding=dict(binding,caller_birth_sha256=owner['caller_birth_sha256'],
        current_stage_origin_proof_sha256=owner['current_stage_origin_proof_sha256'])
    original.current_stage_contract(np,proof,checker_binding)
