"""Stdlib preparation guards; numerical libraries are lazy and root-gated."""
from pathlib import Path
import hashlib
import json
import subprocess
from .spec import NS

ROOT = Path(__file__).resolve().parents[2]
SRC, OUT, REP, ART = [ROOT / name / NS for name in ('src', 'results', 'reports', 'artifacts')]
PREP = OUT / 'preparation_manifest.json'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def readj(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(payload)


def jsave(path, data):
    save(path, (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def committed(path):
    path = Path(path)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), str(path)


def preparation_check(root_start):
    assert root_start, 'Root explicit start required before any project metadata/array read'
    committed(PREP)
    manifest = readj(PREP)
    assert manifest['status'] == 'FROZEN_SOURCE_ONLY_RBP_CELLAXIS_PREPARATION'
    for name, expected in manifest['files'].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve()) and sha256(target) == expected, name
    return manifest
