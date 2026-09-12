"""Pre-registered control, necessity and integrity evaluation (N0-N10, block removals).

Each null is refit with the same six frozen recipes and the same inner-only
nested selection as the real families, then scored once on each untouched outer
fold. Every comparison is made on identical eligible decision sets, with
identical candidate/outcome cohort hashes; where a stratum cannot supply an
eligible donor the affected decisions are dropped from BOTH sides rather than
being quietly compared against a different cohort.

Nothing in this module can change a threshold, a recipe or a split.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .development_training import verify_freeze
from .feature_store import FeatureStore
from .gates import (component_units, frozen_gates, gate_necessity, paired_evidence,
                    paired_sign_test, with_strata)
from .evaluation import pair_comparison
from .gates import metric_frame
from .io import ROOT, sha256, write_json
from .outer_evaluation import (inner_selection, load_scores, outer_scores, score_record,
                               selected_recipes, verify_outer_freeze)
from .providers import FamilyProvider, block_removal_providers, control_providers

CONTROL_EVIDENCE = 'results/mechanism_v2/controls/control_evidence.json'
CONTROL_SELECTIONS = 'results/mechanism_v2/controls/control_selections.json'
REPLICATION = 'results/mechanism_v2/controls/seed_replication.json'


def decision_complete_mask(rows, eligible):
    """Keep only decision sets in which every candidate row is eligible."""
    eligible = np.asarray(eligible, bool)
    frame = pd.DataFrame({'decision': rows.decision_set_id.astype(str).to_numpy(), 'eligible': eligible})
    complete = frame.groupby('decision', sort=False).eligible.transform('all').to_numpy()
    return complete & eligible


class HeadRemovalProvider(FamilyProvider):
    """`ranking_heads` removal: identical features, the optional head switched off."""

    def __init__(self, family):
        super().__init__(family)
        self.name = f'{family}_minus_ranking_heads'

    def audit(self, store):
        record = super().audit(store)
        record.update({'removed_block': 'ranking_heads',
                       'note': 'features identical; the optional source ranking temperatures are removed '
                               'and the model is refit entirely on training rows'})
        return record


def family_by_fold(store, frozen):
    """The family each outer fold's committed inner selection actually chose."""
    selections = selected_recipes(store, frozen)
    return ({outer: record['family'] for outer, record in selections['primary'].items()},
            selections)


def _headless(recipe_by_fold):
    """Per-fold head removal, only where the selected recipe actually has a head."""
    out = {}
    for outer, recipe in recipe_by_fold.items():
        if not recipe['config'].get('ranking_heads'):
            out[outer] = None
            continue
        config = dict(recipe['config'])
        config['ranking_heads'] = False
        out[outer] = {**recipe, 'config': config,
                      'recipe_id': str(recipe.get('recipe_id')) + '_no_heads'}
    return out


def run_control_selections():
    """Inner-only recipe selection for every eligible control provider."""
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    families, _ = family_by_fold(store, frozen)
    providers = control_providers(store, families)
    providers.pop('n0_geometry', None)
    selections = {}
    for name, provider in sorted(providers.items()):
        record = inner_selection(store, provider, 'controls', freeze_sha256=digest, name=name)
        selections[name] = record
        status = ('ineligible: ' + str(record['ineligible_reason'])) if not record['eligible'] \
            else 'selected ' + json.dumps(record['selected_per_outer_fold'])
        print(f'Control inner selection {name}: {status}', flush=True)
        for candidate in (provider.values() if isinstance(provider, dict) else [provider]):
            if candidate is not None:
                candidate.release()
    write_json(CONTROL_SELECTIONS, {
        'format': 'mechanism_v2_control_selection_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'selected_family_by_outer_fold': {str(k): v for k, v in families.items()},
        'note': ('the inner-selected family is not identical in every outer fold, so every '
                 'family-dependent null is anchored on that fold\'s own selected family'),
        'selections': {k: {kk: vv for kk, vv in v.items() if kk != 'selected'}
                        for k, v in selections.items()},
        'outer_outcomes_used': False})
    return selections


