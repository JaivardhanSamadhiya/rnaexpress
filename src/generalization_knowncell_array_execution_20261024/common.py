"""Actual array invocation identities, frozen inputs and owned-process proof."""
import os
import sys
from pathlib import Path
from src.generalization_knowncell_metadata_verification_execution_20261024 import common as prior
from src.generalization_knowncell_array_admission_20261023 import spec as array

policy=prior.policy
ROOT=prior.ROOT
NS='generalization_knowncell_array_execution_20261024'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'preparation_manifest.json'
RUN_ADMISSION=OUT/'run_admission.json'
STATUS='REVIEWED_SOURCE_FOR_ONE_EXACT_ARRAY_INVOCATION_NOT_EXECUTION'
INVOCATION='array_admission'
STAGE='array'
POLICY_SHA=prior.POLICY_SHA
AUTH_SHA=prior.AUTH_SHA
SCOPE_SHA=prior.SCOPE_SHA
SCOPE=prior.SCOPE
CACHE_PREFIX=prior.CACHE_PREFIX
PROCESS_CAP=prior.PROCESS_CAP
JOB_CAP=prior.JOB_CAP
sha,canonical,decode=prior.sha,prior.canonical,prior.decode
valid_sha,relative,save_new=prior.valid_sha,prior.relative,prior.save_new
committed,source_mode=prior.committed,prior.source_mode
resource_policy,resource_failure=prior.resource_policy,prior.resource_failure
OUTPUT=OUT/'array_admission_certificate.json'
BIRTH=OUT/'array_attempt_birth.json'
WORKER_LOG=OUT/'array_worker.log'
COMPLETION=OUT/'array_worker_completion.json'
SUPERVISOR=OUT/'array_supervisor_receipt.json'
REQUEST=array.REQUEST
INDEPENDENT_REPORT=prior.REPORT.relative_to(ROOT).as_posix()
INDEPENDENT_REPORT_SHA='978dc51f46dcefaa963fc5a6305f821a0e6c0873c360191daf1773e65b6c8c51'
INDEPENDENT_GENERATION_SHA='a02831fa2de64efa3ba0ecf5219c4389d1e7893b0a344d751b484f9bd756a232'
INDEPENDENT_SUPERVISOR=prior.SUPERVISOR.relative_to(ROOT).as_posix()
INDEPENDENT_SUPERVISOR_SHA='36d624073edf87895292d5cd699adb81eee553eefe6a4957cc1e587cd347e554'
METADATA_BUNDLE_SHA='1c00b3c49f95c003ff4b5d92096ebe908def2bbd8cd3993283c687ac9f5b19cc'
ARRAY_READY_SHA='19c9d099ec4a052221bd39d993239bd401fc3aa767775c347a198b9259a5687f'
PROVIDER_PREPARATION='results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json'
PROVIDER_PREPARATION_SHA='c10fd9e8f52095e2b8a5eae8b533ed4f66814090ab8844928af7c7392a18694f'


def verify_sources(generation):
    source_mode()
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation)
    manifest=decode(raw)
    assert manifest['status']==STATUS and manifest['invocation']==INVOCATION
    assert manifest['approved_policy_manifest_sha256']==POLICY_SHA
    assert manifest['resource_policy']==resource_policy()
    for name,want in manifest['files'].items():assert sha(relative(name).read_bytes())==valid_sha(want),name
    assert Path(sys.executable).resolve()==Path(manifest['python_executable']).resolve()
    for name,want in manifest['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    source_mode()
    return manifest


def admit_authorization(generation):
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation);committed(MANIFEST,raw)
    verify_sources(generation)
    authorization=policy.admit_authorization(POLICY_SHA)
    assert authorization['approval_sha256']==AUTH_SHA
    original=decode(policy.AUTH.read_bytes())
    assert original['approval_scope_sha256']==SCOPE_SHA
    assert INVOCATION in original['approved_owned_invocations']
    scope_raw=relative(SCOPE).read_bytes();assert sha(scope_raw)==SCOPE_SHA;committed(relative(SCOPE),scope_raw)
    return {'generation_manifest_sha256':generation,'approved_policy_manifest_sha256':POLICY_SHA,
        'approval_scope_sha256':SCOPE_SHA,'approved_invocation':INVOCATION,'approval_sha256':AUTH_SHA,
        'explicit_human_approval':True,'owned_job_required':True,'allowed_stages':list(policy.STAGES)}


def run_contract(value,generation):
    assert value['status']=='FROZEN_ACTUAL_ARRAY_EXECUTION_INPUT_ADMISSION'
    assert value['invocation']==INVOCATION and value['stage']==STAGE
    assert value['generation_manifest_sha256']==valid_sha(generation)
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    pins=value['input_pins']
    assert set(pins)=={REQUEST,INDEPENDENT_REPORT,INDEPENDENT_SUPERVISOR,array.METADATA_BUNDLE}
    for name,want in pins.items():valid_sha(want)
    assert pins[INDEPENDENT_REPORT]==INDEPENDENT_REPORT_SHA
    assert pins[INDEPENDENT_SUPERVISOR]==INDEPENDENT_SUPERVISOR_SHA
    assert pins[array.METADATA_BUNDLE]==METADATA_BUNDLE_SHA
    assert value['runtime_import_authorized'] is True
    assert value['label_access_authorized'] is value['model_fitting_authorized'] is False
    return value


def read_run(generation,run_sha,*,check_commit=False):
    raw=RUN_ADMISSION.read_bytes();assert sha(raw)==valid_sha(run_sha)
    if check_commit:committed(RUN_ADMISSION,raw)
    return run_contract(decode(raw),generation)


def verify_owner(stage,generation,evidence):
    source_mode();assert stage==STAGE
    assert set(evidence)=={'parent_pid','birth_sha256','run_admission_sha256'}
    assert type(evidence['parent_pid']) is int and evidence['parent_pid']==os.getppid()
    raw=BIRTH.read_bytes();assert sha(raw)==valid_sha(evidence['birth_sha256'])
    value=decode(raw)
    assert value['stage']==STAGE and value['invocation']==INVOCATION
    assert value['generation_manifest_sha256']==generation
    assert value['approved_policy_manifest_sha256']==POLICY_SHA and value['authorization_sha256']==AUTH_SHA
    assert value['approval_scope_sha256']==SCOPE_SHA and value['resource_policy']==resource_policy()
    assert value['source_mode']==source_mode() and value['automatic_retry'] is False
    assert value['parent_pid']==os.getppid()
    assert value['run_admission_sha256']==valid_sha(evidence['run_admission_sha256'])
    read_run(generation,evidence['run_admission_sha256'])
    import ctypes
    from ctypes import wintypes
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
        assert not os.path.lexists(path),'Preserve prior or partial array invocation: '+str(path)
