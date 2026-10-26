"""One owned fixed FIT lifecycle invocation; no retry, replay or evaluation."""
import argparse
import os
import sys
import time
from . import common as c
from . import terminal
from .monitor import observe


def command(generation,run_sha,birth_sha):
    return [sys.executable,'-S','-B','-X','pycache_prefix='+str(c.CACHE_PREFIX),'-u','-m','src.'+c.NS+'.worker',
        str(os.getpid()),c.valid_sha(generation),c.valid_sha(run_sha),c.valid_sha(birth_sha)]


def completion_contract(value,generation,run_sha,birth_sha,parent_pid,worker_pid):
    assert value['status']=='PASS_COMPLETE_FROZEN_EVALUATION_WORKER_CALLBACKS_RESTORED' and value['invocation']==c.INVOCATION
    assert value['generation_manifest_sha256']==generation and value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA and value['authorization_sha256']==c.AUTH_SHA and value['approval_scope_sha256']==c.SCOPE_SHA
    assert value['parent_pid']==parent_pid and value['worker_pid']==worker_pid
    assert value['callbacks_restored'] is True and type(value['fresh_calibrated_guard_calls']) is int and value['fresh_calibrated_guard_calls']>0
    assert value['new_optimizer_calls']==0 and value['scientific_verdict'] in ('JOINT_KNOWN_CELL_DEVELOPMENT_GO','NO-GO')
    assert value['CORE_reread'] is False
    assert value['source_mode']==c.source_mode() and value['resource_policy']==c.resource_policy()
    c.valid_sha(value['report_sha256']);return value


def terminal_pair(completion,report,generation,run_sha,birth_sha,parent_pid,worker_pid,started):
    return terminal.validate_report(report,completion,c.read_run(generation,run_sha),generation,run_sha,birth_sha,parent_pid,worker_pid,started)


def run(generation,run_sha,*,root_start=False):
    assert root_start is True;started=time.monotonic()
    authorization=c.admit_authorization(generation);admission=c.read_run(generation,run_sha,check_commit=True)
    c.read_source_admission(generation,admission['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()])
    c.require_new_outputs()
    from src.generalization_pum_process_probe_20261021 import headless
    before=headless.memory();assert c.resource_failure(before,time.monotonic()-started,startup=True) is None
    birth_sha=c.save_new(c.BIRTH,{'status':'ONE_OWNED_COMPLETE_FROZEN_EVALUATION_INVOCATION_CONSUMED','stage':c.STAGE,
        'invocation':c.INVOCATION,'parent_pid':os.getpid(),'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'resource_policy':c.resource_policy(),'source_mode':c.source_mode(),'automatic_retry':False})
    failure=None;observed={};child=None;report_sha=completion_sha=None;terminal_validation=None
    with headless.Job() as job:
        try:
            assert job.limits()=={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,
                'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
            c.verify_sources(generation);assert c.read_run(generation,run_sha)==admission
            failure=c.resource_failure(headless.memory(),time.monotonic()-started,startup=True);assert failure is None,failure
            child=job.spawn(command(generation,run_sha,birth_sha),str(c.ROOT));child.resume()
            observed=observe(job,child,headless.memory,headless.process_memory,time.monotonic,time.sleep,started=started);failure=observed['failure']
        except BaseException as error:
            failure=failure or type(error).__name__+': '+str(error);job.terminate()
            if child is not None and 'final_process_handle_peak_sample' not in observed:
                try:observed['final_process_handle_peak_sample']=headless.process_memory(child.process_handle)
                except BaseException as peak_error:observed['peak_sampling_error']=str(peak_error)
        finally:
            if child is not None:child.close()
    try:
        c.verify_sources(generation);assert failure is None,failure
        assert observed.get('exit_code')==0,'FIT worker did not complete successfully'
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        raw=c.COMPLETION.read_bytes();completion=c.decode(raw);completion_sha=c.sha(raw)
        completion_contract(completion,generation,run_sha,birth_sha,os.getpid(),child.pid)
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        raw=c.OUTPUT.read_bytes();report_sha=c.sha(raw);assert report_sha==completion['report_sha256']
        terminal_validation=terminal_pair(completion,c.decode(raw),generation,run_sha,birth_sha,os.getpid(),child.pid,started)
    except BaseException as error:failure=failure or type(error).__name__+': '+str(error)
    try:
        assert c.admit_authorization(generation)==authorization
        assert c.read_run(generation,run_sha,check_commit=True)==admission
        assert c.sha(c.BIRTH.read_bytes())==birth_sha
        if completion_sha is not None:
            assert c.sha(c.COMPLETION.read_bytes())==completion_sha
            assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
            assert c.sha(c.OUTPUT.read_bytes())==report_sha
        c.verify_sources(generation)
    except BaseException as error:failure=failure or type(error).__name__+': '+str(error)
    after=headless.memory();elapsed=time.monotonic()-started;failure=failure or c.resource_failure(after,elapsed)
    receipt={'status':'PASS_COMPLETE_FROZEN_EVALUATION_PENDING_ROOT_ACCEPTANCE' if failure is None else
        'FAILED_OR_BLOCKED_EVALUATION_INVOCATION_PRESERVED_NO_RETRY','failure':failure,'stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'report_sha256':report_sha,'worker_completion_sha256':completion_sha,'worker_started':child is not None,
        'observed':observed,'memory_before':before,'memory_after':after,'elapsed_seconds':elapsed,'resource_policy':c.resource_policy(),
        'parent_terminal_evaluation_validation':terminal_validation,
        'automatic_retry':False,'new_optimizer_calls':0,'scientific_verdict':None if terminal_validation is None else terminal_validation['scientific_verdict'],
        'scientific_protocol_settings_changed':False,'CORE_reread':False}
    c.save_new(c.SUPERVISOR,receipt);print(receipt['status'],failure,flush=True);assert failure is None,failure


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation-sha',required=True)
    parser.add_argument('--run-admission-sha',required=True);parser.add_argument('--root-start',action='store_true')
    args=parser.parse_args();run(args.generation_sha,args.run_admission_sha,root_start=args.root_start)
