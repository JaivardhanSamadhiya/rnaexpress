"""One capped metadata attempt, requiring exact human approval before birth."""
import argparse
import os
import sys
import time
from . import common as c


def observe(job, child, memory, process_memory, clock, sleep):
    """Pure dependency-injected monitor tested ONLY with invented objects."""
    started = last = clock()
    result = {'failure': None, 'exit_code': None, 'samples': 0,
        'peak_working_set': 0, 'peak_private_commit': 0, 'maximum_monitor_gap_seconds': 0.0,
        'minimum_sampled_physical_available': None, 'minimum_sampled_commit_headroom': None}
    try:
        while True:
            now = clock()
            result['maximum_monitor_gap_seconds'] = max(result['maximum_monitor_gap_seconds'], now - last)
            last = now
            state = memory()
            failure = c.resource_failure(state, now - started)
            result['samples'] += 1
            for key, source in (('minimum_sampled_physical_available', 'physical_available'),
                                ('minimum_sampled_commit_headroom', 'commit_headroom')):
                result[key] = state[source] if result[key] is None else min(result[key], state[source])
            sample = process_memory(child.process_handle)
            result['peak_working_set'] = max(result['peak_working_set'], sample['peak_working_set'])
            result['peak_private_commit'] = max(result['peak_private_commit'], sample['peak_private_commit'])
            accounting = job.accounting()
            assert accounting['active_processes'] <= 2, 'Active-process limit exceeded'
            assert accounting['peak_process_memory_used'] <= c.PROCESS_CAP, 'Process hard limit exceeded'
            assert accounting['peak_job_memory_used'] <= c.JOB_CAP, 'Job hard limit exceeded'
            result['job_accounting'] = accounting
            code = child.exit_code()
            if failure:
                result['failure'] = failure
                job.terminate()
                break
            if code is not None:
                result['exit_code'] = code
                break
            sleep(0.1)
    except BaseException as error:
        result['failure'] = result['failure'] or type(error).__name__ + ': ' + str(error)
        job.terminate()
    finally:
        # Lifetime peak counters are queried before closing the creation handle,
        # including fast exits and failures between the ordinary samples.
        try:
            sample = process_memory(child.process_handle)
            for key in ('peak_working_set', 'peak_private_commit'):
                assert type(sample[key]) is int and sample[key] > 0, 'Final lifetime peak unavailable'
                result[key] = max(result[key], sample[key])
            result['final_process_handle_peak_sample'] = sample
            result['job_accounting'] = job.accounting()
            final_accounting = result['job_accounting']
            assert final_accounting['active_processes'] <= 2
            assert final_accounting['peak_process_memory_used'] <= c.PROCESS_CAP
            assert final_accounting['peak_job_memory_used'] <= c.JOB_CAP
            assert result['peak_private_commit'] <= c.PROCESS_CAP
            final_state = memory()
            result['final_memory_sample'] = final_state
            final_elapsed = clock() - started
            result['elapsed_seconds'] = final_elapsed
            final_failure = c.resource_failure(final_state, final_elapsed)
            if final_failure:
                result['failure'] = result['failure'] or final_failure
                job.terminate()
        except BaseException as error:
            result['failure'] = result['failure'] or type(error).__name__ + ': ' + str(error)
            job.terminate()
    if 'elapsed_seconds' not in result:
        result['elapsed_seconds'] = clock() - started
    return result


def command(stage, expected, birth_sha):
    assert stage in c.IMPLEMENTED_STAGES
    return [sys.executable, '-S', '-B', '-X', 'pycache_prefix=' + str(c.CACHE_PREFIX), '-u', '-m',
        'src.' + c.NS + '.worker', stage, str(os.getpid()), c.valid_sha(expected), c.valid_sha(birth_sha)]


