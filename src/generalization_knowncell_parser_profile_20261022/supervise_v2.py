"""One fresh one-thread invented worker under unchanged owned Job caps."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .common_v2 import *
from src.generalization_pum_process_probe_20261021 import headless


def admitted():
    check_thread_environment(os.environ)
    raw = MANIFEST.read_bytes(); manifest = json.loads(raw)
    assert manifest['status'] == STATUS
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:'+MANIFEST.relative_to(ROOT).as_posix()], cwd=ROOT) == raw
    assert Path(sys.executable).resolve() == Path(manifest['python_executable']).resolve()
    assert sha(sys.executable) == manifest['python_executable_sha256']
    for name, want in manifest['files'].items(): assert sha(ROOT/name) == want, name
    return manifest


def run():
    manifest = admitted()
    for name in ('supervisor_receipt.json', 'invented_profile_receipt.json',
                 'actual_origin_receipt.json', 'pandas_admission_candidate.json', 'invented_worker.log'):
        assert not (OUT/name).exists(), 'Preserve completed or failed attempt; no automatic retry'
    before = headless.memory()
    failure = resource_failure(before, 0., startup=True)
    assert failure is None, failure
    started = last_sample = time.monotonic()
    maximum_gap = 0.; peak = private_peak = 0
    minimum_physical = before['physical_available']; minimum_commit = before['commit_headroom']
    child = None; code = None; accounting = None
    with headless.Job() as job:
        try:
            assert job.limits() == {'process_memory_limit': 768*2**20,
                'job_memory_limit': 896*2**20, 'active_process_limit': 2,
                'limit_flags': headless.original.LIMIT_FLAGS}
            child = job.spawn([sys.executable, '-S', '-B', '-u', '-m',
                'src.generalization_knowncell_parser_profile_20261022.worker_v2'], str(ROOT))
            child.resume()
            while True:
                now = time.monotonic(); maximum_gap = max(maximum_gap, now-last_sample); last_sample = now
                state = headless.memory(); process = headless.process_memory(child.process_handle)
                accounting = job.accounting()
                minimum_physical = min(minimum_physical, state['physical_available'])
                minimum_commit = min(minimum_commit, state['commit_headroom'])
                peak = max(peak, process['peak_working_set']); private_peak = max(private_peak, process['peak_private_commit'])
                failure = resource_failure(state, time.monotonic()-started, accounting['active_processes'])
                code = child.exit_code()
                if failure: job.terminate(); break
                if code is not None: break
                time.sleep(.1)
            final_process = headless.process_memory(child.process_handle)
            peak = max(peak, final_process['peak_working_set'])
            private_peak = max(private_peak, final_process['peak_private_commit'])
            accounting = job.accounting()
        except BaseException as error:
            failure = failure or type(error).__name__+': '+str(error)
            job.terminate()
        finally:
            if child is not None: child.close()
    unchanged = all(sha(ROOT/name) == want for name, want in manifest['files'].items())
    result = OUT/'invented_profile_receipt.json'
    preparation_sha = sha(MANIFEST)
    completion_sha = sha(result) if result.exists() else None
    completion = json.loads(result.read_bytes()) if result.exists() else {}
    origin = OUT/'actual_origin_receipt.json'; candidate = OUT/'pandas_admission_candidate.json'
    complete = (completion.get('status') == 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V2'
                and completion.get('preparation_manifest_sha256') == preparation_sha
                and origin.exists() and candidate.exists()
                and completion.get('actual_origin_receipt_sha256') == sha(origin)
                and completion.get('pandas_admission_candidate_sha256') == sha(candidate))
    if code != 0 or not complete or not unchanged: failure = failure or 'Completion/source integrity failed'
    # Include final provenance hashing/validation in the lifetime deadline and
    # reserve check; serialize only already computed identities afterwards.
    after = headless.memory(); elapsed = time.monotonic()-started
    minimum_physical = min(minimum_physical, after['physical_available'])
    minimum_commit = min(minimum_commit, after['commit_headroom'])
    final_failure = resource_failure(after, elapsed, (accounting or {}).get('active_processes', 0))
    failure = failure or final_failure
    jsave(OUT/'supervisor_receipt.json', {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_BOUNDED_ONE_THREAD_INVENTED_PANDAS_SCIPY_PROFILE_V2' if failure is None else 'FAILED_INVENTED_PROFILE_PRESERVED',
        'failure': failure, 'exit_code': code, 'elapsed_seconds': elapsed,
        'preparation_manifest_sha256': preparation_sha,
        'invented_completion_sha256': completion_sha,
        'peak_worker_working_set_bytes': peak, 'peak_worker_private_commit_bytes': private_peak,
        'job_accounting': accounting, 'memory_before': before, 'memory_after': after,
        'minimum_sampled_physical_available': minimum_physical,
        'minimum_sampled_system_commit_headroom': minimum_commit,
        'maximum_monitor_sample_gap_seconds': maximum_gap,
        'frozen_sources_unchanged': unchanged, 'numerical_threads': 1,
        'biological_inputs_read': False, 'biological_model_fits': 0,
        'original_scientific_guards_changed': False, 'automatic_retry': False})
    print('PARSER_SCIPY_PROFILE', 'PASS' if failure is None else 'FAILED', flush=True)
    assert failure is None, failure


if __name__ == '__main__': run()
