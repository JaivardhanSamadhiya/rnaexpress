"""Owned invented-only profile for the October 30 native epoch.

No biological loader, campaign birth, old admission mutation or automatic retry.
The unchanged 3 GiB floor is checked before birth and throughout execution.
"""
import argparse
import faulthandler
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from . import policy as p
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set as resident


def source_proof(expected):
    p.source_mode()
    value = p.checked_document(p.MANIFEST,expected)
    assert value['status'] == 'FROZEN_NEW_EPOCH_INVENTED_MENU_NUMERICAL_PROFILE'
    for key,want in value['files'].items():
        path = (p.ROOT/key).resolve()
        assert path.is_relative_to(p.ROOT) and not (p.ROOT/key).is_symlink()
        assert p.sha(path) == want, key
    return value


def native_roster():
    home = p.PYTHON.resolve().parent
    candidates = list(home.iterdir()) + list((home/'DLLs').rglob('*'))
    files = {}
    for path in candidates:
        if path.is_file() and path.suffix.lower() in ('.exe','.dll','.pyd'):
            assert not path.is_symlink() and path.resolve().is_relative_to(home)
            files[str(path.resolve())] = p.sha(path)
    assert str(p.PYTHON.resolve()) in files
    return dict(sorted(files.items()))


def freeze():
    p.source_mode()
    assert not p.MANIFEST.exists()
    old = p.checked_document(p.OLD_INVENTORY,p.OLD_SHA)
    new = p.checked_document(p.NEW_INVENTORY,p.NEW_SHA)
    native = native_roster()
    assert all(native.get(key) == want for key,want in new['registered_native_files_sha256'].items())
    assert len(old['selected_scientific_payload_files']) == 7998
    assert new['status'] == 'SOFTWARE_BYTES_CURRENT_NATIVE_MEMBERSHIP_NOT_NUMERICAL_ADMISSION'
    assert new['scientific_payload_membership_and_bytes_unchanged'] is True
    assert new['scientific_payload_files_rehashed'] == 7998
    # Import only deferred source modules to bind their project-source closure.
    for name in (
        'src.generalization_menu_numeric_20261030.engine',
        'src.generalization_menu_numeric_20261030.cases',
        'src.generalization_menu_numeric_20261030.tests',
        'src.generalization_menu_numeric_20261030.inventory',
        'src.generalization_splicebert_runtime_compatibility_20261007.launcher',
        'src.generalization_cdrive_numeric_profile_20261025.runtime',
        'src.generalization_knowncell_parser_profile_v3_20261023.cache_integrity',
        'src.generalization_knowncell_parser_profile_20261022.parser_profile',
        'src.generalization_knowncell_joint_loader_20261022.parsers',
    ):importlib.import_module(name)
    assert not any(key.split('.')[0] in ('numpy','pandas','scipy','torch') for key in sys.modules)
    files = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module,'__file__',None)
        if not name:continue
        path = Path(name).resolve()
        if path.is_relative_to(p.ROOT) and path.suffix == '.py':
            files[path.relative_to(p.ROOT).as_posix()] = p.sha(path)
    for path in (p.OLD_INVENTORY,p.NEW_INVENTORY,
                 p.ROOT/'reports'/p.NS/'design.md'):
        files[path.relative_to(p.ROOT).as_posix()] = p.sha(path)
    p.OUT.mkdir(parents=True,exist_ok=True)
    p.dump(p.MANIFEST,dict(status='FROZEN_NEW_EPOCH_INVENTED_MENU_NUMERICAL_PROFILE',
        files=dict(sorted(files.items())),native_roster=native,
        scientific_payload_files=7998,physical_floor_bytes=3*2**30,
        process_cap_bytes=768*2**20,job_cap_bytes=896*2**20,
        requested_resident_maximum_bytes=190*2**20,resident_ceiling_bytes=192*2**20,
        active_owned_limit=2,deadline_seconds=p.DEADLINE,threads=1,
        expected_invented_optimizer_units=9,automatic_retry=False,
        biological_input_admission=False,biological_fit_authority=False))
    print(json.dumps(dict(status='SOURCE_FROZEN_NOT_EXECUTED',source_pins=len(files),
                         native_paths=len(native),manifest_sha256=p.sha(p.MANIFEST))))