def run(stage, *, root_start=False):
    assert root_start is True and stage in c.IMPLEMENTED_STAGES, 'Only reviewed metadata entrypoint exists'
    c.source_mode()
    initial = c.MANIFEST.read_bytes()
    expected = c.sha(initial)
    authorization = c.admit_authorization(expected)
    for path in (c.birth_path(stage), c.OUT / (stage + '_supervisor_receipt.json'),
                 c.OUT / (stage + '_worker.log'), c.OUT / (stage + '_worker_completion.json'), c.METADATA_BUNDLE):
        assert not path.exists(), 'Preserve previous/partial output; no retry/resume'
    c.verify_sources(expected)
    birth_sha = c.save_new(c.birth_path(stage), {
        'status': 'ONE_EXPLICIT_CALIBRATED_STAGE_OPPORTUNITY_CONSUMED', 'stage': stage,
        'UTC': c.datetime.now(c.timezone.utc).isoformat(), 'parent_pid': os.getpid(),
        'execution_manifest_sha256': expected, 'authorization_sha256': authorization['approval_sha256'],
        'resource_policy': c.resource_policy(), 'source_mode': c.source_mode(), 'automatic_retry': False})
    from src.generalization_pum_process_probe_20261021 import headless
    before = headless.memory()
    failure = c.resource_failure(before, 0, startup=True)
    observed = {}
    child = None
    started = time.monotonic()
    if failure is None:
        with headless.Job() as job:
            try:
                assert job.limits() == {'process_memory_limit': c.PROCESS_CAP,
                    'job_memory_limit': c.JOB_CAP, 'active_process_limit': 2,
                    'limit_flags': headless.original.LIMIT_FLAGS}
                c.verify_sources(expected)
                failure = c.resource_failure(headless.memory(), 0, startup=True)
                assert failure is None, failure
                child = job.spawn(command(stage, expected, birth_sha), str(c.ROOT))
                # Pinned spawn/resume check exact job membership and limits.
                child.resume()
                observed = observe(job, child, headless.memory, headless.process_memory,
                    time.monotonic, time.sleep)
                failure = observed['failure']
            except BaseException as error:
                failure = failure or type(error).__name__ + ': ' + str(error)
                job.terminate()
                if child is not None and 'final_process_handle_peak_sample' not in observed:
                    try:
                        observed['final_process_handle_peak_sample'] = headless.process_memory(child.process_handle)
                    except BaseException as peak_error:
                        observed['peak_sampling_error'] = str(peak_error)
            finally:
                if child is not None:
                    child.close()
    completion_sha = bundle_sha = None
    after = None
    try:
        c.verify_sources(expected)
        assert failure is None, failure
        assert observed.get('exit_code') == 0, 'Worker failed or did not exit'
        assert c.resource_failure(headless.memory(), time.monotonic() - started) is None
        completion_raw = (c.OUT / (stage + '_worker_completion.json')).read_bytes()
        completion = c.decode(completion_raw)
        assert completion['status'] == 'PASS_CALIBRATED_METADATA_WORKER_CALLBACKS_RESTORED'
        assert completion['execution_manifest_sha256'] == expected
        assert completion['birth_sha256'] == birth_sha and completion['callbacks_restored'] is True
        assert completion['numerical_outcome_rows_admitted'] == completion['actual_feature_reads'] == completion['model_fits'] == 0
        assert completion['scientific_packages_imported'] is False
        assert completion['source_mode'] == c.source_mode() and completion['resource_policy'] == c.resource_policy()
        assert completion['metadata_admission_sha256'] == c.sha((c.ROOT / c.METADATA_ADMISSION).read_bytes())
        assert type(completion['fresh_calibrated_guard_calls']) is int and completion['fresh_calibrated_guard_calls'] > 0
        assert c.resource_failure(headless.memory(), time.monotonic() - started) is None
        bundle_sha = c.sha(c.METADATA_BUNDLE.read_bytes())
        assert completion['metadata_bundle_sha256'] == bundle_sha
        assert completion['original_3GiB_resource_guard_unchanged'] is False
        completion_sha = c.sha(completion_raw)
    except BaseException as error:
        failure = failure or type(error).__name__ + ': ' + str(error)
    try:
        # Retain the initially captured identity through all completion hashes.
        final_authorization = c.admit_authorization(expected)
        assert final_authorization['approval_sha256'] == authorization['approval_sha256']
        assert c.sha(c.birth_path(stage).read_bytes()) == birth_sha
        if completion_sha is not None:
            assert c.resource_failure(headless.memory(), time.monotonic() - started) is None
            assert c.sha((c.OUT / (stage + '_worker_completion.json')).read_bytes()) == completion_sha
            assert c.resource_failure(headless.memory(), time.monotonic() - started) is None
            assert c.sha(c.METADATA_BUNDLE.read_bytes()) == bundle_sha
        c.verify_sources(expected)
    except BaseException as error:
        failure = failure or type(error).__name__ + ': ' + str(error)
    after = headless.memory()
    failure = failure or c.resource_failure(after, time.monotonic() - started)
    receipt = {
        'status': ('PASS_CALIBRATED_METADATA_PENDING_INDEPENDENT_RECONSTRUCTION' if failure is None else
                   'FAILED_OR_BLOCKED_CALIBRATED_ATTEMPT_PRESERVED_NO_RETRY'),
        'stage': stage, 'UTC': c.datetime.now(c.timezone.utc).isoformat(), 'failure': failure,
        'execution_manifest_sha256': expected, 'authorization_sha256': authorization['approval_sha256'],
        'birth_sha256': birth_sha, 'worker_started': child is not None, 'observed': observed,
        'memory_before': before, 'memory_after': after, 'elapsed_seconds': time.monotonic() - started,
        'metadata_bundle_sha256': bundle_sha, 'worker_completion_sha256': completion_sha,
        'resource_policy': c.resource_policy(), 'original_3GiB_resource_guard_unchanged': False,
        'scientific_protocol_settings_changed': False, 'independent_metadata_reconstruction_required': True,
        'automatic_retry': False, 'numerical_labels_admitted': 0, 'actual_feature_reads': 0, 'model_fits': 0}
    c.save_new(c.OUT / (stage + '_supervisor_receipt.json'), receipt)
    print(receipt['status'], failure, flush=True)
    assert failure is None, failure


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=c.IMPLEMENTED_STAGES)
    parser.add_argument('--root-start', action='store_true')
    args = parser.parse_args()
    run(args.stage, root_start=args.root_start)
