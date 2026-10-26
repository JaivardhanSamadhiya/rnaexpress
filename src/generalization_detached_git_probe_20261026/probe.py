"""Real owned Git metadata diagnostic; never a study attempt or authority."""
import argparse
import faulthandler
import ctypes as C
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
if __name__=='__main__':
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(CACHE) or os.path.lexists(CACHE):
        raise RuntimeError('Require nonoptimized source-only fixed cache mode')
from src.generalization_current_study_execution_v2_20261026 import common as reader
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set
OUT=ROOT/'results/generalization_detached_git_probe_20261026'
SPEC=OUT/'preparation_manifest.json'
GEN='9da990f95a33b3b9cef65efac864c1b36b72cdb4873239b6b5db5a3502296268'
COMMIT='6ea76d492acade7467c7742f00ed6e1aeba44646'
TARGET='results/'+reader.NS+'/execution_manifest.json'


def save(name,value):
    raw=reader.canonical(value)+b'\n'
    with (OUT/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return reader.digest(raw)
def guard(memory,elapsed,*,startup=False):
    problem=reader.resource_failure(memory,0,startup=startup)
    if problem:raise RuntimeError(problem)
    if not 0<=elapsed<=180:raise RuntimeError('180-second total diagnostic deadline')
def verify(spec_sha):
    raw=SPEC.read_bytes();assert reader.digest(raw)==spec_sha
    spec=reader.decode(raw)
    for name,want in spec['files'].items():assert reader.sha(ROOT/name)==want,name
    for name,want in spec['python_native_files'].items():assert reader.sha(name)==want,name
    manifest_raw=(ROOT/TARGET).read_bytes();assert reader.digest(manifest_raw)==GEN
    for name,want in reader.decode(manifest_raw)['files'].items():assert reader.sha(ROOT/name)==want,name
    assert reader.DETACHED_GIT_PROCESS==8
    return spec


def prepare():
    assert not SPEC.exists()
    files={}
    for name in ('src/generalization_detached_git_probe_20261026/__init__.py',
        'src/generalization_detached_git_probe_20261026/probe.py',
        'src/generalization_current_study_execution_v2_20261026/common.py',
        'src/generalization_current_study_execution_v2_20261026/__init__.py',
        'src/generalization_pum_process_probe_20261021/headless.py',
        'src/generalization_pum_resource_calibration_20261009/winjob.py',
        'src/generalization_owned_workingset_probe_v2_20261025/working_set.py',TARGET):
        files[name]=reader.sha(ROOT/name)
    home=Path(sys.executable).resolve().parent
    return save('preparation_manifest.json',{'status':'FROZEN_INVENTED_DETACHED_GIT_METADATA_ONLY',
        'files':files,'python_native_files':{str(home/name):reader.sha(home/name) for name in ('python.exe','python3.dll','python312.dll')},
        'source_generation':GEN,'target_commit':COMMIT,'actual_study_attempt':False,
        'biological_reads':0,'optimizer_calls':0,'automatic_retry':False})


def child(parent,spec_sha,started):
    verify(spec_sha);assert os.getppid()==parent;results=[]
    for _ in range(4):
        for revision in ('HEAD',COMMIT):
            guard(headless.memory(),time.monotonic()-started)
            raw=reader.committed(TARGET,revision)
            assert reader.digest(raw)==GEN
            results.append({'revision':revision,'raw_sha256':reader.digest(raw),'bytes':len(raw)})
            time.sleep(.05)
    verify(spec_sha);guard(headless.memory(),time.monotonic()-started)
    save('child_completion.json',{'status':'PASS_EXACT_DETACHED_GIT_METADATA_ONLY','parent_pid':parent,
        'child_pid':os.getpid(),'preparation_manifest_sha256':spec_sha,'results':results,
        'actual_study_attempt':False,'biological_reads':0,'optimizer_calls':0})


def roster(job):
    w=headless.original
    class PIDs(C.Structure):
        _fields_=[('assigned',w.DWORD),('listed',w.DWORD),('pids',w.SIZE_T*16)]
    value=job._query(3,PIDs)
    assert value.listed<=16
    return [int(value.pids[i]) for i in range(value.listed)]


def parent(spec_sha):
    started=time.monotonic();verify(spec_sha)
    before=headless.memory();guard(before,time.monotonic()-started,startup=True)
    assert not any((OUT/name).exists() for name in ('parent.jsonl','child_completion.json','receipt.json','child_fault.log'))
    child_process=cap=None;problem=None;child_sha=None
    maximum_active=maximum_roster=peak_private=peak_resident=0;samples=0
    with (OUT/'parent.jsonl').open('x',encoding='utf8',newline='\n') as stream:
        reader.write(stream,{'status':'ONE_INVENTED_METADATA_JOB_STARTED','parent_pid':os.getpid(),'memory':before,'spec_sha256':spec_sha})
        with headless.Job() as job:
            try:
                assert job.limits()==reader.CAPS
                command=[sys.executable,'-S','-B','-X','pycache_prefix='+str(CACHE),'-u','-m',
                    'src.generalization_detached_git_probe_20261026.probe','--child',str(os.getpid()),
                    '--spec-sha',spec_sha,'--started',repr(started)]
                child_process=job.spawn(command,str(ROOT));cap=working_set.apply(job,child_process)
                reader.write(stream,{'status':'OWNED_CHILD_CAPPED_BEFORE_RESUME','child_pid':child_process.pid,'cap':cap,'job_limits':job.limits()})
                child_process.resume();last=-1
                while True:
                    elapsed=time.monotonic()-started;memory=headless.memory();accounting=job.accounting()
                    process=headless.process_memory(child_process.process_handle);ids=roster(job);code=child_process.exit_code()
                    maximum_active=max(maximum_active,accounting['active_processes']);maximum_roster=max(maximum_roster,len(ids))
                    peak_private=max(peak_private,process['peak_private_commit']);peak_resident=max(peak_resident,process['peak_working_set']);samples+=1
                    reader.write(stream,{'status':'OWNED_METADATA_SAMPLE','elapsed_seconds':elapsed,'memory':memory,
                        'job':accounting,'process':process,'exact_owned_job_pids':ids,'exit_code':code})
                    guard(memory,elapsed)
                    assert accounting['active_processes']<=2 and len(ids)<=2
                    assert process['peak_private_commit']<=reader.PRIVATE and process['peak_working_set']<=reader.CEILING
                    assert accounting['peak_job_memory_used']<=reader.CAPS['job_memory_limit']
                    assert job.limits()==reader.CAPS
                    if code is None:working_set.verify(job,child_process,cap)
                    if code is not None:assert code==0;break
                    time.sleep(.02)
                raw=(OUT/'child_completion.json').read_bytes();child_sha=reader.digest(raw);value=reader.decode(raw)
                assert value['status']=='PASS_EXACT_DETACHED_GIT_METADATA_ONLY'
                assert value['parent_pid']==os.getpid() and value['child_pid']==child_process.pid
                assert value['preparation_manifest_sha256']==spec_sha and len(value['results'])==8
                assert all(item['raw_sha256']==GEN for item in value['results'])
                assert value['biological_reads']==value['optimizer_calls']==0
            except BaseException as error:
                problem=type(error).__name__+': '+str(error);job.terminate()
            finally:
                if child_process:
                    try:
                        final_process=headless.process_memory(child_process.process_handle);final_job=job.accounting()
                        reader.write(stream,{'status':'FINAL_OWNED_COUNTERS','process':final_process,'job':final_job})
                        if problem is None:assert final_job['active_processes']==0
                    finally:child_process.close()
        reader.write(stream,{'status':'MANDATORY_TELEMETRY_COMPLETE','failure':problem})
    log_sha=reader.sha(OUT/'parent.jsonl')
    if problem is None:
        try:
            verify(spec_sha);assert reader.sha(OUT/'child_completion.json')==child_sha
            guard(headless.memory(),time.monotonic()-started)
        except BaseException as error:problem=type(error).__name__+': '+str(error)
    result={'status':'PASS_REAL_DETACHED_GIT_OWNED_METADATA_PROBE' if problem is None else 'FAILED_METADATA_PROBE_NO_RETRY',
        'failure':problem,'elapsed_seconds':time.monotonic()-started,'samples':samples,
        'maximum_sampled_active_processes':maximum_active,'maximum_sampled_owned_PID_count':maximum_roster,
        'peak_worker_private_commit':peak_private,'peak_worker_working_set':peak_resident,
        'closed_journal_sha256':log_sha,'child_completion_sha256':child_sha if problem is None else None,
        'preparation_manifest_sha256':spec_sha,'biological_reads':0,'optimizer_calls':0,
        'actual_study_attempt':False,'new_human_authority_created':False,'earlier_third_process_identity_proven':False}
    save('receipt.json',result);print(result['status'],problem,flush=True)
    assert problem is None,problem


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--spec-sha')
    parser.add_argument('--child',type=int);parser.add_argument('--started',type=float);args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.prepare:print('PROBE_SPEC',prepare(),flush=True)
    elif args.child is not None:
        with (OUT/'child_fault.log').open('x',encoding='utf8',buffering=1) as stream:
            sys.stdout=sys.stderr=stream;faulthandler.enable(stream)
            try:child(args.child,args.spec_sha,args.started)
            except BaseException:
                import traceback
                traceback.print_exc();stream.flush();os.fsync(stream.fileno());raise
            finally:faulthandler.disable()
    else:parent(args.spec_sha)
