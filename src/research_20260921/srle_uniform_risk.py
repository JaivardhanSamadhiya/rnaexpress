"""Exact uniform reference for existing candidate sets, without new sequence design."""
from .common import ROOT, sha256, write_new, write_json
from .srle_fixed_choice_risk import indicators, paired_indicators, interval, MODELS
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd

OUT = ROOT / 'results/research_20260921'


def composition(sequence):
    if len(sequence) != 6 or set(sequence) - set('ACGT'):
        raise ValueError('Not a six-base measured identifier')
    return tuple(sequence.count(base) for base in 'ACGT')


def existing_candidates(parent, eligible):
    """Filter existing measured IDs only; do not construct new sequences."""
    key = composition(parent)
    return sorted(s for s in eligible if composition(s) == key
                  and sum(a != b for a, b in zip(parent, s)) == 2)


def uniform_metrics(changes):
    changes = np.asarray(changes, dtype=float)
    if changes.ndim != 2 or changes.shape[1] != 2 or len(changes) < 2 or not np.isfinite(changes).all():
        raise ValueError('Expected at least two candidates with two finite measurements')
    return {'replicates': {str(rep + 1): {k: float(v.mean()) for k, v in indicators(changes[:, rep]).items()}
                           for rep in range(2)},
            'paired_replicates': {k: float(v.mean()) for k, v in paired_indicators(changes[:, 0], changes[:, 1]).items()}}


def eligible_classes(prediction):
    if prediction.kmer.duplicated().any() or prediction.isna().any().any():
        raise ValueError('Invalid saved membership')
    if prediction.test.dtype != bool:
        raise ValueError('Saved membership must be boolean')
    frame = prediction.copy()
    frame['class_key'] = frame.kmer.map(composition)
    groups = {}
    for key, group in frame.groupby('class_key'):
        if int(group.test.sum()) >= 2 and int((~group.test).sum()) >= 2:
            groups[key] = set(group.loc[group.test, 'kmer'])
    return groups


def validate_archived_numeric(archived):
    if not np.isfinite(archived[['oriented_nrs_change', 'regret_gain']].to_numpy(float)).all():
        raise ValueError('Nonfinite archived decision statistic')


def build_reference(prediction, choices, raw, archived):
    validate_archived_numeric(archived)
    groups = eligible_classes(prediction)
    if raw.index.duplicated().any() or choices.duplicated(['parent', 'model', 'direction']).any():
        raise ValueError('Duplicate source identifiers')
    if raw.eligible.dtype != bool or raw.isna().any().any():
        raise ValueError('Invalid saved raw-score schema')
    if archived.duplicated(['parent', 'model', 'direction', 'replicate']).any():
        raise ValueError('Duplicate archived decisions')
    archived_lookup = archived.set_index(['parent', 'model', 'direction', 'replicate'])
    retained, roster, records, pair_records = set(), [], [], []
    max_change_error = max_regret_error = 0.0
    candidate_counts = []
    for parent, group in choices.groupby('parent', sort=True):
        key = composition(parent)
        if key not in groups or parent not in groups[key]:
            raise ValueError('Original parent is not an eligible held-out sequence')
        candidates = existing_candidates(parent, groups[key])
        if len(candidates) < 2 or not group.candidates.eq(len(candidates)).all():
            raise ValueError('Original candidate count differs')
        if (set(zip(group.model, group.direction)) != {(m, d) for m in MODELS for d in (-1, 1)}
                or not group.selected.isin(candidates).all()
                or not group.composition.eq(str(key)).all()):
            raise ValueError('Original decision identity/cohort differs')
        covered = bool(raw.loc[[parent, *candidates], 'eligible'].all())
        if not covered:
            if parent in set(archived.parent):
                raise ValueError('Archived parent no longer passes count eligibility')
            continue
        retained.add(parent)
        candidate_counts.append(len(candidates))
        roster.append([parent, candidates])
        y = raw.loc[candidates, ['NRS1', 'NRS2']].to_numpy(float)
        parent_y = raw.loc[parent, ['NRS1', 'NRS2']].to_numpy(float)
        if not np.isfinite(y).all() or not np.isfinite(parent_y).all() or (np.ptp(y, axis=0) <= 0).any():
            raise ValueError('Invalid retained candidate scores')
        for row in group.itertuples():
            selected_y = raw.loc[row.selected, ['NRS1', 'NRS2']].to_numpy(float)
            for rep in (1, 2):
                previous = archived_lookup.loc[(parent, row.model, row.direction, rep)]
                if previous.selected != row.selected or previous.composition != str(key):
                    raise ValueError('Previously saved choice changed')
                directed = row.direction * (selected_y[rep-1] - parent_y[rep-1])
                regret_gain = row.direction * (selected_y[rep-1] - y[:, rep-1].mean()) / np.ptp(y[:, rep-1])
                max_change_error = max(max_change_error, abs(directed - previous.oriented_nrs_change))
                max_regret_error = max(max_regret_error, abs(regret_gain - previous.regret_gain))
        for direction in (-1, 1):
            metrics = uniform_metrics(direction * (y - parent_y))
            for rep in (1, 2):
                records.append({'composition': str(key), 'direction': direction,
                                'replicate': rep, **metrics['replicates'][str(rep)]})
            pair_records.append({'composition': str(key), 'direction': direction,
                                 **metrics['paired_replicates']})
    if retained != set(archived.parent) or len(archived) != len(retained) * 16:
        raise ValueError('Reconstructed retained cohort differs')
    if max(max_change_error, max_regret_error) > 1e-12:
        raise ValueError('Archived fixed choices do not reproduce from pinned scores')
    return pd.DataFrame(records), pd.DataFrame(pair_records), {
        'retained_parents': len(retained), 'original_parents': int(choices.parent.nunique()),
        'retained_classes': int(archived.composition.nunique()),
        'max_directed_change_reconstruction_error': float(max_change_error),
        'max_regret_gain_reconstruction_error': float(max_regret_error),
        'candidate_count_min': int(min(candidate_counts)), 'candidate_count_max': int(max(candidate_counts)),
        'candidate_count_sum_over_parents': int(sum(candidate_counts)),
        'candidate_roster_sha256': hashlib.sha256(json.dumps(roster, separators=(',', ':')).encode()).hexdigest()}