def payload(manifest,fresh):
    old = p.checked_document(p.OLD_INVENTORY,p.OLD_SHA)
    expected = old['selected_scientific_payload_files']
    assert native_roster() == manifest['native_roster'], 'new native membership/bytes drift'
    components = {key.split('/')[0] for key in expected}
    actual = set()
    for component in components:
        root = p.PREFIX/component
        candidates = [root] if root.is_file() else root.rglob('*')
        for path in candidates:
            if not path.is_file():continue
            assert not path.is_symlink() and path.resolve().is_relative_to(p.PREFIX.resolve())
            key = path.relative_to(p.PREFIX).as_posix()
            assert key in expected and p.sha(path) == expected[key], key
            actual.add(key)
            if len(actual) % 128 == 0:fresh()
    assert actual == set(expected), 'scientific membership drift'
    fresh()
    return expected


def origins(manifest,scientific,threadpoolctl):
    from src.generalization_splicebert_runtime_compatibility_20261007.launcher import process_native_paths
    from src.generalization_cdrive_numeric_profile_20261025.runtime import classify_loaded_native
    from src.generalization_knowncell_parser_profile_v3_20261023.cache_integrity import possible_cache_proof
    natives = {key:want for key,want in scientific.items() if Path(key).suffix.lower() in ('.dll','.pyd')}
    scientific_native,current = classify_loaded_native(process_native_paths(),natives,
        manifest['native_roster'],prefix=p.PREFIX,home=p.PYTHON.parent,hasher=p.sha)
    assert any(Path(key).name.lower() == 'python312.dll' for key in current)
    source = {}
    for name,module in tuple(sys.modules.items()):
        raw = getattr(module,'__file__',None)
        if not raw:continue
        path = Path(raw).resolve()
        if path.is_relative_to(p.PREFIX.resolve()):
            key = path.relative_to(p.PREFIX).as_posix()
            assert key in scientific and p.sha(path) == scientific[key], name
            source[key] = scientific[key]
        elif path.is_relative_to(p.ROOT):
            key = path.relative_to(p.ROOT).as_posix()
            assert key in manifest['files'] and p.sha(path) == manifest['files'][key], name
        elif any(part.lower() == 'site-packages' for part in path.parts):
            raise AssertionError('Foreign scientific source: '+str(path))
    pools = threadpoolctl.threadpool_info()
    assert pools
    for pool in pools:
        path = str(Path(pool['filepath']).resolve())
        assert pool['num_threads'] == 1 and path in scientific_native
    caches = possible_cache_proof(sys.modules,p.PREFIX,scientific)
    return dict(loaded_current_native=current,loaded_scientific_native=scientific_native,
                loaded_scientific_source=source,threadpools=pools,possible_caches=caches)


