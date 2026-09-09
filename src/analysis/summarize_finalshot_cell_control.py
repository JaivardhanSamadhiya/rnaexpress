"""Finalize the cell-vector swap after all nested folds finish, without fitting."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.run_finalshot_direct_models import sha256
from src.analysis.summarize_finalshot_controls import load_archive, context_summary
from src.analysis.summarize_finalshot_direct_models import inner_summary
from src.analysis.summarize_finalshot_m3 import choose_final_family, selected_m3_grid

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'
CONTROL = 'cell_context_permutation'


def verify_row_hashes(family, metadata, expected_hash):
    if family == 'M3':
        records = metadata['seed_refits']
        assert {row['seed'] for row in records} == {17, 41, 89} and len(records) == 3
        records = records + [audit for grid in metadata['inner_grid'] for audit in grid['seed_fit_audits']]
        assert all(row['rows_sha256'] == expected_hash for row in records)
        assert all(row['unit_overlap'] == 0 for row in records)
    else:
        assert metadata.get('rows_sha256', metadata.get('input_hashes', {}).get('rows')) == expected_hash


def main():
    rows_path = ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz'
    rows = pd.read_csv(rows_path)
    primary = pd.read_csv(OUT / 'm0_m3_predictions.csv.gz')
    keys = ['dataset', 'candidate_id', 'decision_set_id', 'biological_unit', 'biological_fold', 'feature_row']
    assert rows[keys].astype(str).equals(primary[keys].astype(str))
    predictions = {k: np.full(len(rows), np.nan) for k in ('M1', 'M2', 'M3', 'nested')}
    selection, audits = [], []
    for fold in range(5):
        paths = {'M1': OUT / f'nested_direct/M1_outer_fold_{fold}.npz',
                 'M2': OUT / f'nested_controls_direct/{CONTROL}/M2_outer_fold_{fold}.npz',
                 'M3': OUT / f'nested_controls_m3/{CONTROL}/M3_outer_fold_{fold}.npz'}
        if not all(path.exists() for path in paths.values()):
            raise RuntimeError(f'Cell control fold {fold} is incomplete; no partial summary written')
        loaded = {name: load_archive(path) for name, path in paths.items()}
        expected = np.flatnonzero(rows.biological_fold.to_numpy() == fold)
        for name, (idx, pred, meta) in loaded.items():
            assert np.array_equal(idx, expected)
            assert meta['outer_fold'] == fold
            verify_row_hashes(name, meta, sha256(rows_path))
            if name != 'M1':
                assert meta['control'] == CONTROL
            predictions[name][idx] = pred
            audits.append({'family': name, 'fold': fold, 'path': paths[name].relative_to(ROOT).as_posix(),
                           'sha256': sha256(paths[name]), 'rows': len(idx)})
        candidates = {name: selected_m3_grid(loaded[name][2]) if name == 'M3' else inner_summary(loaded[name][2])
                      for name in loaded}
        chosen = choose_final_family(candidates)
        selection.append(chosen)
        predictions['nested'][expected] = loaded[chosen][1]
    assert all(np.isfinite(values).all() for values in predictions.values())
    sets, contexts = [], []
    for name, pred in predictions.items():
        table, context = context_summary(rows, primary.M0_geometry.to_numpy(), pred,
                                        f'cell_swap_{name}', CONTROL)
        sets.append(table)
        contexts.append(context)
    context = pd.concat(contexts, ignore_index=True)
    means = context.groupby('model')[['rank_context_value', 'regret_context_value']].mean().reset_index()
    summary = {'control': CONTROL, 'rows': len(rows), 'selected_families': selection,
        'M1_reused_unchanged': True, 'reason': 'M1 has no expression features, so this control is the identity transformation for M1.',
        'metrics': means.to_dict('records'), 'archive_audit': audits,
        'note': 'Descriptive required control; Gate H is assessed by the separate trans-knockout transfer test.',
        'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    pd.concat(sets, ignore_index=True).to_csv(OUT / 'cell_context_control_set_metrics.csv.gz', index=False,
        compression={'method': 'gzip', 'mtime': 0})
    context.to_csv(OUT / 'cell_context_control_context_values.csv', index=False)
    (OUT / 'cell_context_control_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
