"""Independent C-only rehash and provenance checks; no runtime admission."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import stat
import time

BASE=Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025')
EXPECTED='21d55e48e05cfd9c306915ec9fe4de21079edd581729cb963402e3e4d1f35075'


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def main():
    started=time.monotonic()
    assert str(BASE.resolve()).casefold()==str(BASE.absolute()).casefold()
    assert BASE.stat().st_dev==Path('C:/').stat().st_dev
    for path in [BASE,*BASE.parents]:
        assert not os.lstat(path).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,path
    assert sha(BASE/'copy_verified.json')==EXPECTED
    copied=json.loads((BASE/'copy_verified.json').read_bytes())
    plan=json.loads((BASE/'copy_plan.json').read_bytes())
    assert copied['status']=='PASS_BOUNDED_VERIFIED_MATERIAL_COPY_NOT_FULL_DRIVE_BACKUP_OR_EXECUTION_ADMISSION'
    assert copied['copied_file_count']==plan['expected_file_count']==len(plan['files'])==len(copied['files'])==9942
    assert copied['copied_bytes']==plan['expected_bytes']==401930209
    assert copied['elapsed_seconds']<=600
    assert copied['verification_source_sha256']==plan['verification_source_sha256']=='b6c791d578ba2e79d6eda036db86b019c3df77e4e30439f8233a99c7809e75c4'
    assert set(copied['files'])==set(plan['files'])
    progress_raw=(BASE/'progress.jsonl').read_bytes()
    assert progress_raw.endswith(b'\n')
    progress=[json.loads(line) for line in progress_raw.splitlines()]
    assert progress[0]['status']=='BOUNDED_RECOVERY_COPY_STARTED_NOT_RUNTIME_OR_RESEARCH_ADMISSION'
    assert progress[-1]['status']==copied['status'] and progress[-1]['copied']==9942
    assert not (BASE/'copy_failure.json').exists()
    total=0
    for key,item in plan['files'].items():
        name=PurePosixPath(key)
        assert not name.is_absolute() and all(p not in ('.','..') for p in name.parts)
        assert ':' not in key and '\\' not in key and name.as_posix()==key
        path=BASE/key
        assert path.resolve().is_relative_to(BASE.resolve()) and not path.is_symlink()
        assert copied['files'][key]=={'sha256':item['sha256'],'size_bytes':item['size_bytes']}
        assert path.stat().st_size==item['size_bytes'] and sha(path)==item['sha256'],key
        total+=item['size_bytes']
    assert total==401930209
    raw=(BASE/'workspace/results/generalization_knowncell_parser_profile_v3_20261023/payload_inventory.json').read_bytes()
    software=json.loads(raw)['files'];assert len(software)==7998
    for key,want in software.items():assert copied['files']['workspace/data/interim/mechanism_v2/runtime/'+key]['sha256']==want
    protected=json.loads((BASE/'workspace/results/generalization_prelib_binding_descriptive_20261008/protected_user_file_snapshot.json').read_bytes())['user_modified_files_at_turn_start']
    assert len(protected)==33
    for key,want in protected.items():assert copied['files']['workspace/'+key]['sha256']==want
    # Supplemental validation binds parsed documents to their exact copied raw bytes.
    anchors={
        'results/generalization_knowncell_fit_paged_execution_20261025/preparation_manifest.json':'4a8d83023675d17cdc4af37801dc69df4b2c49d7b397a2cfd6ba1aa8b519d632',
        'results/generalization_knowncell_paged_interruption_audit_20261025/interrupted_fit_audit.json':'e2a58d36e70cb7e1aa54a8ff7b0ae16f21f5efd26b69b0f05abb516efdcdbf8d',
        'results/generalization_knowncell_fit_paged_execution_20261025/run_admission.json':'a38f9e98af718c333334cc005f89be287a241412538710e332dd4256fc0631b2',
        'results/generalization_current_python_refresh_v2_20261025/current_native_discovery.json':'1b7f635bc7fc0abb8cf02321f63b24c2ec95e4dce4dd11ec645e565ecf2b4782'}
    for name,want in anchors.items():assert sha(BASE/'workspace'/name)==want
    current=json.loads((BASE/'workspace/results/generalization_current_python_refresh_v2_20261025/current_native_discovery.json').read_bytes())
    home=Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python')
    for name,want in current['current_native_files'].items():
        key='bundled_python/'+Path(name).relative_to(home).as_posix()
        assert copied['files'][key]['sha256']==want
    assert shutil.disk_usage(BASE).free>=2*2**30
    value={'status':'INDEPENDENTLY_VERIFIED_C_MATERIAL_NOT_EXECUTION_ADMISSION',
        'UTC':datetime.now(timezone.utc).isoformat(),'original_copy_receipt_sha256':EXPECTED,
        'closed_progress_sha256':hashlib.sha256(progress_raw).hexdigest(),'copy_plan_sha256':sha(BASE/'copy_plan.json'),
        'rehash_file_count':9942,'rehash_bytes':total,'selected_scientific_payload_files':7998,
        'protected_user_files':33,'copied_bundled_native_files':42,'actual_copy_tool_exit_code_observed':0,
        'copy_tool_session_id':79933,'original_copy_elapsed_seconds':copied['elapsed_seconds'],
        'source_documents_independently_bound_to_raw_copied_bytes':True,'destination_confirmed_real_C_without_ancestor_reparse_points':True,
        'mandatory_copy_progress_closed_before_this_independent_receipt':True,
        'copy_deadline_semantics':'cooperative checks between I/O operations; not a hard interrupt of blocked I/O',
        'full_drive_backup':False,'scientific_or_runtime_admission_granted':False,'biological_model_fits':0,
        'verification_elapsed_seconds':time.monotonic()-started,'verification_source_sha256':sha(__file__)}
    with (BASE/'copy_independently_verified.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(value['status'],sha(BASE/'copy_independently_verified.json'),flush=True)


if __name__=='__main__':main()
