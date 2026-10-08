"""Future root-gated metadata/array preparation; no fitting entry point."""
from .common import *
from . import spec as s
from . import contracts as independent
import gzip
import io
import sys


def runtime():
    # Preserve the original fitter's bootstrap import BEFORE NumPy/pandas.
    from src.generalization_crosscell_20261007 import common as old
    return old.np, old.pd, old


def metadata(root_start=False):
    preparation_check(root_start)
    assert not (OUT / 'metadata_receipt.json').exists()
    np, pd, old = runtime()
    from src.generalization_crosscell_20261007.splits import outer_masks, inner_masks
    from src.generalization_knowncell_20261007.splits import masks, exact_menu_pairs
    from src.generalization_joint_accessibility_20261007.common import certified_core
    assert old.META == s.META and old.TASKS == s.TASKS and old.FOLDS == s.FOLDS
    assert str(certified_core().resolve()) == str(old.CORE.resolve())
    frame, _ = old.load(False)
    assert len(frame) == s.ROWS and not any('delta' in name for name in frame.columns)
    rows = frame.to_dict('records'); audit = []
    for task in s.TASKS:
        for fold in s.FOLDS:
            train, test = outer_masks(frame, task, fold)
            a, b = independent.outer(rows, task, fold)
            assert train.tolist() == a and test.tolist() == b
            source = frame.loc[train].reset_index(drop=True)
            source_rows = source.to_dict('records')
            inner_roster = []
            for held in sorted(source.held_parent_fold.unique()):
                it, iv = inner_masks(source, int(held)); x, y = independent.inner(source_rows, int(held))
                assert it.tolist() == x and iv.tolist() == y
                inner_roster.append({'fold': int(held), 'training_ids': independent.ids(source_rows, x),
                                     'validation_ids': independent.ids(source_rows, y)})
            known_task = next(k for k, v in s.KNOWN_TASKS.items() if v[1] == task)
            kt, ka, ko = masks(frame, known_task, fold)
            ia, ib, ic = independent.known(rows, known_task, fold)
            assert kt.tolist() == ia == a and ka.tolist() == ib and ko.tolist() == ic == b
            audit.append({'task': task, 'fold': fold, 'training_ids': independent.ids(rows, a),
                          'crossed_target_ids': independent.ids(rows, b),
                          'known_target_ids': independent.ids(rows, ib), 'inner': inner_roster})
    pairs, excluded = exact_menu_pairs(frame)
    assert len(pairs) == 2408
    payload = frame.to_csv(index=False, lineterminator='\n').encode()
    save(OUT / 'row_index.csv.gz', gzip.compress(payload, mtime=0))
    jsave(OUT / 'split_roster.json', audit)
    jsave(OUT / 'paired_menu_metadata.json', {'pairs': pairs, 'excluded': excluded})
    jsave(OUT / 'metadata_receipt.json', {'status': 'PASS', 'rows': s.ROWS, 'components': s.COMPONENTS,
        'core_sha256': sha256(old.CORE), 'preparation_manifest_sha256': sha256(PREP),
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in
                  (OUT / 'row_index.csv.gz', OUT / 'split_roster.json', OUT / 'paired_menu_metadata.json')},
        'all_original_crosscell_masks_exactly_replayed': True,
        'same_cell_no_refit_safety_verified': True, 'whole_menus_preserved': True,
        'outcome_columns_read': False, 'arrays_read': False, 'models_read': False, 'fits': 0})


def expected_manifest(path, expected_status):
    committed(path); value = readj(path)
    assert value['status'] == expected_status
    return value


