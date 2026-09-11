"""Development analysis of the frozen outer scores: gates 1, 2, 3, 6 and reporting tables.

Every number here is derived from score vectors that were already produced once
under the committed outer freeze. This module fits nothing, so it cannot tune
anything against an outer outcome. It also computes the prospectively named
sensitivities (sequence-90 clustering, annotated gene groups, the literal
two-per-gene cap, the processing-flag abstention policy) and states plainly when
one of them is ineligible.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .evaluation import pair_comparison
from .feature_store import FeatureStore
from .gates import (absolute_summary, cap_two_per_gene, frozen_gates, gate_distributed_benefit,
                    gate_matched_edits, gate_small_edits, gate_useful_selection, metric_frame,
                    paired_evidence, with_strata)
from .io import ROOT, sha256, write_json
from .outer_evaluation import EVIDENCE, load_scores, verify_outer_freeze

PROCESSING_FLAG_COLUMNS = (0, 1, 2, 3)
SMALL_BANDS = {'0': (0, 0), '1': (1, 1), '2-5': (2, 5), '6-10': (6, 10),
               '11-25': (11, 25), '26-50': (26, 50), '>50': (51, 10 ** 9), '2-10': (2, 10)}


def band_mask(rows, band):
    low, high = SMALL_BANDS[band]
    cost = rows.edit_cost.to_numpy(float)
    return (cost >= low) & (cost <= high)


def sensitivity_components(store, manifest_relative, column='component'):
    """Alternative grouping inventories used only as declared sensitivities."""
    manifest = json.loads((ROOT / manifest_relative).read_text())
    path = manifest.get('outer') or manifest.get('inventory')
    if path is None:
        return None, {'eligible': False, 'reason': f'{manifest_relative} has no row inventory'}
    if 'outer_sha256' in manifest and sha256(ROOT / path) != manifest['outer_sha256']:
        raise ValueError(f'Sensitivity inventory changed: {path}')
    frame = pd.read_csv(ROOT / path)
    if len(frame) != len(store.rows):
        return None, {'eligible': False, 'reason': 'inventory does not span the candidate rows'}
    return frame[column].to_numpy(), {'eligible': True, 'manifest': manifest_relative,
                                      'groups': int(pd.Series(frame[column]).nunique())}


def regrouped(rows, groups):
    work = rows.copy()
    work['component'] = groups
    return work


def processing_flags(store):
    """Top-ranked-edit abstention flag: any strict donor/acceptor or PAS motif change."""
    block = np.asarray(store.blocks['processing_delta'])[store.feature_rows]
    return (np.abs(block[:, list(PROCESSING_FLAG_COLUMNS)]) > 0).any(axis=1)


def family_table(rows, scores, gates):
    baseline = scores['M0'][0]
    table = {}
    for name in sorted(scores):
        if name == 'M0':
            continue
        evidence = paired_evidence(rows, scores[name][0], baseline, label=f'{name}_vs_M0')
        table[name] = evidence
    metrics, _ = metric_frame(rows, baseline)
    table['M0_absolute'] = absolute_summary(metrics)
    return table


def matched_analyses(rows, score, baseline, gates):
    rule = gates['gates']['g3_matched_edits']
    analyses = {'primary': paired_evidence(rows, score, baseline, keys=tuple(rule['strata'][1:]),
                                           label='matched_edit_band_and_class')}
    for extra in rule['additional_reported_strata']:
        keys = tuple(extra[1:])
        analyses['|'.join(keys)] = paired_evidence(rows, score, baseline, keys=keys,
                                                   label='matched_' + '_'.join(keys))
    mikl = rows.dataset.eq('mikl_gse173098').to_numpy()
    motif = rows.motif_family.astype(str).ne('not_applicable').to_numpy()
    analyses['mikl_motif_family_macro'] = paired_evidence(
        rows, score, baseline, keys=('motif_family',), mask=mikl & motif,
        minimum_candidates=gates['eligibility']['mikl_motif_subanalysis_minimum_candidates'],
        label='mikl_motif_family_macro')
    capped = cap_two_per_gene(rows)
    index = capped.index.to_numpy()
    analyses['literal_two_per_gene_cap'] = paired_evidence(
        capped.reset_index(drop=True), score[index], baseline[index],
        keys=tuple(rule['strata'][1:]), label='literal_two_per_gene_cap')
    analyses['cap_plus_four_candidate_minimum'] = {
        'eligible': False,
        'reason': ('a two-per-gene cap leaves at most two candidates in a single-parent decision '
                   'set, so a four-candidate minimum is arithmetically unevaluable'),
        'status': 'unevaluable'}
    return analyses


def band_analyses(rows, score, baseline, gates):
    bands = {}
    for band in list(gates['gates']['g6_small_edits']['reported_bands']) + ['2-10']:
        mask = band_mask(rows, band)
        if not mask.any():
            bands[band] = {'eligible': False, 'reason': 'no candidate rows in this band',
                           'rows': 0}
            continue
        bands[band] = paired_evidence(rows, score, baseline, mask=mask, label=f'band_{band}')
        bands[band]['rows'] = int(mask.sum())
    return bands


def abstention_policy(rows, score, baseline, store, gates):
    """Full cohort versus abstaining when the top-ranked edit carries a processing flag.

    The full-cohort primary metric is never replaced by this. Coverage and the
    common-cohort comparison are reported so a selective result cannot be
    mistaken for the gate.
    """
    flags = processing_flags(store)
    full, _ = metric_frame(rows, score)
    if full.empty:
        return {'eligible': False, 'reason': 'no eligible decisions'}
    lookup = {(str(a), str(b)): bool(c) for a, b, c in
              zip(rows.decision_set_id, rows.candidate_id, flags)}
    flagged = np.array([lookup[(str(a), str(b))] for a, b in
                        zip(full.decision_set_id, full.selected_candidate)])
    covered = full.loc[~flagged, ['dataset', 'component', 'decision_set_id', 'direction']]
    if covered.empty:
        return {'eligible': False, 'reason': 'abstention removes every decision'}
    base, _ = metric_frame(rows, baseline)
    paired = pair_comparison(full, base)
    keys = ['dataset', 'component', 'decision_set_id', 'direction']
    common = paired.merge(covered, on=keys, how='inner', validate='one_to_one')
    from .evaluation import context_values
    covered_point, _, _ = context_values(common)
    full_point, _, _ = context_values(paired)
    return {'eligible': True, 'flag_rule': 'any nonzero strict donor, strict acceptor, canonical '
                                            'PAS or common PAS variant delta in the top-ranked edit',
            'flagged_decision_directions': int(flagged.sum()),
            'coverage': float(1 - flagged.mean()),
            'full_cohort_point': full_point, 'covered_cohort_point': covered_point,
            'policy': 'reported only; the pre-registered primary gate always uses full coverage'}


def analyze_development():
    freeze = verify_outer_freeze()
    gates = frozen_gates()
    store = FeatureStore()
    scores, manifest = load_scores()
    rows = with_strata(store.rows)
    if not all(mask.all() for _, mask in scores.values()):
        raise ValueError('A primary family score vector does not have full candidate coverage')
    baseline = scores['M0'][0]
    primary = scores['primary'][0]
    families = family_table(rows, scores, gates)
    headline = paired_evidence(rows, primary, baseline, label='primary_vs_M0')
    matched = matched_analyses(rows, primary, baseline, gates)
    bands = band_analyses(rows, primary, baseline, gates)
    restricted_mask = band_mask(rows, '2-10')
    restricted = paired_evidence(rows, primary, baseline, mask=restricted_mask,
                                 label='restricted_domain_2_10nt')
    sensitivities = {}
    for name, relative in [('sequence90', 'results/mechanism_v2/manifests/splits_all_alleles90.json'),
                           ('annotated_gene_groups',
                            'results/mechanism_v2/manifests/splits_gene_group_sensitivity.json')]:
        groups, audit = sensitivity_components(store, relative)
        if groups is None:
            sensitivities[name] = audit
            continue
        evidence = paired_evidence(regrouped(rows, groups), primary, baseline,
                                   label=f'sensitivity_{name}')
        evidence['grouping'] = audit
        sensitivities[name] = evidence
    evidence_record = {
        'format': 'mechanism_v2_development_evidence_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'gate_config_sha256': freeze['gate_config_sha256'],
        'score_manifest_sha256': sha256(ROOT / 'results/mechanism_v2/outer/score_manifest.json'),
        'primary_family': manifest['primary_family'],
        'primary_family_agreement': manifest['primary_family_agreement'],
        'family_selections': manifest['family_selections'],
        'primary_selections': manifest['primary_selections'],
        'headline': headline,
        'families_versus_M0': families,
        'matched_edits': matched,
        'edit_bands': bands,
        'restricted_domain_2_10nt': restricted,
        'sensitivities': sensitivities,
        'abstention_policy': abstention_policy(rows, primary, baseline, store, gates),
        'gates': {
            'g1_useful_selection': gate_useful_selection(headline, gates),
            'g2_distributed_benefit': gate_distributed_benefit(headline, gates),
            'g3_matched_edits': gate_matched_edits(matched['primary'], gates),
            'g6_small_edits': gate_small_edits(bands, gates),
        },
        'reused_benchmark_caveat': ('these development datasets have been examined repeatedly in '
                                    'earlier RNAddress experiments; nested estimates on a reused '
                                    'benchmark are not fresh independent confirmation'),
        'holdout_opened': False,
    }
    write_json(EVIDENCE, evidence_record)
    for name, record in evidence_record['gates'].items():
        print(f'{name}: {record["status"]}', flush=True)
    return evidence_record