def class_aggregate(frame, paired=False):
    keys = ['composition', 'direction'] + ([] if paired else ['replicate'])
    means = frame.groupby(keys, sort=True).mean().reset_index()
    counts = frame.groupby(keys, sort=True).size().reset_index(name='parent_count')
    return means.merge(counts, on=keys, validate='one_to_one')


def summarize_reference(groups, pairs, old_groups, old_pairs):
    classes = sorted(groups.composition.unique())
    class_ids = {c: i for i, c in enumerate(classes)}
    groups = groups.copy(); pairs = pairs.copy()
    groups['class_id'] = groups.composition.map(class_ids)
    pairs['class_id'] = pairs.composition.map(class_ids)
    draws = np.random.default_rng(20260921).integers(0, len(classes), (2000, len(classes)))
    metrics = [k for k in indicators([0])]
    paired_metrics = [k for k in paired_indicators([0], [0])]
    expected_ids = list(range(len(classes)))
    summary = {'uniform': {}, 'model_minus_uniform': {m: {} for m in MODELS}}
    for direction in (-1, 1):
        unif_reps = {}; comparisons = {m: {'replicates': {}} for m in MODELS}
        for rep in (1, 2):
            ref = groups[(groups.direction == direction) & (groups.replicate == rep)].set_index('class_id').reindex(expected_ids)
            if ref[metrics].isna().any().any():
                raise ValueError('Incomplete uniform class coverage')
            unif_reps[str(rep)] = {k: interval(ref[k], draws) for k in metrics}
            for model in MODELS:
                old = old_groups[(old_groups.model == model) & (old_groups.direction == direction)
                                 & (old_groups.replicate == rep)].set_index('class_id').reindex(expected_ids)
                if old[metrics].isna().any().any() or not old.parent_count.eq(ref.parent_count).all():
                    raise ValueError('Uniform/policy class cohort mismatch')
                comparisons[model]['replicates'][str(rep)] = {k: interval(old[k] - ref[k], draws) for k in metrics}
        ref_pair = pairs[pairs.direction == direction].set_index('class_id').reindex(expected_ids)
        if ref_pair[paired_metrics].isna().any().any():
            raise ValueError('Incomplete uniform paired coverage')
        summary['uniform'][str(direction)] = {'replicates': unif_reps,
            'paired_replicates': {k: interval(ref_pair[k], draws) for k in paired_metrics}}
        for model in MODELS:
            old = old_pairs[(old_pairs.model == model) & (old_pairs.direction == direction)].set_index('class_id').reindex(expected_ids)
            if old[paired_metrics].isna().any().any():
                raise ValueError('Incomplete saved paired coverage')
            comparisons[model]['paired_replicates'] = {k: interval(old[k] - ref_pair[k], draws) for k in paired_metrics}
            summary['model_minus_uniform'][model][str(direction)] = comparisons[model]
    return summary, groups.drop(columns='composition'), pairs.drop(columns='composition')


