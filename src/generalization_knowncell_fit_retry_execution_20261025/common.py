"""Fixed owned prefit authorization; source/request/run identities stay separate."""
import os
import sys
from pathlib import Path
from .spec import *
policy=prior.policy
sha,canonical,decode=prior.sha,prior.canonical,prior.decode
valid_sha,relative,save_new=prior.valid_sha,prior.relative,prior.save_new
committed,source_mode=prior.committed,prior.source_mode
resource_policy=prior.resource_policy


def resource_failure(snapshot,elapsed,*,startup=False):
    failure=prior.resource_failure(snapshot,elapsed,startup=startup)
    if failure is not None:return failure
    if startup and snapshot['physical_available']<RETRY_STARTUP_PHYSICAL:
        return 'Fresh FIT attempt requires at least 2 GiB available physical RAM before birth/start'
    return None


def retry_authorization_contract(value,generation,scope_sha):
    assert value['status']=='EXPLICIT_HUMAN_AUTHORIZATION_ONE_ADDITIONAL_FIXED_KNOWNCELL_FIT'
    assert value['approved_answer']==RETRY_ANSWER and value['explicit_human_response_recorded'] is True
    assert value['generation_manifest_sha256']==valid_sha(generation)
    assert value['approval_scope_sha256']==valid_sha(scope_sha)
    assert value['failed_supervisor_sha256']==FAILED_SUPERVISOR_SHA
    assert value['additional_attempts_authorized']==1 and value['partial_resume_authorized'] is False
    assert value['automatic_retry_authorized'] is value['spending_authorized'] is False
    assert value['minimum_startup_physical_available']==RETRY_STARTUP_PHYSICAL
    return value


def verify_sources(generation):
    source_mode();raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation)
    value=decode(raw)
    assert value['status']==STATUS and value['invocation']==INVOCATION
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['resource_policy']==resource_policy()
    assert value['runtime_provider_preparation_sha256']==value['files'][runtime.PREPARATION]
    for name,want in value['files'].items():assert sha(relative(name).read_bytes())==valid_sha(want),name
    assert Path(sys.executable).resolve()==Path(value['python_executable']).resolve()
    for name,want in value['python_native_files'].items():assert sha(Path(name).read_bytes())==want
    source_mode();return value


def admit_authorization(generation):
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation);committed(MANIFEST,raw)
    verify_sources(generation);approved=policy.admit_authorization(POLICY_SHA)
    raw=policy.AUTH.read_bytes();assert sha(raw)==AUTH_SHA;auth=decode(raw)
    assert approved['approval_sha256']==AUTH_SHA and auth['approval_scope_sha256']==SCOPE_SHA
    assert INVOCATION in auth['approved_owned_invocations']
    scope=relative(prior.SCOPE).read_bytes();assert sha(scope)==SCOPE_SHA;committed(relative(prior.SCOPE),scope)
    retry_raw=RETRY_AUTH.read_bytes();committed(RETRY_AUTH,retry_raw)
    manifest=verify_sources(generation)
    retry_authorization_contract(decode(retry_raw),generation,manifest['files'][RETRY_SCOPE])
    return {'retry_authorization_sha256':sha(retry_raw),'generation_manifest_sha256':generation,'approved_policy_manifest_sha256':POLICY_SHA,
        'approval_scope_sha256':SCOPE_SHA,'approved_invocation':INVOCATION,'approval_sha256':AUTH_SHA,
        'explicit_human_approval':True,'owned_job_required':True,'allowed_stages':list(policy.STAGES)}


def source_admission_contract(value,generation,manifest):
    fields={'status','stage','invocation','generation_manifest_sha256','controller_source','controller_source_sha256',
        'runtime_provider_preparation_sha256','bridge_readiness_sha256','approved_policy_manifest_sha256',
        'authorization_sha256','approval_scope_sha256','resource_policy','actual_input_or_FIT_authority_granted','stable_scientific_source_bindings'}
    assert set(value)==fields,'Source admission must exclude request/run/static-binding/birth hashes'
    assert value['status']=='REVIEWED_SOURCE_ONLY_FIXED_FIT_CONTROLLER_NOT_INPUT_OR_FIT_AUTHORITY'
    assert value['stage']==STAGE and value['invocation']==INVOCATION and value['generation_manifest_sha256']==generation
    assert value['controller_source']==WORKER_SOURCE and value['controller_source_sha256']==manifest['files'][WORKER_SOURCE]
    assert value['runtime_provider_preparation_sha256']==manifest['files'][runtime.PREPARATION]
    assert value['bridge_readiness_sha256']==manifest['files'][BRIDGE_READY]
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    assert value['actual_input_or_FIT_authority_granted'] is False
    assert value['stable_scientific_source_bindings']==STABLE_SCIENTIFIC_BINDINGS
    return value


