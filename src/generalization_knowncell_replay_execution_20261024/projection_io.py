"""Fixed real exact-commit reader and current FIT context verifier."""
import os
import subprocess
from . import common as c
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_joint_loader_20261022.spec import DIRECT_GIT,DIRECT_GIT_SHA256
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_prefit_projection_20261024 import projection as original_projection
from src.generalization_knowncell_prefit_projection_v2_20261024 import projection
from src.generalization_knowncell_replay_runtime_20261024 import provider


def input_contract(prefit_raw,root_raw,completion,supervisor,run):
    actual=lifecycle.strict_json(prefit_raw);admission=lifecycle.strict_json(root_raw)
    assert actual['resource_exception_applies'] is True
    view=dict(actual);view['resource_exception_applies']=False;lifecycle.validate_prefit(view)
    assert c.sha(prefit_raw)==run['input_pins'][c.PREFIT]
    assert c.sha(root_raw)==run['input_pins'][c.PROJECTION_ADMISSION]
    assert completion['status']=='PASS_EXACT_NINE_POOL_PREFIT_WORKER_CALLBACKS_RESTORED'
    assert completion['prefit_sha256']==c.sha(prefit_raw) and completion['callbacks_restored'] is True
    assert completion['source_pools_prepared']==9 and completion['optimizer_calls']==0 and completion['campaign_started'] is False
    assert completion['saved_label_bits_sha256']==c.LABEL_BITS_SHA and completion['all_row_ids_sha256']==c.ROW_IDS_SHA
    assert supervisor['status']=='PASS_EXACT_NINE_POOL_PREFIT_PENDING_ROOT_REVIEW_AND_COMMIT' and supervisor['failure'] is None
    assert supervisor['prefit_sha256']==c.sha(prefit_raw)
    assert supervisor['worker_completion_sha256']==run['input_pins'][c.PREFIT_COMPLETION]
    for key in ('generation_manifest_sha256','run_admission_sha256','birth_sha256'):
        assert supervisor[key]==completion[key]==actual['prefit_execution'][key]
    assert admission['status']=='ROOT_FROZEN_CALIBRATED_PREFIT_COMPATIBILITY_ADMISSION'
    assert admission['prefit_relative_path']==c.PREFIT and admission['prefit_sha256']==c.sha(prefit_raw)
    assert admission['prefit_commit']==run['actual_prefit_commit']
    assert admission['projection_source_manifest_sha256']==c.PROJECTION_READY_SHA
    assert admission['prefit_owner_receipt_sha256']==run['input_pins'][c.PREFIT_SUPERVISOR]
    assert admission['runtime_binding_sha256']==actual['runtime_binding_sha256']
    assert admission['input_admission_bindings_sha256']==lifecycle.hash_value(actual['input_admission_bindings'])
    assert admission['additional_top_level_provenance_fields']==['prefit_execution']
    assert admission['scientific_settings_changed'] is admission['actual_stage_authority_granted_here'] is False
    return actual,admission


class ExactCommitReader:
    def __init__(self,run):
        self.allowed={c.PREFIT:(run['actual_prefit_commit'],run['input_pins'][c.PREFIT]),
            c.PROJECTION_ADMISSION:(run['projection_root_admission_commit'],run['input_pins'][c.PROJECTION_ADMISSION])}

    def __call__(self,name,commit):
        assert name in self.allowed and commit==self.allowed[name][0]
        assert len(commit)==40 and all(ch in '0123456789abcdef' for ch in commit)
        guard.fresh_gate();assert c.sha(guard.guarded_bytes(DIRECT_GIT))==DIRECT_GIT_SHA256
        guard.fresh_gate()
        assert os.name=='nt'
        # Same DETACHED_PROCESS behavior as the proven headless.GitFacade.
        # That facade intentionally accepts HEAD only, so this narrow reader
        # separately admits exactly the two fixed paths/full40 commits above.
        raw=subprocess.check_output([str(DIRECT_GIT),'show',commit+':'+name],cwd=c.ROOT,
            creationflags=0x00000008)
        guard.fresh_gate();assert c.sha(raw)==self.allowed[name][1]
        return raw


class ActualContextVerifier:
    """Not a Boolean stub: call all fixed real current owner/source/native gates."""
    def __init__(self,generation,run_sha,evidence,runtime_binding,objects,expected):
        self.generation,self.run_sha=generation,run_sha
        self.evidence=c.decode(c.canonical(evidence));self.runtime_binding=c.decode(c.canonical(runtime_binding))
        self.objects=objects;self.expected=lifecycle.canonical_bytes(expected)

    def __call__(self,binding):
        assert lifecycle.canonical_bytes(binding)==self.expected
        c.admit_authorization(self.generation)
        owner=c.verify_owner(c.STAGE,self.generation,self.evidence)
        c.check_live_inputs(self.generation,self.run_sha);c.verify_sources(self.generation)
        assert provider.verify_current_owned(self.runtime_binding,self.evidence,*self.objects)==owner
        assert owner['current_pid']==os.getpid() and owner['parent_pid']==os.getppid()
        guard.fresh_gate();return True


def bind_actual_plan(prefit_raw,root_raw,run,generation,run_sha,evidence,runtime_binding,objects):
    actual=lifecycle.strict_json(prefit_raw);admission=lifecycle.strict_json(root_raw)
    c.admit_authorization(generation);owner=c.verify_owner(c.STAGE,generation,evidence)
    c.check_live_inputs(generation,run_sha)
    assert provider.verify_current_owned(runtime_binding,evidence,*objects)==owner
    owner_receipt={'status':'ACTUAL_CURRENT_REPLAY_OWNER_SOURCE_INPUT_AND_NATIVE_CHECKS_COMPLETED',
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'owner':owner,
        'runtime_request_binding':runtime_binding,'actual_prefit_raw_sha256':c.sha(prefit_raw),
        'root_admission_raw_sha256':c.sha(root_raw),'current_state_verified_by_fixed_real_functions':True}
    context={'status':'ROOT_VERIFIED_CALIBRATED_PREFIT_COMPATIBILITY_CONTEXT',
        'root_admission_relative_path':c.PROJECTION_ADMISSION,'root_admission_commit':run['projection_root_admission_commit'],
        'root_admission_sha256':c.sha(root_raw),'prefit_sha256':c.sha(prefit_raw),
        'current_runtime_binding_sha256':actual['runtime_binding_sha256'],
        'projection_source_manifest_sha256':c.PROJECTION_READY_SHA,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'prefit_owner_receipt_sha256':admission['prefit_owner_receipt_sha256'],
        'current_owner_receipt_sha256':c.sha(c.canonical(owner_receipt)),
        'input_admission_bindings_sha256':admission['input_admission_bindings_sha256'],
        'actual_owner_resource_runtime_and_source_closure_verified':True,'actual_stage_authority_granted_by_this_library':False}
    context_raw=lifecycle.canonical_bytes(context)
    original_projection._bindings(prefit_raw,root_raw,context_raw)
    expected={'admission':admission,'context':context,'actual_prefit_raw_sha256':c.sha(prefit_raw),
        'root_admission_raw_sha256':c.sha(root_raw),'context_raw_sha256':c.sha(context_raw)}
    verifier=ActualContextVerifier(generation,run_sha,evidence,runtime_binding,objects,expected)
    plan=projection.bind_calibrated_plan(prefit_raw,root_raw,context_raw,
        committed_reader=ExactCommitReader(run),verify_root_context=verifier)
    return plan,owner_receipt