def _null_comparison(rows, full_score, null_score, baseline, eligible, label):
    mask = decision_complete_mask(rows, eligible)
    if not mask.any():
        return ({'eligible': False, 'reason': 'no fully eligible decision set for this null'},
                {'eligible': False, 'reason': 'no fully eligible decision set for this null'})
    null_evidence = paired_evidence(rows, null_score, baseline, mask=mask, label=label)
    full_evidence = paired_evidence(rows, full_score, baseline, mask=mask,
                                    label=f'primary_on_{label}_cohort')
    for record in (null_evidence, full_evidence):
        if record.get('eligible'):
            record['cohort_coverage'] = float(mask.mean())
    return null_evidence, full_evidence


def _removal_harm(rows, full_score, reduced_score, baseline, mask, gates):
    full_metrics, _ = metric_frame(rows, full_score, mask=mask)
    reduced_metrics, _ = metric_frame(rows, reduced_score, mask=mask)
    base_metrics, _ = metric_frame(rows, baseline, mask=mask)
    if full_metrics.empty or reduced_metrics.empty:
        return {'eligible': False, 'reason': 'no eligible decisions for the removal comparison'}
    left = component_units(pair_comparison(full_metrics, base_metrics))
    right = component_units(pair_comparison(reduced_metrics, base_metrics))
    shared = left.index.intersection(right.index)
    if len(shared) < 2:
        return {'eligible': False, 'reason': 'fewer than two shared components'}
    difference = left.loc[shared] - right.loc[shared]
    rule = gates['gates']['g7_mechanistic_necessity']
    harm = {k: float(difference[k].mean()) for k in ('rank_gain', 'regret_gain')}
    tests = {k: paired_sign_test(difference[k].to_numpy()) for k in ('rank_gain', 'regret_gain')}
    regret_ok = harm['regret_gain'] >= rule['block_removal_regret_harm_minimum']
    chosen = 'regret_gain' if (regret_ok or harm['regret_gain'] >= harm['rank_gain']) else 'rank_gain'
    return {'eligible': True, 'harm': harm, 'p_value': tests[chosen]['p_value'],
            'p_value_metric': chosen, 'tests': tests, 'test': tests[chosen],
            'components': int(len(shared))}


