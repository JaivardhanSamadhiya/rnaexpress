"""Read-only parent lifecycle validation; never runtime admission or replay."""
from pathlib import Path
import time
from . import common as c
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign
from src.generalization_knowncell_prefit_projection_v2_20261024.projection import CalibratedBoundPlan

PROTECTED=('runtime_acceptance','runtime_acceptance_after_fit','current_owner_context','projection_current_owner_receipt',
    'projection_context_raw','plan_identity','plan_operational_context','checkpoint_runtime_proof_sha256',
    'sampler_identity','bridge_report','campaign_lifecycle')


def fresh(started):
    from src.generalization_pum_process_probe_20261021 import headless
    assert c.resource_failure(headless.memory(),time.monotonic()-started) is None


def bounded(path,started):
    fresh(started);path=Path(path)
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=16*2**20
    with path.open('rb') as stream:raw=stream.read(16*2**20+1)
    assert len(raw)<=16*2**20
    return raw,lc.strict_json(raw)


class ReadOnlySavedCampaign(Campaign):
    """Reuse existing check_saved only, without creating/authorizing a campaign."""
    def __init__(self,directory,plan,birth_sha):
        self.directory=Path(directory);self.plan=plan
        self.identity=plan.identity();self.run_birth_sha=birth_sha
        self.tasks={lc.task_key(task):task for task in lc.task_roster()};self.failed=False
    def write_checkpoint(self,*args,**kwargs):raise AssertionError('Read-only parent checker cannot write checkpoints')
    def finish(self):raise AssertionError('Read-only parent checker cannot finish a campaign')


