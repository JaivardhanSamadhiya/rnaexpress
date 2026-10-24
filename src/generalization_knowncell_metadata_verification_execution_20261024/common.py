"""Real fixed generation/approval/owner contracts, without payload readers."""
from pathlib import Path
import os
import sys
from src.generalization_knowncell_bounded_execution_20261023 import common as policy
from src.generalization_knowncell_metadata_independent_20261023.spec import COUNTS as HELPER_COUNTS, ROW_IDS_SHA as HELPER_ROW_IDS_SHA

ROOT=policy.ROOT
NS='generalization_knowncell_metadata_verification_execution_20261024'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'preparation_manifest.json'
RUN_ADMISSION=OUT/'run_admission.json'
CACHE_PREFIX=policy.CACHE_PREFIX
STAGES=policy.STAGES
INVOCATION='independent_metadata_verification'
STATUS='SOURCE_FROZEN_SECOND_METADATA_EXECUTION_NOT_ACTUAL_INPUT_ADMISSION'
POLICY_SHA='a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
AUTH_SHA='b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3'
SCOPE='reports/generalization_knowncell_bounded_execution_20261023/approval_scope.md'
SCOPE_SHA='c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495'
ACQ_NS='generalization_knowncell_metadata_retry_20261024'
ACQ_GENERATION_SHA='8aee30b96901964bcc118a57dc2f7f4bdfd4d95ad508c811124b44f47ae44ecd'
HELPER_MANIFEST_SHA='1909f90290c0f83d350ee0cf9bdae8af528e16eb1855fa06e5a39237bd4aad23'
HELPER_STATUS='PASS_INDEPENDENT_SUPPLIED_CORE_AND_METADATA_CONTRACT_NOT_IO_OR_FIT_ADMISSION'
ACQ_OUT='results/'+ACQ_NS+'/'
METADATA_ADMISSION='results/generalization_knowncell_joint_loader_20261022/metadata_admission_manifest.json'
METADATA_ADMISSION_SHA='67ea3daeb2eaff94f384d4a4e79015753a265bf8f7ab76268e0caf27dd03b08c'
CORE='results/probabilistic_ranking_20260928/candidate_index.csv'
CORE_SHA='773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d'
INPUT_PATHS={
    'bundle':'results/generalization_knowncell_joint_loader_20261022/admitted_metadata.json',
    'acquisition_completion':ACQ_OUT+'metadata_worker_completion.json',
    'acquisition_supervisor':ACQ_OUT+'metadata_supervisor_receipt.json',
    'acquisition_birth':ACQ_OUT+'metadata_attempt_birth.json',
    'acquisition_generation_manifest':ACQ_OUT+'execution_manifest.json',
    'acquisition_retry_authorization':ACQ_OUT+'authorization.json',
    'metadata_admission':METADATA_ADMISSION,
}
REPORT=OUT/'independent_metadata_report.json'
BIRTH=OUT/'independent_metadata_verification_attempt_birth.json'
WORKER_LOG=OUT/'independent_metadata_verification_worker.log'
COMPLETION=OUT/'independent_metadata_verification_worker_completion.json'
SUPERVISOR=OUT/'independent_metadata_verification_supervisor_receipt.json'
PROCESS_CAP=policy.PROCESS_CAP
JOB_CAP=policy.JOB_CAP
THREAD_KEYS=policy.THREAD_KEYS
sha=policy.sha
canonical=policy.canonical
decode=policy.decode
valid_sha=policy.valid_sha
relative=policy.relative
save_new=policy.save_new
committed=policy.committed
source_mode=policy.source_mode
resource_policy=policy.resource_policy
resource_failure=policy.resource_failure


