"""Assemble fixed feature blocks after both outcome-free caches complete."""
from .common import *
from .route_structure import build_raw_features
from .structure_cache import build_features as build_structure

SHAPES = {'base':246, 'raw':251, 'structure':262, 'lookup':502, 'bert':502, 'combined':518}

def run():
    production_check()
    assert not any((OUT/t/'fits').exists() for t in TRACKS)
    frame, _ = load()
    with np.load(ART/'base_features.npz') as archive:
        base = archive['features'].astype(float)
    assert base.shape == (len(frame),246)
    assert readj(OUT/'structure_cache_production_receipt.json')['status'] == 'PASS'
    raw = build_raw_features(frame, base)
    structured = build_structure(frame, base)
    assert raw.shape == (len(frame),251) and structured.shape == (len(frame),262)
    np.testing.assert_array_equal(structured[:, :251], raw)
    bert_receipt = readj(OUT/'bert_features_receipt.json')
    assert bert_receipt['status'] == 'PASS'
    from .route_bert import row_identity
    assert bert_receipt['row_identity_sha256'] == row_identity(encoded_frame(frame))
    with np.load(ART/'bert_features.npz', allow_pickle=False) as archive:
        bert = archive['features'].astype(float)
    with np.load(ART/'lookup_features.npz', allow_pickle=False) as archive:
        lookup = archive['features'].astype(float)
    assert bert.shape == lookup.shape == (len(frame),256)
    matrices = {'base':base, 'raw':raw, 'structure':structured,
                'lookup':np.column_stack((base,lookup)), 'bert':np.column_stack((base,bert)),
                'combined':np.column_stack((structured,bert))}
    for track in TRACKS:
        matrix = matrices[track]
        assert matrix.shape == (len(frame),SHAPES[track]) and np.isfinite(matrix).all()
        path = ART/(track+'_model_features.npz')
        if path.exists():
            with np.load(path) as archive:
                np.testing.assert_array_equal(archive['features'],matrix)
        else:
            matrixsave(path,matrix)
        print('Assembled',track,matrix.shape,flush=True)
    csvsave(OUT/'row_index.csv.gz',frame[['intervention_id','dataset','parent_context_id','biological_component']],True)
    jsave(OUT/'prepare_receipt.json', {'status':'PASS', 'rows':len(frame), 'shapes':SHAPES,
        'row_ids_sha256':hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'source_only_sequence_features':True, 'reserved_outcomes_opened':False,
        'files':{(ART/(t+'_model_features.npz')).relative_to(ROOT).as_posix():sha256(ART/(t+'_model_features.npz')) for t in TRACKS},
        'production_manifest_sha256':sha256(OUT/'feature_production_manifest.json')})

if __name__ == '__main__': run()