def run_controls():
    """Fit and score every eligible control once; assemble the necessity gate."""
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    gates = frozen_gates()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    scores, manifest = load_scores()
    rows = with_strata(store.rows)
    baseline = scores['M0'][0]
    primary = scores['primary'][0]
    families, selection_records = family_by_fold(store, frozen)
    selections = run_control_selections()
    all_providers = control_providers(store, families)
    nulls, null_records, arrays = {}, {}, {}
    for name, record in sorted(selections.items()):
        if not record['eligible']:
            null_records[name] = {'status': 'ineligible', 'reason': record['ineligible_reason']}
            nulls[name] = {'eligible': False, 'reason': record['ineligible_reason']}
            continue
        provider = all_providers[name]
        score, eligible, audit = outer_scores(store, provider, record['selected'], 'controls',
                                              freeze_sha256=digest, name=name)
        for candidate in (provider.values() if isinstance(provider, dict) else [provider]):
            if candidate is not None:
                candidate.release()
        arrays[name] = score_record(f'data/interim/mechanism_v2/control_scores/{name}.npy',
                                    score, eligible, audit)
        null_evidence, full_evidence = _null_comparison(rows, primary, score, baseline, eligible, name)
        nulls[name] = null_evidence
        null_records[name] = {
            'status': 'evaluated' if null_evidence.get('eligible') else 'ineligible',
            'selected_per_outer_fold': record['selected_per_outer_fold'],
            'outer_folds_without_this_component': record.get('outer_folds_without_this_component', []),
            'provider_audit': record['static_audit'],
            'coverage': float(eligible.mean()),
            'null_evidence': null_evidence,
            'full_model_on_same_cohort': full_evidence}
        print(f'Control {name} scored: coverage {eligible.mean():.4f}', flush=True)
    # Nulls are compared against the full model measured on the same cohort.
    comparison = {}
    for name, evidence in nulls.items():
        if not evidence.get('eligible'):
            comparison[name] = evidence
            continue
        comparison[name] = evidence
    n0 = paired_evidence(rows, scores['M0'][0], baseline, label='n0_geometry_self_baseline')
    null_records['n0_geometry'] = {
        'status': 'evaluated',
        'note': 'N0 is the inner-selected geometry baseline itself; it is the comparison baseline, '
                'so its gain against itself is identically zero by construction',
        'null_evidence': {'eligible': True, 'point': {'rank_gain': 0.0, 'regret_gain': 0.0},
                          'components': n0['components'],
                          'selected': n0['selected'], 'baseline': n0['baseline']}}
    comparison['n0_geometry'] = null_records['n0_geometry']['null_evidence']
    removals = {}
    selection_by_fold = selection_records['primary']
    for block in gates['gates']['g7_mechanistic_necessity']['block_removal_family']:
        if block == 'ranking_heads':
            recipe_by_fold = _headless(selection_by_fold)
            providers = {outer: (HeadRemovalProvider(families[outer])
                                 if recipe_by_fold.get(outer) is not None else None)
                         for outer in selection_by_fold}
        else:
            providers = block_removal_providers(store, families, block)
            recipe_by_fold = {outer: (selection_by_fold[outer] if providers.get(outer) else None)
                              for outer in selection_by_fold}
        usable = sorted(o for o in providers if providers[o] is not None
                        and recipe_by_fold.get(o) is not None)
        if not usable:
            removals[block] = {
                'eligible': False,
                'reason': (f'no outer fold\'s inner-selected model contains a removable {block} '
                           f'component; selected families were '
                           f'{ {str(k): v for k, v in families.items()} }')}
            print(f'Block removal {block}: absent from every selected model', flush=True)
            continue
        score, eligible, audit = outer_scores(store, providers, recipe_by_fold, 'controls',
                                              freeze_sha256=digest, name=f'removal_{block}')
        arrays[f'removal_{block}'] = score_record(
            f'data/interim/mechanism_v2/control_scores/removal_{block}.npy', score, eligible, audit)
        mask = decision_complete_mask(rows, eligible)
        removals[block] = _removal_harm(rows, primary, score, baseline, mask, gates)
        removals[block]['provider'] = f'removal_{block}'
        removals[block]['outer_folds_evaluated'] = usable
        removals[block]['outer_folds_skipped'] = audit['outer_folds_skipped']
        removals[block]['coverage'] = float(mask.mean())
        print(f'Block removal {block}: folds {usable}, '
              f'{json.dumps(removals[block].get("harm", {}))}', flush=True)
    headline = paired_evidence(rows, primary, baseline, label='primary_vs_M0')
    necessity = gate_necessity(headline, comparison, removals, gates)
    record = {
        'format': 'mechanism_v2_control_evidence_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'gate_config_sha256': freeze['gate_config_sha256'],
        'selected_family_by_outer_fold': {str(k): v for k, v in families.items()},
        'control_score_arrays': arrays,
        'nulls': null_records,
        'block_removals': removals,
        'gates': {'g7_mechanistic_necessity': necessity},
        'limitations': [
            'A single global renaming of a freely learned linear coefficient vector is '
            'mathematically invariant and is not used as a necessity test.',
            'Trans identity controls mismatch externally named RBP availability weights rather than '
            'merely relabelling a free coefficient vector.',
            'These are predictive necessity tests; none of them demonstrates experimentally that an '
            'RBP mediates localization.',
            'N10 is not applicable: independent stability admission failed and no stability block '
            'exists. It is never zero-filled or reported as a passed necessity control.',
            'The inner-selected family differs across outer folds, so a block present in only some '
            'selected models is evaluated on the folds that contain it, with the comparison cohort '
            'restricted identically on both sides and the coverage stated.'],
        'outer_outcomes_used_for_selection': False,
    }
    write_json(CONTROL_EVIDENCE, record)
    print(f'g7_mechanistic_necessity: {necessity["status"]}', flush=True)
    return record


