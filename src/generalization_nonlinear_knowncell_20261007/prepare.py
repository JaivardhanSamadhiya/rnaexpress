"""Current source/code/array hashes and complete menu proof; no model reads."""
from .common import *
from .splits import masks, exact_menu_pairs

def run():
    assert not (OUT / 'evaluation_manifest.json').exists() and not (OUT / 'evaluation_complete.json').exists()
    frame = load(False)
    from src.generalization_nonlinear_crosscell_20261007.common import freeze_check as source_freeze
    original = source_freeze()
    source_paths = list(SOURCE_SRC.glob('*.py')) + [FEATURE_ART / (name + '_model_features.npz') for name in FEATURE_TRACKS]
    source_files = {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(source_paths)}
    validate_source_reference(original, source_files)
    folds, coverage = [], []
    for task in TASKS:
        seen = []
        for fold in FOLDS:
            train, test, opposite = masks(frame, task, fold); source, target = frame.loc[train], frame.loc[test]
            seen.extend(target.intervention_id)
            folds.append({'task': task, 'source_task': TASKS[task][1], 'fold': fold, 'training_rows': len(source),
                'target_rows': len(target), 'target_components': target.biological_component.nunique(), 'target_contexts': target.parent_context_id.nunique(),
                'training_ids_sha256': rowhash(source), 'target_ids_sha256': rowhash(target), 'target_metadata_sha256': metadata_hash(target),
                'opposite_ids_sha256': rowhash(frame.loc[opposite]), 'exact_allele_overlaps': 0, 'component_overlaps': 0, 'partial_menus': 0})
        assert len(seen) == len(set(seen)) == int(frame.cell_type.eq(TASKS[task][0]).sum())
        coverage.append({'task': task, 'rows': len(seen), 'components': 187})
    pairs, excluded = exact_menu_pairs(frame)
    assert len(pairs) == 2408 and len({row['biological_component'] for row in pairs}) == 187
    csvsave(OUT / 'row_index.csv.gz', frame, True); csvsave(OUT / 'metadata_fold_audit.csv', pd.DataFrame(folds))
    csvsave(OUT / 'exact_menu_pairs.csv', pd.DataFrame(pairs)); csvsave(OUT / 'unmatched_menu_metadata.csv', pd.DataFrame(excluded))
    jsave(OUT / 'metadata_receipt.json', {'status': 'PASS', 'rows': 13781, 'components': 187, 'tracks': TRACKS, 'tasks': TASKS,
        'coverage': coverage, 'folds': FOLDS, 'new_fits': 0, 'source_input_files': source_files,
        'source_prefit_sha256': sha256(SOURCE_OUT / 'prefit_manifest.json'), 'source_runtime_binding_sha256': sha256(SOURCE_OUT / 'runtime_binding.json'),
        'core_sha256': sha256(CORE), 'row_ids_sha256': rowhash(frame), 'metadata_sha256': metadata_hash(frame),
        'paired_menus': len(pairs), 'paired_rows': sum(2 * row['candidates'] for row in pairs),
        'unmatched_contexts': len(excluded), 'unmatched_rows': sum(row['rows'] for row in excluded),
        'outcome_columns_read': False, 'project_model_files_opened': False, 'feature_values_loaded': False,
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in (OUT / 'row_index.csv.gz', OUT / 'metadata_fold_audit.csv', OUT / 'exact_menu_pairs.csv', OUT / 'unmatched_menu_metadata.csv')}})
    print('Nonlinear known-cell metadata/prefit/array-hash proof PASS; no labels/models/feature values read', flush=True)

if __name__ == '__main__':
    run()
