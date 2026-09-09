"""Descriptive exact-geometry TDP identifiability check; no fitted model or gate."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.summarize_finalshot_diagnostics import paired_source
from src.modeling.v4_decision_models import geometry_features

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'


def exact_geometry_keys(features):
    return [hashlib.sha256(np.ascontiguousarray(row, dtype='<f4').tobytes()).hexdigest() for row in features]


def main():
    rows = pd.read_csv(ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz')
    predictions = pd.read_csv(OUT / 'm0_m3_predictions.csv.gz')
    keys = ['dataset', 'candidate_id', 'decision_set_id', 'biological_unit', 'biological_fold', 'feature_row']
    assert rows[keys].astype(str).equals(predictions[keys].astype(str))
    mask = rows.dataset.eq('tdp43_gse288185')
    frame = rows.loc[mask].reset_index(drop=True)
    pred = predictions.loc[mask].reset_index(drop=True)
    geometry = geometry_features(frame, categories=True)
    frame['geometry_hash'] = exact_geometry_keys(geometry)
    frame['original_decision_set_id'] = frame.decision_set_id
    frame['decision_set_id'] = frame.decision_set_id + '||geometry:' + frame.geometry_hash
    size = frame.groupby('decision_set_id').candidate_id.transform('size')
    eligible = size.ge(2)
    summary = {'status': 'descriptive; exact matching convention implemented September 9, not a new gate',
        'source_rows': len(frame), 'geometry_columns': geometry.shape[1],
        'matching': 'Bitwise equality of all 28 frozen geometry features within existing decision sets; minimum two candidates for ranking.',
        'eligible_rows_before_outcome_variation_check': int(eligible.sum()),
        'eligible_sets_before_outcome_variation_check': int(frame.loc[eligible].decision_set_id.nunique()),
        'eligible_units_before_outcome_variation_check': int(frame.loc[eligible].biological_unit.nunique()),
        'motif_labels': sorted(frame.motif_family.unique().tolist()),
        'TARDBP_checkpoint_available': False, 'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    frame[['candidate_id', 'biological_unit', 'original_decision_set_id', 'geometry_hash']].assign(
        candidate_count_in_exact_geometry_set=size, eligible=eligible).to_csv(OUT / 'tdp_exact_geometry_audit.csv', index=False)
    varying = frame.groupby('decision_set_id').localization_effect.transform('nunique').ge(2)
    usable = eligible & varying
    summary['usable_rows'] = int(usable.sum())
    if usable.any():
        result = paired_source(frame.loc[usable].reset_index(drop=True),
                               pred.loc[usable].reset_index(drop=True), 'TDP_exact_geometry_descriptive')
        summary['metrics'] = result[['dataset', 'requested_direction', 'biological_units_full',
            'decision_sets_full', 'rank_context_value', 'regret_context_value']].to_dict('records')
    else:
        summary['metrics'] = []
        summary['interpretation'] = 'No within-parent alternatives support this exact-geometry comparison. Do not relax matching after this finding.'
    (OUT / 'tdp_exact_geometry_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
