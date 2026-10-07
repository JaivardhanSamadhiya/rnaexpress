"""Metadata and runtime preparation; reuse matrices only after linear freeze."""
import sys
from .common import *
from .splits import outer_masks, inner_masks
from .routes import runtime_binding, CONFIGS, FIXED
from .ridge import CONFIGS as RIDGE_CONFIGS


def metadata():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT/track/'fits').exists() for track in TRACKS)
    frame, _ = load(False)
    csvsave(OUT/'row_index.csv.gz', frame, True)
    counts = []
    for task in TASKS:
        for fold in FOLDS:
            train, test = outer_masks(frame, task, fold)
            source = frame.loc[train].reset_index(drop=True)
            for inner in sorted(source.held_parent_fold.unique()): inner_masks(source, int(inner))
            counts.append({'task': task, 'fold': fold, 'source_rows': int(train.sum()),
                           'target_rows': int(test.sum()), 'source_components': source.biological_component.nunique(),
                           'target_components': frame.loc[test].biological_component.nunique()})
    csvsave(OUT/'metadata_fold_audit.csv', pd.DataFrame(counts))
    jsave(OUT/'runtime_binding.json', runtime_binding())
    jsave(OUT/'metadata_receipt_v2.json', {'status': 'PASS', 'rows': len(frame), 'components': 187,
        'core_sha256': sha256(CORE), 'row_ids_sha256': hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'tracks': TRACKS, 'widths': WIDTHS, 'hgb_configurations': CONFIGS, 'ridge_configurations':RIDGE_CONFIGS,'fixed_parameters': FIXED,
        'outcome_columns_read': False, 'estimator_fits': 0, 'new_features_extracted': 0,
        'original_alleles_retained': True, 'exact_linear_masks_reused': True})
    print('Nonlinear metadata/runtime preparation PASS; no estimator fits', flush=True)


def matrices():
    metadata()
    manifest_path = LINEAR_OUT/'prefit_manifest.json'
    committed = subprocess.check_output(['git','show','HEAD:'+manifest_path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert committed == manifest_path.read_bytes(), 'Root must commit linear cross-cell freeze first'
    manifest = readj(manifest_path)
    assert manifest['status'] == 'FROZEN_PREFIT'
    for name, expected in manifest['files'].items(): assert sha256(ROOT/name) == expected, name
    prepared = readj(LINEAR_OUT/'prepare_receipt.json'); assert prepared['status'] == 'PASS'
    frame, _ = load(False)
    ids = hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    assert prepared['row_ids_sha256'] == ids
    paths = {track: FEATURE_ART/(track+'_model_features.npz') for track in FEATURE_TRACKS}
    base = None
    for track, path in paths.items():
        assert sha256(path) == manifest['files'][path.relative_to(ROOT).as_posix()]
        with np.load(path) as archive: x = archive['features']
        assert x.shape == (13781, FEATURE_WIDTHS[track]) and np.isfinite(x).all()
        if track == 'simple': simple = x.copy()
        elif track == 'base':
            base = x.copy(); np.testing.assert_array_equal(simple, base[:,:102])
        else: np.testing.assert_array_equal(x[:,:246], base)
    jsave(OUT/'feature_admission_receipt.json', {'status': 'PASS', 'rows': len(frame), 'widths': WIDTHS,
        'row_ids_sha256': ids, 'linear_prefit_sha256': sha256(manifest_path),
        'feature_paths': {track: path.relative_to(ROOT).as_posix() for track,path in paths.items()},
        'feature_hashes': {track: sha256(path) for track,path in paths.items()},
        'same_immutable_arrays_reused': True, 'outcome_columns_read': False, 'estimator_fits': 0})
    print('Seven exact linear arrays admitted for future nonlinear fits; no fitting', flush=True)


if __name__ == '__main__': {'metadata': metadata, 'matrices': matrices}[sys.argv[1]]()
