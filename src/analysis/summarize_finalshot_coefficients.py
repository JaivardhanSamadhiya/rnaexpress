"""Describe individual coefficient directions without interpreting group signs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.modeling.finalshot_models import FinalShotFeatureStore

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'


def main():
    rows = pd.read_csv(ROOT / 'results/v4_phaseB/model_candidate_rows.csv.gz')
    store = FinalShotFeatureStore(rows, ROOT / 'data/interim/finalshot_rbpnet_features.npy',
                                 OUT / 'rbp_feature_dictionary.csv', OUT / 'rbp_expression_proxy.csv')
    dictionary = pd.read_csv(OUT / 'rbp_feature_dictionary.csv').sort_values('column_index')
    records = []
    for family in ('M1', 'M2', 'M3'):
        layout = store.layout('M2' if family == 'M3' else family)
        for fold in range(5):
            paths = sorted((ROOT / f'data/interim/finalshot_m3_cache/outer{fold}').glob('refit_*.npz')) if family == 'M3' else [OUT / f'nested_direct/{family}_outer_fold_{fold}.npz']
            assert len(paths) == (3 if family == 'M3' else 1)
            for path in paths:
                with np.load(path, allow_pickle=False) as a:
                    coef = a['coefficient']
                    meta = json.loads(str(a['metadata_json'].item()))
                assert len(coef) == layout.feature_count and np.isfinite(coef).all()
                for group, rbp in enumerate(layout.group_names):
                    names = dictionary.loc[dictionary.group_index.eq(group), 'summary'].tolist()
                    for block, columns in [('base', layout.base_columns[group]), ('expression_interaction', layout.interaction_columns[group])]:
                        for name, column in zip(names, columns):
                            records.append({'family': family, 'outer_fold': fold,
                                'seed': meta.get('seed', 42017), 'human_rbp': rbp,
                                'summary': name, 'block': block, 'coefficient': float(coef[column])})
    frame = pd.DataFrame(records)
    frame.to_csv(OUT / 'rbp_coefficient_directions.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    keys = ['family', 'human_rbp', 'summary', 'block']
    folds = frame.groupby(keys + ['outer_fold']).coefficient.median().reset_index()
    folds['positive'] = folds.coefficient.gt(0)
    folds['negative'] = folds.coefficient.lt(0)
    result = folds.groupby(keys).agg(median_coefficient=('coefficient', 'median'),
        positive_folds=('positive', 'sum'), negative_folds=('negative', 'sum')).reset_index()
    result['nonzero_folds'] = result.positive_folds + result.negative_folds
    result['dominant_sign_fraction_among_nonzero'] = result[['positive_folds', 'negative_folds']].max(axis=1) / result.nonzero_folds.replace(0, np.nan)
    result.to_csv(OUT / 'rbp_coefficient_direction_stability.csv', index=False)
    print(f'{len(frame)} coefficient records; {len(result)} feature summaries', flush=True)


if __name__ == '__main__':
    main()