def read_source_admission(generation,want):
    raw=SOURCE_ADMISSION.read_bytes();assert sha(raw)==valid_sha(want);committed(SOURCE_ADMISSION,raw)
    return source_admission_contract(decode(raw),generation,verify_sources(generation))


def run_contract(value,generation):
    assert value['status']=='FROZEN_ONE_EXACT63_CHECKPOINT84_UNIT_FIT_RUN'
    assert value['stage']==STAGE and value['invocation']==INVOCATION and value['generation_manifest_sha256']==valid_sha(generation)
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    assert value['runtime_import_authorized'] is value['array_reload_authorized'] is value['saved_label_read_authorized'] is value['pool_preparation_authorized'] is True
    assert value['CORE_read_authorized'] is False and value['model_fitting_authorized'] is True
    assert value['data_pins']=={NPZ:NPZ_SHA}
    assert set(value['input_pins'])==set(INPUT_PINS)|{REQUEST,STATIC_BINDING,SOURCE_ADMISSION.relative_to(ROOT).as_posix(),PREFIT,PREFIT_COMPLETION,PREFIT_SUPERVISOR,PROJECTION_ADMISSION}
    for name,want in INPUT_PINS.items():assert value['input_pins'][name]==want
    for want in value['input_pins'].values():valid_sha(want)
    for name in ('actual_prefit_commit','projection_root_admission_commit'):
        commit=value[name]
        assert isinstance(commit,str) and len(commit)==40 and all(ch in '0123456789abcdef' for ch in commit)
    assert value['checkpoint_count']==63 and value['optimizer_units']==84 and value['resume'] is False
    valid_sha(value['retry_authorization_sha256'])
    assert value['minimum_startup_physical_available']==RETRY_STARTUP_PHYSICAL
    assert value['failed_supervisor_sha256']==FAILED_SUPERVISOR_SHA
    return value


def read_run(generation,want,*,check_commit=False):
    raw=RUN_ADMISSION.read_bytes();assert sha(raw)==valid_sha(want)
    if check_commit:committed(RUN_ADMISSION,raw)
    value=run_contract(decode(raw),generation)
    assert sha(RETRY_AUTH.read_bytes())==value['retry_authorization_sha256'],'Additional actual human response bytes differ from run admission'
    return value


def check_live_inputs(generation,run_sha):
    """Fresh same-input bytes within the continuously monitored owned stage."""
    from src.generalization_knowncell_joint_loader_20261022 import guard
    value=read_run(generation,run_sha)
    for name,want in {**value['input_pins'],**value['data_pins']}.items():
        guard.fresh_gate()
        path=relative(name);assert path.stat().st_size<=64*2**20
        with path.open('rb') as stream:raw=stream.read(64*2**20+1)
        assert len(raw)<=64*2**20 and sha(raw)==want,'Admitted FIT input bytes changed: '+name
    return value


def verify_owner(stage,generation,evidence):
    source_mode();assert stage==STAGE
    assert set(evidence)=={'parent_pid','birth_sha256','run_admission_sha256'}
    assert type(evidence['parent_pid']) is int and evidence['parent_pid']==os.getppid()
    raw=BIRTH.read_bytes();assert sha(raw)==valid_sha(evidence['birth_sha256']);value=decode(raw)
    assert value['stage']==STAGE and value['invocation']==INVOCATION and value['parent_pid']==os.getppid()
    assert value['generation_manifest_sha256']==generation and value['run_admission_sha256']==valid_sha(evidence['run_admission_sha256'])
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    assert value['source_mode']==source_mode() and value['automatic_retry'] is False
    read_run(generation,evidence['run_admission_sha256'])
    import ctypes
    from ctypes import wintypes
    assert os.name=='nt'
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype=wintypes.BOOL
    answer=wintypes.BOOL()
    assert kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(answer)) and answer.value
    return {'current_pid':os.getpid(),'parent_pid':os.getppid(),'manifest_sha256':generation,
        'birth_sha256':evidence['birth_sha256'],'in_owned_job':True,'continuous_monitoring_owned_by_controller':True}


def require_new_outputs():
    for path in (BIRTH,WORKER_LOG,COMPLETION,SUPERVISOR,OUTPUT,CAMPAIGN,CHECKPOINT_PROOFS):assert not os.path.lexists(path),'Preserve prior or partial FIT: '+str(path)
