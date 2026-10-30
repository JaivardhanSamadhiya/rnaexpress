"""New runtime epoch; no inherited completed-study resource exception."""
from pathlib import Path
import hashlib
import json
import math
import os

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_menu_numeric_20261030'
OUT = ROOT / 'results' / NS
MANIFEST = OUT / 'preparation_manifest.json'
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
PYTHON = Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
CACHE = ROOT / 'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
NEW_INVENTORY = OUT / 'software_inventory.json'
NEW_SHA = '38494d53203c0649321c99092616b52e800ca1fda651a4354c99c4701521b5bc'
OLD_INVENTORY = ROOT / 'results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json'
OLD_SHA = '34ff960c2e0a69f724eff36324f72dec8c8208c48c93f6ddfd3ed7db2fa7ee33'
THREADS = dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'1')
THREADS.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
DEADLINE = 240


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def dump(path, value):
    with path.open('x',encoding='utf8',newline='\n') as stream:
        stream.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def resource_failure(state, elapsed):
    if not math.isfinite(elapsed) or elapsed < 0:return 'invalid elapsed time'
    if elapsed > DEADLINE:return '240-second invented-profile deadline'
    if state['physical_available'] < 3*2**30:return 'unchanged 3 GiB physical RAM floor'
    if state['commit_headroom'] < 1920*2**20:return 'global commit reserve'
    if state['disk_available'] < 2**30:return 'disk reserve'
    return None


def checked_document(path, expected):
    if sha(path) != expected:raise ValueError('changed bound document: '+str(path))
    return json.loads(path.read_bytes())


def source_mode():
    import sys
    assert sys.flags.no_site == 1 and sys.dont_write_bytecode and sys.flags.optimize == 0
    assert sys.pycache_prefix == str(CACHE) and not CACHE.exists() and not CACHE.is_symlink()
    assert Path(sys.executable).resolve() == PYTHON.resolve()
