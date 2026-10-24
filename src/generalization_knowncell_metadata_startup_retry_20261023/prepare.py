"""Source/test-only additive freeze; never opens admitted metadata inputs."""
import ast
from datetime import datetime,timezone
import sys
from .common import *


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    old_raw=(ROOT/V2_MANIFEST).read_bytes();assert sha(old_raw)==V2_SHA
    old=read_json(old_raw);assert old['status']==v2.STATUS and len(old['files'])==75
    pins=dict(old['files'])
    for name,want in pins.items():assert sha((ROOT/name).read_bytes())==want,name
    pins[V2_MANIFEST]=V2_SHA
    blocked_raw=(ROOT/OLD_BLOCKED).read_bytes();assert sha(blocked_raw)==OLD_BLOCKED_SHA
    blocked_document(blocked_raw);pins[OLD_BLOCKED]=OLD_BLOCKED_SHA
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=read_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_ONE_STARTUP_OPPORTUNITY_CONTROLS_NOT_EXECUTION' and receipt['tests']==13
    assert receipt['source_files']=={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sources}
    assert receipt['actual_jobs_or_workers_started']==receipt['project_payloads_read']==receipt['model_fits']==0
    assert receipt['native_scientific_imports'] is False
    for path in sources:ast.parse(path.read_text(encoding='utf-8'))
    own=sources+[ROOT/'src'/NS/'.gitattributes',ROOT/'reports'/NS/'.gitattributes',
                 ROOT/'reports'/NS/'protocol.md',OUT/'.gitattributes',receipt_path,
                 OUT/'synthetic_tests_attempt_01.log']
    pins.update({p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in own})
    for name,want in old['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    save_new(MANIFEST,{'status':STATUS,'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,
        'original_worker_manifest_sha256':V2_SHA,'preserved_first_blocked_receipt_sha256':OLD_BLOCKED_SHA,
        'original_worker_command_and_cache_prefix_unchanged':True,'original_bundle_and_completion_paths_unchanged':True,
        'python_executable':old['python_executable'],'python_native_files':old['python_native_files'],
        'optional_explicit_pre_spawn_wait_seconds_max':60,'worker_launches_max':1,'automatic_retry':False,'resume':False,
        'physical_RAM_floor':3*2**30,'disk_floor':2**30,'system_commit_reserve':2**30,'numerical_threads':1,
        'process_cap':768*2**20,'job_cap':896*2**20,'active_process_cap':2,'metadata_stage_lifetime_seconds':300,
        'old75pins_preserved':True,'old_blocked_receipt_immutable':True,'guard_changes':False,
        'project_payloads_read_during_preparation':0,'numerical_outcomes_admitted':0,'model_fits':0,
        'exact_HEAD_addon_V2_and_first_block_receipt_required_before_explicit_root_start':True})
    print('ONE_EXPLICIT_METADATA_STARTUP_OPPORTUNITY_READY',len(pins),sha(MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