def child(expected,parent_pid):
    assert os.getppid() == parent_pid
    started = time.monotonic()
    manifest = source_proof(expected)
    assert all(os.environ.get(k) == v for k,v in p.THREADS.items())
    def fresh():
        problem = p.resource_failure(headless.memory(),time.monotonic()-started)
        assert problem is None, problem
    fresh()
    scientific = payload(manifest,fresh)
    home = p.PYTHON.parent
    sys.path[:] = [str(p.PREFIX),str(p.ROOT),str(home/'python312.zip'),
                   str(home/'DLLs'),str(home/'Lib'),str(home)]
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    imported = []
    for name in ('numpy','pandas','scipy','scipy.optimize','scipy.special','threadpoolctl'):
        fresh()
        imported.append(importlib.import_module(name))
    np,pd,scipy,optimize,special,threadpoolctl = imported
    for module,version in ((np,'1.26.4'),(pd,'2.2.3'),(scipy,'1.14.1')):
        assert module.__version__ == version
        assert Path(module.__file__).resolve() == p.PREFIX/module.__name__/'__init__.py'
    fresh()
    before = origins(manifest,scientific,threadpoolctl)
    from src.generalization_knowncell_parser_profile_20261022.parser_profile import run as parser
    from .cases import run as numeric
    parser_result = parser(pd)
    fresh()
    numerical_result = numeric(np,optimize.minimize,special.expit)
    fresh()
    after = origins(manifest,scientific,threadpoolctl)
    source_proof(expected)
    p.dump(p.OUT/'child.json',dict(status='PASS_INVENTED_NEW_EPOCH_NUMERICAL_PROFILE',
        manifest_sha256=expected,parent_pid=parent_pid,child_pid=os.getpid(),
        native_before=before,native_after=after,parser=parser_result,numerical=numerical_result,
        biological_inputs_read=False,biological_model_fits=0,elapsed_seconds=time.monotonic()-started))


