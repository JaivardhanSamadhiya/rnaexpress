"""Immutable values only; no localization outcomes, feature matrices or models."""
from pathlib import Path
import json
import subprocess
from src.generalization_conservation_native_20261007 import common as old
from src.generalization_conservation_header_pilot_20261008 import pilot

ROOT = old.ROOT
NS = 'generalization_conservation_values_20261008'
OUT, ART = ROOT / 'results' / NS, ROOT / 'artifacts' / NS
MANIFEST = OUT / 'value_manifest.json'


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (OUT, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(payload)


def jsave(path, value):
    save(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def certify():
    assert subprocess.check_output(['git', 'show', 'HEAD:' + MANIFEST.relative_to(ROOT).as_posix()], cwd=ROOT) == MANIFEST.read_bytes(), 'Commit exact full-value freeze'
    value = old.read(MANIFEST)
    assert value['status'] == 'FROZEN_EXACT_SITE_VALUES_FROM_OBSERVED_HEADER_PILOTS'
    for name, expected in value['files'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and old.sha(path) == expected, name
    for name in value['own_files']:
        assert subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) == (ROOT / name).read_bytes(), name
    pilot.check_design()
    return value
