"""One separately owned bounded array invocation, no retry or resume."""
import argparse
import os
import sys
import time
from . import common as c
from .worker import validate_certificate
from src.generalization_knowncell_metadata_verification_execution_20261024.monitor import observe


def command(generation,run_sha,birth_sha):
    return [sys.executable,'-S','-B','-X','pycache_prefix='+str(c.CACHE_PREFIX),'-u','-m',
        'src.'+c.NS+'.worker',str(os.getpid()),c.valid_sha(generation),c.valid_sha(run_sha),c.valid_sha(birth_sha)]


def completion_contract(value,generation,run_sha,birth_sha,parent_pid,worker_pid):
    assert value['status']=='PASS_EXACT_ARRAY_WORKER_CALLBACKS_RESTORED'
    assert value['invocation']==c.INVOCATION and value['generation_manifest_sha256']==generation
    assert value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA and value['authorization_sha256']==c.AUTH_SHA
    assert value['approval_scope_sha256']==c.SCOPE_SHA
    assert value['parent_pid']==parent_pid and value['worker_pid']==worker_pid
    assert value['callbacks_restored'] is True and type(value['fresh_calibrated_guard_calls']) is int
    assert value['fresh_calibrated_guard_calls']>0
    assert value['numerical_outcomes_admitted']==value['model_fits']==0 and value['array_reads']==1
    assert value['source_mode']==c.source_mode() and value['resource_policy']==c.resource_policy()
    c.valid_sha(value['certificate_sha256'])
    return value


def run(generation,run_sha,*,root_start=False):
    assert root_start is True
    started=time.monotonic()
    authorization=c.admit_authorization(generation)
    admission=c.read_run(generation,run_sha,check_commit=True)
    c.require_new_outputs()
    from src.generalization_pum_process_probe_20261021 import headless
    # Do not consume the opportunity on a failed parent-side startup preflight.
    before=headless.memory();assert c.resource_failure(before,time.monotonic()-started,startup=True) is None
    birth_sha=c.save_new(c.BIRTH,{'status':'ONE_OWNED_EXACT_ARRAY_INVOCATION_CONSUMED',
        'stage':c.STAGE,'invocation':c.INVOCATION,'parent_pid':os.getpid(),
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
        'source_mode':c.source_mode(),'automatic_retry':False})
    failure=None;observed={};child=None;certificate_sha=completion_sha=None
    with headless.Job() as job:
        try:
            assert job.limits()=={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,
                'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
            c.verify_sources(generation);assert c.read_run(generation,run_sha)==admission
            failure=c.resource_failure(headless.memory(),time.monotonic()-started,startup=True)
            assert failure is None,failure
            child=job.spawn(command(generation,run_sha,birth_sha),str(c.ROOT));child.resume()
            observed=observe(job,child,headless.memory,headless.process_memory,time.monotonic,time.sleep)
            failure=observed['failure']
        except BaseException as error:
            failure=failure or type(error).__name__+': '+str(error);job.terminate()
            if child is not None and 'final_process_handle_peak_sample' not in observed:
                try:observed['final_process_handle_peak_sample']=headless.process_memory(child.process_handle)
                except BaseException as peak_error:observed['peak_sampling_error']=str(peak_error)
        finally:
            if child is not None:child.close()
    try:
        c.verify_sources(generation);assert failure is None,failure
        assert observed.get('exit_code')==0,'Array worker did not complete successfully'
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        raw=c.COMPLETION.read_bytes()
        completion=completion_contract(c.decode(raw),generation,run_sha,birth_sha,os.getpid(),child.pid)
        completion_sha=c.sha(raw)
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        raw=c.OUTPUT.read_bytes();certificate_sha=c.sha(raw)
        assert certificate_sha==completion['certificate_sha256']
        certificate=validate_certificate(c.decode(raw),generation,run_sha,birth_sha)
        assert certificate['parent_pid']==os.getpid() and certificate['worker_pid']==child.pid
    except BaseException as error:failure=failure or type(error).__name__+': '+str(error)
    try:
        assert c.admit_authorization(generation)==authorization
        assert c.read_run(generation,run_sha,check_commit=True)==admission
        assert c.sha(c.BIRTH.read_bytes())==birth_sha
        if completion_sha is not None:
            assert c.sha(c.COMPLETION.read_bytes())==completion_sha
            assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
            assert c.sha(c.OUTPUT.read_bytes())==certificate_sha
        c.verify_sources(generation)
    except BaseException as error:failure=failure or type(error).__name__+': '+str(error)
    after=headless.memory();elapsed=time.monotonic()-started
    failure=failure or c.resource_failure(after,elapsed)
    receipt={'status':'PASS_EXACT_ARRAY_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT' if failure is None else
        'FAILED_OR_BLOCKED_ARRAY_INVOCATION_PRESERVED_NO_RETRY','failure':failure,
        'stage':c.STAGE,'invocation':c.INVOCATION,'generation_manifest_sha256':generation,
        'run_admission_sha256':run_sha,'birth_sha256':birth_sha,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'certificate_sha256':certificate_sha,'worker_completion_sha256':completion_sha,
        'worker_started':child is not None,'observed':observed,'memory_before':before,'memory_after':after,
        'elapsed_seconds':elapsed,'resource_policy':c.resource_policy(),'automatic_retry':False,
        'numerical_outcomes_admitted':0,'model_fits':0,'scientific_protocol_settings_changed':False}
    c.save_new(c.SUPERVISOR,receipt);print(receipt['status'],failure,flush=True)
    assert failure is None,failure


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation-sha',required=True)
    parser.add_argument('--run-admission-sha',required=True);parser.add_argument('--root-start',action='store_true')
    args=parser.parse_args();run(args.generation_sha,args.run_admission_sha,root_start=args.root_start)
