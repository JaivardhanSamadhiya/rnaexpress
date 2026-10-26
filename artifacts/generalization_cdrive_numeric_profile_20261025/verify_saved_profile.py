"""Independent saved-file verification only; no scientific imports or jobs.

This reads exact saved invented-profile JSON, source and software bytes on C:.
It never invokes the producer, proof API, numerical kernels, Git or Win32 API.
"""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025/workspace')
NS = 'generalization_cdrive_numeric_profile_20261025'
OUT = ROOT / 'results' / NS
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
PROFILE_SHA = 'd732628ebaaa1840e0f8d173fc03f359729310333fbab3794703742a86b3400b'
PINS = {
    'results/' + NS + '/preparation_manifest.json': PROFILE_SHA,
    'results/' + NS + '/receipt.json': 'd14659258b5ec76ca2c1e687a55d25352f51cc3296e5663e32bffd1fbddda527',
    'results/' + NS + '/toy_child.json': '25bb6b042cb4c0be7c553c3a232210c30e555fd55b03d8dc62c924a2ed91b5f3',
    'results/' + NS + '/parent.jsonl': '9f133388b6d2b8e6f77fc0bd50588833f094cc87243dcb5c10ea8c1723b897f8',
    'results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json':
        '34ff960c2e0a69f724eff36324f72dec8c8208c48c93f6ddfd3ed7db2fa7ee33',
    'results/generalization_knowncell_parser_profile_v4_20261023/verified_native_status.json':
        'e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821',
    'results/generalization_knowncell_parser_profile_v4_20261023/invented_profile_receipt.json':
        'dfc00f70af703437b394f74fbd92f8f81e0926b82a0be5b95a01cabebd29c312',
}
MIB = 2**20
PRIVATE, JOB, RESIDENT, REQUEST = 768*MIB, 896*MIB, 192*MIB, 190*MIB
BUFFER = 384*MIB
verified = {}
runtime_files = {}


def sha(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink()
    assert path.drive.casefold() == 'c:', 'C-only verification'
    before = path.stat()
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    return value.hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('utf8')


def decode(raw):
    def unique(items):
        value = {}
        for key, item in items:
            assert key not in value, 'Duplicate key'
            value[key] = item
        return value
    def nonfinite(value):
        raise AssertionError('Nonfinite JSON literal: ' + value)
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    assert isinstance(value, dict)
    return value


def local(name, want):
    assert '\\' not in name and ':' not in name and '..' not in Path(name).parts
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT.resolve())
    assert sha(path) == want, name
    assert name not in verified or verified[name] == want
    verified[name] = want
    return path


def runtime_pin(path, want):
    path = Path(path)
    assert sha(path) == want, str(path)
    key = str(path.resolve())
    assert key not in runtime_files or runtime_files[key] == want
    runtime_files[key] = want


def memory(value, startup=False):
    assert value['physical_available'] >= (512 if startup else 256)*MIB
    assert value['commit_headroom'] >= (1920*MIB if startup else 2**30)
    assert value['disk_available'] >= 2**30
    assert value['physical_available'] <= value['physical_total']


def counters(process, job):
    assert 0 <= process['private_commit'] <= process['peak_private_commit'] <= PRIVATE
    assert 0 <= process['working_set'] <= process['peak_working_set'] <= RESIDENT
    assert 0 <= job['active_processes'] <= 2
    assert job['terminated_processes'] == 0 and job['total_processes'] == 1
    assert job['peak_process_memory_used'] <= PRIVATE and job['peak_job_memory_used'] <= JOB


