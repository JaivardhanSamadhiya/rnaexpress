"""Prospective source-bound supervisor; no scientific execution at import."""
import argparse
from datetime import datetime,timezone
import subprocess
import sys
import time
from .common import *
from src.generalization_knowncell_metadata_execution_20261023.supervise import monitor,ObservedChild
from src.generalization_pum_process_probe_20261021 import headless


def admitted():
    source_mode()
    assert all(os.environ.get(key)=='1' for key in THREAD_KEYS)
    raw=MANIFEST.read_bytes()
    committed=headless.GitFacade(subprocess).check_output(
        ['git','show','HEAD:'+MANIFEST.relative_to(ROOT).as_posix()],cwd=ROOT)
    assert committed==raw,'V2 execution manifest is not exact committed bytes'
    expected=sha(raw);manifest=verify_sources(expected)
    interpreter(manifest)
    return manifest,expected


def final_peak(observed,probe):
    """Require a final lifetime peak query while the process handle is live."""
    value=probe()
    for field in ('peak_working_set','peak_private_commit'):
        assert type(value[field]) is int and value[field]>0,'Unavailable final lifetime peak'
        observed[field]=max(observed.get(field,0),value[field])
    observed['final_process_handle_peak_sample']=value
    return observed


def worker_command(expected):
    valid_sha(expected)
    return [sys.executable,'-S','-B','-X','pycache_prefix='+str(CACHE_PREFIX),'-u','-m',
            'src.generalization_knowncell_metadata_execution_v2_20261023.worker','--manifest-sha',expected]


def run(*,root_start=False):
    assert root_start is True,'Explicit root-start is required'
    manifest,expected=admitted()
    for path in (ROOT/BUNDLE,OUT/'worker.log',OUT/'worker_completion.json',OUT/'supervisor_receipt.json'):
        assert not path.exists(),'Preserve existing/partial attempt; no retry/resume'
    before=headless.memory();startup_failure=resource_failure(before,0)
    if startup_failure:
        verify_sources(expected)
        save_new(OUT/'supervisor_receipt.json',{
            'status':'BLOCKED_ORIGINAL_METADATA_V2_STARTUP_FLOOR_NO_WORKER',
            'UTC':datetime.now(timezone.utc).isoformat(),'failure':startup_failure,
            'memory_before':before,'initial_committed_execution_manifest_sha256':expected,
            'worker_started':False,'project_payloads_opened':0,'model_fits':0,
            'automatic_retry':False,'source_mode':source_mode(),'original_resource_guards_unchanged':True})
        verify_sources(expected)
        print('METADATA_V2_STARTUP_BLOCKED',startup_failure,flush=True)
        return
    started=time.monotonic();child=None;observed={};failure=None
    with headless.Job() as job:
        try:
            assert job.limits()=={'process_memory_limit':768*2**20,'job_memory_limit':896*2**20,
                                 'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
            verify_sources(expected)
            failure=resource_failure(headless.memory(),time.monotonic()-started)
            assert failure is None,failure
            child=job.spawn(worker_command(expected),str(ROOT));child.resume()
            observed=monitor(job,ObservedChild(child),headless.memory,time.monotonic,time.sleep)
            failure=observed['failure']
        except BaseException as error:
            failure=failure or type(error).__name__+': '+str(error);job.terminate()
        finally:
            if child is not None:
                try:final_peak(observed,lambda:headless.process_memory(child.process_handle))
                except BaseException as error:
                    failure=failure or 'Final lifetime peak unavailable: '+type(error).__name__+': '+str(error)
                    job.terminate()
                finally:child.close()
    bundle_sha=None;completion_sha=None
    try:
        verify_sources(expected)
        assert observed.get('exit_code')==0,'Metadata worker did not exit successfully'
        assert failure is None,failure
        assert resource_failure(headless.memory(),time.monotonic()-started) is None
        completion_raw=(OUT/'worker_completion.json').read_bytes();completion=read_json(completion_raw)
        completion_sha=sha(completion_raw)
        assert completion['status']=='PASS_SOURCE_BOUND_ORIGINAL_FLOOR_METADATA_V2_WORKER'
        assert completion['initial_committed_execution_manifest_sha256']==expected
        assert completion['metadata_admission_sha256']==manifest['metadata_admission_sha256']
        assert completion['source_mode']==source_mode()
        assert resource_failure(headless.memory(),time.monotonic()-started) is None
        bundle_sha=sha((ROOT/BUNDLE).read_bytes())
        assert completion['metadata_bundle_sha256']==bundle_sha
        assert completion['numeric_outcome_rows_admitted']==completion['actual_feature_reads']==completion['models_fitted']==0
        assert completion['scientific_packages_imported'] is False
    except BaseException as error:failure=failure or type(error).__name__+': '+str(error)
    after=headless.memory();failure=failure or resource_failure(after,time.monotonic()-started)
    verify_sources(expected) # Never replace the captured identity with late bytes.
    save_new(OUT/'supervisor_receipt.json',{
        'status':'PASS_SOURCE_BOUND_ORIGINAL_FLOOR_METADATA_V2' if failure is None else 'FAILED_METADATA_V2_ATTEMPT_PRESERVED',
        'UTC':datetime.now(timezone.utc).isoformat(),'failure':failure,
        'initial_committed_execution_manifest_sha256':expected,'metadata_bundle_sha256':bundle_sha,
        'worker_completion_sha256':completion_sha,'elapsed_seconds':time.monotonic()-started,
        'memory_before':before,'memory_after':after,'observed':observed,
        'worker_started':child is not None,'automatic_retry':False,'source_mode':source_mode(),
        'original_resource_guards_unchanged':True,'numerical_outcomes_admitted':0,'array_reads':0,'model_fits':0,
        'independent_metadata_replay_still_required':True})
    verify_sources(expected)
    assert failure is None,failure
    print('METADATA_V2_COMPLETED_PENDING_INDEPENDENT_REPLAY',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root-start',action='store_true')
    run(root_start=parser.parse_args().root_start)
