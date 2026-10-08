"""Guarded one-CPU outcome-free GQ production; both ensembles folded fresh."""
import math
import os
import sys
import time
from .guards import *
from .spec import request_plan, sequence_hash, positions_key, request_hash, spec_hash, count_pools, transformed_counts

def cache_path(sequence):
    stamp = sha256(OUT / 'feature_production_manifest.json')
    key = sequence_hash(sequence)
    return ART / 'allele_cache' / stamp / key[:2] / (key + '.json')

def identity(sequence, requested):
    return {'sequence_sha256': sequence_hash(sequence), 'request_sha256': request_hash(requested),
        'spec_sha256': spec_hash(), 'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'backend_receipt_sha256': sha256(FEAS_OUT / 'backend_feasibility_receipt.json')}

def validate(sequence, requested, path=None):
    path = cache_path(sequence) if path is None else Path(path)
    birth_path = path.with_suffix('.birth.json'); birth = readj(birth_path)
    expected = identity(sequence, requested)
    assert birth['identity'] == expected and birth['role'] == 'IMMUTABLE_DIGEST_AT_FIRST_CREATION_NOT_RETROACTIVE'
    assert birth['cache_sha256'] == sha256(path)
    value = readj(path)
    assert value['identity'] == expected and value['sequence'] == sequence and value['length'] == len(sequence)
    assert value['keys'] == [positions_key(p) for p in requested] and len(set(value['keys'])) == len(requested)
    assert len(value['global_raw']) == 6 and len(value['local_raw']) == len(requested)
    assert all(len(v) == 6 for v in value['local_raw']) and len(value['physics']) == 2
    assert len(value['global_counts']) == 6 and len(value['local_counts']) == len(requested)
    assert value['global_raw'] == transformed_counts(value['global_counts'])
    assert value['local_raw'] == [transformed_counts(v) for v in value['local_counts']]
    numbers = value['global_raw'] + value['physics'] + [v for row in value['local_raw'] for v in row]
    assert all(math.isfinite(v) for v in numbers) and 0 <= value['physics'][1] <= 1 and value['physics'][0] <= 2e-6
    measured = value['native_measure']
    assert measured['G_on_minus_off'] == value['physics'][0]
    assert measured['modeled_at_least_one_GQ_probability'] == value['physics'][1]
    return value

def save_cache(sequence, requested, backend):
    path = cache_path(sequence); birth_path = path.with_suffix('.birth.json')
    if path.exists():
        assert birth_path.exists(), 'Preserve orphan; no retroactive creation receipt'
        validate(sequence, requested); return path
    assert not birth_path.exists()
    pending = path.with_suffix('.pending'); assert not pending.exists(), 'Preserve interrupted partial cache'
    global_counts, local_counts = count_pools(backend.gq_patterns(sequence), len(sequence), requested)
    measured = backend.measure(sequence)
    value = {'identity': identity(sequence, requested), 'sequence': sequence, 'length': len(sequence),
        'keys': [positions_key(p) for p in requested], 'global_counts': global_counts, 'local_counts': local_counts,
        'global_raw': transformed_counts(global_counts), 'local_raw': [transformed_counts(c) for c in local_counts],
        'physics': [measured['G_on_minus_off'], measured['modeled_at_least_one_GQ_probability']],
        'native_measure': measured, 'both_ensembles_fresh': True}
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with pending.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    birth = {'identity': value['identity'], 'cache_sha256': sha256(pending),
             'role': 'IMMUTABLE_DIGEST_AT_FIRST_CREATION_NOT_RETROACTIVE'}
    # No completed cache is overwritten. An interrupted rename/sidecar gap fails closed.
    pending.rename(path); jsave(birth_path, birth); validate(sequence, requested)
    return path

def run():
    assert sys.argv[1:] == ['--root-start']
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert all(os.environ.get(k) == '1' for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    production_check(); backend_reference = backend_check(); source_control_paths(); headroom = resource_check('production')
    assert not (OUT / 'features_receipt.json').exists(), 'Preserve completed production'
    # Native import occurs only after the root-committed production guard.
    from src.generalization_gquad_feasibility_20261007 import backend
    backend.environment(); actual = backend.runtime_identity()
    assert actual == backend_reference['runtime'], 'Actual native version/origin/bytes differ from synthetic certification'
    original, encoded = sequence_rows(); roster, row_positions = request_plan(encoded)
    plan = readj(ART / 'sequence_request_manifest.json')
    assert plan['original_metadata_sha256'] == metadata_digest(original) and plan['encoded_metadata_sha256'] == metadata_digest(encoded)
    assert plan['requests'] == {sequence_hash(s): request_hash(r) for s, r in roster.items()}
    assert len(roster) == 18220 and len(row_positions) == 26258 and plan['spec_sha256'] == spec_hash()
    before = structure_index_check(True); started = time.perf_counter(); entries = []; coverage = {}
    for index, sequence in enumerate(sorted(roster, key=lambda s: (-len(s), sequence_hash(s)))):
        path = save_cache(sequence, roster[sequence], backend); value = validate(sequence, roster[sequence])
        entries.append({'sequence_sha256': sequence_hash(sequence), 'request_sha256': request_hash(roster[sequence]),
            'path': path.relative_to(ROOT).as_posix(), 'sha256': sha256(path),
            'birth_path': path.with_suffix('.birth.json').relative_to(ROOT).as_posix(), 'birth_sha256': sha256(path.with_suffix('.birth.json'))})
        group = coverage.setdefault(str(len(sequence)), {'alleles': 0, 'raw_any_box': 0, 'positive_modeled_GQ_metric': 0})
        group['alleles'] += 1; group['raw_any_box'] += int(sum(value['global_counts']) > 0)
        group['positive_modeled_GQ_metric'] += int(value['physics'][1] > 0)
        if (index + 1) % 250 == 0:
            print('GQ fresh both ensembles', index + 1, '/', len(roster), 'seconds', round(time.perf_counter() - started, 1), flush=True)
    after = structure_index_check(True); assert before == after
    jsave(ART / 'cache_index.json', {'alleles': entries, 'spec_sha256': spec_hash(),
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json')})
    jsave(OUT / 'features_receipt.json', {'status': 'PASS', 'rows': 26258, 'alleles': 18220,
        'original_metadata_sha256': metadata_digest(original), 'encoded_metadata_sha256': metadata_digest(encoded),
        'cache_index_sha256': sha256(ART / 'cache_index.json'), 'spec_sha256': spec_hash(),
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'actual_runtime': actual, 'ordinary_structure_before': before, 'ordinary_structure_after': after,
        'birth_hashes_required': True, 'both_ensembles_fresh': True, 'coverage_counts_only_after_production_freeze': coverage,
        'headroom_before_native_import': headroom,
        'elapsed_seconds': time.perf_counter() - started, 'threads': 1, 'labels_read': False, 'models_fit': 0})

if __name__ == '__main__':
    run()
