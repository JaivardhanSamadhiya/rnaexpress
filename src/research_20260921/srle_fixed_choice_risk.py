"""Post hoc risk audit of existing fixed choices; no fit or sequence generation."""
from .common import ROOT, sha256, write_new, write_json
import json
import subprocess
import numpy as np
import pandas as pd

OUT = ROOT / 'results/research_20260921'
SOURCE_HASH = '7aff528234b2dff858d4d87fad4dbeee8fe709a8c4fe343705955ab3d2e46a69'
CHECKPOINT_HASH = 'bc35263bda2d97cf27d7e2eca0f2902fbb76d7afba0d531a85a25335124c4e12'
MODELS = ('composition', 'kmer123', 'position_additive', 'position_pair')
TIE_TOLERANCE = 1e-12
SCALE = .1


def indicators(values):
    x = np.asarray(values, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError('Nonfinite directed score change')
    return {'mean_directed_change': x,
            'fraction_positive': (x > TIE_TOLERANCE).astype(float),
            'fraction_negative': (x < -TIE_TOLERANCE).astype(float),
            'fraction_numerical_tie': (np.abs(x) <= TIE_TOLERANCE).astype(float),
            'mean_loss_including_zero': np.where(x < -TIE_TOLERANCE, -x, 0),
            'fraction_benefit_at_least_0_1': (x >= SCALE).astype(float),
            'fraction_harm_at_least_0_1': (x <= -SCALE).astype(float)}


def paired_indicators(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid paired directed changes')
    pos = (a > TIE_TOLERANCE) & (b > TIE_TOLERANCE)
    neg = (a < -TIE_TOLERANCE) & (b < -TIE_TOLERANCE)
    opposite = ((a > TIE_TOLERANCE) & (b < -TIE_TOLERANCE)) | ((b > TIE_TOLERANCE) & (a < -TIE_TOLERANCE))
    return {'fraction_positive_both': pos.astype(float),
            'fraction_negative_both': neg.astype(float),
            'fraction_opposite_signs': opposite.astype(float),
            'fraction_involving_tie': (~(pos | neg | opposite)).astype(float),
            'mean_smaller_directed_change': np.minimum(a, b)}


def validate_frame(frame):
    keys = ['parent', 'model', 'direction', 'replicate']
    if frame.empty or frame.isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('Missing or duplicated decision keys')
    if (set(frame.model) != set(MODELS) or set(frame.direction) != {-1, 1}
            or set(frame.replicate) != {1, 2}):
        raise ValueError('Unexpected model, direction or replicate')
    if frame.groupby('parent').size().ne(16).any():
        raise ValueError('Each parent must have all comparison decisions')
    if frame.groupby('parent').composition.nunique().ne(1).any():
        raise ValueError('Parent composition varies')
    if frame.groupby(['parent', 'model', 'direction']).selected.nunique().ne(1).any():
        raise ValueError('Selected identity changed between replicates')
    if not np.isfinite(frame.oriented_nrs_change.to_numpy(float)).all():
        raise ValueError('Nonfinite directed changes')


def interval(values, draws):
    values = np.asarray(values, dtype=float)
    return {'estimate': float(values.mean()),
            'descriptive_ci95': np.quantile(values[draws].mean(axis=1), [.025, .975]).tolist()}


def summarize(frame):
    validate_frame(frame)
    classes = sorted(frame.composition.unique())
    class_ids = {c: i for i, c in enumerate(classes)}
    draws = np.random.default_rng(20260921).integers(0, len(classes), (2000, len(classes)))
    records, paired_records, summary = [], [], {}
    for model in MODELS:
        summary[model] = {}
        for direction in (-1, 1):
            decisions = frame[(frame.model == model) & (frame.direction == direction)]
            by_replicate = {}
            for rep in (1, 2):
                group = decisions[decisions.replicate == rep]
                metrics = pd.DataFrame(indicators(group.oriented_nrs_change.to_numpy()), index=group.index)
                metrics['composition'] = group.composition
                means = metrics.groupby('composition').mean().reindex(classes)
                if means.isna().any().any():
                    raise ValueError('A composition class lacks comparison data')
                by_replicate[str(rep)] = {name: interval(means[name], draws) for name in means.columns}
                sizes = group.groupby('composition').size()
                for c, row in means.iterrows():
                    records.append({'class_id': class_ids[c], 'model': model,
                                    'direction': direction, 'replicate': rep,
                                    'parent_count': int(sizes[c]), **row.to_dict()})
            joined = decisions.pivot(index=['parent', 'composition'], columns='replicate', values='oriented_nrs_change')
            pairs = pd.DataFrame(paired_indicators(joined[1].to_numpy(), joined[2].to_numpy()), index=joined.index)
            means = pairs.groupby(level='composition').mean().reindex(classes)
            pair_summary = {name: interval(means[name], draws) for name in means.columns}
            for c, row in means.iterrows():
                paired_records.append({'class_id': class_ids[c], 'model': model,
                                       'direction': direction, **row.to_dict()})
            summary[model][str(direction)] = {'replicates': by_replicate,
                                             'paired_replicates': pair_summary}
    return summary, pd.DataFrame(records), pd.DataFrame(paired_records)


def run():
    freeze_path = OUT / 'srle_fixed_choice_risk_freeze.json'
    freeze_bytes = freeze_path.read_bytes()
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + freeze_path.relative_to(ROOT).as_posix()], cwd=ROOT)
    if freeze_bytes != committed:
        raise ValueError('Risk audit must be committed before execution')
    freeze = json.loads(freeze_bytes)
    if freeze['versions'] != {'numpy': np.__version__, 'pandas': pd.__version__}:
        raise ValueError('Risk audit numerical-library versions changed')
    for path, expected in freeze['files'].items():
        if sha256(ROOT / path) != expected:
            raise ValueError('Risk audit dependency changed: ' + path)
    source = OUT / 'raw_swap_evaluation.csv'
    checkpoint = OUT / 'checkpoint_receipt.json'
    if sha256(source) != SOURCE_HASH or sha256(checkpoint) != CHECKPOINT_HASH:
        raise ValueError('Archived input changed')
    cp = json.loads(checkpoint.read_text())
    original = OUT / 'raw_swap_result.json'
    if sha256(original) != cp['artifact_hashes'][original.relative_to(ROOT).as_posix()]:
        raise ValueError('Original summary differs from checkpoint')
    frame = pd.read_csv(source)
    if len(frame) != 9472 or frame.parent.nunique() != 592 or frame.composition.nunique() != 60:
        raise ValueError('Archived cohort differs')
    summary, groups, pairs = summarize(frame)
    previous = json.loads(original.read_text())
    errors = []
    for rep in (1, 2):
        for model in MODELS:
            combined = np.mean([summary[model][str(d)]['replicates'][str(rep)]['mean_directed_change']['estimate'] for d in (-1, 1)])
            error = abs(combined - previous['replicates'][str(rep)]['models'][model]['oriented_nrs_change'])
            errors.append(float(error))
    if max(errors) > 1e-12:
        raise ValueError('Separated directions do not reproduce archived mean')
    spec = ROOT / 'reports/research_20260921/srle_fixed_choice_risk_spec_20260924.md'
    paths = [source, checkpoint, original, spec, ROOT / 'src/research_20260921/srle_fixed_choice_risk.py']
    group_path = OUT / 'srle_fixed_choice_risk_groups_20260924.csv'
    pair_path = OUT / 'srle_fixed_choice_risk_pairs_20260924.csv'
    write_new(group_path, groups.to_csv(index=False, lineterminator='\n').encode())
    write_new(pair_path, pairs.to_csv(index=False, lineterminator='\n').encode())
    result = {'scope': 'Post hoc descriptive risk/consistency audit of already-open fixed decisions; no new validation.',
              'parents': 592, 'classes': 60, 'source_rows': 9472,
              'direction_labels': {'-1': 'decrease NRS', '1': 'increase NRS'},
              'tie_tolerance': TIE_TOLERANCE, 'fixed_descriptive_scale': SCALE,
              'bootstrap': {'seed': 20260921, 'draws': 2000, 'unit': 'composition class'},
              'max_difference_recombined_archived_mean': max(errors),
              'models': summary, 'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths},
              'freeze_sha256': sha256(freeze_path),
              'output_hashes': {p.relative_to(ROOT).as_posix(): sha256(p) for p in [group_path, pair_path]},
              'new_outcomes': False, 'models_fit': 0, 'choices_changed': 0,
              'gates_changed': 0, 'sequence_identifiers_exported': False}
    write_json(OUT / 'srle_fixed_choice_risk_result_20260924.json', result)
    for model in ('kmer123', 'position_pair'):
        for direction in (-1, 1):
            row = summary[model][str(direction)]
            print(json.dumps({'model': model, 'direction': direction,
                              'mean_changes': [row['replicates'][str(r)]['mean_directed_change']['estimate'] for r in (1, 2)],
                              'negative_fractions': [row['replicates'][str(r)]['fraction_negative']['estimate'] for r in (1, 2)],
                              'paired': row['paired_replicates']}, indent=2))


if __name__ == '__main__':
    run()
