"""Replay monitor with the original total-stage start; no new resident policy."""
from . import common as c


def observe(job, child, memory, process_memory, clock, sleep, *, record=None, started):
    """Pure dependency-injected monitor tested ONLY with invented objects."""
    last = clock()
    assert type(started) in (int,float) and 0<=started<=last,'Original total-stage start required'
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
            result['last_process_handle_sample']=dict(sample)
            result['peak_working_set'] = max(result['peak_working_set'], sample['peak_working_set'])
            result['peak_private_commit'] = max(result['peak_private_commit'], sample['peak_private_commit'])
            accounting = job.accounting()
            assert accounting['active_processes'] <= 2, 'Active-process limit exceeded'
            assert accounting['peak_process_memory_used'] <= c.PROCESS_CAP, 'Process hard limit exceeded'
            assert accounting['peak_job_memory_used'] <= c.JOB_CAP, 'Job hard limit exceeded'
            result['job_accounting'] = accounting
            code = child.exit_code()
            if record is not None:
                record({'elapsed_seconds': now-started, 'system_memory': state,
                    'child_memory': sample, 'job_accounting': accounting,
                    'exit_code': code, 'pending_failure': failure})
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
            result['final_process_handle_peak_sample']=dict(sample)
            for key in ('peak_working_set', 'peak_private_commit'):
                assert type(sample[key]) is int and sample[key] > 0, 'Final lifetime peak unavailable'
                result[key] = max(result[key], sample[key])
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