def validate_campaign(report,prefit_raw,admission_raw,run,started):
    """Pure saved-plan reconstruction supplements actual parent-owned proof.

    Direct construction here checks saved declarations only. It is NEVER a
    substitute for the worker's real binder or actual current-owner verifier.
    No optimizer, score replay, configuration arithmetic or gate is run.
    """
    root=lc.strict_json(admission_raw)
    context_raw=report['projection_context_raw'].encode('utf8')
    plan=CalibratedBoundPlan(root['prefit_relative_path'],root['prefit_commit'],prefit_raw,c.sha(prefit_raw),
        root['runtime_binding_sha256'],admission_raw,context_raw)
    assert plan.prefit_sha256==run['input_pins'][c.PREFIT]
    assert c.sha(admission_raw)==run['input_pins'][c.PROJECTION_ADMISSION]
    assert root['prefit_commit']==run['actual_prefit_commit']
    assert plan.identity()==report['plan_identity']
    assert plan.operational_context()==report['plan_operational_context']
    assert plan.operational_context()['current_owner_receipt_sha256']==c.sha(c.canonical(report['projection_current_owner_receipt']))
    directory=c.CAMPAIGN/'checkpoints'
    tasks={lc.task_key(task):task for task in lc.task_roster()}
    expected={'campaign_birth.json','campaign_complete.json'}|{key+suffix for key in tasks
        for suffix in ('.birth.json','.model.json','.complete.json')}
    assert len(expected)==191 and directory.is_dir() and not directory.is_symlink()
    assert {path.name for path in directory.iterdir()}==expected,'Exact191-file closed lifecycle roster required'
    hashes={}
    for name in sorted(expected):
        raw,_=bounded(directory/name,started);hashes[name]=c.sha(raw)
    _,birth=bounded(directory/'campaign_birth.json',started)
    assert birth=={'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**plan.identity()}
    reader=ReadOnlySavedCampaign(directory,plan,hashes['campaign_birth.json'])
    total=0
    for key,task in tasks.items():
        fresh(started);receipt=reader.check_saved(key)
        assert receipt['optimizer_units']==task['optimizer_units'];total+=receipt['optimizer_units']
    assert total==84
    _,complete=bounded(directory/'campaign_complete.json',started)
    assert complete==report['campaign_lifecycle']
    assert complete['status']=='COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE'
    assert complete['checkpoint_count']==63 and complete['optimizer_units']==84
    assert complete['campaign_birth_sha256']==hashes['campaign_birth.json']
    assert complete['checkpoint_receipt_sha256']=={key:hashes[key+'.complete.json'] for key in tasks}
    for key,value in plan.identity().items():assert complete[key]==value
    assert complete['inner_checkpoints']==54 and complete['outer_checkpoints']==9
    assert complete['independent_numeric_and_selection_replay_complete'] is complete['biological_or_gate_claim'] is False
    for name,want in hashes.items():
        raw,_=bounded(directory/name,started);assert c.sha(raw)==want,'Lifecycle bytes changed during parent semantic check'
    return {'status':'PASS_PARENT191_FILE_LIFECYCLE_BINDINGS_NOT_INDEPENDENT_REPLAY',
        'files_sha256':hashes,'checkpoints':63,'optimizer_units':84,
        'saved_plan_reconstruction_grants_no_current_authority':True,'new_optimizer_calls':0}


def validate_report(report,completion,run,generation,run_sha,birth_sha,parent_pid,worker_pid,started):
    assert report['status']=='ACTUAL_ONE_OWNED_FIXED_FIT_LIFECYCLE_NOT_REPLAY_OR_EVALUATION'
    for name,want in (('generation_manifest_sha256',generation),('run_admission_sha256',run_sha),('birth_sha256',birth_sha),
        ('parent_pid',parent_pid),('worker_pid',worker_pid),('approved_policy_manifest_sha256',c.POLICY_SHA),
        ('authorization_sha256',c.AUTH_SHA),('approval_scope_sha256',c.SCOPE_SHA)):
        assert report[name]==completion[name]==want,name
    assert report['invocation']==completion['invocation']==c.INVOCATION
    assert completion['status']=='PASS_FIXED_FIT_WORKER_CALLBACKS_RESTORED_LIFECYCLE_ONLY'
    assert completion['callbacks_restored'] is True and completion['fresh_calibrated_guard_calls']>0
    assert completion['source_mode']==c.source_mode() and completion['resource_policy']==c.resource_policy()
    for name,want in (('checkpoints',63),('optimizer_units',84),('checkpoint_runtime_refreshes',63)):
        assert report[name]==completion[name]==want
    for name in ('CORE_reread','independent_replay_complete','evaluation_or_gate_run'):assert report[name] is completion[name] is False
    assert report['original_resource_guards_unchanged'] is False
    assert report['source_pools_rebuilt']==9 and report['saved_label_bits_sha256']==c.LABEL_BITS_SHA and report['all_row_ids_sha256']==c.ROW_IDS_SHA
    assert report['actual_prefit_sha256']==completion['actual_prefit_sha256']==run['input_pins'][c.PREFIT]
    assert report['projection_root_admission_sha256']==run['input_pins'][c.PROJECTION_ADMISSION]
    assert report['source_npz_read']['actual_sha256']==c.NPZ_SHA and report['source_npz_read']['fresh_original_resource_gate_before_open'] is False
    assert report['label_reparse_recast_or_recomputation'] is report['original_scientific_settings_changed'] is report['biological_or_generalization_claim'] is False
    protected={name:report[name] for name in PROTECTED}
    assert c.sha(c.canonical(protected))==report['protected_provenance_sha256']
    keys=list(c.runtime.CHECKPOINT_KEYS);assert set(report['checkpoint_runtime_proof_sha256'])==set(keys)
    assert {p.name for p in c.CHECKPOINT_PROOFS.iterdir()}=={key+'.json' for key in keys}
    def check_proof(proof,phase):
        assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
        assert proof['current_pid']==worker_pid and proof['parent_pid']==parent_pid and proof['caller_birth_sha256']==birth_sha
        assert proof['stable_admitted_runtime_binding_sha256']==report['plan_identity']['runtime_binding_sha256']
        assert proof['request_binding']['request_sha256']==run['input_pins'][c.REQUEST]
        assert proof['request_binding']['request_relative_path']==c.REQUEST
        assert proof['static_root_binding_sha256']==run['input_pins'][c.STATIC_BINDING]
        assert proof['reviewed_controller_admission_sha256']==run['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()]
        assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True and proof['invented_only'] is False
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
        assert proof['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['numpy_version']=='1.26.4' and proof['pandas_version']=='2.2.3' and proof['scipy_version']=='1.14.1'
        assert proof['numerical_threads']==1 and proof['source_cache_remained_absent'] is True
        assert proof['optimizer_calls']==0 and proof['runtime_and_FIT_authority_granted_here'] is False
        assert proof['full_committed_evidence_admission_this_call'] is (phase in ('before_fit','after_fit'))
    for index,key in enumerate(keys,1):
        raw,proof=bounded(c.CHECKPOINT_PROOFS/(key+'.json'),started)
        assert c.sha(raw)==report['checkpoint_runtime_proof_sha256'][key]
        assert proof['checkpoint_key']==key and proof['checkpoint_refresh_count']==index and proof['provider_phase']=='checkpoint'
        assert proof['phase']=='before_checkpoint' and proof['full_committed_evidence_admission_this_call'] is False
        check_proof(proof,'checkpoint')
    check_proof(report['runtime_acceptance'],'before_fit')
    check_proof(report['runtime_acceptance_after_fit'],'after_fit')
    assert report['runtime_acceptance']['checkpoint_refresh_count']==0
    assert report['runtime_acceptance_after_fit']['checkpoint_refresh_count']==63
    context=report['current_owner_context']
    assert context['current_stage_origin_proof_sha256']==c.sha(lc.canonical_bytes(report['runtime_acceptance']))
    assert context['caller_birth_sha256']==birth_sha and context['current_pid']==worker_pid and context['parent_pid']==parent_pid
    calibration=report['resource_calibration']
    assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['birth_sha256']==birth_sha and calibration['authorization_sha256']==c.AUTH_SHA
    assert calibration['current_pid']==worker_pid and calibration['parent_pid']==parent_pid
    assert calibration['scientific_protocol_settings_changed'] is False
    fresh(started)
    prefit_raw,_=bounded(c.relative(c.PREFIT),started);root_raw,_=bounded(c.relative(c.PROJECTION_ADMISSION),started)
    return validate_campaign(report,prefit_raw,root_raw,run,started)
