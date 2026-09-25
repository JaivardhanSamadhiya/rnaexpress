"""Immutable output helpers for the requested evidence delivery directory."""
from .common import ROOT, sha256
import csv
import io
import json

ART = ROOT / 'artifacts/research_20260925'


def save(name, payload):
    path = (ART / name).resolve()
    if not path.is_relative_to(ART.resolve()) or path == ART.resolve():
        raise PermissionError('Output outside evidence directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError('Preserving existing evidence: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(payload)
    return path


def save_json(name, obj):
    return save(name, (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())


def save_csv(name, rows):
    if not rows:
        raise ValueError('Empty evidence table')
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return save(name, buf.getvalue().encode('utf-8'))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))
