"""Freeze static source and tests; actual acquisition/run inputs are deferred."""
import ast
import sys
from pathlib import Path
from . import common as c

HELPER_MANIFEST='results/generalization_knowncell_metadata_independent_20261023/preparation_manifest.json'
HELPER_SHA='1909f90290c0f83d350ee0cf9bdae8af528e16eb1855fa06e5a39237bd4aad23'


def run():
    assert not c.RUN_ADMISSION.exists(),'Actual input admission is not source preparation'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    policy_raw=c.policy.MANIFEST.read_bytes();assert c.sha(policy_raw)==c.POLICY_SHA
    policy=c.decode(policy_raw);assert len(policy['files'])==326
    pins=dict(policy['files'])
    for name,want in pins.items():assert c.sha(c.relative(name).read_bytes())==want,name
    pins[c.policy.MANIFEST.relative_to(c.ROOT).as_posix()]=c.POLICY_SHA
    # Root explicitly permits hashing these five preserved failure diagnostic
    # outputs as raw bytes only. Never decode/display their contents here.
    retry_name=c.ACQ_OUT+'execution_manifest.json'
    retry_raw=c.relative(retry_name).read_bytes();assert c.sha(retry_raw)==c.ACQ_GENERATION_SHA
    retry=c.decode(retry_raw);assert len(retry['files'])==347
    for name,want in retry['files'].items():
        assert c.sha(c.relative(name).read_bytes())==want,name
        assert name not in pins or pins[name]==want;pins[name]=want
    pins[retry_name]=c.ACQ_GENERATION_SHA
    for path,want in ((c.policy.AUTH,c.AUTH_SHA),(c.relative(c.SCOPE),c.SCOPE_SHA)):
        assert c.sha(path.read_bytes())==want;pins[path.relative_to(c.ROOT).as_posix()]=want
    helper_raw=c.relative(HELPER_MANIFEST).read_bytes();assert c.sha(helper_raw)==HELPER_SHA
    helper=c.decode(helper_raw)
    for name,want in helper['files'].items():
        assert c.sha(c.relative(name).read_bytes())==want
        assert name not in pins or pins[name]==want;pins[name]=want
    pins[HELPER_MANIFEST]=HELPER_SHA
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    receipt_path=c.OUT/'synthetic_tests_receipt_reviewed.json';receipt=c.decode(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_SECOND_METADATA_PRODUCTION_SOURCE_NOT_ACTUAL_EXECUTION'
    assert receipt['tests']>=15
    assert receipt['source_files']=={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources}
    assert receipt['actual_jobs']==receipt['actual_resource_probes']==receipt['project_payloads_read']==receipt['model_fits']==0
    assert receipt['scientific_imports'] is False and receipt['actual_input_admission_present'] is False
    own=sources+[c.ROOT/folder/c.NS/'.gitattributes' for folder in ('src','reports','results')]
    own += [receipt_path,c.OUT/'synthetic_tests_attempt_01.log',c.OUT/'synthetic_tests_attempt_02.log',
            c.OUT/'synthetic_tests_receipt.json',c.OUT/'draft_source_01.json',c.OUT/'run_admission_template.json',
            c.ROOT/'reports'/c.NS/'protocol.md',
            c.ROOT/'reports/generalization_knowncell_metadata_independent_review_20261024/independent_review.md']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(c.ROOT).as_posix()]=c.sha(raw)
    for name,want in policy['python_native_files'].items():assert c.sha(Path(name).read_bytes())==want
    c.save_new(c.MANIFEST,{'status':c.STATUS,'invocation':c.INVOCATION,'category':'metadata',
        'files':pins,'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'resource_authorization_sha256':c.AUTH_SHA,'approved_resource_policy':c.resource_policy(),
        'python_executable':policy['python_executable'],'python_native_files':policy['python_native_files'],
        'independent_helper_source_manifest_sha256':HELPER_SHA,'original326pins_preserved':True,
        'corrected_retry347closure_and_generation_sha256':c.ACQ_GENERATION_SHA,
        'preserved_failure_diagnostics_hashed_as_raw_bytes_only_without_content_decode_or_display':True,
        'guard_restore_and_monitor_bodies_reused_by_copy_not_old_private_dependency_injection':True,
        'actual_run_admission_created':False,'actual_successful_acquisition_payloads_read':False,
        'actual_failure_diagnostics_content_decoded_or_displayed':False,
        'actual_CORE_read':False,'actual_jobs':0,'actual_resource_probes':0,'model_fits':0,
        'root_actual_input_admission_review_commit_and_start_still_required':True,
        'failed_original_acquisition_is_not_success_evidence':True,
        'source_generation_identity_distinct_from_approved_policy_identity':True})
    print('SECOND_METADATA_EXECUTION_SOURCE_READY',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
