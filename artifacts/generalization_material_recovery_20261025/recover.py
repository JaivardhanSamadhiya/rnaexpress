"""One bounded copy into new private C: material; never repairs source files.

No scientific imports or computations. A partial copy is never execution
admission. The C: log survives a source-drive read/write failure.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import sys
import time

SOURCE=Path('D:/rnaexpress')
BACKUP=Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025')
HOME=Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python')
MAX_TOTAL=1024*2**20
MAX_FILE=128*2**20
RESERVE=2*2**30
DEADLINE=600
START=time.monotonic()
LAST_HASH_SOURCE=None


def digest(path):
    global LAST_HASH_SOURCE
    LAST_HASH_SOURCE=str(path)
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def path_key(name):
    assert isinstance(name,str) and '\\' not in name and ':' not in name
    path=PurePosixPath(name)
    assert not path.is_absolute() and path.parts and all(p not in ('.','..') for p in path.parts)
    assert path.as_posix()==name
    return name


def emit(stream,value):
    stream.write(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')
    stream.flush();os.fsync(stream.fileno())


def save(path,value):
    with path.open('x',encoding='utf8',newline='\n') as stream:emit(stream,value)


def budget(required=0):
    assert time.monotonic()-START<=DEADLINE,'600-second recovery-copy deadline'
    assert shutil.disk_usage(BACKUP).free>=RESERVE+required,'C: reserve would be violated'


def main():
    assert SOURCE.resolve()==Path('D:/rnaexpress').resolve()
    assert BACKUP.parent.is_dir() and not BACKUP.exists()
    assert Path(sys.executable).resolve()==(HOME/'python.exe').resolve()
    assert sys.flags.no_site and sys.dont_write_bytecode
    BACKUP.mkdir()
    with (BACKUP/'progress.jsonl').open('x',encoding='utf8',newline='\n') as log:
        emit(log,{'status':'BOUNDED_RECOVERY_COPY_STARTED_NOT_RUNTIME_OR_RESEARCH_ADMISSION',
            'UTC':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'source_root':str(SOURCE),
            'destination_root':str(BACKUP),'max_copy_bytes':MAX_TOTAL,'C_free_reserve':RESERVE,
            'deadline_seconds':DEADLINE,'source_files_modified':False,'automatic_retry':False})
        plan={};copied={};total=0;current=None;phase='plan'
        try:
            def add(src,dst,want):
                budget()
                dst=path_key(dst);src=Path(src)
                assert isinstance(want,str) and len(want)==64
                assert not src.is_symlink()
                assert src.resolve().is_relative_to(SOURCE.resolve()) or src.resolve().is_relative_to(HOME.resolve())
                value={'source':str(src),'sha256':want}
                assert dst not in plan or plan[dst]==value,'Conflicting copy source: '+dst
                plan[dst]=value

            def project(name,want):
                name=path_key(name);add(SOURCE/name,'workspace/'+name,want)

            def document(name,want):
                path=SOURCE/name
                assert digest(path)==want,name
                project(name,want)
                return json.loads(path.read_bytes())

            fit=document('results/generalization_knowncell_fit_paged_execution_20261025/preparation_manifest.json',
                '4a8d83023675d17cdc4af37801dc69df4b2c49d7b397a2cfd6ba1aa8b519d632')
            for name,want in fit['files'].items():project(name,want)
            audit=document('results/generalization_knowncell_paged_interruption_audit_20261025/interrupted_fit_audit.json',
                'e2a58d36e70cb7e1aa54a8ff7b0ae16f21f5efd26b69b0f05abb516efdcdbf8d')
            for name,want in audit['files_sha256'].items():project(name,want)
            run_name='results/generalization_knowncell_fit_paged_execution_20261025/run_admission.json'
            run=document(run_name,'a38f9e98af718c333334cc005f89be287a241412538710e332dd4256fc0631b2')
            for name,want in {**run['input_pins'],**run['data_pins']}.items():project(name,want)
            snapshot=SOURCE/'results/generalization_prelib_binding_descriptive_20261008/protected_user_file_snapshot.json'
            project(snapshot.relative_to(SOURCE).as_posix(),digest(snapshot))
            protected=json.loads(snapshot.read_bytes())['user_modified_files_at_turn_start']
            assert len(protected)==33
            for name,want in protected.items():project(name,want)
            expanded_name='results/generalization_knowncell_parser_profile_v3_20261023/payload_inventory.json'
            assert expanded_name in fit['files']
            expanded=document(expanded_name,fit['files'][expanded_name])
            assert len(expanded['files'])==7998
            for name,want in expanded['files'].items():project('data/interim/mechanism_v2/runtime/'+path_key(name),want)
            discovery_name='results/generalization_current_python_refresh_v2_20261025/current_native_discovery.json'
            discovery=document(discovery_name,'1b7f635bc7fc0abb8cf02321f63b24c2ec95e4dce4dd11ec645e565ecf2b4782')
            assert len(discovery['current_native_files'])==42
            for name,want in discovery['current_native_files'].items():
                native=Path(name)
                assert native.resolve().is_relative_to(HOME.resolve())
                add(native,'bundled_python/'+native.relative_to(HOME).as_posix(),want)
            for folder,dirs,files in os.walk(HOME/'Lib'):
                dirs[:]=[name for name in dirs if name not in ('site-packages','__pycache__')]
                for name in files:
                    path=Path(folder)/name
                    if path.suffix=='.pyc':continue
                    add(path,'bundled_python/'+path.relative_to(HOME).as_posix(),digest(path))
            for path in HOME.glob('*.zip'):add(path,'bundled_python/'+path.name,digest(path))
            # New work is source/report metadata only, not unadmitted datasets.
            namespaces=('generalization_current_python_refresh_20261025','generalization_current_python_refresh_v2_20261025',
                'generalization_current_numeric_refresh_20261025','generalization_current_runtime_extension_design_20261025',
                'generalization_background_lifetime_probe_20261025','generalization_knowncell_paged_interruption_audit_20261025',
                'generalization_knowncell_replay_v4_execution_20261025','generalization_knowncell_replay_v4_runtime_20261025',
                'generalization_knowncell_evaluation_v2_execution_20261025','generalization_knowncell_evaluation_v2_runtime_20261025',
                'generalization_launcher_source_review_20261025','generalization_material_recovery_20261025')
            for ns in namespaces:
                for kind in ('src','reports','results','artifacts'):
                    directory=SOURCE/kind/ns
                    if not directory.is_dir():continue
                    for path in directory.iterdir():
                        if path.is_file():
                            name=path.relative_to(SOURCE).as_posix();project(name,digest(path))
            for name in ('HANDOFF_TO_NEW_CODEX.md','reports/generalization_research_checkpoint_20261024/status.md'):
                project(name,digest(SOURCE/name))
            for dst,item in plan.items():
                current=item['source'];budget();src=Path(current);size=src.stat().st_size
                assert 0<=size<=MAX_FILE,item['source']
                item['size_bytes']=size;total+=size
                assert total<=MAX_TOTAL,'Material exceeds bounded recovery budget'
            budget(total)
            save(BACKUP/'copy_plan.json',{'files':plan,'expected_file_count':len(plan),'expected_bytes':total,
                'verification_source_sha256':digest(Path(__file__)),'scientific_OR_runtime_admission_granted':False})
            emit(log,{'status':'PLAN_COMPLETE','files':len(plan),'bytes':total})
            phase='copy'
            for key,item in plan.items():
                current=item['source'];budget(item['size_bytes'])
                source=Path(current);dest=BACKUP/key
                assert dest.resolve().is_relative_to(BACKUP.resolve())
                dest.parent.mkdir(parents=True,exist_ok=True)
                before=source.stat();actual=hashlib.sha256();size=0
                with source.open('rb') as src,dest.open('xb') as target:
                    for block in iter(lambda:src.read(1<<20),b''):
                        budget();size+=len(block)
                        assert size<=item['size_bytes']<=MAX_FILE
                        actual.update(block);assert target.write(block)==len(block)
                    target.flush();os.fsync(target.fileno())
                after=source.stat()
                assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
                assert size==item['size_bytes'] and actual.hexdigest()==item['sha256'],current
                assert digest(dest)==item['sha256'],str(dest)
                copied[key]={'sha256':item['sha256'],'size_bytes':size}
                if len(copied)%100==0:emit(log,{'status':'VERIFIED_COPY_PROGRESS','copied':len(copied),'planned':len(plan),'latest_source':current})
            budget()
            value={'status':'PASS_BOUNDED_VERIFIED_MATERIAL_COPY_NOT_FULL_DRIVE_BACKUP_OR_EXECUTION_ADMISSION',
                'UTC':datetime.now(timezone.utc).isoformat(),'files':copied,'copied_file_count':len(copied),
                'copied_bytes':total,'elapsed_seconds':time.monotonic()-START,'protected_user_files':33,
                'original_D_files_modified':False,'scientific_packages_imported':False,'biological_models_fit':0,
                'full_drive_backup':False,'scientific_OR_runtime_admission_granted':False,
                'verification_source_sha256':digest(Path(__file__))}
            save(BACKUP/'copy_verified.json',value)
            emit(log,{'status':value['status'],'copied':len(copied),'bytes':total})
            print(value['status'],len(copied),total,flush=True)
        except BaseException as error:
            value={'status':'FAILED_OR_PARTIAL_BOUNDED_COPY_NO_RETRY','UTC':datetime.now(timezone.utc).isoformat(),
                'phase':phase,'current_source':current,'exception_type':type(error).__name__,'error':str(error),
                'last_hash_source':LAST_HASH_SOURCE,
                'errno':getattr(error,'errno',None),'filename':getattr(error,'filename',None),
                'copied_file_count':len(copied),'planned_file_count':len(plan),'verified_files':copied,
                'elapsed_seconds':time.monotonic()-START,'source_files_modified':False,
                'scientific_OR_runtime_admission_granted':False}
            save(BACKUP/'copy_failure.json',value);emit(log,value)
            raise


if __name__=='__main__':main()
