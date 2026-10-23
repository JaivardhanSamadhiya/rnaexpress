"""Bound one invented-only NumPy calibration, never biological entry points."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

from . import invented
from src.generalization_pum_process_probe_20261021 import headless

ROOT, OUT = invented.ROOT, invented.OUT


def admitted():
    path = OUT / 'preparation_manifest.json'
    data = path.read_bytes()
    manifest = json.loads(data)
    assert manifest['status'] == 'FROZEN_INVENTED_ONLY_NUMPY_CALIBRATION'
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT
    ) == data
    assert Path(sys.executable).resolve() == Path(manifest['python_executable']).resolve()
    assert invented.sha(sys.executable) == manifest['python_executable_sha256']
    for rel, want in manifest['files'].items():
        assert invented.sha(ROOT / rel) == want, rel
    return path, manifest


def run():
    path, manifest = admitted()
    assert not (OUT / 'supervisor_receipt.json').exists()
    assert not (OUT / 'invented_numpy_receipt.json').exists()
    before = headless.memory()
    assert before['physical_available'] >= 512 * 2**20
    assert before['commit_headroom'] >= 896 * 2**20 + 2**30
    assert before['disk_available'] >= 2**30
    started = time.monotonic()
    peak = private_peak = 0
    failure = None
    code = None
    child = None
    accounting = None
    with headless.Job() as job:
        try:
            child = job.spawn([sys.executable, '-B', '-u', '-m',
                               'src.generalization_prelib_numpy_profile_20261022.invented'], str(ROOT))
            child.resume()
            while True:
                state = headless.memory()
                process = headless.process_memory(child.process_handle)
                accounting = job.accounting()
                peak = max(peak, process['peak_working_set'])
                private_peak = max(private_peak, process['peak_private_commit'])
                if state['physical_available'] < 256 * 2**20:
                    failure = 'Physical reserve below256MiB'
                if state['commit_headroom'] < 2**30:
                    failure = failure or 'System commitment reserve below1GiB'
                if time.monotonic() - started > 120:
                    failure = failure or 'Invented120second deadline exceeded'
                if accounting['active_processes'] > 2:
                    failure = failure or 'Owned active-process cap exceeded'
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
    unchanged = all(invented.sha(ROOT / rel) == want for rel, want in manifest['files'].items())
    result_path = OUT / 'invented_numpy_receipt.json'
    result_ok = result_path.exists() and json.loads(result_path.read_bytes())['status'] == 'PASS_INVENTED_NUMPY_RIDGE_AND_SPAN_ONLY'
    result_sha = invented.sha(result_path) if result_path.exists() else None
    after = headless.memory()
    elapsed = time.monotonic() - started
    if elapsed > 120 or after['physical_available'] < 256 * 2**20 or after['commit_headroom'] < 2**30:
        failure = failure or 'Final lifetime resource/deadline reserve violated'
    if not unchanged or code != 0 or not result_ok:
        failure = failure or 'Invented completion or frozen source check failed'
    receipt = {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_BOUNDED_INVENTED_NUMPY_PROFILE' if failure is None else 'FAILED_INVENTED_PROFILE_PRESERVED',
        'failure': failure, 'exit_code': code, 'elapsed_seconds': elapsed,
        'preparation_manifest_sha256': invented.sha(path),
        'invented_completion_sha256': result_sha,
        'peak_worker_working_set_bytes': peak, 'peak_worker_private_commit_bytes': private_peak,
        'job_accounting': accounting, 'memory_before': before, 'memory_after': after,
        'frozen_sources_unchanged': unchanged,
        'biological_models_fit': 0, 'biological_inputs_read': False,
        'original_scientific_guards_changed': False,
    }
    with (OUT / 'supervisor_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2), flush=True)
    assert failure is None, failure


if __name__ == '__main__':
    run()
