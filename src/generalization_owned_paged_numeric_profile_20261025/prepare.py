"""Freeze source/software/invented references without starting a native job."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NS=Path(__file__).parent.name
OUT=ROOT/'results'/NS


def run():
    accepted=ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/verified_native_status.json'
    assert hashlib.sha256(accepted.read_bytes()).hexdigest()=='e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821'
    certified=json.loads(accepted.read_bytes())
    assert certified['status']=='VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    for name,want in certified['verified_files'].items():
        assert hashlib.sha256((accepted.parent/name).read_bytes()).hexdigest()==want,name
    tests=OUT/'synthetic_tests_receipt_final.json'
    tested=json.loads(tests.read_bytes())
    assert tested['status']=='PASS_INVENTED_EXACT_NUMERICAL_RESULT_CONTRADICTIONS' and tested['tests']==1
    assert tested['native_jobs_or_biological_payload_reads']==0
    expected_sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(__file__).parent.glob('*.py')}
    assert tested['source_sha256']==expected_sources
    baseline=ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/preparation_manifest.json'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='61781e1ef932a2eb36a368279d96bd52b35bf0eaf286dc8f80021e42fd5a2daa'
    files=dict(json.loads(baseline.read_bytes())['files'])
    for name,want in files.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==want,name
    from src.generalization_knowncell_parser_profile_20261022.common import check_payload_files
    from src.generalization_knowncell_parser_profile_v3_20261023.common import (
        BASE_INVENTORY,INVENTORY,PREFIX,ADDITIONAL_CACHES,sha,
    )
    original_inventory=json.loads(BASE_INVENTORY.read_bytes())
    assert check_payload_files(original_inventory['files'])==7996
    expanded=json.loads(INVENTORY.read_bytes())
    assert expanded['files']==dict(original_inventory['files'],**ADDITIONAL_CACHES)
    for name,want in ADDITIONAL_CACHES.items():assert sha(PREFIX/name)==want
    for name,want in expanded['current_python_native_files'].items():assert sha(name)==want
    extras=[baseline,accepted,tests,
        OUT/'preparation_manifest_before_independent_review.json',OUT/'synthetic_tests_receipt.json',
        OUT/'synthetic_tests_receipt_reviewed.json',
        ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/invented_profile_receipt.json',
        ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/actual_origin_receipt.json',
        ROOT/'results/generalization_owned_workingset_probe_v2_20261025/receipt.json',
        ROOT/'results/generalization_owned_workingset_probe_v2_20261025/toy_child.json',
        ROOT/'results/generalization_owned_workingset_probe_v2_20261025/parent.jsonl',
        ROOT/'results/generalization_owned_workingset_probe_v2_20261025/synthetic_tests_receipt.json',
    ]
    for part,ns in (('src',NS),('reports',NS),('src','generalization_owned_workingset_probe_v2_20261025')):
        extras.extend(p for p in (ROOT/part/ns).iterdir() if p.is_file())
    for path in extras:
        assert not path.is_symlink()
        name=path.relative_to(ROOT).as_posix();want=hashlib.sha256(path.read_bytes()).hexdigest()
        assert name not in files or files[name]==want
        files[name]=want
    value={'status':'FROZEN_INVENTED_OWNED_PAGING_NUMERICAL_PROFILE','files':dict(sorted(files.items())),
        'biological_datasets_read':False,'biological_model_fits':0,
        'invented_optimizer_units':12,'padding_bytes':384*2**20,
        'requested_working_set_maximum':190*2**20,'measured_resident_ceiling':192*2**20,
        'private_process_cap':768*2**20,'job_cap':896*2**20,'active_process_limit':2,
        'startup_physical_floor':512*2**20,'live_physical_floor':256*2**20,
        'startup_commit_headroom':1920*2**20,'live_commit_and_disk_floor':2**30,
        'deadline_seconds':150,'threads':1,'automatic_retry':False,
        'existing_payload_files_freshly_hashed_at_preparation':7998,
        'full_biological_FIT_or_old_interpreter_parity_established':False}
    with (OUT/'preparation_manifest.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print(hashlib.sha256((OUT/'preparation_manifest.json').read_bytes()).hexdigest(),len(files))


if __name__=='__main__':run()