def matrices(root_start=False):
    preparation_check(root_start)
    assert not (OUT / 'array_receipt.json').exists()
    metadata_receipt = readj(OUT / 'metadata_receipt.json')
    assert metadata_receipt['status'] == 'PASS' and metadata_receipt['preparation_manifest_sha256'] == sha256(PREP)
    for name, expected in metadata_receipt['files'].items():
        assert sha256(ROOT / name) == expected, name
    np, pd, old = runtime()
    frame, _ = old.load(False)
    assert sha256(old.CORE) == metadata_receipt['core_sha256']
    pd.testing.assert_frame_equal(frame, pd.read_csv(OUT / 'row_index.csv.gz', low_memory=False))
    # Exact committed source manifests, not merely current internally-consistent receipts.
    original = expected_manifest(old.OUT / 'prefit_manifest.json', 'FROZEN_PREFIT')
    assert sha256(old.CORE) == original['files'][old.CORE.relative_to(ROOT).as_posix()]
    rbp_out = ROOT / 'results/generalization_rbp_20261007'
    rbp = expected_manifest(rbp_out / 'prefit_manifest.json', 'FROZEN_PREFIT')
    joint_out = ROOT / 'results/generalization_joint_accessibility_20261007'
    joint = expected_manifest(joint_out / 'prefit_manifest.json', 'FROZEN_JOINT_ACCESSIBILITY_PREFIT')
    source = readj(joint_out / 'input_receipt.json')
    assert source['status'] == 'PASS' and source['rows'] == s.CORE_ROWS
    assert sha256(joint_out / 'input_receipt.json') == joint['files'][(joint_out / 'input_receipt.json').relative_to(ROOT).as_posix()]
    for track in ('base', 'raw', 'access'):
        name = source['feature_paths'][track]
        assert source['files'][name] == rbp['files'][name] == joint['files'][name]
    base = None; paths = {}; hashes = {}; source_files = {}
    for track in s.TRACKS:
        if track in s.REUSED_CONTROLS:
            path = old.ART / (track + '_model_features.npz')
            name = path.relative_to(ROOT).as_posix(); expected = original['files'][name]
            assert sha256(path) == expected
            with np.load(path, allow_pickle=False) as data:
                assert data.files == ['features']; value = np.asarray(data['features'], dtype=float)
            assert value.shape == (s.ROWS, s.WIDTHS[track]) and np.isfinite(value).all()
            if track == 'base': base = value.copy()
            paths[track] = name; source_files[name] = expected
        else:
            path = ROOT / source['feature_paths'][track]
            name = path.relative_to(ROOT).as_posix()
            assert sha256(path) == source['files'][name] == joint['files'][name]
            with np.load(path, allow_pickle=False) as data:
                assert data.files == ['features']; full = data['features']
                assert full.shape == (s.CORE_ROWS, s.WIDTHS[track]) and np.isfinite(full).all()
                value = np.asarray(full[frame.original_core_row.to_numpy(int)], dtype=float)
            assert base is not None
            independent.byte_equality(np.ascontiguousarray(value[:, :246], dtype='<f8').tobytes(),
                                      np.ascontiguousarray(base, dtype='<f8').tobytes(), track + ' base246')
            buffer = io.BytesIO(); np.savez_compressed(buffer, features=value)
            new = ART / (track + '_model_features.npz'); save(new, buffer.getvalue())
            paths[track] = new.relative_to(ROOT).as_posix(); source_files[name] = sha256(path)
        hashes[track] = hashlib.sha256(np.ascontiguousarray(value, dtype='<f8').tobytes()).hexdigest()
        if track == 'simple': simple = value.copy()
        if track == 'base':
            independent.byte_equality(np.ascontiguousarray(simple, dtype='<f8').tobytes(),
                                      np.ascontiguousarray(base[:, :102], dtype='<f8').tobytes(), 'simple102 exact base prefix')
        del value
    # The full source inventories are pinned by their committed source freezes;
    # confirm SAME original metadata/order before admitting sliced feature bytes.
    original_rows = pd.read_csv(ROOT / 'artifacts/generalization_rbp_20261007/model_row_index.csv.gz', usecols=s.IDENTITY, low_memory=False)[s.IDENTITY]
    joint_rows = pd.read_csv(joint_out / 'row_index.csv.gz', usecols=s.IDENTITY, low_memory=False)[s.IDENTITY]
    for path, manifest in ((ROOT / 'artifacts/generalization_rbp_20261007/model_row_index.csv.gz', rbp),
                           (joint_out / 'row_index.csv.gz', joint)):
        assert sha256(path) == manifest['files'][path.relative_to(ROOT).as_posix()]
    pd.testing.assert_frame_equal(original_rows, joint_rows)
    pd.testing.assert_frame_equal(frame[s.IDENTITY].reset_index(drop=True), original_rows.iloc[frame.original_core_row.to_numpy(int)].reset_index(drop=True))
    jsave(OUT / 'array_receipt.json', {'status': 'PASS', 'rows': s.ROWS, 'widths': s.WIDTHS,
        'feature_paths': paths, 'parsed_float64_matrix_sha256': hashes,
        'files': {name: sha256(ROOT / name) for name in paths.values()},
        'source_array_files': source_files,
        'original_crosscell_prefit_sha256': sha256(old.OUT / 'prefit_manifest.json'),
        'RBP_prefit_sha256': sha256(rbp_out / 'prefit_manifest.json'),
        'joint_prefit_sha256': sha256(joint_out / 'prefit_manifest.json'),
        'metadata_receipt_sha256': sha256(OUT / 'metadata_receipt.json'),
        'preparation_manifest_sha256': sha256(PREP), 'base_simple_exact_bytes': True,
        'every_new_track_has_exact_original_base_prefix': True,
        'models_read': False, 'outcome_columns_read': False, 'fits': 0,
        'control_checkpoint_reuse_not_yet_admitted': True})


if __name__ == '__main__':
    commands = {'metadata': metadata, 'matrices': matrices}
    commands[sys.argv[1]]('--root-start' in sys.argv[2:])
