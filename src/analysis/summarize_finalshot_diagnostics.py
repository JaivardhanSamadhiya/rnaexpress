"""Summarize completed controls, directional bands, and RBP group stability."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.analysis.summarize_finalshot_controls import assemble_control, context_summary
from src.analysis.summarize_finalshot_direct_models import aggregate
from src.analysis.analyze_finalshot_grouped_gates import add_metrics
from src.modeling.v4_phaseB2_context import edit_band

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'
BASE = 'M0_geometry'
FULL = 'M1_M2_M3_nested_selected'
GZIP = {'method': 'gzip', 'mtime': 0}


def paired_source(frame: pd.DataFrame, predictions: pd.DataFrame, label: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    sets = pd.concat([add_metrics(frame, predictions[m].to_numpy(float), m, label)
                      for m in (BASE, FULL)], ignore_index=True)
    _, source = aggregate(sets)
    paired = source[source.model.eq(FULL)].merge(source[source.model.eq(BASE)],
        on=['dataset', 'requested_direction'], suffixes=('_full', '_base'), validate='one_to_one')
    paired['rank_context_value'] = paired.directional_rank_percentile_full - paired.directional_rank_percentile_base
    paired['regret_context_value'] = paired.normalized_regret_base - paired.normalized_regret_full
    paired['diagnostic'] = label
    return paired


def main() -> None:
    rows = pd.read_csv(ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz')
    pred = pd.read_csv(OUT / 'm0_m3_predictions.csv.gz')
    keys = ['dataset', 'candidate_id', 'decision_set_id', 'biological_unit', 'biological_fold', 'feature_row']
    assert rows[keys].astype(str).equals(pred[keys].astype(str))
    eligible, score, selected = assemble_control('parent_binding_knockout', rows)
    assert eligible.all()
    sets, context = context_summary(rows, pred[BASE].to_numpy(float), score,
                                   'parent_knockout_nested', 'parent_binding_knockout')
    _, observed = context_summary(rows, pred[BASE].to_numpy(float), pred[FULL].to_numpy(float),
                                 'observed_nested', 'parent_binding_knockout')
    summary = {'control': 'parent_binding_knockout', 'rows': len(rows),
               'selected_families': selected,
               'observed_rank_gain': float(observed.rank_context_value.mean()),
               'observed_regret_gain': float(observed.regret_context_value.mean()),
               'knockout_rank_gain': float(context.rank_context_value.mean()),
               'knockout_regret_gain': float(context.regret_context_value.mean()),
               'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    (OUT / 'parent_binding_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    sets.to_csv(OUT / 'parent_binding_set_metrics.csv.gz', index=False, compression=GZIP)
    context.to_csv(OUT / 'parent_binding_context_values.csv', index=False)
    bands = edit_band(rows.edit_cost)
    diagnostics = []
    for name in ['1', '2-5', '6-10', '2-10', '11-25', '26-50', '>50']:
        mask = bands.isin(['2-5', '6-10']) if name == '2-10' else bands.eq(name)
        diagnostics.append(paired_source(rows.loc[mask].reset_index(drop=True),
                           pred.loc[mask].reset_index(drop=True), f'band:{name}'))
    # Source-defined classes and motif labels are descriptive, never selected
    # using observed gains. All available groups are reported.
    for source in ('tdp43_gse288185', 'moffatt_gse334718'):
        for cls in sorted(rows.loc[rows.dataset.eq(source), 'intervention_class'].unique()):
            mask = rows.dataset.eq(source) & rows.intervention_class.eq(cls)
            diagnostics.append(paired_source(rows.loc[mask].reset_index(drop=True),
                               pred.loc[mask].reset_index(drop=True), f'class:{cls}'))
        for band in ['1', '2-5', '6-10', '11-25', '26-50', '>50']:
            for cls in sorted(rows.loc[rows.dataset.eq(source), 'intervention_class'].unique()):
                mask = rows.dataset.eq(source) & rows.intervention_class.eq(cls) & bands.eq(band)
                if mask.any():
                    diagnostics.append(paired_source(rows.loc[mask].reset_index(drop=True),
                        pred.loc[mask].reset_index(drop=True), f'class_band:{cls}:{band}'))
    pd.concat(diagnostics, ignore_index=True).to_csv(OUT / 'directional_source_diagnostics.csv', index=False)
    dictionary = pd.read_csv(OUT / 'rbp_feature_dictionary.csv')
    rbps = dictionary.drop_duplicates('group_index').sort_values('group_index').human_rbp.tolist()
    group_records = []
    for family in ('M1', 'M2', 'M3'):
        for fold in range(5):
            if family == 'M3':
                paths = sorted((ROOT / f'data/interim/finalshot_m3_cache/outer{fold}').glob('refit_*.npz'))
                assert len(paths) == 3
            else:
                paths = [OUT / f'nested_direct/{family}_outer_fold_{fold}.npz']
            for path in paths:
                with np.load(path, allow_pickle=False) as a:
                    norms = a['group_norms']
                    meta = json.loads(str(a['metadata_json'].item()))
                assert len(norms) == 103
                for rbp, norm in zip(rbps, norms):
                    group_records.append({'family': family, 'outer_fold': fold,
                                          'seed': meta.get('seed', 42017), 'human_rbp': rbp,
                                          'norm': float(norm), 'nonzero': bool(norm > 0)})
    groups = pd.DataFrame(group_records)
    groups.to_csv(OUT / 'rbp_group_fold_norms.csv', index=False)
    fold_groups = groups.groupby(['family', 'outer_fold', 'human_rbp']).agg(
        norm=('norm', 'median'), selected=('nonzero', 'all')).reset_index()
    stability = fold_groups.groupby(['family', 'human_rbp']).agg(
        selected_folds=('selected', 'sum'), selection_fraction=('selected', 'mean'),
        median_norm=('norm', 'median')).reset_index()
    stability['stable_at_least_three_folds'] = stability.selected_folds.ge(3)
    stability.to_csv(OUT / 'rbp_group_stability.csv', index=False)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
