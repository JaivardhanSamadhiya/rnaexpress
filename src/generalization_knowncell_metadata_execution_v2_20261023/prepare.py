"""Additive source freeze, preserving all V1 bytes and the old admission."""
import ast
from datetime import datetime, timezone
from .common import *


def run():
    old_raw=(ROOT/V1_MANIFEST).read_bytes()
    assert sha(old_raw)==V1_SHA
    old=read_json(old_raw)
    assert old['status']=='FROZEN_ORIGINAL_FLOOR_METADATA_ONLY_EXECUTION'
    pins=dict(old['files'])
    assert len(pins)==61
    for name,want in pins.items():assert sha((ROOT/name).read_bytes())==want,name
    pins[V1_MANIFEST]=V1_SHA
    assert sha((ROOT/SRC_INIT).read_bytes())==SRC_INIT_SHA
    pins[SRC_INIT]=SRC_INIT_SHA
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=read_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_SOURCE_BOUND_METADATA_V2_CONTROL_CHECKS'
    assert receipt['actual_worker_or_job_started'] is False and receipt['scientific_imports'] is False
    assert receipt['project_payloads_read']==receipt['model_fits']==0
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    assert receipt['sources']=={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    policy='results/generalization_knowncell_source_policy_20261023/source_cache_policy_receipt.json'
    policy_raw=(ROOT/policy).read_bytes();proof=read_json(policy_raw)
    assert proof['status']=='PASS_INVENTED_SOURCE_CACHE_BYPASS_WITH_ABSENT_PREFIX'
    assert proof['normal_stale_cache_value']==11 and proof['bypass_current_source_value']==22
    own=sources+[ROOT/'src'/NS/'.gitattributes',ROOT/'reports'/NS/'.gitattributes',
                 ROOT/'reports'/NS/'protocol.md',OUT/'.gitattributes',receipt_path,ROOT/policy]
    pins.update({p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in own})
    # Copy only existing interpreter declarations; rehash their actual bytes.
    for name,want in old['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    save_new(MANIFEST, {
        'status':STATUS,'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,
        'python_executable':old['python_executable'],'python_native_files':old['python_native_files'],
        'metadata_admission_sha256':old['metadata_admission_sha256'],
        'allowed_project_payloads':old['allowed_project_payloads'],'output_bundle':BUNDLE,
        'source_cache_prefix':str(CACHE_PREFIX),'source_cache_policy_test_sha256':sha(policy_raw),
        'initial_committed_manifest_SHA_required_through_completion':True,
        'original61pins_preserved':True,'metadata_admission_bytes_unchanged':True,
        'physical_RAM_floor':3*2**30,'disk_floor':2**30,'numerical_threads':1,
        'system_commit_reserve':2**30,'process_cap':768*2**20,'job_cap':896*2**20,
        'active_process_cap':2,'lifetime_seconds':300,'automatic_retry':False,
        'project_payloads_read_during_preparation':0,'model_fits':0,'numerical_outcomes_admitted':0,
        'guard_changes':False,'root_review_and_commit_required_before_explicit_start':True})
    print('SOURCE_BOUND_METADATA_V2_READY',len(pins),sha(MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