def run_seed_replication():
    """Gate 9: refit the selected recipes at the replication seeds, without reselection."""
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    gates = frozen_gates()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    rows = with_strata(store.rows)
    selections = selected_recipes(store, frozen)
    providers = {outer: FamilyProvider(selections['primary'][outer]['family'])
                 for outer in selections['primary']}
    m0_provider = FamilyProvider('M0')
    m0_recipe = {outer: selections['family'][outer]['M0'] for outer in selections['family']}
    rule = gates['gates']['g9_stability_and_integrity']
    seeds = [store.design['seed']] + list(rule['replication_seeds'])
    per_seed, replay = {}, {}
    for seed in seeds:
        suffix = '' if seed == store.design['seed'] else f'_seed{seed}'
        primary, _, _ = outer_scores(store, providers, selections['primary'], 'controls',
                                     freeze_sha256=digest, seed=seed, suffix=suffix)
        base, _, _ = outer_scores(store, m0_provider, m0_recipe, 'controls',
                                  freeze_sha256=digest, seed=seed, suffix=suffix)
        evidence = paired_evidence(rows, primary, base, label=f'primary_vs_M0_seed_{seed}',
                                   bootstrap=0)
        from .gates import (gate_distributed_benefit, gate_matched_edits, gate_small_edits,
                            gate_useful_selection)
        matched = paired_evidence(rows, primary, base, bootstrap=0,
                                  keys=tuple(gates['gates']['g3_matched_edits']['strata'][1:]),
                                  label=f'matched_seed_{seed}')
        from .development_analysis import band_analyses
        bands = band_analyses(rows, primary, base, gates)
        per_seed[str(seed)] = {
            'point': evidence['point'], 'components': evidence['components'],
            'categories': {
                'g1_useful_selection': gate_useful_selection(evidence, gates)['status'],
                'g3_matched_edits': gate_matched_edits(matched, gates)['status'],
                'g6_small_edits': gate_small_edits(bands, gates)['status'],
            }}
    values = {metric: [per_seed[s]['point'][metric] for s in per_seed]
              for metric in ('rank_gain', 'regret_gain')}
    deviations = {metric: float(np.std(v, ddof=1)) for metric, v in values.items()}
    categories = [tuple(sorted(per_seed[s]['categories'].items())) for s in per_seed]
    checks = {
        'standard_deviation_within_limit': all(
            v <= rule['primary_gain_standard_deviation_maximum'] for v in deviations.values()),
        'gate_category_agreement': len(set(categories)) == 1,
    }
    record = {'format': 'mechanism_v2_seed_replication_v1',
              'outer_freeze_git_commit': freeze['git_commit'],
              'seeds': seeds, 'per_seed': per_seed, 'primary_gain_standard_deviation': deviations,
              'checks': checks,
              'gate': {'gate': 'g9_stability_and_integrity',
                       'status': 'pass' if all(checks.values()) else 'fail',
                       'checks': checks, 'thresholds': rule,
                       'note': 'recipe selection was never repeated against outer outcomes; only the '
                               'already-selected recipes were refit at the replication seeds'},
              'replay': replay}
    write_json(REPLICATION, record)
    print(f'g9_stability_and_integrity: {record["gate"]["status"]} '
          f'(SD {json.dumps(deviations)})', flush=True)
    return record
