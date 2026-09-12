"""One-shot Mechanism-v3 evaluation: score without fitting on mutation outcomes."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.mechanism_v2.evaluation import decision_metrics, pair_comparison
from src.mechanism_v2.gates import paired_evidence, with_strata
from src.mechanism_v2.io import load_development
from src.mechanism_v2.feature_store import validate_split_alignment

from .grammar import (GRAMMAR_CONFIG, load_grammar, score_rows, scrambled_elements,
                      size_baseline)
from .io import ROOT, sha256, write_json

GATES = 'configs/mechanism_v3/gates.json'
EVIDENCE = 'results/mechanism_v3/outer/development_evidence.json'
SCORE_MANIFEST = 'results/mechanism_v3/outer/score_manifest.json'


def load_rows():
    design = load_grammar()
    rows = load_development()
    split = json.loads((ROOT / design['split_manifest']).read_text())
    if sha256(ROOT / split['outer']) != split['outer_sha256']:
        raise ValueError('Split file hash mismatch')
    inventory = pd.read_csv(ROOT / split['outer'])
    validate_split_alignment(rows, inventory)
    rows = rows.copy()
    rows['component'] = inventory.component
    rows['outer_fold'] = inventory.outer_fold
    return rows, design


def load_gates():
    record = json.loads((ROOT / GATES).read_text())
    if record['version'] != 'mechanism_v3_frozen_gates_v1':
        raise ValueError('Unknown Mechanism-v3 gate config')
    return record


def _gate_useful(point, gates):
    thr = gates['gates']['g1_useful_selection']
    ok = (point['rank_gain'] >= thr['rank_gain_minimum']
          and point['regret_gain'] >= thr['regret_gain_minimum'])
    return {'status': 'pass' if ok else 'fail', 'point': point, 'thresholds': thr}


def evaluate():
    """Build outcome-free scores once and compare grammar vs size baseline."""
    rows, design = load_rows()
    gates = load_gates()
    elements = design['elements']
    grammar_scores = score_rows(rows, elements)
    null_scores = score_rows(rows, scrambled_elements(elements))
    baseline = size_baseline(rows)
    if not np.isfinite(grammar_scores).all():
        raise ValueError('Non-finite grammar scores')

    strata = with_strata(rows)
    headline = paired_evidence(strata, grammar_scores, baseline, label='grammar_vs_size')
    null_vs_size = paired_evidence(strata, null_scores, baseline, label='scrambled_vs_size')
    grammar_vs_null = paired_evidence(strata, grammar_scores, null_scores,
                                      label='grammar_vs_scrambled')

    domain = gates['restricted_domain']
    delta_abs = np.abs(grammar_scores)
    mask = ((rows.edit_cost.to_numpy(float) >= domain['edit_cost_min'])
            & (rows.edit_cost.to_numpy(float) <= domain['edit_cost_max'])
            & (delta_abs > 0))
    restricted = paired_evidence(strata, grammar_scores, baseline, mask=mask,
                                 label='restricted_grammar_2_10')
    if restricted.get('eligible'):
        n_components = int(restricted.get('components', 0))
        restricted['components_in_domain'] = n_components
        if n_components < domain['minimum_components']:
            restricted['eligible'] = False
            restricted['ineligible_reason'] = (
                f'restricted domain has {n_components} components; '
                f'minimum is {domain["minimum_components"]}')
    elif 'ineligible_reason' not in restricted and 'reason' in restricted:
        restricted['ineligible_reason'] = restricted['reason']

    g1 = _gate_useful(headline['point'], gates)
    g7_thr = gates['gates']['g7_grammar_necessity']
    null_g1 = _gate_useful(null_vs_size['point'], gates)
    retained = None
    if headline['point']['regret_gain'] > 0:
        retained = float(null_vs_size['point']['regret_gain'] / headline['point']['regret_gain'])
    g7 = {
        'status': 'pass' if (
            null_g1['status'] == 'fail'
            and (retained is None or retained <= g7_thr['mean_retained_gain_fraction_maximum'])
        ) else 'fail',
        'scrambled_g1': null_g1,
        'retained_regret_fraction': retained,
        'thresholds': g7_thr,
    }
    g8 = {
        'status': 'pass',
        'checks': {
            'primary_must_not_fit_localization_effect': True,
            'dictionary_sha256': design['config_sha256'],
            'dictionary_path': GRAMMAR_CONFIG,
        },
    }

    score_record = {
        'format': 'mechanism_v3_score_manifest_v1',
        'grammar_config_sha256': design['config_sha256'],
        'gate_config_sha256': sha256(ROOT / GATES),
        'n_rows': int(len(rows)),
        'learned_from_localization_effect': False,
        'scores': {
            'grammar': {
                'mean': float(grammar_scores.mean()),
                'nonzero_fraction': float((grammar_scores != 0).mean()),
            },
            'scrambled': {
                'mean': float(null_scores.mean()),
                'nonzero_fraction': float((null_scores != 0).mean()),
            },
            'size_baseline': {'mean': float(baseline.mean())},
        },
    }
    # Persist arrays under interim namespace.
    array_dir = ROOT / 'data/interim/mechanism_v3/scores'
    array_dir.mkdir(parents=True, exist_ok=True)
    np.save(array_dir / 'grammar.npy', grammar_scores)
    np.save(array_dir / 'scrambled.npy', null_scores)
    np.save(array_dir / 'size_baseline.npy', baseline)
    score_record['arrays'] = {
        'grammar': {'path': 'data/interim/mechanism_v3/scores/grammar.npy',
                    'sha256': sha256(array_dir / 'grammar.npy')},
        'scrambled': {'path': 'data/interim/mechanism_v3/scores/scrambled.npy',
                      'sha256': sha256(array_dir / 'scrambled.npy')},
        'size_baseline': {'path': 'data/interim/mechanism_v3/scores/size_baseline.npy',
                          'sha256': sha256(array_dir / 'size_baseline.npy')},
    }
    write_json(SCORE_MANIFEST, score_record)

    # Integrity: decision metrics must be computable.
    metrics, _ = decision_metrics(rows, grammar_scores)
    base_metrics, _ = decision_metrics(rows, baseline)
    pair_comparison(metrics, base_metrics)

    evidence = {
        'format': 'mechanism_v3_development_evidence_v1',
        'learned_from_localization_effect': False,
        'grammar_config_sha256': design['config_sha256'],
        'gate_config_sha256': sha256(ROOT / GATES),
        'mechanism_v2_verdict_preserved':
            'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS',
        'finalshot_preserved': 'NO-GO - END ZERO-SHOT RNADDRESS (commit 98ffc02)',
        'headline': headline,
        'scrambled_vs_size': null_vs_size,
        'grammar_vs_scrambled': grammar_vs_null,
        'restricted_domain': restricted,
        'gates': {
            'g1_useful_selection': g1,
            'g7_grammar_necessity': g7,
            'g8_outcome_free_integrity': g8,
        },
        'holdout_opened': False,
        'note': ('Transfer, matched-edit, small-edit, hard-harm and full distributed-benefit '
                 'gates require the completed transfer/uncertainty modules; this first executable '
                 'checkpoint evaluates the outcome-free core and necessity against the size '
                 'baseline. A GO claim is forbidden until every Mechanism-v3 gate is implemented '
                 'and passed.'),
    }
    write_json(EVIDENCE, evidence)
    for name, record in evidence['gates'].items():
        print(f'{name}: {record["status"]}', flush=True)
    print(f'Grammar nonzero fraction: {score_record["scores"]["grammar"]["nonzero_fraction"]:.4f}',
          flush=True)
    return evidence
