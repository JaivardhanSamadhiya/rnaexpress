"""Prepare identical, outcome-independent inputs; never fit a biological model."""
from .common import *
from .routes import build_features, endpoint_sign, CONFIGS, ENDPOINT_SIGNS


def run():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT / track / 'fits').exists() for track in TRACKS)
    previous = ROOT / 'results/generalization_next_20261007/short_feature_receipt.json'
    receipt = readj(previous)
    assert receipt['status'] == 'PASS' and receipt['rows'] == 26258
    assert receipt['columns'] == 246 and receipt['original_alleles_retained_for_purge']
    assert sha256(BASE) == receipt['files'][BASE.relative_to(ROOT).as_posix()]
    frame, _ = load()
    row_hash = hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    assert row_hash == receipt['row_ids_sha256'], 'Corrected baseline row mapping'
    with np.load(BASE) as archive:
        base = archive['features'].astype(float)
    matrix = build_features(frame, base)
    np.testing.assert_array_equal(matrix[:,:246],base)
    matrixsave(ART / 'shared_model_features.npz', matrix)
    index = frame[['intervention_id','dataset','parent_context_id','biological_component',
                   'endpoint_class','parent_sequence','mutant_sequence']].copy()
    index['routing_sign'] = endpoint_sign(frame)
    csvsave(OUT/'row_index.csv.gz', index, True)
    jsave(OUT/'experiment_config.json', {'tracks':TRACKS,'configurations':CONFIGS,
        'endpoint_signs':ENDPOINT_SIGNS,'rows':len(frame),'columns':247,
        'fitted_columns':246,'numerical_threads':1,'checkpoint_count':80,
        'source_only_selection':True,'sign_selection_from_outcomes':False,
        'independent_confirmation':False,'auxiliary_rows':0})
    jsave(OUT/'prepare_receipt.json', {'status':'PASS','rows':len(frame),'shape':list(matrix.shape),
        'base_path':BASE.relative_to(ROOT).as_posix(),'base_sha256':sha256(BASE),
        'shared_features_sha256':sha256(ART/'shared_model_features.npz'),
        'row_ids_sha256':row_hash,'core_sha256':sha256(CORE),
        'endpoint_rows':frame.groupby('endpoint_class').size().to_dict(),
        'endpoint_sign_is_not_fitted':True,'metadata_unchanged':True,
        'source_outcomes_used_for_features':False,'new_outcomes_opened':False,
        'rows_added_or_removed':0,'fits_started':False})
    print('Prepared identical',matrix.shape,'inputs for both tracks; no fits',flush=True)


if __name__ == '__main__': run()
