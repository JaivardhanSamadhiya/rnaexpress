"""Root-started, non-resumable metadata controller with the original floors."""
from datetime import datetime, timezone
import subprocess
import sys
import time
from .common import *
from src.generalization_pum_process_probe_20261021 import headless


def admitted():
    assert all(os.environ.get(key) == '1' for key in THREAD_KEYS)
    raw = MANIFEST.read_bytes()
    manifest = verify_sources(json.loads(raw))
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + MANIFEST.relative_to(ROOT).as_posix()], cwd=ROOT) == raw
    assert Path(sys.executable).resolve() == Path(manifest['python_executable']).resolve()
    for name, expected in manifest['python_native_files'].items():
        assert sha(Path(name).read_bytes()) == expected, name
    return manifest


def monitor(job, child, probe, monotonic, sleep):
    """Injectable only for invented tests; actual run supplies native functions."""
    started = last = monotonic()
    result = {'failure': None, 'exit_code': None, 'peak_working_set': 0,
              'peak_private_commit': 0, 'maximum_sample_gap': 0.,
              'minimum_physical': None, 'minimum_commit': None}
    while True:
        now = monotonic()
        result['maximum_sample_gap'] = max(result['maximum_sample_gap'], now - last)
        last = now
        state = probe()
        accounting = job.accounting()
        process = child.memory()
        for field, key in (('minimum_physical', 'physical_available'), ('minimum_commit', 'commit_headroom')):
            result[field] = state[key] if result[field] is None else min(result[field], state[key])
        result['peak_working_set'] = max(result['peak_working_set'], process['peak_working_set'])
        result['peak_private_commit'] = max(result['peak_private_commit'], process['peak_private_commit'])
        result['failure'] = resource_failure(state, now-started, accounting['active_processes'])
        result['exit_code'] = child.exit_code()
        result['job_accounting'] = accounting
        if result['failure']:
            job.terminate()
            return result
        if result['exit_code'] is not None:
            return result
        sleep(.1)


class ObservedChild:
    def __init__(self, child):
        self.child = child
    def memory(self):
        return headless.process_memory(self.child.process_handle)
    def exit_code(self):
        return self.child.exit_code()


def run():
    manifest = admitted()
    for path in (ROOT/BUNDLE, OUT/'worker.log', OUT/'worker_completion.json', OUT/'supervisor_receipt.json'):
        assert not path.exists(), 'Preserve prior or partial attempt; no retry/resume'
    before = headless.memory()
    startup_failure = resource_failure(before, 0)
    if startup_failure:
        save_new(OUT/'supervisor_receipt.json', {
            'status': 'BLOCKED_ORIGINAL_METADATA_STARTUP_FLOOR_NO_WORKER',
            'UTC': datetime.now(timezone.utc).isoformat(), 'failure': startup_failure,
            'memory_before': before, 'execution_manifest_sha256': sha(MANIFEST.read_bytes()),
            'worker_started': False, 'project_payloads_opened': 0, 'model_fits': 0,
            'automatic_retry': False, 'original_resource_guards_unchanged': True})
        print('METADATA_STARTUP_BLOCKED', startup_failure, flush=True)
        return
    started = time.monotonic()
    child = None
    observed = {}
    failure = None
    with headless.Job() as job:
        try:
            assert job.limits() == {'process_memory_limit': 768*2**20, 'job_memory_limit': 896*2**20,
                                   'active_process_limit': 2, 'limit_flags': headless.original.LIMIT_FLAGS}
            # Fresh original floor immediately before spawn, after Job setup.
            failure = resource_failure(headless.memory(), time.monotonic()-started)
            assert failure is None, failure
            child = job.spawn([sys.executable, '-S', '-B', '-u', '-m',
                               'src.generalization_knowncell_metadata_execution_20261023.worker'], str(ROOT))
            child.resume()
            observed = monitor(job, ObservedChild(child), headless.memory, time.monotonic, time.sleep)
            failure = observed['failure']
        except BaseException as error:
            failure = failure or type(error).__name__ + ': ' + str(error)
            job.terminate()
        finally:
            if child is not None:
                child.close()
    # Source/receipt verification is part of the lifetime. The actual admitted
    # metadata bundle is hashed only after a fresh original-floor check.
    bundle_sha = None
    try:
        verify_sources(manifest)
        assert observed.get('exit_code') == 0, 'Metadata worker did not exit successfully'
        assert failure is None, failure
        assert resource_failure(headless.memory(), time.monotonic()-started) is None
        completion = json.loads((OUT/'worker_completion.json').read_bytes())
        assert completion['status'] == 'PASS_ORIGINAL_FLOOR_METADATA_ONLY_WORKER'
        assert completion['execution_manifest_sha256'] == sha(MANIFEST.read_bytes())
        # The hash does not substitute for independent metadata replay later.
        assert resource_failure(headless.memory(), time.monotonic()-started) is None
        bundle_sha = sha((ROOT/BUNDLE).read_bytes())
        assert completion['metadata_bundle_sha256'] == bundle_sha
        assert completion['numeric_outcome_rows_admitted'] == completion['actual_feature_reads'] == completion['models_fitted'] == 0
    except BaseException as error:
        failure = failure or type(error).__name__ + ': ' + str(error)
    after = headless.memory()
    failure = failure or resource_failure(after, time.monotonic()-started)
    save_new(OUT/'supervisor_receipt.json', {
        'status': 'PASS_BOUNDED_ORIGINAL_FLOOR_METADATA_ONLY' if failure is None else 'FAILED_METADATA_ATTEMPT_PRESERVED',
        'UTC': datetime.now(timezone.utc).isoformat(), 'failure': failure,
        'execution_manifest_sha256': sha(MANIFEST.read_bytes()), 'metadata_bundle_sha256': bundle_sha,
        'elapsed_seconds': time.monotonic()-started, 'memory_before': before, 'memory_after': after,
        'observed': observed, 'worker_started': child is not None, 'automatic_retry': False,
        'original_resource_guards_unchanged': True, 'numerical_outcomes_admitted': 0,
        'array_reads': 0, 'model_fits': 0, 'independent_metadata_replay_still_required': True})
    assert failure is None, failure
    print('METADATA_ONLY_COMPLETED_PENDING_INDEPENDENT_REPLAY', flush=True)


if __name__ == '__main__':
    run()
