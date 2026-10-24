"""One root-requested startup opportunity; exact unchanged V2 child only."""
import argparse
from datetime import datetime,timezone
import time
from .common import *

headless=original.headless


def _base(admission):
    return {'initial_committed_addon_manifest_sha256':admission.addon_sha256,
            'initial_committed_execution_manifest_sha256':admission.v2_sha256,
            'preserved_first_blocked_receipt_sha256':OLD_BLOCKED_SHA,
            'explicit_root_start':True,'automatic_retry':False,'resume':False,
            'original_worker_and_output_paths_unchanged':True,
            'original_resource_guards_unchanged':True,'source_mode':source_mode()}


def run(*,root_start=False,wait_seconds=0):
    assert root_start is True,'Explicit root-start is required'
    assert type(wait_seconds) is int and 0<=wait_seconds<=60
    admission=admitted()
    require_absent(worker_paths())
    require_absent((OUT/'attempt_birth.json',OUT/'supervisor_receipt.json'))
    # Exclusive birth consumes the only opportunity, including a new low-RAM block.
    base=_base(admission)
    birth=dict(base,status='BORN_ONE_EXPLICIT_METADATA_STARTUP_OPPORTUNITY',
               UTC=datetime.now(timezone.utc).isoformat(),wait_seconds_requested=wait_seconds,
               worker_command=original.worker_command(admission.v2_sha256))
    birth_sha=save_new(OUT/'attempt_birth.json',birth)
    before=None;after=None;wait_elapsed=0.;samples=0;started=None
    child=None;observed={};failure=None;bundle_sha=None;completion_sha=None;stage='startup_wait';blocked=False
    try:
        before,failure,wait_elapsed,samples=wait_for_floor(
            wait_seconds,headless.memory,time.monotonic,time.sleep)
        blocked=failure is not None
        if failure is None:
            # The original300s stage begins after the separately bounded wait.
            started=time.monotonic();stage='owned_job'
            with headless.Job() as job:
                try:
                    assert job.limits()=={'process_memory_limit':768*2**20,'job_memory_limit':896*2**20,
                                         'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
                    verify_sources(admission.addon_sha256,admission.v2_sha256)
                    require_absent(worker_paths())
                    failure=resource_failure(headless.memory(),time.monotonic()-started)
                    assert failure is None,failure
                    child=job.spawn(original.worker_command(admission.v2_sha256),str(ROOT))
                    child.resume()
                    observed=original.monitor(job,original.ObservedChild(child),headless.memory,time.monotonic,time.sleep)
                    failure=observed['failure']
                except BaseException as error:
                    failure=failure or type(error).__name__+': '+str(error);job.terminate()
                finally:
                    if child is not None:
                        try:original.final_peak(observed,lambda:headless.process_memory(child.process_handle))
                        except BaseException as error:
                            failure=failure or 'Final lifetime peak unavailable: '+type(error).__name__+': '+str(error)
                            job.terminate()
                        finally:child.close()
            stage='completion_provenance'
            verify_sources(admission.addon_sha256,admission.v2_sha256)
            assert observed.get('exit_code')==0,'Metadata worker did not exit successfully'
            assert failure is None,failure
            assert resource_failure(headless.memory(),time.monotonic()-started) is None
            completion_raw=(v2.OUT/'worker_completion.json').read_bytes()
            completion=read_json(completion_raw);completion_sha=sha(completion_raw)
            assert completion['status']=='PASS_SOURCE_BOUND_ORIGINAL_FLOOR_METADATA_V2_WORKER'
            assert completion['initial_committed_execution_manifest_sha256']==admission.v2_sha256
            assert completion['metadata_admission_sha256']==admission.original()['metadata_admission_sha256']
            assert completion['source_mode']==source_mode()
            assert completion['numeric_outcome_rows_admitted']==completion['actual_feature_reads']==completion['models_fitted']==0
            assert completion['scientific_packages_imported'] is False
            assert resource_failure(headless.memory(),time.monotonic()-started) is None
            bundle_sha=sha((ROOT/v2.BUNDLE).read_bytes())
            assert completion['metadata_bundle_sha256']==bundle_sha
    except BaseException as error:
        failure=failure or type(error).__name__+': '+str(error)
    # All source, birth and result hashes precede the final lifetime/resource test.
    try:
        verify_sources(admission.addon_sha256,admission.v2_sha256)
        assert sha((OUT/'attempt_birth.json').read_bytes())==birth_sha
    except BaseException as error:
        failure=failure or type(error).__name__+': '+str(error)
    after=headless.memory()
    elapsed=0. if started is None else time.monotonic()-started
    failure=failure or resource_failure(after,elapsed)
    status=('BLOCKED_ONE_EXPLICIT_METADATA_STARTUP_OPPORTUNITY_NO_WORKER' if blocked else
            'PASS_EXACT_V2_METADATA_WORKER_VIA_SEPARATE_STARTUP_OPPORTUNITY')
    if failure is not None and not blocked:status='FAILED_ONE_EXPLICIT_METADATA_OPPORTUNITY_PRESERVED'
    receipt=dict(base,status=status,UTC=datetime.now(timezone.utc).isoformat(),
                 failure=failure,stage=stage,attempt_birth_sha256=birth_sha,
                 metadata_bundle_sha256=bundle_sha,worker_completion_sha256=completion_sha,
                 wait_seconds_requested=wait_seconds,wait_elapsed_seconds=wait_elapsed,
                 readiness_samples=samples,elapsed_metadata_stage_seconds=elapsed,
                 memory_before=before,memory_after=after,observed=observed,
                 worker_started=child is not None,project_payloads_opened=0 if child is None else None,
                 numerical_outcomes_admitted=0,array_reads=0,model_fits=0,
                 independent_metadata_replay_still_required=True)
    save_new(OUT/'supervisor_receipt.json',receipt)
    if blocked:
        print('EXPLICIT_METADATA_STARTUP_OPPORTUNITY_BLOCKED',failure,flush=True)
        return receipt
    assert failure is None,failure
    print('EXACT_V2_METADATA_COMPLETED_PENDING_INDEPENDENT_REPLAY',flush=True)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root-start',action='store_true')
    parser.add_argument('--wait-seconds',type=int,default=0)
    args=parser.parse_args();run(root_start=args.root_start,wait_seconds=args.wait_seconds)
