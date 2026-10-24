"""Source, original approval, fixed labels input and actual owned-job gates."""
import os
import sys
from pathlib import Path
from .spec import *
policy=prior.policy
sha,canonical,decode=prior.sha,prior.canonical,prior.decode
valid_sha,relative,save_new=prior.valid_sha,prior.relative,prior.save_new
committed,source_mode=prior.committed,prior.source_mode
resource_policy,resource_failure=prior.resource_policy,prior.resource_failure


def verify_sources(generation):
    source_mode();raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation)
    value=decode(raw)
    assert value['status']==STATUS and value['invocation']==INVOCATION
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['resource_policy']==resource_policy()
    for name,want in value['files'].items():assert sha(relative(name).read_bytes())==valid_sha(want),name
    assert Path(sys.executable).resolve()==Path(value['python_executable']).resolve()
    for name,want in value['python_native_files'].items():assert sha(Path(name).read_bytes())==want
    source_mode();return value


def admit_authorization(generation):
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation);committed(MANIFEST,raw)
    verify_sources(generation)
    approved=policy.admit_authorization(POLICY_SHA)
    auth_raw=policy.AUTH.read_bytes();assert sha(auth_raw)==AUTH_SHA
    auth=decode(auth_raw);assert approved['approval_sha256']==AUTH_SHA
    assert auth['approval_scope_sha256']==SCOPE_SHA and INVOCATION in auth['approved_owned_invocations']
    scope_raw=relative(prior.SCOPE).read_bytes();assert sha(scope_raw)==SCOPE_SHA;committed(relative(prior.SCOPE),scope_raw)
    return {'generation_manifest_sha256':generation,'approved_policy_manifest_sha256':POLICY_SHA,
        'approval_scope_sha256':SCOPE_SHA,'approved_invocation':INVOCATION,'approval_sha256':AUTH_SHA,
        'explicit_human_approval':True,'owned_job_required':True,'allowed_stages':list(policy.STAGES)}


def run_contract(value,generation):
    assert value['status']=='FROZEN_ORIGINAL_PANDAS_LABEL_EXECUTION_INPUT_ADMISSION'
    assert value['invocation']==INVOCATION and value['stage']==STAGE
    assert value['generation_manifest_sha256']==valid_sha(generation)
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    assert value['runtime_import_authorized'] is value['label_access_authorized'] is True
    assert value['model_fitting_authorized'] is False
    pins=value['input_pins']
    assert set(pins)=={REQUEST,METADATA_BUNDLE,ARRAY_CERTIFICATE,ARRAY_SUPERVISOR,INDEPENDENT_REPORT,INDEPENDENT_SUPERVISOR}
    for want in pins.values():valid_sha(want)
    assert pins[METADATA_BUNDLE]==METADATA_SHA
    assert pins[ARRAY_CERTIFICATE]==ARRAY_CERTIFICATE_SHA and pins[ARRAY_SUPERVISOR]==ARRAY_SUPERVISOR_SHA
    assert pins[INDEPENDENT_REPORT]==INDEPENDENT_REPORT_SHA and pins[INDEPENDENT_SUPERVISOR]==INDEPENDENT_SUPERVISOR_SHA
    return value


def read_run(generation,run_sha,*,check_commit=False):
    raw=RUN_ADMISSION.read_bytes();assert sha(raw)==valid_sha(run_sha)
    if check_commit:committed(RUN_ADMISSION,raw)
    return run_contract(decode(raw),generation)


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
    for path in (BIRTH,WORKER_LOG,COMPLETION,SUPERVISOR,OUTPUT):
        assert not os.path.lexists(path),'Preserve prior or partial labels invocation: '+str(path)
