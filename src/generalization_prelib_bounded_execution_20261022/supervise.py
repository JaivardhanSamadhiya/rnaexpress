"""Exactly one explicitly authorized original stage in a capped owned job."""
import datetime
import json
import os
import sys
import time

from . import worker
from src.generalization_pum_process_probe_20261021 import headless


def run(phase):
    manifest = worker.admit(phase)
    output = worker.OUT / (phase + '_supervisor_receipt.json')
    assert not output.exists()
    before = headless.memory()
    worker.resource_guard(before)
    started = last = time.monotonic()
    failure = None
    code = None
    child = None
    accounting = None
    peak = private_peak = 0
    min_physical, min_commit = before['physical_available'], before['commit_headroom']
    max_gap = 0.0
    with headless.Job() as job:
        try:
            child = job.spawn([sys.executable, '-B', '-u', '-m',
                               'src.generalization_prelib_bounded_execution_20261022.worker',
                               phase, str(os.getpid())], str(worker.ROOT))
            child.resume()
            while True:
                now = time.monotonic()
                max_gap = max(max_gap, now - last)
                last = now
                state = headless.memory()
                min_physical = min(min_physical, state['physical_available'])
                min_commit = min(min_commit, state['commit_headroom'])
                process = headless.process_memory(child.process_handle)
                accounting = job.accounting()
                peak = max(peak, process['peak_working_set'])
                private_peak = max(private_peak, process['peak_private_commit'])
                if state['physical_available'] < 256 * 2**20:
                    failure = 'Physical reserve below256MiB'
                if state['commit_headroom'] < 2**30:
                    failure = failure or 'System commitment reserve below1GiB'
                if state['disk_available'] < 256 * 2**20:
                    failure = failure or 'Disk reserve below256MiB'
                if now - started > 1800:
                    failure = failure or 'Owned stage30minute deadline exceeded'
                if accounting['active_processes'] > 2:
                    failure = failure or 'Active-process cap exceeded'
                code = child.exit_code()
                if failure:
                    job.terminate()
                    break
                if code is not None:
                    break
                time.sleep(0.1)
            final = headless.process_memory(child.process_handle)
            peak = max(peak, final['peak_working_set'])
            private_peak = max(private_peak, final['peak_private_commit'])
            accounting = job.accounting()
        except BaseException as error:
            failure = failure or type(error).__name__ + ': ' + str(error)
            job.terminate()
        finally:
            if child is not None:
                child.close()
    unchanged = all(worker.sha(worker.ROOT / rel) == want for rel, want in manifest['files'].items())
    complete = worker.BIO / worker.COMPLETION[phase]
    native = worker.OUT / (phase + '_worker_receipt.json')
    complete_sha = worker.sha(complete) if complete.exists() else None
    native_sha = worker.sha(native) if native.exists() else None
    manifest_sha = worker.sha(worker.MANIFEST)
    native_ok = False
    if native.exists() and complete_sha is not None:
        try:
            worker.check_worker_binding(json.loads(native.read_bytes()), phase, manifest_sha, complete_sha)
            native_ok = True
        except (AssertionError, KeyError, ValueError) as error:
            failure = failure or 'Worker completion binding failed: ' + type(error).__name__
    after = headless.memory()
    elapsed = time.monotonic() - started
    min_physical = min(min_physical, after['physical_available'])
    min_commit = min(min_commit, after['commit_headroom'])
    if (elapsed > 1800 or after['physical_available'] < 256 * 2**20
            or after['commit_headroom'] < 2**30 or after['disk_available'] < 256 * 2**20):
        failure = failure or 'Final lifetime reserve/deadline check failed'
    if code != 0 or not unchanged or complete_sha is None or not native_ok:
        failure = failure or 'Original completion or frozen provenance check failed'
    receipt = {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': phase,
        'status': 'PASS_BOUNDED_ORIGINAL_PRELIB_STAGE' if failure is None else 'FAILED_STAGE_PRESERVED_NO_AUTOMATIC_RETRY',
        'failure': failure, 'exit_code': code, 'elapsed_seconds': elapsed,
        'execution_manifest_sha256': manifest_sha, 'scientific_completion_sha256': complete_sha,
        'worker_receipt_sha256': native_sha, 'frozen_sources_unchanged': unchanged,
        'peak_worker_working_set_bytes': peak, 'peak_worker_private_commit_bytes': private_peak,
        'job_accounting': accounting, 'memory_before': before, 'memory_after': after,
        'minimum_sampled_physical_available': min_physical,
        'minimum_sampled_system_commit_headroom': min_commit,
        'maximum_monitor_gap_seconds': max_gap, 'scientific_worker_count': 1,
        'biological_fits_performed': 399 if phase == 'fit' and failure is None else None,
        'localization_generalization_pass': False,
    }
    worker.save(output, receipt)
    print(json.dumps(receipt, indent=2), flush=True)
    assert failure is None, failure


if __name__ == '__main__':
    run(sys.argv[1])
