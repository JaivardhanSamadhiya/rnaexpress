"""Read-only saved native/invented evidence audit; no scientific imports/jobs."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/generalization_owned_paged_numeric_profile_20261025'
GENERATION='7ea9881afeadf5c357a80df862ae1941ba9bf49a5854f30ae53f16343a4e21d1'
RECEIPT='9eda13d5a7e0de4d4eba58c069456f19dd1603bf804b85229380e55e090fd06f'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def run():
    raw=(OUT/'preparation_manifest.json').read_bytes();assert sha(raw)==GENERATION
    manifest=json.loads(raw)
    for name,want in manifest['files'].items():assert sha((ROOT/name).read_bytes())==want,name
    raw=(OUT/'receipt.json').read_bytes();assert sha(raw)==RECEIPT
    parent=json.loads(raw);assert parent['status']=='PASS_OWNED_PAGED_INVENTED_NATIVE_NUMERICAL_PROFILE'
    assert parent['failure'] is None and parent['preparation_manifest_sha256']==GENERATION
    assert parent['biological_rows_read']==parent['scientific_attempts']==0
    assert parent['invented_optimizer_units']==12 and parent['full_FIT_or_old_interpreter_parity_established'] is False
    assert 0<parent['elapsed_seconds']<=150 and parent['minimum_sampled_physical_available']>=256*2**20
    assert 384*2**20<parent['peak_private_commit']<=768*2**20
    assert 0<parent['peak_working_set']<=192*2**20
    assert parent['requested_resident_maximum']==190*2**20
    assert parent['measured_resident_ceiling']==192*2**20
    cap=parent['additional_resident_cap'];before,after=cap['before'],cap['after']
    assert after=={'minimum':before['minimum'],'maximum':190*2**20,'flags':(before['flags']&3)|4}
    assert cap['only_suspended_owned_child_changed'] is True
    assert cap['private_and_job_caps_or_live_guards_changed'] is False
    assert parent['unchanged_job_caps']=={'active_process_limit':2,'job_memory_limit':896*2**20,
        'process_memory_limit':768*2**20,'limit_flags':8968}
    raw=(OUT/'toy_child.json').read_bytes();assert sha(raw)==parent['child_completion_sha256']
    child=json.loads(raw)
    assert child['status']=='PASS_INVENTED_PAGED_NATIVE_NUMERICAL_PROFILE'
    assert child['preparation_manifest_sha256']==GENERATION
    assert child['biological_rows_read']==child['biological_model_fits']==0
    assert child['bytes']==384*2**20 and len(child['hashes'])==3 and len(set(child['hashes']))==1
    expected=hashlib.sha256()
    for page in range(child['bytes']//4096):expected.update(bytes([page%251])+bytes(4095))
    assert set(child['hashes'])=={expected.hexdigest()}
    baseline_path=ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/invented_profile_receipt.json'
    baseline_raw=baseline_path.read_bytes()
    assert sha(baseline_raw)=='dfc00f70af703437b394f74fbd92f8f81e0926b82a0be5b95a01cabebd29c312'
    assert child['original_profile_sha256']==sha(baseline_raw)
    baseline=json.loads(baseline_raw)
    canonical=lambda value:json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode('utf8')
    assert canonical(child['optimizer'])==canonical(baseline['optimizer'])
    assert sha(canonical(child['optimizer']))==child['canonical_optimizer_sha256']
    assert child['optimizer']['scipy_optimizer_units']==12 and child['optimizer']['biological_model_fits']==0
    native_count=0
    for proof_name in ('initial_native_proof','final_native_proof'):
        proof=child[proof_name]
        assert proof['old_interpreter_bitwise_parity_established'] is False
        assert proof['fresh_full_NumPy_payload_check'] is True
        for kind in ('actually_loaded_scientific_native_files','actually_loaded_current_python_native_files'):
            for name,want in proof[kind].items():assert sha(Path(name).read_bytes())==want;native_count+=1
        for name,want in proof['actually_loaded_scientific_modules'].items():
            assert sha((ROOT/'data/interim/mechanism_v2/runtime'/name).read_bytes())==want
        assert proof['actually_loaded_threadpools']
        assert all(item['num_threads']==1 for item in proof['actually_loaded_threadpools'])
    raw=(OUT/'parent.jsonl').read_bytes();assert sha(raw)==parent['closed_parent_log_sha256']
    journal=[json.loads(line) for line in raw.splitlines()]
    assert journal[-1]['status']=='MANDATORY_PARENT_TELEMETRY_COMPLETE' and journal[-1]['failure'] is None
    for sample in journal:
        if 'child_memory' not in sample:continue
        assert sample['failure'] is None
        assert sample['memory']['physical_available']>=256*2**20
        assert sample['memory']['commit_headroom']>=2**30 and sample['memory']['disk_available']>=2**30
        assert sample['elapsed_seconds']<=150
        assert sample['child_memory']['peak_private_commit']<=768*2**20
        assert sample['child_memory']['peak_working_set']<=192*2**20
        assert sample['job']['peak_job_memory_used']<=896*2**20
    from src.generalization_github_publication_20261009.publish import protect
    assert protect()==33
    value={'status':'VERIFIED_INVENTED_NATIVE_PAGING_NUMERICAL_PROFILE_NOT_BIOLOGICAL_ADMISSION',
        'source_generation_sha256':GENERATION,'supervisor_receipt_sha256':RECEIPT,
        'child_completion_sha256':parent['child_completion_sha256'],
        'closed_parent_journal_sha256':parent['closed_parent_log_sha256'],
        'frozen_files_rehashed':len(manifest['files']),'loaded_native_entries_rehashed':native_count,
        'original_twelve_invented_optimizer_results_exact':True,'three_full_buffer_hashes_independently_recomputed':True,
        'protected_original_user_files':33,'biological_rows_read':0,'biological_fits_or_attempts':0,
        'full_study_runtime_or_biological_generalization_established':False,
        'verification_source_sha256':sha(Path(__file__).read_bytes())}
    with (OUT/'verified_native_status.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print(value['status'],sha((OUT/'verified_native_status.json').read_bytes()))


if __name__=='__main__':run()
