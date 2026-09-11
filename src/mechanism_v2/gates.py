"""Gate arithmetic over already-frozen predictions.

This module never fits a model, never chooses a recipe and never reads a
threshold that is not in `configs/mechanism_v2/frozen_gates.json`. Its only job
is to turn two score vectors into paired, honestly-weighted evidence and then to
compare that evidence against the committed numbers. Unavailable evidence is
returned as `eligible: false`, which is a failure to demonstrate, not a pass.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .evaluation import (context_values, decision_metrics, distributed_benefit, holm_adjust,
                         paired_component_bootstrap, pair_comparison)
from .io import ROOT, sha256
from .primitives import edit_band

GATE_CONFIG = 'configs/mechanism_v2/frozen_gates.json'


def frozen_gates():
    record = json.loads((ROOT / GATE_CONFIG).read_text())
    if record['version'] != 'mechanism_v2_frozen_gates_v1':
        raise ValueError('Unknown frozen gate configuration')
    return record


def gate_config_sha256():
    return sha256(ROOT / GATE_CONFIG)


def with_strata(rows):
    """Attach the declared, outcome-blind stratification columns once."""
    work = rows.copy()
    work['edit_band'] = edit_band(work.edit_cost.to_numpy())
    work['gene_label'] = work.gene_name.astype(str).str.strip().str.lower()
    return work


def restrict_decisions(rows, keys):
    """Split each original decision set by declared strata; never merge across sets."""
    work = rows if not keys else rows.copy()
    if not keys:
        return work
    missing = [k for k in keys if k not in work.columns]
    if missing:
        raise KeyError(f'Unknown stratification column: {missing}')
    label = work[list(keys)].astype(str).apply(lambda c: c.str.replace('|', '_', regex=False))
    suffix = label.agg('|'.join, axis=1)
    work['decision_set_id'] = work.decision_set_id.astype(str) + '||' + suffix
    return work


def cap_two_per_gene(rows):
    """Literal historical two-candidates-per-gene cap, deterministic and lexical."""
    work = rows.copy()
    order = work.sort_values(['decision_set_id', 'gene_label', 'candidate_id'])
    keep = order.groupby(['decision_set_id', 'gene_label'], sort=False).head(2).index
    return work.loc[work.index.isin(keep)]


def metric_frame(rows, score, *, keys=(), mask=None, minimum_candidates=2):
    work = rows if mask is None else rows.loc[np.asarray(mask, bool)]
    values = np.asarray(score, float)
    if mask is not None:
        values = values[np.asarray(mask, bool)]
    work = restrict_decisions(work, tuple(keys)).reset_index(drop=True)
    return decision_metrics(work, values, minimum_candidates=minimum_candidates)


def absolute_summary(metrics):
    if metrics.empty:
        return {'eligible': False, 'reason': 'no eligible decision sets'}
    cells = metrics.groupby(['dataset', 'component', 'direction'])[
        ['regret', 'rank', 'good_at_3', 'good_at_5', 'random_expected_regret']].mean()
    contexts = cells.groupby(['dataset', 'direction']).mean()
    summary = {k: float(contexts[k].mean()) for k in contexts.columns}
    summary.update({'eligible': True, 'decisions': int(len(metrics)),
                    'components': int(metrics.component.nunique())})
    return summary


def paired_evidence(rows, score, baseline, *, keys=(), mask=None, minimum_candidates=2,
                    bootstrap=None, label='', direction=None, minimum_decisions=1):
    """Paired gains on identical eligible decision sets, plus honest uncertainty."""
    gates = frozen_gates()
    full, excluded = metric_frame(rows, score, keys=keys, mask=mask,
                                  minimum_candidates=minimum_candidates)
    base, _ = metric_frame(rows, baseline, keys=keys, mask=mask,
                           minimum_candidates=minimum_candidates)
    if direction is not None:
        if direction not in {'increase', 'decrease'}:
            raise ValueError('Direction must be increase or decrease')
        full = full.loc[full.direction.eq(direction)].reset_index(drop=True)
        base = base.loc[base.direction.eq(direction)].reset_index(drop=True)
    if full.empty or base.empty:
        return {'label': label, 'eligible': False, 'reason': 'no eligible decision sets',
                'strata': list(keys), 'direction': direction,
                'excluded': excluded.to_dict('records')}
    if len(full) < minimum_decisions:
        return {'label': label, 'eligible': False, 'direction': direction, 'strata': list(keys),
                'reason': f'{len(full)} eligible decision sets below the required {minimum_decisions}'}
    paired = pair_comparison(full, base)
    point, units, contexts = context_values(paired)
    record = {'label': label, 'eligible': True, 'strata': list(keys), 'direction': direction,
              'point': point, 'decisions': int(paired.decision_set_id.nunique()),
              'paired_rows': int(len(paired)),
              'components': int(paired.component.nunique()),
              'contexts': contexts.to_dict('records'),
              'selected': absolute_summary(full), 'baseline': absolute_summary(base),
              'distributed': distributed_benefit(paired),
              'excluded_decisions': int(len(excluded))}
    resamples = gates['bootstrap']['resamples'] if bootstrap is None else bootstrap
    if resamples:
        audit, _ = paired_component_bootstrap(paired, resamples, gates['bootstrap']['seed'])
        record['bootstrap'] = audit
    return record


def _both_thresholds(point, rank_minimum, regret_minimum):
    return bool(point['rank_gain'] >= rank_minimum and point['regret_gain'] >= regret_minimum)


def gate_useful_selection(evidence, gates):
    rule = gates['gates']['g1_useful_selection']
    if not evidence.get('eligible'):
        return {'gate': 'g1_useful_selection', 'status': 'ineligible', 'reason': evidence.get('reason')}
    point = evidence['point']
    passed = _both_thresholds(point, rule['rank_gain_minimum'], rule['regret_gain_minimum'])
    return {'gate': 'g1_useful_selection', 'status': 'pass' if passed else 'fail',
            'rank_gain': point['rank_gain'], 'regret_gain': point['regret_gain'],
            'thresholds': rule, 'selected_absolute': evidence['selected'],
            'baseline_absolute': evidence['baseline']}


def gate_distributed_benefit(evidence, gates):
    rule = gates['gates']['g2_distributed_benefit']
    if not evidence.get('eligible'):
        return {'gate': 'g2_distributed_benefit', 'status': 'ineligible', 'reason': evidence.get('reason')}
    distributed = evidence['distributed']
    bootstrap = evidence.get('bootstrap')
    checks = {
        'median_above_zero': bool(distributed['median'] > rule['median_component_regret_gain_minimum_exclusive']),
        'fraction_improved': bool(distributed['fraction_improved'] >= rule['fraction_components_improved_minimum']),
        'leave_best_out_above_zero': bool((distributed['leave_best_one_out_mean'] or -np.inf)
                                          > rule['leave_best_component_out_mean_minimum_exclusive']),
    }
    if bootstrap and bootstrap['eligible']:
        checks['lower_bounds'] = bool(all(
            bootstrap['confidence95'][k][0] >= rule['paired_lower_bound_minimum']
            for k in ('rank_gain', 'regret_gain')))
    else:
        checks['lower_bounds'] = False
    status = 'pass' if all(checks.values()) else 'fail'
    if bootstrap and not bootstrap['eligible']:
        status = 'ineligible'
    return {'gate': 'g2_distributed_benefit', 'status': status, 'checks': checks,
            'distributed': distributed, 'bootstrap': bootstrap, 'thresholds': rule}


def gate_matched_edits(evidence, gates):
    rule = gates['gates']['g3_matched_edits']
    if not evidence.get('eligible'):
        return {'gate': 'g3_matched_edits', 'status': 'ineligible', 'reason': evidence.get('reason')}
    point = evidence['point']
    components = evidence['components']
    if components < rule['minimum_components']:
        return {'gate': 'g3_matched_edits', 'status': 'ineligible',
                'reason': f'{components} independent components below the required {rule["minimum_components"]}',
                'point': point, 'components': components, 'thresholds': rule}
    passed = _both_thresholds(point, rule['rank_gain_minimum'], rule['regret_gain_minimum'])
    return {'gate': 'g3_matched_edits', 'status': 'pass' if passed else 'fail',
            'point': point, 'components': components, 'thresholds': rule}


def _task_improves_both(point):
    return bool(point['rank_gain'] > 0 and point['regret_gain'] > 0)


def gate_leave_source(tasks, gates):
    """`tasks` maps source-direction name to a paired-evidence record."""
    rule = gates['gates']['g4_leave_source']
    eligible = {k: v for k, v in tasks.items() if v.get('eligible')}
    if not eligible:
        return {'gate': 'g4_leave_source', 'status': 'ineligible', 'reason': 'no eligible leave-source task',
                'tasks': tasks}
    improving = [k for k, v in eligible.items() if _task_improves_both(v['point'])]
    regret = {k: v['point']['regret_gain'] for k, v in eligible.items()}
    rank = {k: v['point']['rank_gain'] for k, v in eligible.items()}
    macro_regret = float(np.mean(list(regret.values())))
    macro_rank = float(np.mean(list(rank.values())))
    by_source = {}
    for key, value in regret.items():
        by_source.setdefault(key.rsplit('|', 1)[0], 0.0)
        by_source[key.rsplit('|', 1)[0]] += max(0.0, value)
    positive_total = sum(by_source.values())
    share = max(by_source.values()) / positive_total if positive_total > 0 else None
    checks = {
        'tasks_improving_both': len(improving) >= rule['minimum_tasks_improving_both'],
        'macro_regret_gain': macro_regret >= rule['macro_regret_gain_minimum'],
        'macro_rank_gain': macro_rank > rule['macro_rank_gain_minimum_exclusive'],
        'no_single_source_dominates': share is None or share <= rule['maximum_single_source_share_of_positive_regret_gain'],
        'all_six_tasks_eligible': len(eligible) == rule['total_tasks'],
    }
    status = 'pass' if all(checks.values()) else 'fail'
    if not checks['all_six_tasks_eligible']:
        status = 'ineligible'
    return {'gate': 'g4_leave_source', 'status': status, 'checks': checks,
            'macro_regret_gain': macro_regret, 'macro_rank_gain': macro_rank,
            'tasks_improving_both': sorted(improving), 'eligible_tasks': sorted(eligible),
            'per_task_regret_gain': regret, 'per_task_rank_gain': rank,
            'largest_source_share_of_positive_regret_gain': share, 'thresholds': rule}


def _context_family(tasks, total, minimum, macro_minimum, name):
    eligible = {k: v for k, v in tasks.items() if v.get('eligible')}
    if not eligible:
        return {'status': 'ineligible', 'reason': f'no eligible {name} task', 'tasks': tasks}
    improving = [k for k, v in eligible.items() if _task_improves_both(v['point'])]
    macro_regret = float(np.mean([v['point']['regret_gain'] for v in eligible.values()]))
    macro_rank = float(np.mean([v['point']['rank_gain'] for v in eligible.values()]))
    checks = {'tasks_improving_both': len(improving) >= minimum,
              'macro_regret_gain': macro_regret >= macro_minimum,
              'all_tasks_eligible': len(eligible) == total}
    status = 'pass' if all(checks.values()) else 'fail'
    if not checks['all_tasks_eligible']:
        status = 'ineligible'
    return {'status': status, 'checks': checks, 'macro_regret_gain': macro_regret,
            'macro_rank_gain': macro_rank, 'tasks_improving_both': sorted(improving),
            'eligible_tasks': sorted(eligible),
            'per_task_regret_gain': {k: v['point']['regret_gain'] for k, v in eligible.items()},
            'per_task_rank_gain': {k: v['point']['rank_gain'] for k, v in eligible.items()}}


def gate_cross_context(cell_tasks, reporter_tasks, gates):
    rule = gates['gates']['g5_cross_context']
    cell = _context_family(cell_tasks, rule['cell_tasks_total'], rule['cell_tasks_improving_both_minimum'],
                           rule['macro_regret_gain_minimum'], 'cross-cell')
    reporter = _context_family(reporter_tasks, rule['reporter_tasks_total'],
                               rule['reporter_tasks_improving_both_minimum'],
                               rule['macro_regret_gain_minimum'], 'cross-reporter')
    statuses = {cell['status'], reporter['status']}
    status = 'pass' if statuses == {'pass'} else ('ineligible' if 'ineligible' in statuses else 'fail')
    return {'gate': 'g5_cross_context', 'status': status, 'cross_cell': cell,
            'cross_reporter': reporter, 'thresholds': rule}


def gate_small_edits(bands, gates):
    """`bands` maps a band label (including the pooled '2-10') to paired evidence."""
    rule = gates['gates']['g6_small_edits']
    primary = bands.get(rule['primary_band'], {})
    if not primary.get('eligible'):
        return {'gate': 'g6_small_edits', 'status': 'ineligible',
                'reason': f'the {rule["primary_band"]} band has no eligible evidence', 'bands': bands}
    point = primary['point']
    rank_ok = point['rank_gain'] >= rule['rank_gain_minimum']
    regret_ok = point['regret_gain'] >= rule['regret_gain_minimum']
    companion = (point['regret_gain'] if rank_ok and not regret_ok else
                 point['rank_gain'] if regret_ok and not rank_ok else
                 min(point['rank_gain'], point['regret_gain']))
    checks = {'primary_threshold': bool(rank_ok or regret_ok),
              'companion_not_harmful': bool(companion >= rule['companion_gain_minimum'])}
    subbands = {}
    for band in rule['required_subbands']:
        evidence = bands.get(band, {})
        if not evidence.get('eligible'):
            subbands[band] = {'status': 'ineligible', 'reason': 'no eligible evidence'}
            continue
        value = evidence['point']['regret_gain']
        subbands[band] = {'status': 'pass' if value >= rule['subband_regret_gain_minimum'] else 'fail',
                          'regret_gain': value, 'rank_gain': evidence['point']['rank_gain']}
    checks['subbands'] = all(v.get('status') == 'pass' for v in subbands.values())
    status = 'pass' if all(bool(v) for v in checks.values()) else 'fail'
    if any(v.get('status') == 'ineligible' for v in subbands.values()):
        status = 'ineligible'
    return {'gate': 'g6_small_edits', 'status': status, 'checks': checks, 'point': point,
            'subbands': subbands, 'components': primary['components'],
            'reported_bands': {k: (v['point'] if v.get('eligible') else
                                   {'eligible': False, 'reason': v.get('reason')})
                                for k, v in bands.items()},
            'thresholds': rule}


def retained_fraction(full_point, null_point, metric):
    """Fraction of the full gain that the null retains; undefined, never clipped."""
    full = full_point[metric]
    if not full > 0:
        return None
    return float(null_point[metric] / full)


def gate_necessity(full_evidence, nulls, removals, gates):
    rule = gates['gates']['g7_mechanistic_necessity']
    if not full_evidence.get('eligible'):
        return {'gate': 'g7_mechanistic_necessity', 'status': 'ineligible',
                'reason': 'no eligible full-model evidence'}
    useful = gates['gates']['g1_useful_selection']
    full_point = full_evidence['point']
    null_records = {}
    for name, evidence in nulls.items():
        if not evidence.get('eligible'):
            null_records[name] = {'status': 'ineligible', 'reason': evidence.get('reason')}
            continue
        point = evidence['point']
        retained = {m: retained_fraction(full_point, point, m) for m in ('rank_gain', 'regret_gain')}
        defined = [v for v in retained.values() if v is not None]
        destroyed_one = any(v is not None and v <= 1 - rule['minimum_destroyed_fraction_of_one_metric']
                            for v in retained.values())
        mean_retained = float(np.mean(defined)) if defined else None
        meets_both = _both_thresholds(point, useful['rank_gain_minimum'], useful['regret_gain_minimum'])
        null_records[name] = {
            'status': 'evaluated', 'point': point, 'components': evidence['components'],
            'retained_fraction': retained, 'mean_retained_fraction': mean_retained,
            'destroys_at_least_one_metric_by_half': bool(destroyed_one),
            'mean_retained_within_limit': (None if mean_retained is None
                                            else bool(mean_retained <= rule['maximum_mean_retained_gain_fraction'])),
            'null_meets_both_useful_selection_thresholds': bool(meets_both),
            'retention_defined': bool(defined)}
    primary = {}
    for name in rule['primary_nulls']:
        record = null_records.get(name, {'status': 'absent'})
        if record.get('status') != 'evaluated':
            primary[name] = {'status': 'ineligible', 'detail': record}
            continue
        ok = (record['destroys_at_least_one_metric_by_half']
              and record['mean_retained_within_limit'] is True
              and not record['null_meets_both_useful_selection_thresholds'])
        primary[name] = {'status': 'pass' if ok else 'fail', 'detail': record}
    removal_records, pvalues, names = {}, [], []
    for block in rule['block_removal_family']:
        record = removals.get(block)
        if record is None or not record.get('eligible'):
            removal_records[block] = {'status': 'absent', 'p_value': 1.0,
                                      'reason': (record or {}).get('reason', 'component not present in the selected model'),
                                      'claim': False}
            names.append(block)
            pvalues.append(1.0)
            continue
        harm = record['harm']
        regret_ok = harm['regret_gain'] >= rule['block_removal_regret_harm_minimum']
        rank_ok = harm['rank_gain'] >= rule['block_removal_rank_harm_minimum']
        companion = (harm['rank_gain'] if regret_ok and not rank_ok else
                     harm['regret_gain'] if rank_ok and not regret_ok else
                     min(harm['rank_gain'], harm['regret_gain']))
        removal_records[block] = {
            'status': 'evaluated', 'harm': harm, 'p_value': float(record['p_value']),
            'effect_threshold_met': bool(regret_ok or rank_ok),
            'companion_not_harmful': bool(companion >= rule['block_removal_companion_minimum']),
            'components': record.get('components'), 'test': record.get('test')}
        names.append(block)
        pvalues.append(float(record['p_value']))
    adjusted = holm_adjust(pvalues)
    for block, value in zip(names, adjusted):
        removal_records[block]['holm_adjusted_p_value'] = float(value)
        record = removal_records[block]
        record['claim'] = bool(record.get('status') == 'evaluated'
                               and record.get('effect_threshold_met')
                               and record.get('companion_not_harmful')
                               and value < rule['block_removal_alpha'])
    checks = {'primary_nulls': all(v['status'] == 'pass' for v in primary.values()),
              'at_least_one_interpretable_block_necessary': any(v.get('claim') for v in removal_records.values())}
    status = 'pass' if all(checks.values()) else 'fail'
    if any(v['status'] == 'ineligible' for v in primary.values()):
        status = 'ineligible'
    return {'gate': 'g7_mechanistic_necessity', 'status': status, 'checks': checks,
            'primary_nulls': primary, 'nulls': null_records, 'block_removals': removal_records,
            'n10_stability': rule['n10_stability'], 'thresholds': rule}


def gate_hard_harm(task_points, distributed, gates):
    rule = gates['gates']['g10_hard_harm']
    violations = {k: v for k, v in task_points.items() if v < rule['task_regret_gain_minimum']}
    worst = distributed['worst_decile_mean'] if distributed else None
    checks = {'no_task_below_limit': not violations,
              'worst_decile_within_limit': bool(worst is not None
                                                 and worst >= rule['worst_decile_component_mean_regret_gain_minimum'])}
    return {'gate': 'g10_hard_harm', 'status': 'pass' if all(checks.values()) else 'fail',
            'checks': checks, 'violations': violations,
            'worst_decile_component_mean_regret_gain': worst,
            'tasks_considered': len(task_points), 'thresholds': rule}


def paired_sign_test(values, resamples=10000, seed=20260909, alternative='greater'):
    """One-sided paired randomization test over independent components.

    Sign flips are the exchangeability assumption of a paired design under the
    null of no systematic effect. The p-value is the standard (1 + count) / (1 + n)
    form, so it can never be reported as exactly zero.
    """
    x = np.asarray(values, float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Finite one-dimensional paired values required')
    if x.size < 2:
        raise ValueError('At least two independent units required')
    if alternative != 'greater':
        raise ValueError('Only the prospectively specified one-sided alternative is implemented')
    observed = float(x.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(resamples, x.size))
    draws = (signs * x).mean(axis=1)
    p = float((1 + int((draws >= observed).sum())) / (1 + resamples))
    return {'observed_mean': observed, 'units': int(x.size), 'resamples': int(resamples),
            'seed': int(seed), 'p_value': p, 'alternative': 'greater',
            'test': 'paired component sign-flip randomization'}


def harm_record(full_evidence, reduced_evidence, paired_units, resamples=10000, seed=20260909):
    """Paired harm caused by removing a block, with a one-sided randomization p-value."""
    if not (full_evidence.get('eligible') and reduced_evidence.get('eligible')):
        return {'eligible': False, 'reason': 'full or reduced evidence ineligible'}
    harm = {k: float(full_evidence['point'][k] - reduced_evidence['point'][k])
            for k in ('rank_gain', 'regret_gain')}
    test = paired_sign_test(paired_units, resamples=resamples, seed=seed)
    return {'eligible': True, 'harm': harm, 'p_value': test['p_value'], 'test': test,
            'components': int(len(paired_units))}


def component_units(paired):
    """Component-level mean gains: the independent units for paired testing."""
    _, units, _ = context_values(paired)
    return units.groupby('component')[['rank_gain', 'regret_gain']].mean()


def paired_difference_units(rows, score_a, score_b, baseline, *, keys=(), mask=None):
    """Component-level difference of (A minus baseline) and (B minus baseline)."""
    full_a, _ = metric_frame(rows, score_a, keys=keys, mask=mask)
    full_b, _ = metric_frame(rows, score_b, keys=keys, mask=mask)
    base, _ = metric_frame(rows, baseline, keys=keys, mask=mask)
    left = component_units(pair_comparison(full_a, base))
    right = component_units(pair_comparison(full_b, base))
    shared = left.index.intersection(right.index)
    if not len(shared):
        raise ValueError('No shared components for a paired comparison')
    return (left.loc[shared] - right.loc[shared])


def category(status_map):
    """Coarse gate category used for cross-seed agreement checks."""
    return {name: record.get('status') for name, record in sorted(status_map.items())}
