"""One-worker resumable outcome-free joint interval/motif feature production."""
import io
import os
import sys
import time
from .common import *
from .runtime import check as runtime_check
from .scoring import pooled_blocks
from .feasibility import joint_probabilities, SPEC
from src.generalization_rbp_20261007.scoring import scan
from src.generalization_rbp_20261007.projection import load_projections
from src.generalization_rbp_20261007.production import requests, request_hash, positions_key, sequence_hash

def spec_hash():
    from .scoring import PLAN
    return hashlib.sha256(json.dumps({'fold': SPEC, 'pool': PLAN}, sort_keys=True, allow_nan=False).encode()).hexdigest()

def cache_path(sequence):
    stamp = sha256(OUT / 'feature_production_manifest.json')[:16]
    key = sequence_hash(sequence)
    return ART / 'joint_cache' / stamp / key[:2] / (key + '.npz')

def creation_identity(sequence, requested):
    return {'sequence_sha256': sequence_hash(sequence), 'requests_sha256': request_hash(requested),
        'spec_sha256': spec_hash(), 'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'runtime_binding_sha256': sha256(OUT / 'runtime_binding_receipt.json'),
        'projection_receipt_sha256': sha256(RBP_OUT / 'projection_receipt.json'),
        'role': 'IMMUTABLE_DIGEST_AT_FIRST_CACHE_CREATION', 'length': len(sequence), 'mode': 'joint'}

def validate(path, sequence, requested, creation=None):
    path = Path(path)
    birth = readj(path.with_suffix('.json')) if creation is None else creation
    expected = creation_identity(sequence, requested)
    assert {key: birth[key] for key in expected} == expected
    assert birth['cache_sha256'] == sha256(path), 'Cache differs from immutable first-creation digest'
    with np.load(path, allow_pickle=False) as data:
        assert set(data.files) == {'sequence', 'sequence_sha256', 'requests_sha256', 'spec_sha256', 'keys', 'global', 'local'}
        assert data['sequence'].item() == sequence
        assert data['sequence_sha256'].item() == expected['sequence_sha256']
        assert data['requests_sha256'].item() == expected['requests_sha256'] and data['spec_sha256'].item() == expected['spec_sha256']
        keys = data['keys'].tolist(); global_value, local = data['global'].copy(), data['local'].copy()
    assert keys == [positions_key(value) for value in requested] and len(keys) == len(set(keys))
    assert global_value.shape == (128,) and local.shape == (len(requested), 128)
    assert global_value.dtype == local.dtype == np.dtype('float64')
    assert np.isfinite(global_value).all() and np.isfinite(local).all()
    return global_value, dict(zip(keys, local))

def score(sequence, requested, matrices):
    probability = joint_probabilities(sequence)
    blocks = scan(sequence)
    global_pools = pooled_blocks(blocks, len(sequence), (), probability)
    global_value = np.r_[global_pools[:, 0] @ matrices[0], global_pools[:, 1] @ matrices[1]]
    local = []
    for positions in requested:
        pools = pooled_blocks(blocks, len(sequence), positions, probability)
        local.append(np.r_[pools[:, 2] @ matrices[2], pools[:, 3] @ matrices[3]])
    assert len(requested)
    return global_value, np.asarray(local, dtype=np.float64)

def save_cache(sequence, requested, matrices):
    path = cache_path(sequence); sidecar = path.with_suffix('.json')
    if path.exists():
        assert sidecar.exists(), 'Preserve orphan cache; no retroactive birth digest'
        validate(path, sequence, requested)
        return path
    assert not sidecar.exists(), 'Preserve orphan creation receipt'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.pending')
    assert not temporary.exists(), 'Preserve partial cache and report interrupted write'
    global_value, local = score(sequence, requested, matrices)
    with temporary.open('xb') as stream:
        np.savez_compressed(stream, **{'sequence': sequence, 'sequence_sha256': sequence_hash(sequence),
            'requests_sha256': request_hash(requested), 'spec_sha256': spec_hash(),
            'keys': np.asarray([positions_key(value) for value in requested]), 'global': global_value, 'local': local})
        stream.flush(); os.fsync(stream.fileno())
    creation = {**creation_identity(sequence, requested), 'cache_sha256': sha256(temporary)}
    validate(temporary, sequence, requested, creation)
    temporary.rename(path); jsave(sidecar, creation); validate(path, sequence, requested)
    return path

def run():
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1'
    production_check(); runtime_check()
    assert not (OUT / 'joint_production_receipt.json').exists(), 'Preserve completed production'
    original, encoded = sequence_frames(); roster, row_positions = requests(encoded)
    assert len(roster) == 18220 and len(row_positions) == 26258
    plan = readj(ART / 'sequence_request_manifest.json')
    assert plan['original_metadata_sha256'] == metadata_identity(original) and plan['encoded_metadata_sha256'] == metadata_identity(encoded)
    assert plan['requests'] == {sequence_hash(sequence): request_hash(requested) for sequence, requested in roster.items()}
    matrices = load_projections(); entries = []; start = time.perf_counter()
    for index, sequence in enumerate(sorted(roster, key=lambda value: (-len(value), sequence_hash(value)))):
        path = save_cache(sequence, roster[sequence], matrices)
        entries.append({'sequence_sha256': sequence_hash(sequence), 'request_sha256': request_hash(roster[sequence]),
            'length': len(sequence), 'path': path.relative_to(ROOT).as_posix(), 'sha256': sha256(path),
            'creation_path': path.with_suffix('.json').relative_to(ROOT).as_posix(), 'creation_sha256': sha256(path.with_suffix('.json'))})
        if (index + 1) % 250 == 0:
            print('joint accessibility', index + 1, '/', len(roster), 'elapsed seconds', round(time.perf_counter() - start, 1), flush=True)
    jsave(ART / 'joint_cache_index.json', {'alleles': entries, 'spec_sha256': spec_hash(),
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json')})
    jsave(OUT / 'joint_production_receipt.json', {'status': 'PASS', 'alleles': 18220, 'rows': 26258,
        'elapsed_seconds': time.perf_counter() - start, 'threads': 1, 'project_outcomes_read': False,
        'cache_index_sha256': sha256(ART / 'joint_cache_index.json'), 'immutable_creation_hashes': True,
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'original_metadata_sha256': metadata_identity(original), 'encoded_metadata_sha256': metadata_identity(encoded),
        'spec_sha256': spec_hash(), 'runtime_binding_sha256': sha256(OUT / 'runtime_binding_receipt.json'),
        'projection_receipt_sha256': sha256(RBP_OUT / 'projection_receipt.json')})

if __name__ == '__main__':
    run()
