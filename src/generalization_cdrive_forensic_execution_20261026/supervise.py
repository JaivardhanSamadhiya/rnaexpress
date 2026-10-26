"""Explicitly root-started one-attempt parent for separate read-only forensics."""
import argparse
import os
from pathlib import Path
import sys
import time

_CACHE=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
if __name__=='__main__':
    assert sys.flags.no_site==1 and sys.dont_write_bytecode and sys.pycache_prefix==str(_CACHE) and not _CACHE.exists()

from . import common as c
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set as resident


def counts_ok(process,accounting):
    assert process['peak_private_commit']<=c.PRIVATE_CAP
    assert accounting['peak_job_memory_used']<=c.JOB_CAP and accounting['peak_process_memory_used']<=c.PRIVATE_CAP
    assert process['working_set']<=process['peak_working_set']<=c.RESIDENT_CEILING
    assert accounting['active_processes']<=2


def run(generation,*,root_start_readonly=False):
    assert root_start_readonly is True,'Explicit root-start-readonly is mandatory'
    started=time.monotonic();manifest=c.sources(generation,committed=True)
    c.bind_read_set(manifest);c.old_absences()
    before=headless.memory();assert c.resource_failure(before,time.monotonic()-started,startup=True) is None
    for path in (c.BIRTH,c.CHILD_IDENTITY,c.CHILD_OWNER,c.REPORT,c.COMPLETION,c.SUPERVISOR,c.JOURNAL,c.FAULT_LOG):
        assert not os.path.lexists(path),'No resume or overwrite: '+str(path)
    assert not list(c.OUT.glob('runtime_*.json'))
    birth_sha=c.save_new(c.BIRTH,{'status':'NEW_EXCLUSIVE_READONLY_FORENSIC_ATTEMPT_NOT_FIT_RETRY',
        'stage':c.STAGE,'generation_manifest_sha256':generation,'parent_pid':os.getpid(),
        'total_started_monotonic':started,'automatic_retry':False,
        'input_pin_map_sha256':c.digest(c.canonical(manifest['readonly_input_pins'])),
        'model_fitting_authorized':False,'biological_readonly_inputs_authorized':True})
    identity_sha=c.save_new(c.CHILD_IDENTITY,{'parent_pid':os.getpid(),
        'birth_sha256':birth_sha,'generation_manifest_sha256':generation,
        'prospective_job_limits':c.JOB_LIMITS,'resident_request':c.RESIDENT_REQUEST})
    child=None;cap=None;problem=None;report_sha=completion_sha=owner_sha=None
    samples=peak_private=peak_resident=0;minimum_physical=before['physical_available']
    with c.JOURNAL.open('x',encoding='utf8',newline='\n') as stream:
        c.write(stream,{'status':'NEW_READONLY_PARENT_STARTED','parent_pid':os.getpid(),'birth_sha256':birth_sha,
                        'generation_manifest_sha256':generation,'memory':before,'native_origins':headless.native_origins()})
        with headless.Job() as job:
            try:
                assert job.limits()==c.JOB_LIMITS
                # Identity is frozen before PID exists; a separate parent-owned
                # record binds the real PID/membership/cap before first resume.
                command=[sys.executable,'-S','-B','-X','pycache_prefix='+str(c.SOURCE_CACHE),'-u','-m',
                    'src.'+c.NS+'.worker',str(os.getpid()),generation,birth_sha,identity_sha,repr(started)]
                assert c.resource_failure(headless.memory(),time.monotonic()-started,startup=True) is None
                child=job.spawn(command,str(c.ROOT));cap=resident.apply(job,child)
                job._membership(child.process_handle)
                owner_sha=c.save_new(c.CHILD_OWNER,{'parent_pid':os.getpid(),'worker_pid':child.pid,
                    'generation_manifest_sha256':generation,'birth_sha256':birth_sha,'job_limits':c.JOB_LIMITS,
                    'owned_child_identity_sha256':identity_sha,
                    'resident_cap':cap,'exact_parent_owned_Job_membership_checked_before_resume':True})
                c.write(stream,{'status':'OWNED_CHILD_IDENTIFIED_BEFORE_RESUME','worker_pid':child.pid,
                    'identity_sha256':identity_sha,'current_child_record_sha256':owner_sha,'resident_cap':cap,'job_limits':job.limits()})
                child.resume();last=-10
                while True:
                    elapsed=time.monotonic()-started;state=headless.memory()
                    process=headless.process_memory(child.process_handle);accounting=job.accounting();code=child.exit_code()
                    samples+=1;peak_private=max(peak_private,process['peak_private_commit']);peak_resident=max(peak_resident,process['peak_working_set'])
                    minimum_physical=min(minimum_physical,state['physical_available'])
                    pending=c.resource_failure(state,elapsed)
                    adverse=process['peak_private_commit']>c.PRIVATE_CAP or process['peak_working_set']>c.RESIDENT_CEILING or accounting['peak_job_memory_used']>c.JOB_CAP or accounting['active_processes']>2
                    if elapsed-last>=1 or code is not None or pending or adverse:
                        c.write(stream,{'status':'OWNED_READONLY_SAMPLE','elapsed_seconds':elapsed,'memory':state,
                            'process':process,'job':accounting,'exit_code':code,'failure':pending});last=elapsed
                    counts_ok(process,accounting);assert job.limits()==c.JOB_LIMITS
                    if code is None:resident.verify(job,child,cap)
                    if pending:raise RuntimeError(pending)
                    if code is not None:
                        assert code==0,'Forensic worker exit '+str(code);break
                    time.sleep(.1)
                report_raw=c.REPORT.read_bytes();completion_raw=c.COMPLETION.read_bytes()
                report_sha,completion_sha=c.digest(report_raw),c.digest(completion_raw)
                c.terminal(c.decode(report_raw),c.decode(completion_raw),generation,birth_sha,identity_sha,owner_sha,os.getpid(),child.pid)
                assert c.sha(c.CHILD_IDENTITY)==identity_sha
                assert c.sha(c.BIRTH)==birth_sha
                assert c.sha(c.CHILD_OWNER)==owner_sha
                for key,want in c.decode(report_raw)['checkpoint_current_runtime_proof_sha256'].items():
                    assert c.sha(c.OUT/('runtime_'+key+'.json'))==want
                c.sources(generation)
            except BaseException as error:
                problem=type(error).__name__+': '+str(error);job.terminate()
            finally:
                if child is not None:
                    try:
                        process=headless.process_memory(child.process_handle);accounting=job.accounting()
                        c.write(stream,{'status':'FINAL_LIFETIME_COUNTERS','process':process,'job':accounting})
                        counts_ok(process,accounting)
                        peak_private=max(peak_private,process['peak_private_commit']);peak_resident=max(peak_resident,process['peak_working_set'])
                        if problem is None:assert accounting['active_processes']==0
                    except BaseException as error:
                        problem=problem or type(error).__name__+': '+str(error);job.terminate()
                    finally:child.close()
        c.write(stream,{'status':'MANDATORY_PARENT_TELEMETRY_COMPLETE','failure':problem})
    log_sha=c.sha(c.JOURNAL)
    if problem is None:
        try:
            c.sources(generation);c.old_absences()
            assert c.sha(c.REPORT)==report_sha and c.sha(c.COMPLETION)==completion_sha
            assert c.sha(c.BIRTH)==birth_sha and c.sha(c.CHILD_IDENTITY)==identity_sha
            assert c.sha(c.CHILD_OWNER)==owner_sha
            def fresh():assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
            c.rehash_read_set(manifest,fresh=fresh)
        except BaseException as error:problem=type(error).__name__+': '+str(error)
    final=headless.memory();elapsed=time.monotonic()-started
    minimum_physical=min(minimum_physical,final['physical_available'])
    problem=problem or c.resource_failure(final,elapsed)
    result={'status':c.PARENT_PASS if problem is None else 'FAILED_NEW_FORENSIC_JOB_NO_RETRY',
        'generation_manifest_sha256':generation,'birth_sha256':birth_sha,'owned_child_identity_sha256':identity_sha,
        'current_child_record_sha256':owner_sha,
        'parent_pid':os.getpid(),'worker_pid':child.pid if child else None,'failure':problem,
        'elapsed_seconds':elapsed,'samples':samples,'peak_private_commit':peak_private,'peak_working_set':peak_resident,
        'minimum_sampled_physical_available':minimum_physical,'final_memory':final,
        'closed_journal_sha256':log_sha,'validated_report_sha256':report_sha if problem is None else None,
        'validated_completion_sha256':completion_sha if problem is None else None,
        'biological_inputs_read':True if report_sha else 'unknown_if_worker_failed_before_report',
        'new_optimizer_calls':0,'old_campaign_completion_synthesized':False,'original_formal_replay_still_ineligible':True,
        'evaluation_or_gate_run':False,'outer_performance_computed_or_published':False}
    c.save_new(c.SUPERVISOR,result)
    print(result['status'],problem,flush=True);assert problem is None,problem


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root-start-readonly',action='store_true',required=True)
    parser.add_argument('--manifest-sha',required=True);args=parser.parse_args()
    run(args.manifest_sha,root_start_readonly=args.root_start_readonly)
