"""Fixed operational contracts. Source preparation never grants approval."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_bounded_execution_20261023'
OUT = ROOT / 'results' / NS
MANIFEST = OUT / 'execution_manifest.json'
AUTH = OUT / 'authorization.json'
CACHE_PREFIX = ROOT / 'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
STAGES = ('metadata', 'array', 'labels', 'prefit', 'fit', 'replay', 'evaluation')
IMPLEMENTED_STAGES = ('metadata',)
THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
STATUS = 'PROPOSED_FIXED_KNOWNCELL_RESOURCE_CALIBRATION_AWAITING_EXACT_HUMAN_APPROVAL'
METADATA_BUNDLE = ROOT / 'results/generalization_knowncell_joint_loader_20261022/admitted_metadata.json'
METADATA_ADMISSION = 'results/generalization_knowncell_joint_loader_20261022/metadata_admission_manifest.json'
PROCESS_CAP = 768 * 2**20
JOB_CAP = 896 * 2**20


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def decode(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            assert key not in value, 'Duplicate JSON key'
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(AssertionError('Nonfinite JSON token')))


def valid_sha(value):
    assert isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    return value


def relative(name):
    assert isinstance(name, str) and name == name.replace('\\', '/')
    assert not name.startswith('/') and ':' not in name and '..' not in name.split('/')
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT.resolve())
    return path


def save_new(path, value):
    raw = canonical(value)
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return sha(raw)


def source_mode():
    assert sys.flags.no_site == 1 and sys.dont_write_bytecode is True, 'Require -S -B'
    assert sys.pycache_prefix == str(CACHE_PREFIX), 'Require exact shared absent cache prefix'
    assert not os.path.lexists(CACHE_PREFIX), 'Source cache prefix must remain absent'
    assert sys.implementation.cache_tag == 'cpython-312' and sys.version_info[:2] == (3, 12)
    assert all(os.environ.get(key) == '1' for key in THREAD_KEYS), 'Exactly one numerical thread'
    assert os.environ.get('PYTHONUTF8') == os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    return {'no_site': True, 'dont_write_bytecode': True,
        'cache_prefix': str(CACHE_PREFIX), 'cache_prefix_absent': True, 'numerical_threads': 1}


def committed(path, raw):
    from src.generalization_pum_process_probe_20261021 import headless
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + Path(path).relative_to(ROOT).as_posix()], cwd=ROOT) == raw


def verify_sources(expected_sha):
    source_mode()
    raw = MANIFEST.read_bytes()
    assert sha(raw) == valid_sha(expected_sha), 'Initial execution manifest identity changed'
    manifest = decode(raw)
    assert manifest['status'] == STATUS and manifest['stages'] == list(STAGES)
    assert manifest['implemented_entrypoints'] == list(IMPLEMENTED_STAGES)
    assert manifest['cache_prefix'] == str(CACHE_PREFIX)
    assert manifest['resource_policy'] == resource_policy()
    for name, want in manifest['files'].items():
        assert sha(relative(name).read_bytes()) == valid_sha(want), name
    executable = Path(sys.executable).resolve()
    assert executable == Path(manifest['python_executable']).resolve()
    assert {Path(name).resolve() for name in manifest['python_native_files']} == {
        executable, executable.parent / 'python3.dll', executable.parent / 'python312.dll'}
    for name, want in manifest['python_native_files'].items():
        assert sha(Path(name).read_bytes()) == valid_sha(want), name
    source_mode()
    return manifest


def resource_policy():
    return {'startup_physical_available': 512 * 2**20, 'active_physical_available': 256 * 2**20,
        'disk_available': 2**30, 'startup_commit_headroom': JOB_CAP + 2**30,
        'active_commit_headroom': 2**30, 'process_cap': PROCESS_CAP, 'job_cap': JOB_CAP,
        'active_process_cap': 2, 'scientific_workers': 1, 'numerical_threads': 1,
        'lifetime_seconds_per_stage': 1800, 'monitor_poll_seconds': 0.1,
        'automatic_retry': False, 'resume': False, 'spending_authorized': False}


def resource_failure(snapshot, elapsed, *, startup=False):
    assert isinstance(snapshot, dict)
    for key in ('physical_available', 'commit_headroom', 'disk_available'):
        assert type(snapshot[key]) is int and snapshot[key] >= 0
    assert type(elapsed) in (int, float) and 0 <= elapsed < float('inf')
    policy = resource_policy()
    if snapshot['physical_available'] < policy['startup_physical_available' if startup else 'active_physical_available']:
        return 'Physical reserve below ' + ('512 MiB startup' if startup else '256 MiB active')
    if snapshot['commit_headroom'] < policy['startup_commit_headroom' if startup else 'active_commit_headroom']:
        return 'Insufficient global system commit headroom'
    if snapshot['disk_available'] < policy['disk_available']:
        return 'Workspace disk below 1 GiB'
    if elapsed > policy['lifetime_seconds_per_stage']:
        return 'Owned stage exceeded 30-minute deadline'
    return None


def approval_contract(record, manifest_sha):
    assert record['status'] == 'EXACT_HUMAN_KNOWNCELL_RESOURCE_APPROVAL_RECORDED'
    assert record['execution_manifest_sha256'] == valid_sha(manifest_sha)
    assert record['approved_stages'] == list(STAGES)
    assert record['resource_policy'] == resource_policy()
    assert record['spending_authorized'] is False and record['scientific_protocol_changes_authorized'] is False
    assert record['automatic_retry_authorized'] is False and record['scheduled_tasks_authorized'] is False
    assert isinstance(record['question'], str) and record['question']
    assert record['answer'] == 'Approve this exact known-cell resource calibration'
    assert isinstance(record['question_item_id'], str) and record['question_item_id']
    return True


def admit_authorization(manifest_sha):
    manifest_raw = MANIFEST.read_bytes()
    assert sha(manifest_raw) == valid_sha(manifest_sha), 'Initial committed manifest identity changed'
    committed(MANIFEST, manifest_raw)
    verify_sources(manifest_sha)
    raw = AUTH.read_bytes()  # Deliberately absent until the human actually approves.
    record = decode(raw)
    approval_contract(record, manifest_sha)
    committed(AUTH, raw)
    return {'manifest_sha256': manifest_sha, 'approval_sha256': sha(raw),
        'explicit_human_approval': True, 'allowed_stages': list(STAGES), 'owned_job_required': True}


def birth_path(stage):
    assert stage in STAGES
    return OUT / (stage + '_attempt_birth.json')


def verify_stage_admission(stage, manifest_sha, expected_sha):
    """Future nonmetadata eligibility; missing admission always fails closed.

    This verifies the declared closure's bytes, not automatic completeness of
    arbitrary dynamic imports. Independent source review and the future stage's
    own scientific/input admission remain required.
    """
    assert stage in STAGES and stage not in IMPLEMENTED_STAGES
    path = OUT / (stage + '_controller_admission.json')
    raw = path.read_bytes()
    assert sha(raw) == valid_sha(expected_sha)
    committed(path, raw)
    document = decode(raw)
    assert document['status'] == 'FROZEN_INDEPENDENTLY_REVIEWED_KNOWNCELL_STAGE_CONTROLLER'
    assert document['stage'] == stage and document['resource_execution_manifest_sha256'] == manifest_sha
    assert document['scientific_protocol_settings_changed'] is False
    assert document['spending_authorized'] is False
    module = document['controller_module']
    assert isinstance(module, str) and module.startswith('src.generalization_knowncell_')
    assert all(part.isidentifier() for part in module.split('.'))
    module_path = module.replace('.', '/') + '.py'
    files = document['files']
    assert isinstance(files, dict) and files and files[module_path] == valid_sha(document['controller_source_sha256'])
    review = document['independent_source_review']
    assert review.startswith('reports/generalization_knowncell_') and review.endswith('.md')
    assert files[review] == valid_sha(document['independent_source_review_sha256'])
    for name, want in files.items():
        assert name.startswith(('src/', 'reports/', 'results/', 'artifacts/'))
        assert name.endswith(('.py', '.json', '.md', '.log', '/.gitattributes'))
        assert sha(relative(name).read_bytes()) == valid_sha(want), name
        if name.startswith('src/') and name.endswith('.py'):
            parent = relative(name).parent
            while parent.is_relative_to(ROOT / 'src'):
                init = parent / '__init__.py'
                if init.is_file():
                    assert init.relative_to(ROOT).as_posix() in files, 'Missing regular parent package pin'
                parent = parent.parent
    assert sha(path.read_bytes()) == expected_sha, 'Stage admission changed during verification'
    return {'stage_controller_admission_sha256': expected_sha,
        'controller_module': module, 'declared_source_closure_verified': True,
        'scientific_input_and_FIT_admissions_verified_here': False}


def verify_owner(stage, manifest_sha, evidence):
    """Prove parent relation plus membership; parent verifies exact job/limits.

    IsProcessInJob(NULL) in the child alone proves membership in a job. Exact
    owned-job membership and hard limits are checked through the suspended
    creation handle in the pinned supervisor BEFORE resume. Both halves bind
    the immutable birth and source SHA; no claim of querying an unnamed exact
    parent job from the child is made.
    """
    source_mode()
    assert stage in STAGES
    required = {'parent_pid', 'birth_sha256'}
    if stage not in IMPLEMENTED_STAGES:
        required.add('stage_controller_admission_sha256')
    assert set(evidence) == required
    assert type(evidence['parent_pid']) is int and evidence['parent_pid'] == os.getppid()
    raw = birth_path(stage).read_bytes()
    assert sha(raw) == valid_sha(evidence['birth_sha256'])
    birth = decode(raw)
    assert birth['stage'] == stage and birth['execution_manifest_sha256'] == manifest_sha
    assert birth['parent_pid'] == os.getppid() and birth['resource_policy'] == resource_policy()
    assert birth['source_mode'] == source_mode() and birth['automatic_retry'] is False
    assert birth['authorization_sha256'] == sha(AUTH.read_bytes())
    eligibility = {}
    if stage not in IMPLEMENTED_STAGES:
        assert birth['stage_controller_admission_sha256'] == valid_sha(evidence['stage_controller_admission_sha256'])
        eligibility = verify_stage_admission(stage, manifest_sha, evidence['stage_controller_admission_sha256'])
    import ctypes
    from ctypes import wintypes
    assert os.name == 'nt'
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype = wintypes.BOOL
    answer = wintypes.BOOL()
    assert kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(answer)), 'Job membership query failed'
    assert answer.value, 'Scientific worker must already belong to capped owned job'
    return {'current_pid': os.getpid(), 'parent_pid': os.getppid(), 'in_owned_job': True,
        'birth_sha256': evidence['birth_sha256'], 'manifest_sha256': manifest_sha,
        'continuous_monitoring_owned_by_controller': True, **eligibility}
