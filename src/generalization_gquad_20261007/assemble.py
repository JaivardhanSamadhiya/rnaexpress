"""Outcome-free 5-track inputs; reuse only byte-identical committed arrays."""
from .common import *
from .guards import source_control_paths, sequence_rows, metadata_digest, structure_index_check, resource_check
from .production import validate
from .spec import request_plan, positions_key, sequence_hash, request_hash, delta_blocks, spec_hash

def checked_block(path, digest, columns):
    assert sha256(path) == digest
    with np.load(path, allow_pickle=False) as data:
        assert data.files == ['features']; value = np.asarray(data['features'], dtype=np.float64)
    assert value.shape == (26258, columns) and np.isfinite(value).all()
    return value

def run():
    production_check(); source_paths = source_control_paths(); resource_check('assembly')
    assert not (OUT / 'input_receipt.json').exists() and not any((OUT / t / 'fits').exists() for t in TRACKS)
    original, encoded = sequence_rows(); roster, positions = request_plan(encoded)
    receipt = readj(OUT / 'features_receipt.json'); index_path = ART / 'cache_index.json'
    assert receipt['status'] == 'PASS' and receipt['production_manifest_sha256'] == sha256(OUT / 'feature_production_manifest.json')
    assert receipt['original_metadata_sha256'] == metadata_digest(original) and receipt['encoded_metadata_sha256'] == metadata_digest(encoded)
    assert receipt['cache_index_sha256'] == sha256(index_path) and receipt['spec_sha256'] == spec_hash()
    index = readj(index_path); entries = {e['sequence_sha256']: e for e in index['alleles']}
    assert len(entries) == 18220 and set(entries) == {sequence_hash(s) for s in roster}
    cache = {}
    for s, requested in roster.items():
        entry = entries[sequence_hash(s)]
        assert entry['request_sha256'] == request_hash(requested)
        assert sha256(ROOT / entry['path']) == entry['sha256'] and sha256(ROOT / entry['birth_path']) == entry['birth_sha256']
        value = validate(s, requested, ROOT / entry['path'])
        cache[s] = (value['global_raw'], dict(zip(value['keys'], value['local_raw'])), value['physics'])
    raw, physics = [], []
    for row, p in zip(encoded, positions):
        a, b = cache[row['parent_sequence']], cache[row['mutant_sequence']]; key = positions_key(p)
        r, v = delta_blocks(a[0], a[1][key], a[2], b[0], b[1][key], b[2]); raw.append(r); physics.append(v)
    raw, physics = np.asarray(raw, dtype=np.float64), np.asarray(physics, dtype=np.float64)
    assert raw.shape == (26258, 12) and physics.shape == (26258, 2) and np.isfinite(raw).all() and np.isfinite(physics).all()
    matrixsave(ART / 'raw_delta_block.npz', raw); matrixsave(ART / 'physics_delta_block.npz', physics)
    previous = readj(NEXT_OUT / 'prepare_receipt.json'); pins = canonical_map(previous['files'])
    base = checked_block(source_paths['base'], pins[source_paths['base'].relative_to(ROOT).as_posix()], 246)
    ordinary = checked_block(source_paths['structure'], pins[source_paths['structure'].relative_to(ROOT).as_posix()], 262)
    np.testing.assert_array_equal(base, ordinary[:, :246])
    paths = {'base': source_paths['base']}
    for track, blocks in [('raw', (base, raw)), ('ordinary_raw', (ordinary, raw)),
                          ('physical', (base, raw, physics)), ('combined', (ordinary, raw, physics))]:
        matrix = np.column_stack(blocks); assert matrix.shape == (26258, SHAPES[track])
        path = ART / (track + '_model_features.npz'); matrixsave(path, matrix); paths[track] = path
    pd.testing.assert_frame_equal(pd.read_csv(OUT / 'row_index.csv.gz')[IDENTITY], pd.DataFrame(original)[IDENTITY])
    structure = structure_index_check(True); assert structure == receipt['ordinary_structure_after']
    jsave(OUT / 'input_receipt.json', {'status': 'PASS', 'rows': 26258, 'shapes': SHAPES,
        'original_metadata_sha256': metadata_digest(original), 'encoded_metadata_sha256': metadata_digest(encoded),
        'row_index_sha256': sha256(OUT / 'row_index.csv.gz'), 'features_receipt_sha256': sha256(OUT / 'features_receipt.json'),
        'production_manifest_sha256': sha256(OUT / 'feature_production_manifest.json'),
        'source_control_prefit_manifest_sha256': sha256(NEXT_OUT / 'prefit_manifest.json'),
        'feature_paths': {t: p.relative_to(ROOT).as_posix() for t, p in paths.items()},
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in list(paths.values()) + [ART / 'raw_delta_block.npz', ART / 'physics_delta_block.npz']},
        'ordinary_structure_rehashed_unchanged': structure, 'outcomes_read': False, 'models_fit': 0})

if __name__ == '__main__':
    run()
