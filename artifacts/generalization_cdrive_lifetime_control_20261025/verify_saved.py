"""Independent stdlib-only verification of the closed, saved C lifetime toy."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_cdrive_lifetime_control_20261025'
OUT=ROOT/'results'/NS
def sha(raw):return hashlib.sha256(raw).hexdigest()


def run():
    captured={name:(OUT/name).read_bytes() for name in ('preparation_manifest.json','receipt.json','toy_child.json','parent.jsonl')}
    manifest,receipt,child=(json.loads(captured[name]) for name in ('preparation_manifest.json','receipt.json','toy_child.json'))
    assert sha(captured['preparation_manifest.json'])=='873696b41cd78a48a253fe918802f672fd760416c7ad53fc6a3aed04016dd333'
    assert receipt['status']=='PASS_OWNED_CDRIVE_LIFETIME_CONTROL_ONLY' and receipt['failure'] is None
    assert receipt['preparation_manifest_sha256']==child['preparation_manifest_sha256']==sha(captured['preparation_manifest.json'])
    assert receipt['child_completion_sha256']==sha(captured['toy_child.json'])
    assert receipt['closed_parent_log_sha256']==sha(captured['parent.jsonl'])
    assert captured['parent.jsonl'].endswith(b'\n')
    log=[json.loads(line) for line in captured['parent.jsonl'].splitlines()]
    assert log[0]['status']=='ONE_OWNED_TOY_PAGING_PROBE_STARTED'
    assert log[1]['status']=='EXACT_ADDITIONAL_RESIDENT_CAP_INSTALLED'
    assert log[-1]=={'status':'MANDATORY_PARENT_TELEMETRY_COMPLETE','failure':None}
    assert log[-2]['status']=='FINAL_OWNED_LIFETIME_COUNTERS' and log[-2]['job']['active_processes']==0
    assert child['parent_pid']==log[0]['parent_pid'] and child['child_pid']==log[1]['child_pid']
    assert log[1]['cap']==receipt['additional_resident_cap']
    assert log[1]['cap']['after']['maximum']==190*2**20 and log[1]['cap']['only_suspended_owned_child_changed'] is True
    pattern=hashlib.sha256()
    for page in range(16*2**20//4096):pattern.update(bytes([page%251])+bytes(4095))
    assert child['hashes']==[pattern.hexdigest()]*3 and child['bytes']==16*2**20
    assert 1080<=child['elapsed_seconds']<=receipt['elapsed_seconds']<=1140
    assert receipt['project_payload_reads']==child['project_payload_reads']==receipt['optimizer_calls']==child['optimizer_calls']==receipt['scientific_attempts']==0
    assert receipt['historical_termination_cause_established'] is receipt['full_FIT_or_numerical_parity_established'] is False
    samples=[value for value in log if 'elapsed_seconds' in value]
    assert len(samples)>1000 and samples[-1]['exit_code']==0
    assert [value['elapsed_seconds'] for value in samples]==sorted(value['elapsed_seconds'] for value in samples)
    for sample in samples:
        assert sample['failure'] is None
        assert sample['child_memory']['peak_private_commit']<=768*2**20
        assert sample['child_memory']['working_set']<=sample['child_memory']['peak_working_set']<=192*2**20
        assert sample['job']['peak_job_memory_used']<=896*2**20 and sample['job']['active_processes']<=2
        assert sample['memory']['physical_available']>=256*2**20
        assert sample['memory']['commit_headroom']>=2**30 and sample['memory']['disk_available']>=2**30
    for name,want in {**manifest['files'],**log[0]['source_sha256']}.items():assert sha((ROOT/name).read_bytes())==want,name
    for name,want in manifest['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    assert receipt['peak_private_commit']==max(value['child_memory']['peak_private_commit'] for value in samples)
    assert receipt['peak_working_set']==max(value['child_memory']['peak_working_set'] for value in samples)
    assert receipt['minimum_sampled_physical_available']<=min(value['memory']['physical_available'] for value in samples)
    for name,raw in captured.items():assert (OUT/name).read_bytes()==raw
    result={'status':'VERIFIED_SAVED_C18_MINUTE_CONTROL_NOT_BIOLOGICAL_ADMISSION',
        'saved_files_sha256':{name:sha(raw) for name,raw in captured.items()},
        'independent_verifier_sha256':sha(Path(__file__).read_bytes()),'persisted_samples_verified':len(samples),
        'elapsed_seconds':receipt['elapsed_seconds'],'private_peak_bytes':receipt['peak_private_commit'],
        'resident_peak_bytes':receipt['peak_working_set'],'physical_minimum_bytes':receipt['minimum_sampled_physical_available'],
        'scientific_conclusion':False,'historical_failure_cause_known':False,'new_native_jobs':0,'biological_payload_reads':0}
    with (OUT/'independent_saved_verification.json').open('xb') as stream:
        stream.write((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(result['status'],sha((OUT/'independent_saved_verification.json').read_bytes()))


if __name__=='__main__':run()
