"""Standard-library identities and bounded profile policy; no native calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_parser_profile_20261022'
SRC, REP, OUT = [ROOT / part / NS for part in ('src', 'reports', 'results')]
MANIFEST = OUT / 'preparation_manifest.json'
INVENTORY = OUT / 'payload_inventory.json'
RUNTIME = ROOT / 'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
PYTHON = ROOT / 'results/generalization_current_python_20261022/current_python_inventory.json'
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
COMPONENTS = (
    'numpy', 'numpy.libs', 'numpy-1.26.4.dist-info',
    'pandas', 'pandas.libs', 'pandas-2.2.3.dist-info',
    'scipy', 'scipy.libs', 'scipy-1.14.1.dist-info',
    'dateutil', 'python_dateutil-2.9.0.post0.dist-info',
    'pytz', 'pytz-2026.3.post1.dist-info', 'tzdata', 'tzdata-2026.3.dist-info',
    'six.py', 'six-1.17.0.dist-info', 'packaging', 'packaging-26.3.dist-info',
    'threadpoolctl.py', 'threadpoolctl-3.6.0.dist-info',
)
THREAD_ENV = {name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                                    'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
OPTIONS = {'maxiter': 500, 'ftol': 1e-11, 'gtol': 1e-7}
PENALTIES = (.005, .05, .5)
STATUS = 'FROZEN_INVENTED_ONE_THREAD_PANDAS_SCIPY_CURRENT_PYTHON_PROFILE'
NATIVE_PASS = 'PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER'


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''): value.update(block)
    return value.hexdigest()


def jsave(path, value):
    path = Path(path)
    assert path.parent.resolve() == OUT.resolve()
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def payload_members(files):
    """No filename/type guessing: explicitly enumerated old-receipt components."""
    wanted = {name: value for name, value in files.items() if name.split('/')[0] in COMPONENTS}
    assert {name.split('/')[0] for name in wanted} == set(COMPONENTS), 'Required package absent; do not install'
    return wanted


def native_members(files):
    return {name: value for name, value in files.items() if Path(name).suffix.lower() in ('.dll', '.pyd')}


def check_payload_files(expected, prefix=PREFIX):
    prefix = Path(prefix).resolve()
    actual = set()
    for component in COMPONENTS:
        path = prefix / component
        paths = [path] if path.is_file() else path.rglob('*')
        for item in paths:
            if item.is_file():
                assert not item.is_symlink() and item.resolve().is_relative_to(prefix)
                actual.add(item.relative_to(prefix).as_posix())
    assert actual == set(expected), 'Unexpected/missing pinned package payload'
    for name, want in expected.items(): assert sha(prefix / name) == want, name
    return len(actual)


def resource_failure(state, elapsed, active_processes=1, startup=False):
    if elapsed > 120: return 'Invented120second deadline exceeded'
    if state['physical_available'] < (512 if startup else 256) * 2**20: return 'Physical reserve floor violated'
    required_commit = 2**30 + (896 * 2**20 if startup else 0)
    if state['commit_headroom'] < required_commit: return 'System commitment reserve violated'
    if state['disk_available'] < (1024 if startup else 256) * 2**20: return 'Disk reserve violated'
    if active_processes > 2: return 'Owned active-process cap exceeded'
    return None


def check_thread_environment(environ):
    assert all(environ.get(key) == value for key, value in THREAD_ENV.items()), 'Exact one-thread UTF8/no-bytecode environment required'


def certificate_python_files(attestation):
    executable = Path(attestation['python_executable']).resolve()
    expected = {executable, executable.parent/'python3.dll', executable.parent/'python312.dll'}
    files = attestation['python_native_files']
    assert len(files) == 3 and {Path(name).resolve() for name in files} == expected
    assert all(isinstance(value,str) and len(value)==64 for value in files.values())
    return dict(files)
