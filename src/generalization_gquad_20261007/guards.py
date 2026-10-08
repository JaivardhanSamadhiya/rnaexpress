"""Standard-library provenance and metadata guards; never import a backend."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import subprocess
import ctypes
import shutil
from .spec import TRACKS, SHAPES

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_gquad_20261007'
SRC, OUT, REP, ART = [ROOT / p / NS for p in ('src', 'results', 'reports', 'artifacts')]
NEXT_ART, NEXT_OUT = ROOT / 'artifacts/generalization_next_20261007', ROOT / 'results/generalization_next_20261007'
FEAS_OUT = ROOT / 'results/generalization_gquad_feasibility_20261007'
IDENTITY = ['intervention_id', 'dataset', 'biological_component', 'parent_context_id', 'parent_sequence', 'mutant_sequence']
STUDIES = ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle']
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def readj(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(root.resolve()) for root in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve existing artifact: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(payload)

def jsave(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())

def committed(path):
    path = Path(path)
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), 'Root must commit exact bytes: ' + str(path)

def canonical_map(mapping):
    result = {}; aliases = set()
    for key, value in mapping.items():
        name = key.replace('\\', '/')
        assert not name.startswith('/') and ':' not in name and all(part not in ('', '.', '..') for part in name.split('/'))
        assert name.casefold() not in aliases, 'Path alias/collision'
        aliases.add(name.casefold()); result[name] = value
    return result

def hash_files(mapping):
    for name, expected in canonical_map(mapping).items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha256(path) == expected, name

def metadata_digest(rows):
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=IDENTITY, lineterminator='\n')
    writer.writeheader(); writer.writerows({k: row[k] for k in IDENTITY} for row in rows)
    return hashlib.sha256(buffer.getvalue().encode()).hexdigest()

def sequence_rows():
    reference_path = NEXT_OUT / 'prefit_manifest.json'; committed(reference_path)
    reference = readj(reference_path); assert reference['status'] == 'FROZEN_PREFIT'
    pins = canonical_map(reference['files'])
    short_path = NEXT_OUT / 'short_feature_receipt.json'
    assert sha256(short_path) == pins[short_path.relative_to(ROOT).as_posix()]
    short = readj(short_path); assert short['status'] == 'PASS' and short['rows'] == 26258
    rows = []
    for filename in ('sequence_inventory.csv.gz', 'encoded_sequence_inventory.csv.gz'):
        path = NEXT_ART / filename; name = path.relative_to(ROOT).as_posix()
        assert sha256(path) == pins[name] == canonical_map(short['files'])[name]
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            assert set(IDENTITY) <= set(reader.fieldnames)
            rows.append([{key: record[key] for key in IDENTITY} for record in reader])
    original, encoded = rows
    assert len(original) == len(encoded) == 26258 and len({r['intervention_id'] for r in original}) == 26258
    assert {r['dataset'] for r in original} == set(STUDIES)
    context_path = ROOT / 'artifacts/generalization_20261007/reporter_context_metadata.json'
    assert sha256(context_path) == 'e7ee4fea706d3b7e611f63d491304cfe835efcd3c9b6a9a4f0282abf384f725c'
    design = readj(context_path)['local_design']; left, right = design['left_20nt_dna'], design['right_20nt_dna']
    assert len(left) == len(right) == 20 and design['template_dna'] == left + 'N' * 6 + right
    for a, b in zip(original, encoded):
        assert all(a[k] == b[k] for k in IDENTITY[:4])
        expected = (left + a['parent_sequence'] + right, left + a['mutant_sequence'] + right) if a['dataset'] == 'srle' else (a['parent_sequence'], a['mutant_sequence'])
        assert (b['parent_sequence'], b['mutant_sequence']) == expected
        assert len(b['parent_sequence']) == len(b['mutant_sequence']) and set(b['parent_sequence'] + b['mutant_sequence']) <= set('ACGT')
        assert len(b['parent_sequence']) in ((46,) if a['dataset'] == 'srle' else (150, 190, 260))
    return original, encoded

def source_control_paths():
    path = NEXT_OUT / 'prefit_manifest.json'; committed(path)
    ref = readj(path); assert ref['status'] == 'FROZEN_PREFIT'; pins = canonical_map(ref['files'])
    receipt_path = NEXT_OUT / 'prepare_receipt.json'
    assert sha256(receipt_path) == pins[receipt_path.relative_to(ROOT).as_posix()]
    receipt = readj(receipt_path); assert receipt['status'] == 'PASS'
    result = {}
    for track, columns in (('base', 246), ('structure', 262)):
        target = NEXT_ART / (track + '_model_features.npz'); name = target.relative_to(ROOT).as_posix()
        assert sha256(target) == pins[name] == canonical_map(receipt['files'])[name]
        result[track] = target
    return result

def backend_check():
    ready_path = FEAS_OUT / 'readiness_receipt.json'; committed(ready_path)
    ready = readj(ready_path); assert ready['status'] == 'PASS_SOURCE_BINDING'
    for field in ('files', 'prior_receipts'):
        if field in ready:
            hash_files(ready[field])
    backend_path, precision_path = FEAS_OUT / 'backend_feasibility_receipt.json', FEAS_OUT / 'single_event_precision_receipt.json'
    committed(backend_path); committed(precision_path)
    backend, precision = readj(backend_path), readj(precision_path)
    assert backend['status'] == 'PASS' and precision['status'] == 'PASS_FIXED_ABSOLUTE_PRECISION'
    hash_files(precision['files'])
    assert backend['project_alleles_folded'] == 0 and backend['models_fit'] == 0 and not backend['labels_read']
    hash_files(backend['source_files']); hash_files(backend['runtime']['files']); hash_files(backend['source_code_and_declared_protocol'])
    assert backend['runtime']['version'] == '2.7.2' and not backend['runtime']['binary_recompiled_from_inspected_source']
    return backend

def structure_index_check(rehash=False):
    index_path = NEXT_ART / 'structure_postproduction_sha256_index.json'
    audit_path = NEXT_OUT / 'structure_postproduction_audit_receipt.json'
    reference_path = NEXT_OUT / 'prefit_manifest.json'; committed(reference_path)
    pins = canonical_map(readj(reference_path)['files'])
    for path in (index_path, audit_path):
        assert sha256(path) == pins[path.relative_to(ROOT).as_posix()]
    index, audit = readj(index_path), readj(audit_path)
    assert audit['status'] == 'PASS' and len(index['alleles']) == 18220
    assert len({item['path'] for item in index['alleles']}) == 18220
    if rehash:
        for item in index['alleles']:
            target = (ROOT / item['path']).resolve(); assert target.is_relative_to(NEXT_ART.resolve())
            assert target.stat().st_size == item['bytes'] and sha256(target) == item['sha256'], item['path']
    return {'index_sha256': sha256(index_path), 'audit_sha256': sha256(audit_path),
            'files': 18220, 'actual_cache_bytes_rehashed': bool(rehash)}

def manifest_check(filename, status):
    path = OUT / filename; committed(path)
    manifest = readj(path); assert manifest['status'] == status
    hash_files(manifest['files']); return manifest

def production_check():
    return manifest_check('feature_production_manifest.json', 'FROZEN_GQUAD_FEATURE_PRODUCTION')

def freeze_check():
    return manifest_check('prefit_manifest.json', 'FROZEN_GQUAD_PREFIT')

def tests_check():
    receipt = readj(OUT / 'synthetic_tests_receipt_final.json')
    assert receipt['status'] == 'PASS' and receipt['models_fit'] == receipt['project_alleles_folded'] == 0
    assert set(receipt['source_hashes']) == {p.name for p in SRC.glob('*.py')}
    for name, expected in receipt['source_hashes'].items():
        assert sha256(SRC / name) == expected, name

def resource_check(stage):
    """Fresh Windows headroom; root also coordinates other workers."""
    assert stage in ('production', 'assembly', 'fit')
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in
            ('total_phys', 'avail_phys', 'total_page', 'avail_page', 'total_virtual', 'avail_virtual', 'avail_extended')]
    memory = Memory(); memory.length = ctypes.sizeof(memory)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    free_gib = memory.avail_phys / 2**30; disk_gib = shutil.disk_usage(ROOT).free / 2**30
    floor = 3. if stage == 'fit' else 1.
    assert free_gib >= floor and disk_gib >= 1., 'Preserve work; await fresh RAM/disk headroom: ' + str((stage, free_gib, disk_gib))
    return {'stage': stage, 'fresh_free_RAM_GiB': free_gib, 'fresh_free_disk_GiB': disk_gib,
            'required_RAM_GiB': floor, 'required_disk_GiB': 1., 'one_thread': True}
