"""One root-started invented profile. No biological reader or FIT authority."""
import argparse
import faulthandler
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

SOURCE_CACHE = Path(__file__).resolve().parents[2] / 'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'


def source_mode():
    assert sys.flags.no_site == 1 and sys.dont_write_bytecode
    assert sys.pycache_prefix == str(SOURCE_CACHE), 'Exact absent source-cache prefix required'
    assert not SOURCE_CACHE.exists() and not SOURCE_CACHE.is_symlink()


if __name__ == '__main__':
    source_mode()

from . import spec
from .contracts import canonical, compare_results, decode, digest, relative_key, resource_failure, validate_child
from src.generalization_owned_workingset_probe_v2_20261025 import working_set as resident
from src.generalization_pum_process_probe_20261021 import headless


def write(stream, value):
    stream.write(canonical(value).decode('utf8') + '\n')
    stream.flush()
    os.fsync(stream.fileno())


def source_proof(expected_sha, *, committed=False):
    source_mode()
    raw = spec.MANIFEST.read_bytes()
    assert digest(raw) == expected_sha, 'Initially bound profile manifest changed'
    value = decode(raw)
    assert value['status'] == spec.STATUS
    for key, want in value['files'].items():
        relative_key(key)
        path = spec.ROOT / key
        assert not path.is_symlink() and digest(path.read_bytes()) == want, key
    if committed:
        actual = headless.GitFacade(subprocess).check_output(
            ['git', 'show', 'HEAD:' + spec.MANIFEST.relative_to(spec.ROOT).as_posix()], cwd=spec.ROOT)
        assert actual == raw, 'Actual source/software profile manifest must be committed'
    return value