def write_event(stream,value):
    stream.write(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')
    stream.flush();os.fsync(stream.fileno())


def run(expected):
    started = time.monotonic()
    source_proof(expected)
    # Verify the exact committed freeze before consuming this profile's one birth.
    assert p.sha(headless.DIRECT_GIT) == headless.DIRECT_GIT_SHA, 'Direct Git binary changed'
    committed = subprocess.check_output([str(headless.DIRECT_GIT),'-c','maintenance.auto=false',
        '-c','gc.auto=0','show','HEAD:'+p.MANIFEST.relative_to(p.ROOT).as_posix()],
        cwd=p.ROOT,creationflags=headless.DETACHED_PROCESS,timeout=30)
    assert committed == p.MANIFEST.read_bytes()
    before = headless.memory()
    problem = p.resource_failure(before,time.monotonic()-started)
    if problem:
        print(json.dumps(dict(status='NOT_STARTED_RESOURCE_PREFLIGHT',reason=problem,memory=before,
                              attempt_consumed=False,scientific_imports=0)))
        return
    assert not (p.OUT/'parent.jsonl').exists(), 'No retry or overwrite'
    owned = cap = None
    peak_private = peak_resident = peak_job = 0
    minimum_physical = before['physical_available']
    child_sha = None
    with (p.OUT/'parent.jsonl').open('x',encoding='utf8',newline='\n') as stream:
        write_event(stream,dict(status='OWNED_INVENTED_PROFILE_BIRTH',memory=before,manifest_sha256=expected))
        with headless.Job() as job:
            try:
                limits = job.limits()
                assert limits == dict(process_memory_limit=768*2**20,job_memory_limit=896*2**20,
                    active_process_limit=2,limit_flags=headless.original.LIMIT_FLAGS)
                command = [str(p.PYTHON),'-S','-B','-X','pycache_prefix='+str(p.CACHE),'-u',
                           '-m','src.'+p.NS+'.profile','--child',str(os.getpid()),'--manifest-sha',expected]
                assert p.resource_failure(headless.memory(),time.monotonic()-started) is None
                owned = job.spawn(command,str(p.ROOT))
                cap = resident.apply(job,owned)
                write_event(stream,dict(status='RESIDENT_CAP_INSTALLED_BEFORE_RESUME',cap=cap,child_pid=owned.pid))
                owned.resume()
                while True:
                    state = headless.memory();elapsed = time.monotonic()-started
                    counters = headless.process_memory(owned.process_handle); accounting = job.accounting()
                    peak_private = max(peak_private,counters['peak_private_commit'])
                    peak_resident = max(peak_resident,counters['peak_working_set'])
                    peak_job = max(peak_job,accounting['peak_job_memory_used'])
                    minimum_physical = min(minimum_physical,state['physical_available'])
                    code = owned.exit_code();problem = p.resource_failure(state,elapsed)
                    write_event(stream,dict(elapsed_seconds=elapsed,memory=state,process=counters,
                        job=accounting,exit_code=code,resource_failure=problem))
                    assert problem is None,problem
                    assert peak_private <= 768*2**20 and peak_job <= 896*2**20
                    assert peak_resident <= 192*2**20 and accounting['active_processes'] <= 2
                    assert job.limits() == limits
                    if code is not None:
                        assert code == 0, 'Child exit '+str(code)
                        break
                    resident.verify(job,owned,cap)
                    time.sleep(.25)
                child_result = json.loads((p.OUT/'child.json').read_bytes())
                assert child_result['status'] == 'PASS_INVENTED_NEW_EPOCH_NUMERICAL_PROFILE'
                assert child_result['manifest_sha256'] == expected and child_result['child_pid'] == owned.pid
                assert child_result['parent_pid'] == os.getpid()
                assert child_result['numerical']['invented_optimizer_units'] == 9
                assert child_result['biological_model_fits'] == 0 and not child_result['biological_inputs_read']
                child_sha = p.sha(p.OUT/'child.json')
                source_proof(expected)
            except BaseException as error:
                problem = type(error).__name__+': '+str(error)
                job.terminate()
            finally:
                if owned is not None:
                    try:
                        final = headless.process_memory(owned.process_handle); accounting = job.accounting()
                        write_event(stream,dict(status='FINAL_LIFETIME_COUNTERS',process=final,job=accounting))
                        peak_private = max(peak_private,final['peak_private_commit'])
                        peak_resident = max(peak_resident,final['peak_working_set'])
                        peak_job = max(peak_job,accounting['peak_job_memory_used'])
                        assert peak_private <= 768*2**20 and peak_resident <= 192*2**20 and peak_job <= 896*2**20
                        if problem is None:assert accounting['active_processes'] == 0
                    except BaseException as error:
                        problem = problem or type(error).__name__+': '+str(error)
                        job.terminate()
                    finally:owned.close()
        write_event(stream,dict(status='CLOSED_OWNED_JOB_AND_PARENT_TELEMETRY',failure=problem))
    after = headless.memory()
    problem = problem or p.resource_failure(after,time.monotonic()-started)
    p.dump(p.OUT/'receipt.json',dict(status='PASS_INVENTED_RUNTIME_NOT_BIOLOGICAL_ADMISSION' if problem is None
        else 'FAILED_INVENTED_PROFILE_NO_RETRY',failure=problem,closed_parent_log_sha256=p.sha(p.OUT/'parent.jsonl'),
        child_sha256=child_sha,manifest_sha256=expected,peak_private_bytes=peak_private,
        peak_job_bytes=peak_job,peak_resident_bytes=peak_resident,
        minimum_sampled_physical_bytes=min(minimum_physical,after['physical_available']),
        elapsed_seconds=time.monotonic()-started,biological_model_fits=0,biological_inputs_read=False))
    assert problem is None,problem
    print('PASS_INVENTED_RUNTIME_NOT_BIOLOGICAL_ADMISSION')


if __name__ == '__main__':
    p.source_mode()
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--manifest-sha')
    parser.add_argument('--child',type=int)
    args = parser.parse_args()
    if args.freeze:
        assert args.manifest_sha is None and args.child is None
        freeze()
    else:
        assert args.manifest_sha and len(args.manifest_sha) == 64
        if args.child is None:run(args.manifest_sha)
        else:
            with (p.OUT/'child_fault.log').open('x',encoding='utf8',buffering=1) as log:
                sys.stdout = sys.stderr = log
                faulthandler.enable(file=log)
                try:child(args.manifest_sha,args.child)
                except BaseException:
                    import traceback
                    traceback.print_exc(file=log);log.flush();os.fsync(log.fileno());raise
                finally:faulthandler.disable()