def verify():
    assert ROOT.resolve() == Path(__file__).resolve().parents[2]
    assert sys.flags.no_site == 1 and sys.dont_write_bytecode
    cache = ROOT / 'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    assert sys.pycache_prefix == str(cache) and not cache.exists() and not cache.is_symlink()
    assert not any(name.split('.')[0] in ('numpy', 'scipy', 'pandas', 'torch', 'openvino') for name in sys.modules)
    for name, want in PINS.items():
        local(name, want)
    manifest = decode((OUT/'preparation_manifest.json').read_bytes())
    assert manifest['file_count'] == len(manifest['files']) == 164
    for name, want in manifest['files'].items():
        assert not name.startswith('data/'), 'Only source/static metadata belongs in this closure'
        local(name, want)
    assert manifest['fresh_inventory_sha256'] == PINS['results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json']
    assert manifest['numerical_native_profile_executed'] is False
    assert manifest['biological_admission_granted'] is False
    receipt = decode((OUT/'receipt.json').read_bytes())
    child = decode((OUT/'toy_child.json').read_bytes())
    journal_raw = (OUT/'parent.jsonl').read_bytes()
    lines = journal_raw.splitlines()
    assert lines and all(lines)
    journal = [decode(line) for line in lines]
    assert receipt['status'] == 'PASS_INVENTED_CURRENT42_RUNTIME_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    assert receipt['failure'] is None
    assert child['status'] == 'PASS_INVENTED_CURRENT42_PAGED_PARSER_OPTIMIZER_EXTRAS'
    assert receipt['preparation_manifest_sha256'] == child['preparation_manifest_sha256'] == PROFILE_SHA
    assert receipt['child_completion_sha256'] == PINS['results/'+NS+'/toy_child.json']
    assert receipt['closed_parent_log_sha256'] == digest(journal_raw)
    assert receipt['full_FIT_or_old_interpreter_parity_established'] is False
    for value in (receipt, child):
        assert value['biological_rows_read'] == 0 and value['biological_admission_granted'] is False
        assert value['invented_optimizer_units'] == 12
    assert child['biological_model_fits'] == 0 and receipt['scientific_attempts'] == 0
    assert child['old_interpreter_bitwise_parity_established'] is False
    assert math.isfinite(receipt['elapsed_seconds']) and 0 <= child['elapsed_seconds'] <= receipt['elapsed_seconds'] <= 150
    assert receipt['requested_resident_maximum'] == REQUEST and receipt['measured_resident_ceiling'] == RESIDENT
    assert receipt['unchanged_job_caps'] == {'active_process_limit':2,'process_memory_limit':PRIVATE,
        'job_memory_limit':JOB,'limit_flags':8968}
    cap = receipt['additional_resident_cap']
    assert cap == journal[1]['cap']
    assert cap['only_suspended_owned_child_changed'] is True
    assert cap['private_and_job_caps_or_live_guards_changed'] is False
    assert cap['after'] == {'minimum':cap['before']['minimum'], 'maximum':REQUEST,
                            'flags':(cap['before']['flags'] & 3) | 4}
    assert 0 < cap['before']['minimum'] <= REQUEST
    assert (cap['before']['flags'] & 3) in (0,1,2) and cap['before']['flags'] & ~15 == 0
    assert journal[0]['status'] == 'ONE_OWNED_INVENTED_CURRENT42_PROFILE_STARTED'
    assert journal[0]['parent_pid'] == child['parent_pid']
    assert journal[1]['status'] == 'EXACT_ADDITIONAL_RESIDENT_CAP_INSTALLED'
    assert journal[1]['child_pid'] == child['child_pid'] != child['parent_pid']
    memory(journal[0]['memory_before'], startup=True)
    memory(receipt['memory_after'])
    samples = [row for row in journal if 'elapsed_seconds' in row]
    assert samples and 0 < len(samples) <= receipt['samples']
    elapsed = [row['elapsed_seconds'] for row in samples]
    assert elapsed == sorted(elapsed) and all(math.isfinite(x) and 0 <= x <= receipt['elapsed_seconds'] for x in elapsed)
    for row in samples:
        memory(row['memory']); counters(row['child_memory'], row['job'])
        assert row['failure'] is None
    assert all(row['exit_code'] is None for row in samples[:-1]) and samples[-1]['exit_code'] == 0
    assert samples[-1]['job']['active_processes'] == 0
    assert journal[-2]['status'] == 'FINAL_OWNED_LIFETIME_COUNTERS'
    counters(journal[-2]['process'], journal[-2]['job'])
    assert journal[-2]['job']['active_processes'] == 0
    assert journal[-1] == {'status':'MANDATORY_PARENT_TELEMETRY_COMPLETE','failure':None}
    all_process = [row['child_memory'] for row in samples] + [journal[-2]['process']]
    assert max(value['peak_private_commit'] for value in all_process) == receipt['peak_private_commit'] > BUFFER
    assert max(value['peak_working_set'] for value in all_process) == receipt['peak_working_set'] <= RESIDENT
    visible_minimum = min([journal[0]['memory_before']['physical_available'],receipt['memory_after']['physical_available']] +
                          [row['memory']['physical_available'] for row in samples])
    assert 256*MIB <= receipt['minimum_sampled_physical_available'] <= visible_minimum
    for value in journal[0]['native_origins'].values():
        runtime_pin(value['path'], value['sha256'])
    # Independent streaming reconstruction: no retained 384 MiB allocation.
    pattern = hashlib.sha256()
    zero_tail = b'\0' * 4095
    for index in range(BUFFER//4096):
        pattern.update(bytes((index % 251,)) + zero_tail)
    pattern_sha = pattern.hexdigest()
    assert child['bytes'] == BUFFER and child['hashes'] == [pattern_sha]*3
    baseline_path = ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/invented_profile_receipt.json'
    baseline = decode(baseline_path.read_bytes())
    assert baseline['status'] == 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4'
    assert child['original_V4_result_sha256'] == sha(baseline_path)
    status = decode((baseline_path.parent/'verified_native_status.json').read_bytes())
    assert status['status'] == 'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    for name, want in status['verified_files'].items():
        local((baseline_path.parent/name).relative_to(ROOT).as_posix(), want)
    results_sha = {}
    assert set(child['results']) == {'parser','optimizer','extra_deferred_native_contracts'}
    for key in child['results']:
        assert canonical(child['results'][key]) == canonical(baseline[key]), key
        results_sha[key] = digest(canonical(baseline[key]))
    assert results_sha == child['canonical_result_sha256']
    assert child['results']['optimizer']['scipy_optimizer_units'] == 12
    inventory = decode((ROOT/'results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json').read_bytes())
    assert inventory['status'] == 'PASS_CDRIVE_CURRENT42_UNCHANGED7998_BYTES_COMPATIBILITY_PENDING'
    assert Path(inventory['actual_selected_scientific_prefix']).resolve() == PREFIX.resolve()
    assert inventory['storage_relocation_explicitly_verified'] is True
    assert inventory['private_material_verification_sha256'] == 'a10f4a3fd85c6e24887ed0d8756d7d351c21ce4e51057ac0fc7cb56876e4d4f5'
    current, payload = inventory['current_bundled_stdlib_native_files'], inventory['selected_scientific_payload_files']
    assert len(current) == 42 and len(payload) == 7998
    for name, want in current.items():
        runtime_pin(name, want)
    assert child['current_payload_check']['current42_native_files_freshly_checked'] == current
    assert child['current_payload_check']['fresh_inventory_sha256'] == manifest['fresh_inventory_sha256']
    assert child['current_payload_check']['old_exact_runtime_identity_passes'] is False
    assert child['current_payload_check']['unused_pandas_SciPy_payload_rehashed_in_worker'] is False
    numpy_count = sum(name.split('/')[0] in ('numpy','numpy.libs','numpy-1.26.4.dist-info') for name in payload)
    assert child['current_payload_check']['fresh_NumPy_payload_files'] == numpy_count == 1230
    phases = {}
    for phase in ('initial_native_proof','final_native_proof'):
        proof = child[phase]
        assert proof['status'] == 'PASS_ACTUAL_CURRENT42_NATIVE_AND_UNCHANGED_LOADED_SCIENTIFIC_ORIGINS'
        assert proof['fresh_inventory_sha256'] == manifest['fresh_inventory_sha256']
        assert proof['native_discovery_sha256'] == inventory['native_discovery_sha256']
        assert proof['old_exact_runtime_identity_passes'] is proof['old_interpreter_bitwise_parity_established'] is False
        assert proof['biological_admission_granted'] is False
        for name, want in proof['actually_loaded_current_bundled_native_files'].items():
            assert current[name] == want; runtime_pin(name,want)
        for name, want in proof['actually_loaded_Python_DLLs'].items():
            assert Path(name).name.casefold() in ('python3.dll','python312.dll')
            assert current[name] == want; runtime_pin(name,want)
        assert 'python312.dll' in {Path(name).name.casefold() for name in proof['actually_loaded_Python_DLLs']}
        for name, want in proof['actually_loaded_scientific_modules'].items():
            assert payload[name] == want; runtime_pin(PREFIX/name,want)
        for name, want in proof['actually_loaded_scientific_native_files'].items():
            path = Path(name); key = path.relative_to(PREFIX).as_posix()
            assert payload[key] == want; runtime_pin(path,want)
        pools = proof['actually_loaded_threadpools']
        assert pools and {pool['user_api'] for pool in pools} <= {'blas','openmp'}
        for pool in pools:
            path = Path(pool['filepath']); key = path.relative_to(PREFIX).as_posix()
            assert pool['num_threads'] == 1; runtime_pin(path,payload[key])
        numpy = proof['numpy_original_payload_proof']
        assert numpy['status'] == 'PASS' and numpy['numpy_version'] == '1.26.4'
        assert Path(numpy['numpy_origin']).resolve() == (PREFIX/'numpy/__init__.py').resolve()
        for name,want in numpy['loaded_NumPy_files'].items():
            assert payload[name] == want; runtime_pin(PREFIX/name,want)
        for name,want in numpy['actually_loaded_NumPy_native_modules'].items():
            assert payload[name] == want; runtime_pin(PREFIX/name,want)
        caches = proof['possible_bytecode_payload_proof']
        assert caches['status'] == 'PASS_EXISTING_POSSIBLE_BYTECODE_PAYLOADS_BOUND'
        assert caches['execution_from_cache_established'] is False
        for value in caches['possible_existing_bytecode_payloads'].values():
            path = Path(value['resolved_path']); key = path.relative_to(PREFIX).as_posix()
            assert key == value['relative_path'] and payload[key] == value['sha256']
            runtime_pin(path,value['sha256'])
        phases[phase] = {'scientific_module_files':len(proof['actually_loaded_scientific_modules']),
            'scientific_native_files':len(proof['actually_loaded_scientific_native_files']),
            'bundled_native_files_recorded_loaded':len(proof['actually_loaded_current_bundled_native_files'])}
    fault = OUT/'child_fault.log'
    assert fault.read_bytes() == b''
    local(fault.relative_to(ROOT).as_posix(),sha(fault))
    self_key = Path(__file__).resolve().relative_to(ROOT).as_posix()
    local(self_key,sha(__file__))
    # A second fresh pass catches drift during this saved-file review.
    for name,want in dict(verified).items():
        assert sha(ROOT/name) == want,name
    for name,want in dict(runtime_files).items():
        assert sha(name) == want,name
    assert not cache.exists()
    assert not any(name.split('.')[0] in ('numpy','scipy','pandas','torch','openvino') for name in sys.modules)
    return {
        'status':'VERIFIED_CDRIVE_CURRENT42_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION',
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'initial_manifest_sha256':PROFILE_SHA,'source_manifest_pins_verified':164,
        'supplied_source_commit':'c52b26af9f81fdb659e4146c6c9b5e7201f00bb2',
        'git_commit_reverified_by_this_helper':False,
        'verified_files':dict(sorted(verified.items())),
        'freshly_rehashed_saved_runtime_files':dict(sorted(runtime_files.items())),
        'freshly_rehashed_runtime_file_count':len(runtime_files),'fresh_current_bundled_native_count':42,
        'native_origins_reenumerated_in_verifier':False,
        'saved_before_after_origin_proofs_consistent_with_fresh_bytes':True,'saved_origin_phase_counts':phases,
        'canonical_original_V4_result_sha256':results_sha,'independent_buffer_pattern_sha256':pattern_sha,
        'retained_invented_padding_bytes':BUFFER,'buffer_hash_checks':3,'invented_optimizer_units':12,
        'parent_pid':child['parent_pid'],'child_pid':child['child_pid'],
        'recorded_resource_samples':receipt['samples'],'persisted_resource_snapshots':len(samples),
        'all_recorded_resource_snapshots_pass':True,
        'unpersisted_100ms_samples_not_independently_reconstructed':True,
        'elapsed_seconds':receipt['elapsed_seconds'],'peak_private_commit':receipt['peak_private_commit'],
        'peak_working_set':receipt['peak_working_set'],
        'minimum_sampled_physical_available':receipt['minimum_sampled_physical_available'],
        'old_exact_runtime_identity_passes':False,'old_interpreter_bitwise_parity_established':False,
        'all_unused7998_payloads_rehashed_by_verifier':False,'all_stdlib_source_bytes_inventoried':False,
        'numerical_imports_or_operations_by_verifier':False,'new_jobs_or_model_fits':0,
        'biological_rows_read':0,'metadata_array_label_FIT_admissions_granted_here':False,
        'prior_interruption_cause_established':False,
        'scope':'Saved invented-case compatibility only, not biological acceptance, full old-runtime equivalence, or full-study completion.',
    }


if __name__ == '__main__':
    result = verify()
    destination = OUT/'verified_current_status.json'
    with destination.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(result,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(result['status'],sha(destination),result['freshly_rehashed_runtime_file_count'],flush=True)