def expected_buffer_sha():
    value = hashlib.sha256()
    for page in range(spec.BYTES // 4096):
        value.update(bytes([page % 251]) + bytes(4095))
    return value.hexdigest()


def baseline_results():
    value = decode(spec.BASELINE.read_bytes())
    assert value['status'] == 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4'
    return {key: value[key] for key in ('parser', 'optimizer', 'extra_deferred_native_contracts')}


def child(parent_pid, expected_sha):
    assert os.getppid() == parent_pid
    started = time.monotonic()
    manifest = source_proof(expected_sha)

    def fresh():
        assert resource_failure(headless.memory(), time.monotonic() - started) is None

    from .runtime import actual_proof, bootstrap
    np, pd, scipy, minimize, expit, threadpoolctl, runtime, inventory, payload_proof = bootstrap(manifest, fresh)
    fresh()
    initial = actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory, manifest)
    buffers = []
    for offset in range(0, spec.BYTES, 16 * 2**20):
        fresh()
        block = bytearray(16 * 2**20)
        for page in range(0, len(block), 4096):
            block[page] = ((offset + page) // 4096) % 251
        buffers.append(block)
    expected = expected_buffer_sha()
    hashes = []

    def full_hash():
        value = hashlib.sha256()
        for block in buffers:
            fresh()
            value.update(block)
        assert value.hexdigest() == expected
        hashes.append(value.hexdigest())

    full_hash()
    # These three functions are the original unchanged invented cases.
    from src.generalization_knowncell_parser_profile_20261022.parser_profile import run as parser_checks
    from src.generalization_knowncell_parser_profile_20261022.optimizer_profile import run as optimizer_checks
    from src.generalization_knowncell_parser_profile_20261022.extras_v2 import run as extras_checks
    fresh()
    parser = parser_checks(pd)
    fresh()
    optimizer = optimizer_checks(np, minimize, expit)
    fresh()
    extras = extras_checks(np, pd)
    fresh()
    results = {'parser': parser, 'optimizer': optimizer, 'extra_deferred_native_contracts': extras}
    results_sha = compare_results(results, baseline_results())
    full_hash()
    full_hash()
    final = actual_proof(np, pd, scipy, threadpoolctl, runtime, inventory, manifest)
    source_proof(expected_sha)
    fresh()
    with (spec.OUT / 'toy_child.json').open('x', encoding='utf8', newline='\n') as stream:
        write(stream, {
            'status': spec.CHILD_PASS, 'parent_pid': parent_pid, 'child_pid': os.getpid(),
            'bytes': spec.BYTES, 'hashes': hashes, 'elapsed_seconds': time.monotonic() - started,
            'results': results, 'canonical_result_sha256': results_sha,
            'initial_native_proof': initial, 'final_native_proof': final,
            'current_payload_check': payload_proof,
            'preparation_manifest_sha256': expected_sha,
            'original_V4_result_sha256': digest(spec.BASELINE.read_bytes()),
            'fresh_inventory_sha256': manifest['files'][spec.INVENTORY.relative_to(spec.ROOT).as_posix()],
            'biological_rows_read': 0, 'biological_model_fits': 0, 'invented_optimizer_units': 12,
            'old_interpreter_bitwise_parity_established': False,
            'biological_admission_granted': False,
        })


def parent(expected_sha):
    started = time.monotonic()  # Includes initial source/commit verification.
    source_proof(expected_sha, committed=True)
    before = headless.memory()
    assert resource_failure(before, time.monotonic() - started, startup=True) is None
    expected_limits = {'process_memory_limit': 768 * 2**20, 'job_memory_limit': 896 * 2**20,
                       'active_process_limit': 2, 'limit_flags': headless.original.LIMIT_FLAGS}
    child_process = None
    cap = None
    problem = None
    child_sha = None
    samples = peak_private = peak_resident = 0
    minimum_physical = before['physical_available']
    with (spec.OUT / 'parent.jsonl').open('x', encoding='utf8', newline='\n') as stream:
        write(stream, {'status': 'ONE_OWNED_INVENTED_CURRENT42_PROFILE_STARTED', 'parent_pid': os.getpid(),
                       'native_origins': headless.native_origins(), 'memory_before': before})
        with headless.Job() as job:
            try:
                assert job.limits() == expected_limits
                command = [sys.executable, '-S', '-B', '-X', 'pycache_prefix=' + str(spec.SOURCE_CACHE),
                           '-u', '-m', 'src.' + spec.NS + '.probe', '--child', str(os.getpid()),
                           '--manifest-sha', expected_sha]
                assert resource_failure(headless.memory(), time.monotonic() - started, startup=True) is None
                child_process = job.spawn(command, str(spec.ROOT))
                cap = resident.apply(job, child_process)
                write(stream, {'status': 'EXACT_ADDITIONAL_RESIDENT_CAP_INSTALLED',
                               'child_pid': child_process.pid, 'cap': cap})
                child_process.resume()
                last = -10
                while True:
                    elapsed = time.monotonic() - started
                    state = headless.memory()
                    problem = resource_failure(state, elapsed)
                    counters = headless.process_memory(child_process.process_handle)
                    accounting = job.accounting()
                    samples += 1
                    peak_private = max(peak_private, counters['peak_private_commit'])
                    peak_resident = max(peak_resident, counters['peak_working_set'])
                    minimum_physical = min(minimum_physical, state['physical_available'])
                    code = child_process.exit_code()
                    # Persist offending raw counters before their predicates.
                    if elapsed - last >= 1 or code is not None or problem or \
                            peak_private > 768 * 2**20 or peak_resident > spec.RESIDENT_CEILING or \
                            accounting['peak_job_memory_used'] > 896 * 2**20 or accounting['active_processes'] > 2:
                        write(stream, {'elapsed_seconds': elapsed, 'memory': state, 'child_memory': counters,
                                       'job': accounting, 'exit_code': code, 'failure': problem})
                        last = elapsed
                    assert peak_private <= 768 * 2**20 and accounting['peak_job_memory_used'] <= 896 * 2**20
                    assert counters['working_set'] <= spec.RESIDENT_CEILING and peak_resident <= spec.RESIDENT_CEILING
                    assert accounting['active_processes'] <= 2 and job.limits() == expected_limits
                    if code is None:
                        resident.verify(job, child_process, cap)
                    if problem:
                        raise RuntimeError(problem)
                    if code is not None:
                        assert code == 0, 'Invented child exit ' + str(code)
                        break
                    time.sleep(.1)
                raw = (spec.OUT / 'toy_child.json').read_bytes()
                child_sha = digest(raw)
                result = decode(raw)
                validate_child(result, baseline_results(), expected_sha, os.getpid(), child_process.pid, expected_buffer_sha())
                source_proof(expected_sha)
                assert peak_private > spec.BYTES and peak_resident <= spec.RESIDENT_CEILING
            except BaseException as error:
                problem = type(error).__name__ + ': ' + str(error)
                job.terminate()
            finally:
                if child_process is not None:
                    try:
                        final = headless.process_memory(child_process.process_handle)
                        accounting = job.accounting()
                        write(stream, {'status': 'FINAL_OWNED_LIFETIME_COUNTERS', 'process': final, 'job': accounting})
                        peak_private = max(peak_private, final['peak_private_commit'])
                        peak_resident = max(peak_resident, final['peak_working_set'])
                        assert peak_private <= 768 * 2**20
                        assert accounting['peak_job_memory_used'] <= 896 * 2**20
                        assert peak_resident <= spec.RESIDENT_CEILING
                        if problem is None:
                            assert accounting['active_processes'] == 0
                    except BaseException as error:
                        problem = problem or type(error).__name__ + ': ' + str(error)
                        job.terminate()
                    finally:
                        child_process.close()
        write(stream, {'status': 'MANDATORY_PARENT_TELEMETRY_COMPLETE', 'failure': problem})
    # All mandatory parent progress writes and the owned Job close precede this.
    log_sha = digest((spec.OUT / 'parent.jsonl').read_bytes())
    if problem is None:
        try:
            source_proof(expected_sha)
            assert digest((spec.OUT / 'toy_child.json').read_bytes()) == child_sha
        except BaseException as error:
            problem = type(error).__name__ + ': ' + str(error)
    final_memory = headless.memory()
    elapsed = time.monotonic() - started
    minimum_physical = min(minimum_physical, final_memory['physical_available'])
    problem = problem or resource_failure(final_memory, elapsed)
    value = {
        'status': spec.PARENT_PASS if problem is None else 'FAILED_INVENTED_CURRENT42_PROFILE_NO_RETRY',
        'failure': problem, 'samples': samples, 'elapsed_seconds': elapsed,
        'peak_private_commit': peak_private, 'peak_working_set': peak_resident,
        'requested_resident_maximum': resident.MAXIMUM, 'measured_resident_ceiling': spec.RESIDENT_CEILING,
        'minimum_sampled_physical_available': minimum_physical, 'additional_resident_cap': cap,
        'closed_parent_log_sha256': log_sha, 'memory_after': final_memory,
        'unchanged_job_caps': expected_limits, 'biological_rows_read': 0,
        'invented_optimizer_units': 12 if problem is None else None,
        'scientific_attempts': 0, 'full_FIT_or_old_interpreter_parity_established': False,
        'biological_admission_granted': False, 'preparation_manifest_sha256': expected_sha,
        'child_completion_sha256': child_sha if problem is None else None,
    }
    with (spec.OUT / 'receipt.json').open('x', encoding='utf8', newline='\n') as result_stream:
        write(result_stream, value)
    print(value['status'], problem, flush=True)
    assert problem is None, problem


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', type=int)
    parser.add_argument('--manifest-sha', required=True)
    args = parser.parse_args()
    if args.child is None:
        parent(args.manifest_sha)
    else:
        # Detached owned child gets an exclusive visible diagnostic sink.
        with (spec.OUT / 'child_fault.log').open('x', encoding='utf8', buffering=1) as log:
            sys.stdout = sys.stderr = log
            faulthandler.enable(file=log)
            try:
                child(args.child, args.manifest_sha)
            except BaseException:
                import traceback
                traceback.print_exc(file=log)
                log.flush()
                os.fsync(log.fileno())
                raise
            finally:
                faulthandler.disable()