def run():
    freeze_path = OUT / 'srle_uniform_risk_freeze.json'
    frozen_bytes = freeze_path.read_bytes()
    if subprocess.check_output(['git', 'show', 'HEAD:' + freeze_path.relative_to(ROOT).as_posix()], cwd=ROOT) != frozen_bytes:
        raise ValueError('Comparator audit must be committed before execution')
    freeze = json.loads(frozen_bytes)
    if freeze['versions'] != {'numpy': np.__version__, 'pandas': pd.__version__}:
        raise ValueError('Numerical-library versions differ')
    for path, expected in freeze['files'].items():
        if sha256(ROOT / path) != expected:
            raise ValueError('Frozen comparator dependency differs: ' + path)
    prediction = pd.read_csv(OUT / 'robustness_predictions.csv', usecols=['kmer', 'test'])
    choices = pd.read_csv(OUT / 'robustness_swap_predictions.csv', usecols=['parent', 'composition', 'model', 'direction', 'selected', 'candidates'])
    raw = pd.read_csv(OUT / 'raw_replication_scores.csv', usecols=['kmer', 'eligible', 'NRS1', 'NRS2']).set_index('kmer')
    archived = pd.read_csv(OUT / 'raw_swap_evaluation.csv')
    old_groups = pd.read_csv(OUT / 'srle_fixed_choice_risk_groups_20260924.csv')
    old_pairs = pd.read_csv(OUT / 'srle_fixed_choice_risk_pairs_20260924.csv')
    parent_metrics, parent_pairs, checks = build_reference(prediction, choices, raw, archived)
    if checks['retained_parents'] != 592 or checks['retained_classes'] != 60:
        raise ValueError('Unexpected fixed cohort')
    summary, groups, pairs = summarize_reference(class_aggregate(parent_metrics), class_aggregate(parent_pairs, True), old_groups, old_pairs)
    group_path = OUT / 'srle_uniform_risk_groups_20260924.csv'
    pair_path = OUT / 'srle_uniform_risk_pairs_20260924.csv'
    write_new(group_path, groups.to_csv(index=False, lineterminator='\n').encode())
    write_new(pair_path, pairs.to_csv(index=False, lineterminator='\n').encode())
    result = {'scope': 'Post hoc exact uniform reference for existing fixed-choice risk; no new independent validation.',
              'checks': checks, 'comparisons': summary, 'difference_convention': 'model minus exact uniform expectation, for every metric',
              'uniform_identity': 'One candidate identity per parent, held fixed across the two replicates',
              'bootstrap': {'seed': 20260921, 'draws': 2000, 'unit': 'composition class'},
              'freeze_sha256': sha256(freeze_path),
              'outputs': {p.relative_to(ROOT).as_posix(): sha256(p) for p in [group_path, pair_path]},
              'models_fit': 0, 'choices_changed': 0, 'gates_changed': 0,
              'new_outcomes': False, 'sequence_identifiers_exported': False}
    write_json(OUT / 'srle_uniform_risk_result_20260924.json', result)
    print(json.dumps(checks, indent=2))
    for direction in (-1, 1):
        d = str(direction)
        print(json.dumps({'direction': direction, 'uniform_paired': summary['uniform'][d]['paired_replicates'],
                          'pair_minus_uniform_paired': summary['model_minus_uniform']['position_pair'][d]['paired_replicates'],
                          'kmer_minus_uniform_paired': summary['model_minus_uniform']['kmer123'][d]['paired_replicates']}, indent=2))


if __name__ == '__main__':
    run()
