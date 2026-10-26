"""Exactly one explicitly authorized new stage; no retry, resume or scheduler."""
import argparse
import os
import sys
import time
from pathlib import Path
if __name__=='__main__':
    _cache=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(_cache) or os.path.lexists(_cache):
        raise RuntimeError('Require nonoptimized source-only Python and the absent fixed cache prefix')
from . import common as c,validate
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set


def counters(process,job):
    assert process['peak_private_commit']<=c.PRIVATE
    assert process['working_set']<=process['peak_working_set']<=c.CEILING
    assert job['peak_process_memory_used']<=c.PRIVATE and job['peak_job_memory_used']<=c.CAPS['job_memory_limit']
    assert job['active_processes']<=2


def run(stage,generation,*,root_start_readonly=False):
    assert root_start_readonly is True
    started=time.monotonic();manifest=c.sources(generation,check_commit=True)
    run_raw,admitted=c.admission(stage,generation);run_sha=c.digest(run_raw)
    c.old_absences()
    before=headless.memory();assert c.resource_failure(before,time.monotonic()-started,startup=True) is None
    names=('attempt_birth.json','owned_child_identity.json','owned_child_started.json','worker_report.json',
        'worker_completion.json','supervisor_receipt.json','parent.jsonl','worker_fault.log')
    assert all(not os.path.lexists(stage.path(name)) for name in names)
    assert not list(stage.directory.glob('runtime_*.json'))
    assert not os.path.lexists(stage.path('campaign')) and not os.path.lexists(stage.path('current_prefit.json'))
    birth_sha=c.save_new(stage.path('attempt_birth.json'),{
        'status':'NEW_ROOT_READONLY_CURRENT_VERIFICATION_NOT_FIT',
        'stage':stage.name,'source_manifest_sha256':generation,'run_admission_sha256':run_sha,
        'read_only_authority_sha256':admitted['read_only_authority_sha256'],
        'parent_pid':os.getpid(),'started_monotonic':started,'automatic_retry':False})
    identity_sha=c.save_new(stage.path('owned_child_identity.json'),{'parent_pid':os.getpid(),
        'source_manifest_sha256':generation,'birth_sha256':birth_sha,'job_limits':c.CAPS,
        'resident_request':c.RESIDENT})
    child=cap=None;problem=None;report_sha=completion_sha=owner_sha=None
    samples=peak_private=peak_resident=0;minimum_physical=before['physical_available'];validated=None
    def fresh():assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
    with stage.path('parent.jsonl').open('x',encoding='utf8',newline='\n') as stream:
        c.write(stream,{'status':'ROOT_READONLY_VERIFICATION_PARENT_STARTED','stage':stage.name,
            'source_manifest_sha256':generation,'birth_sha256':birth_sha,'parent_pid':os.getpid(),
            'memory':before,'native_origins':headless.native_origins()})
        with headless.Job() as job:
            try:
                assert job.limits()==c.CAPS
                command=[sys.executable,'-S','-B','-X','pycache_prefix='+str(c.CACHE),'-u','-m',
                    'src.'+c.NS+'.worker',stage.name,generation,run_sha,birth_sha,identity_sha,
                    str(os.getpid()),repr(started)]
                assert c.resource_failure(headless.memory(),time.monotonic()-started,startup=True) is None
                child=job.spawn(command,str(c.ROOT));cap=working_set.apply(job,child)
                job._membership(child.process_handle)
                owner_sha=c.save_new(stage.path('owned_child_started.json'),{'parent_pid':os.getpid(),
                    'worker_pid':child.pid,'source_manifest_sha256':generation,'birth_sha256':birth_sha,
                    'owned_child_identity_sha256':identity_sha,'job_limits':c.CAPS,'resident_cap':cap,
                    'exact_parent_owned_membership_checked_before_resume':True})
                c.write(stream,{'status':'OWNED_CHILD_IDENTIFIED_BEFORE_RESUME','worker_pid':child.pid,
                    'owned_child_identity_sha256':identity_sha,'current_child_record_sha256':owner_sha,
                    'resident_cap':cap,'job_limits':job.limits()})
                child.resume();last=-10
                while True:
                    elapsed=time.monotonic()-started;memory=headless.memory()
                    process=headless.process_memory(child.process_handle);accounting=job.accounting();code=child.exit_code()
                    samples+=1;peak_private=max(peak_private,process['peak_private_commit'])
                    peak_resident=max(peak_resident,process['peak_working_set']);minimum_physical=min(minimum_physical,memory['physical_available'])
                    failure=c.resource_failure(memory,elapsed)
                    adverse=process['peak_private_commit']>c.PRIVATE or process['peak_working_set']>c.CEILING or accounting['peak_job_memory_used']>c.CAPS['job_memory_limit'] or accounting['active_processes']>2
                    if elapsed-last>=1 or code is not None or failure or adverse:
                        c.write(stream,{'status':'CURRENT_STAGE_SAMPLE','elapsed_seconds':elapsed,'memory':memory,
                            'process':process,'job':accounting,'exit_code':code,'failure':failure});last=elapsed
                    counters(process,accounting);assert job.limits()==c.CAPS
                    if code is None:working_set.verify(job,child,cap)
                    if failure:raise RuntimeError(failure)
                    if code is not None:assert code==0,'Worker exit '+str(code);break
                    time.sleep(.1)
                report_raw=stage.path('worker_report.json').read_bytes();completion_raw=stage.path('worker_completion.json').read_bytes()
                report_sha,completion_sha=c.digest(report_raw),c.digest(completion_raw)
                validated=validate.terminal(stage,c.decode(report_raw),c.decode(completion_raw),admitted,
                    generation,run_sha,birth_sha,identity_sha,owner_sha,os.getpid(),child.pid,fresh=fresh)
                c.sources(generation);fresh()
            except BaseException as error:
                problem=type(error).__name__+': '+str(error);job.terminate()
            finally:
                if child is not None:
                    try:
                        process=headless.process_memory(child.process_handle);accounting=job.accounting()
                        c.write(stream,{'status':'FINAL_LIFETIME_COUNTERS','process':process,'job':accounting})
                        counters(process,accounting)
                        peak_private=max(peak_private,process['peak_private_commit']);peak_resident=max(peak_resident,process['peak_working_set'])
                        if problem is None:assert accounting['active_processes']==0
                    except BaseException as error:
                        problem=problem or type(error).__name__+': '+str(error);job.terminate()
                    finally:child.close()
        c.write(stream,{'status':'MANDATORY_PARENT_TELEMETRY_COMPLETE','failure':problem})
    log_sha=c.sha(stage.path('parent.jsonl'))
    if problem is None:
        try:
            c.sources(generation);c.old_absences();fresh()
            assert c.sha(stage.path('worker_report.json'))==report_sha
            assert c.sha(stage.path('worker_completion.json'))==completion_sha
            assert c.sha(stage.path('attempt_birth.json'))==birth_sha
            assert c.sha(stage.path('owned_child_identity.json'))==identity_sha
            assert c.sha(stage.path('owned_child_started.json'))==owner_sha
            assert c.sha(stage.path('run_admission.json'))==run_sha
            for name,want in admitted['input_pins'].items():c.read_exact(name,want,fresh=fresh)
            report=c.decode(stage.path('worker_report.json').read_bytes())
            for key,want in report['checkpoint_current_runtime_proof_sha256'].items():assert c.sha(stage.path('runtime_'+key+'.json'))==want
            assert c.sha(c.relative(admitted['current_prefit_relative_path']))==admitted['current_prefit_sha256']
            for name,want in admitted['checkpoint_pins'].items():
                fresh();assert c.sha(c.PRODUCER/'fit/campaign/checkpoints'/name)==want
            if stage.name=='evaluate':assert c.sha(c.Stage('replay').path('worker_report.json'))==admitted['replay_report_sha256']
        except BaseException as error:problem=type(error).__name__+': '+str(error)
    final=headless.memory();elapsed=time.monotonic()-started
    minimum_physical=min(minimum_physical,final['physical_available'])
    problem=problem or c.resource_failure(final,elapsed)
    result={'status':'PASS_CURRENT_READONLY_VERIFICATION_STAGE' if problem is None else 'FAILED_CURRENT_READONLY_VERIFICATION_NO_RETRY',
        'stage':stage.name,'source_manifest_sha256':generation,'run_admission_sha256':run_sha,
        'read_only_authority_sha256':admitted['read_only_authority_sha256'],
        'birth_sha256':birth_sha,'owned_child_identity_sha256':identity_sha,'current_child_record_sha256':owner_sha,
        'parent_pid':os.getpid(),'worker_pid':child.pid if child else None,'failure':problem,
        'elapsed_seconds':elapsed,'samples':samples,'peak_private_commit':peak_private,'peak_working_set':peak_resident,
        'minimum_sampled_physical_available':minimum_physical,'final_memory':final,'closed_journal_sha256':log_sha,
        'validated_report_sha256':report_sha if problem is None else None,
        'validated_completion_sha256':completion_sha if problem is None else None,
        'validated_stage_outputs':validated if problem is None else None,
        'old_missing_completion_synthesized':False,'evaluation_or_gate_run':stage.name=='evaluate',
        'model_fits_or_refits':0,'automatic_retry':False}
    c.save_new(stage.path('supervisor_receipt.json'),result)
    try:print(result['status'],stage.name,problem,flush=True)
    except OSError:pass  # Optional console follows the durable terminal receipt.
    assert problem is None,problem


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=c.STAGES)
    parser.add_argument('--manifest-sha',required=True);parser.add_argument('--root-start-readonly',action='store_true',required=True)
    args=parser.parse_args();run(c.Stage(args.stage),args.manifest_sha,root_start_readonly=args.root_start_readonly)
