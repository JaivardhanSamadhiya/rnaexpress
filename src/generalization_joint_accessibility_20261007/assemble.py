"""Hash-verified joint matrix assembly with byte-identical frozen controls."""
from .common import *
from .production import requests, validate, positions_key, sequence_hash

def validate_control_reference(reference, actual):
    assert reference['status'] == 'FROZEN_PREFIT'
    required = {(RBP_OUT / 'prepare_receipt.json').relative_to(ROOT).as_posix()}
    required |= {(RBP_ART / (track + '_model_features.npz')).relative_to(ROOT).as_posix() for track in CONTROLS}
    assert set(actual) == required
    for name, expected in actual.items():
        assert reference['files'][name] == expected, 'Original control freeze byte mismatch: ' + name

def source_controls():
    manifest_path = RBP_OUT / 'prefit_manifest.json'; committed(manifest_path)
    reference = readj(manifest_path); prepared = readj(RBP_OUT / 'prepare_receipt.json')
    assert prepared['status'] == 'PASS'
    actual = {(RBP_OUT / 'prepare_receipt.json').relative_to(ROOT).as_posix(): sha256(RBP_OUT / 'prepare_receipt.json')}
    paths = {}
    for track in CONTROLS:
        path = RBP_ART / (track + '_model_features.npz'); name = path.relative_to(ROOT).as_posix()
        actual[name] = sha256(path); assert actual[name] == prepared['files'][name]; paths[track] = path
    validate_control_reference(reference, actual)
    previous = pd.read_csv(RBP_ART / 'model_row_index.csv.gz', usecols=IDENTITY, low_memory=False)[IDENTITY]
    rows = pd.read_csv(OUT / 'row_index.csv.gz', usecols=IDENTITY, low_memory=False)[IDENTITY]
    assert sha256(RBP_ART / 'model_row_index.csv.gz') == reference['files'][(RBP_ART / 'model_row_index.csv.gz').relative_to(ROOT).as_posix()]
    pd.testing.assert_frame_equal(previous, rows)
    return paths

def checked_block(path, digest, columns):
    assert sha256(path) == digest
    with np.load(path, allow_pickle=False) as data:
        assert data.files == ['features']; value = data['features'].copy()
    assert value.shape == (26258, columns) and np.isfinite(value).all()
    return value

def run():
    production_check(); assert not (OUT / 'input_receipt.json').exists()
    assert not any((OUT / track / 'fits').exists() for track in TRACKS)
    original, encoded = sequence_frames(); roster, positions = requests(encoded)
    receipt = readj(OUT / 'joint_production_receipt.json')
    assert receipt['status'] == 'PASS' and receipt['production_manifest_sha256'] == sha256(OUT / 'feature_production_manifest.json')
    assert receipt['original_metadata_sha256'] == metadata_identity(original) and receipt['encoded_metadata_sha256'] == metadata_identity(encoded)
    index_path = ART / 'joint_cache_index.json'; assert sha256(index_path) == receipt['cache_index_sha256']
    entries = readj(index_path)['alleles']; assert len(entries) == len(roster) == 18220
    lookup = {entry['sequence_sha256']: entry for entry in entries}
    assert len(lookup) == len(roster) and set(lookup) == {sequence_hash(value) for value in roster}
    cache = {}
    for sequence, requested in roster.items():
        entry = lookup[sequence_hash(sequence)]
        assert sha256(ROOT / entry['path']) == entry['sha256']
        assert sha256(ROOT / entry['creation_path']) == entry['creation_sha256']
        cache[sequence] = validate(ROOT / entry['path'], sequence, requested)
    joint = np.empty((26258, 256), dtype=np.float32)
    for i, (parent, mutant, sites) in enumerate(zip(encoded.parent_sequence, encoded.mutant_sequence, positions)):
        left, right = cache[parent], cache[mutant]; key = positions_key(sites)
        joint[i] = np.r_[right[0] - left[0], right[1][key] - left[1][key]]
    assert np.isfinite(joint).all(); del cache
    paths = source_controls(); access = checked_block(paths['access'], sha256(paths['access']), 758)
    base = checked_block(paths['base'], sha256(paths['base']), 246); raw = checked_block(paths['raw'], sha256(paths['raw']), 502)
    np.testing.assert_array_equal(access[:, :502], raw); np.testing.assert_array_equal(raw[:, :246], base)
    marginal = access[:, 502:758]
    matrixsave(ART / 'joint_projected_delta.npz', joint)
    for track, value in [('duplicate_marginal', np.column_stack((access, marginal))), ('joint', np.column_stack((access, joint)))]:
        path = ART / (track + '_model_features.npz'); matrixsave(path, value); paths[track] = path
    files = {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths.values()}
    files[(ART / 'joint_projected_delta.npz').relative_to(ROOT).as_posix()] = sha256(ART / 'joint_projected_delta.npz')
    files[(OUT / 'row_index.csv.gz').relative_to(ROOT).as_posix()] = sha256(OUT / 'row_index.csv.gz')
    jsave(OUT / 'input_receipt.json', {'status': 'PASS', 'rows': 26258, 'shapes': SHAPES, 'files': files,
        'feature_paths': {track: path.relative_to(ROOT).as_posix() for track, path in paths.items()},
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'joint_production_receipt_sha256': sha256(OUT / 'joint_production_receipt.json'),
        'cache_index_sha256': sha256(index_path), 'creation_digests_checked': 18220,
        'source_control_prefit_sha256': sha256(RBP_OUT / 'prefit_manifest.json'),
        'original_metadata_sha256': metadata_identity(original), 'encoded_metadata_sha256': metadata_identity(encoded),
        'outcomes_used_for_features': False, 'all_controls_byte_identical_to_prior_prefit': True})

if __name__ == '__main__':
    run()