def verify_sources(expected_sha):
    source_mode()
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(expected_sha),'Initial generation identity changed'
    document=decode(raw)
    assert document['status']==STATUS and document['invocation']==INVOCATION
    assert document['approved_policy_manifest_sha256']==POLICY_SHA
    assert document['approved_resource_policy']==resource_policy()
    assert document['approval_scope_sha256']==SCOPE_SHA
    for name,want in document['files'].items():assert sha(relative(name).read_bytes())==valid_sha(want),name
    assert Path(sys.executable).resolve()==Path(document['python_executable']).resolve()
    assert document['python_native_files']==decode(policy.MANIFEST.read_bytes())['python_native_files']
    for name,want in document['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    source_mode()
    return document


def admit_authorization(generation_sha):
    raw=MANIFEST.read_bytes();assert sha(raw)==valid_sha(generation_sha)
    committed(MANIFEST,raw);verify_sources(generation_sha)
    original=policy.admit_authorization(POLICY_SHA)
    auth_raw=policy.AUTH.read_bytes();assert sha(auth_raw)==AUTH_SHA
    auth=decode(auth_raw)
    assert original['approval_sha256']==AUTH_SHA and auth['approval_scope_sha256']==SCOPE_SHA
    assert auth['approved_owned_invocations']==[
        'metadata_acquisition',INVOCATION,'array_admission','original_pandas_label_admission',
        'fixed_prefit','fixed_63_checkpoint_84_optimizer_unit_fit',
        'independent_checkpoint_and_source_selection_replay','complete_outer_evaluation']
    scope_raw=relative(SCOPE).read_bytes();assert sha(scope_raw)==SCOPE_SHA;committed(relative(SCOPE),scope_raw)
    return {'generation_manifest_sha256':generation_sha,'approved_policy_manifest_sha256':POLICY_SHA,
            'approval_scope_sha256':SCOPE_SHA,'approval_sha256':AUTH_SHA,
            'approved_invocation':INVOCATION,'explicit_human_approval':True,
            'allowed_stages':list(STAGES),'owned_job_required':True,
            'source_generation_is_reviewed_not_directly_human_approved':True}


def run_contract(document,generation_sha):
    assert document['status']=='ROOT_FROZEN_ACTUAL_SECOND_METADATA_INPUT_ADMISSION'
    assert document['invocation']==INVOCATION and document['category']=='metadata'
    assert document['generation_manifest_sha256']==valid_sha(generation_sha)
    assert document['approved_policy_manifest_sha256']==POLICY_SHA
    assert document['approval_scope_sha256']==SCOPE_SHA and document['authorization_sha256']==AUTH_SHA
    assert document['resource_policy']==resource_policy()
    assert document['acquisition_namespace']==ACQ_NS
    assert document['acquisition_generation_manifest_sha256']==ACQ_GENERATION_SHA
    valid_sha(document['acquisition_retry_authorization_sha256'])
    pins=document['input_pins'];assert isinstance(pins,dict) and set(pins)==set(INPUT_PATHS.values())
    for name,want in pins.items():assert name in INPUT_PATHS.values();valid_sha(want)
    assert pins[METADATA_ADMISSION]==METADATA_ADMISSION_SHA
    assert document['core_path']==CORE and document['core_sha256']==CORE_SHA
    assert document['numeric_outcome_parsing_authorized'] is False
    assert document['array_access_authorized'] is False and document['model_fitting_authorized'] is False
    return document


def read_run(generation_sha,run_sha,*,check_commit=False):
    raw=RUN_ADMISSION.read_bytes();assert sha(raw)==valid_sha(run_sha),'Initial input admission identity changed'
    if check_commit:committed(RUN_ADMISSION,raw)
    return run_contract(decode(raw),generation_sha)


def birth_path(stage):
    assert stage=='metadata';return BIRTH


def verify_owner(stage,generation_sha,evidence):
    source_mode();assert stage=='metadata'
    assert set(evidence)=={'parent_pid','birth_sha256','run_admission_sha256'}
    assert type(evidence['parent_pid']) is int and evidence['parent_pid']==os.getppid()
    raw=BIRTH.read_bytes();assert sha(raw)==valid_sha(evidence['birth_sha256'])
    birth=decode(raw)
    assert birth['invocation']==INVOCATION and birth['category']=='metadata'
    assert birth['generation_manifest_sha256']==generation_sha
    assert birth['approved_policy_manifest_sha256']==POLICY_SHA
    assert birth['authorization_sha256']==AUTH_SHA and birth['approval_scope_sha256']==SCOPE_SHA
    assert birth['run_admission_sha256']==valid_sha(evidence['run_admission_sha256'])
    assert birth['parent_pid']==os.getppid() and birth['resource_policy']==resource_policy()
    assert birth['source_mode']==source_mode() and birth['automatic_retry'] is False
    assert sha(policy.AUTH.read_bytes())==AUTH_SHA
    read_run(generation_sha,evidence['run_admission_sha256'])
    # Exact Job/limits are verified by the pinned parent's suspended creation
    # and resume code; this query proves current membership in a Job only.
    import ctypes
    from ctypes import wintypes
    assert os.name=='nt'
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype=wintypes.BOOL
    answer=wintypes.BOOL()
    assert kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(answer))
    assert answer.value,'Verification child must belong to the owned capped Job'
    return {'current_pid':os.getpid(),'parent_pid':os.getppid(),'manifest_sha256':generation_sha,
            'birth_sha256':evidence['birth_sha256'],'in_owned_job':True,
            'continuous_monitoring_owned_by_controller':True,'invocation':INVOCATION,
            'approved_policy_manifest_sha256':POLICY_SHA,'run_admission_sha256':evidence['run_admission_sha256']}


def require_new_outputs():
    for path in (BIRTH,WORKER_LOG,COMPLETION,SUPERVISOR,REPORT):
        assert not os.path.lexists(path),'Preserve prior/partial second invocation; no resume: '+str(path)


def json_normalized(value):
    raw=canonical(value);result=decode(raw)
    assert canonical(result)==raw,'JSON normalization changed canonical scientific values'
    return result
