"""Assemble the frozen evidence into the required reports and one allowed verdict.

This module does no fitting and applies no threshold of its own. It reads the
committed evidence files, evaluates the two gates that need evidence from more
than one stage (hard harm, and the optional trans clause), and then writes the
verdict. A development-only result can never become a GO: that rule is in the
frozen gate configuration, not in this code's discretion.
"""
from __future__ import annotations

import json

import numpy as np

from .gates import frozen_gates, gate_hard_harm
from .io import ROOT, sha256, write_json, write_once
from .outer_evaluation import verify_outer_freeze

VERDICT = 'results/mechanism_v2/outer/final_verdict.json'
ALLOWED = ('STRONG GO - UNIVERSAL ZERO-SHOT RNADDRESS SUPPORTED',
           'PARTIAL GO - RESTRICTED ZERO-SHOT DOMAIN SUPPORTED',
           'NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS')
STAGES = {
    'development': 'results/mechanism_v2/outer/development_evidence.json',
    'controls': 'results/mechanism_v2/controls/control_evidence.json',
    'replication': 'results/mechanism_v2/controls/seed_replication.json',
    'transfer': 'results/mechanism_v2/transfer/transfer_evidence.json',
    'probes': 'results/mechanism_v2/outer/shortcut_probes.json',
    'uncertainty': 'results/mechanism_v2/outer/uncertainty.json',
}


def load_stages():
    stages, digests = {}, {}
    for name, relative in STAGES.items():
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(f'Required evidence stage missing: {relative}')
        stages[name] = json.loads(path.read_text())
        digests[relative] = sha256(path)
    return stages, digests


def harm_points(stages):
    """Every eligible task-level and small-band regret gain the hard-harm rule covers."""
    points = {}
    for key, entry in stages['transfer']['tasks'].items():
        if entry['kind'] not in ('leave_source', 'cross_cell', 'cross_reporter'):
            continue
        for direction, evidence in entry.get('directions', {}).items():
            if evidence.get('eligible'):
                points[f'{key}|{direction}'] = float(evidence['point']['regret_gain'])
    for band, evidence in stages['development']['edit_bands'].items():
        if band in ('2-5', '6-10', '2-10') and evidence.get('eligible'):
            points[f'band_{band}'] = float(evidence['point']['regret_gain'])
    return points


def trans_clause(stages, gates):
    rule = gates['trans_clause']
    family = stages['development']['primary_family']
    if family != 'M7':
        return {'applies': False, 'primary_family': family,
                'reason': 'the primary selected family does not retain the trans block, so no trans '
                          'claim is made'}
    cell = stages['transfer']['gates']['g5_cross_context']['cross_cell']
    return {'applies': True, 'primary_family': family, 'status': 'not_evaluated',
            'reason': ('a genuine M7-versus-M6 cross-cell transfer comparison is required before any '
                       'trans claim; it is recorded as outstanding rather than assumed'),
            'cross_cell_reference': cell.get('status'), 'thresholds': rule}


def collect_gates(stages, gates):
    table = dict(stages['development']['gates'])
    table.update(stages['transfer']['gates'])
    table.update(stages['controls']['gates'])
    table['g8_shortcut_resistance'] = stages['probes']['gate']
    table['g9_stability_and_integrity'] = stages['replication']['gate']
    distributed = stages['development']['headline'].get('distributed')
    table['g10_hard_harm'] = gate_hard_harm(harm_points(stages), distributed, gates)
    return table


def determine_verdict(table, gates, stages):
    """One allowed verdict. All ten gates must actually pass, and the holdout is separate."""
    statuses = {name: record.get('status') for name, record in table.items()}
    failed = sorted(k for k, v in statuses.items() if v == 'fail')
    ineligible = sorted(k for k, v in statuses.items() if v == 'ineligible')
    passed = sorted(k for k, v in statuses.items() if v == 'pass')
    development_complete = not failed and not ineligible
    if development_complete:
        verdict = ALLOWED[2]
        rationale = ('Every development gate passed. Under the frozen protocol a development-only '
                     'result cannot be a GO: the one authorized Astrocyte holdout test has not been '
                     'opened, so no universal or restricted GO is claimed at this checkpoint. The '
                     'pre-holdout freeze is the next authorized step, and the verdict recorded here '
                     'remains the conservative one until that independent test is completed.')
        holdout = 'pre-holdout freeze authorized for review; holdout still sealed'
    else:
        verdict = ALLOWED[2]
        rationale = ('At least one pre-registered development gate did not pass, so universal '
                     'zero-shot intervention selection is not supported. A post-hoc restricted '
                     'domain is forbidden by the frozen protocol, so PARTIAL GO is unavailable '
                     'unless the single prospectively named restricted domain passes every gate on '
                     'its own, which it does not when the shared gates fail.')
        holdout = 'sealed; the pre-holdout freeze conditions are not satisfied'
    return {'verdict': verdict, 'allowed_verdicts': list(ALLOWED), 'rationale': rationale,
            'gate_status': statuses, 'gates_passed': passed, 'gates_failed': failed,
            'gates_ineligible': ineligible,
            'development_gates_all_passed': development_complete,
            'astrocyte_holdout': holdout, 'holdout_opened': False,
            'finalshot_historical_result': 'NO-GO - END ZERO-SHOT RNADDRESS (commit 98ffc02, unchanged)',
            'restricted_domain_rule': gates['restricted_domain']['post_hoc_domains']}


def _point(evidence, metric):
    if not evidence or not evidence.get('eligible'):
        return 'ineligible'
    return f'{evidence["point"][metric]:+.4f}'


def _row(name, evidence):
    if not evidence or not evidence.get('eligible'):
        reason = (evidence or {}).get('reason', 'not evaluated')
        return f'| {name} | ineligible | ineligible | - | {reason} |'
    point = evidence['point']
    return (f'| {name} | {point["rank_gain"]:+.4f} | {point["regret_gain"]:+.4f} | '
            f'{evidence["components"]} | {evidence["decisions"]} decisions |')


def write_reports(stages, table, verdict, digests):
    development = stages['development']
    controls = stages['controls']
    transfer = stages['transfer']
    header = (f'Generated from the committed outer freeze at '
              f'`{development["outer_freeze_git_commit"][:12]}`. '
              f'Gate thresholds: `{development["gate_config_sha256"][:12]}`.')
    lines = ['# Mechanism-v2 outer evaluation', '',
             'Status: frozen outer evaluation, executed once. Astrocyte remains sealed.', '',
             header, '',
             f'Primary selected family: **{development["primary_family"]}**. Per-fold primary recipes: '
             f'`{json.dumps(development["primary_selections"])}`. Family agreement across folds: '
             f'`{json.dumps(development["primary_family_agreement"]["counts"])}`.', '',
             '## Selector versus the geometry baseline', '',
             '| comparison | rank gain | regret gain | components | scope |',
             '| --- | ---: | ---: | ---: | --- |',
             _row('primary selector vs M0 (full coverage)', development['headline'])]
    for family, evidence in sorted(development['families_versus_M0'].items()):
        if family == 'M0_absolute':
            continue
        lines.append(_row(f'{family} vs M0', evidence))
    headline = development['headline']
    lines += ['', '## Absolute selected performance', '',
              f'* selector: regret {headline["selected"]["regret"]:.4f}, '
              f'rank {headline["selected"]["rank"]:.4f}, '
              f'Good@3 {headline["selected"]["good_at_3"]:.4f}, '
              f'Good@5 {headline["selected"]["good_at_5"]:.4f}, '
              f'random expected regret {headline["selected"]["random_expected_regret"]:.4f}',
              f'* M0 baseline: regret {headline["baseline"]["regret"]:.4f}, '
              f'rank {headline["baseline"]["rank"]:.4f}',
              '', '## Distributed benefit', '',
              f'```json\n{json.dumps(headline["distributed"], indent=2)}\n```', '',
              '## Paired component bootstrap', '',
              f'```json\n{json.dumps(headline.get("bootstrap"), indent=2)}\n```', '',
              '## Matched-edit and small-edit analyses', '',
              '| analysis | rank gain | regret gain | components | scope |',
              '| --- | ---: | ---: | ---: | --- |']
    for name, evidence in development['matched_edits'].items():
        lines.append(_row(f'matched: {name}', evidence))
    for band, evidence in development['edit_bands'].items():
        lines.append(_row(f'edit band {band}', evidence))
    lines.append(_row('restricted domain 2-10 nt', development['restricted_domain_2_10nt']))
    lines += ['', '## Declared sensitivities', '',
              '| sensitivity | rank gain | regret gain | components | scope |',
              '| --- | ---: | ---: | ---: | --- |']
    for name, evidence in development['sensitivities'].items():
        lines.append(_row(name, evidence))
    lines += ['', '## Uncertainty and coverage', '',
              f'```json\n{json.dumps(stages["uncertainty"]["inner_coverage_policy"], indent=2)}\n```',
              '', f'Full coverage remains the gate. {development["reused_benchmark_caveat"]}', '']
    write_once('reports/mechanism_v2/outer_evaluation.md', '\n'.join(lines).encode('utf-8'))

    lines = ['# Mechanism-v2 controls, necessity and integrity', '', header, '',
             '## Prospectively specified nulls', '',
             '| null | rank gain | regret gain | components | status |',
             '| --- | ---: | ---: | ---: | --- |']
    for name, record in sorted(controls['nulls'].items()):
        lines.append(_row(name, record.get('null_evidence')))
    necessity = controls['gates']['g7_mechanistic_necessity']
    lines += ['', '## Primary necessity comparison', '',
              f'```json\n{json.dumps(necessity.get("primary_nulls"), indent=2)}\n```', '',
              '## Block removal family (Holm over seven enumerated hypotheses)', '',
              f'```json\n{json.dumps(necessity.get("block_removals"), indent=2)}\n```', '',
              '## Seed replication', '',
              f'```json\n{json.dumps(stages["replication"]["per_seed"], indent=2)}\n```', '',
              f'Primary-gain standard deviation: '
              f'`{json.dumps(stages["replication"]["primary_gain_standard_deviation"])}`.', '',
              '## Shortcut resistance', '',
              f'```json\n{json.dumps(stages["probes"]["probes"], indent=2)}\n```', '',
              f'{stages["probes"]["interpretation"]}', '',
              '## Stated limitations', '']
    lines += [f'* {item}' for item in controls['limitations']]
    lines.append('')
    write_once('reports/mechanism_v2/controls_and_necessity.md', '\n'.join(lines).encode('utf-8'))

    lines = ['# Mechanism-v2 purged transfer evaluation', '', header, '',
             f'Inventory: `{transfer["inventory_scope"]}`.', '',
             '| directed transfer | rank gain | regret gain | components | scope |',
             '| --- | ---: | ---: | ---: | --- |']
    for key in sorted(transfer['tasks']):
        entry = transfer['tasks'][key]
        for direction in ('increase', 'decrease'):
            lines.append(_row(f'{entry["kind"]}: {key} ({direction})',
                              entry.get('directions', {}).get(direction)))
    ineligible = [(k, f) for k, v in transfer['tasks'].items() for f in v.get('ineligible_folds', [])]
    lines += ['', '## Ineligible folds, reported rather than passed', '']
    lines += [f'* `{item["task"]}`: {item["reason"]}' for _, item in ineligible] or ['* none']
    lines += ['', '## Gates', '',
              f'```json\n{json.dumps(transfer["gates"], indent=2)}\n```', '', '## Notes', '']
    lines += [f'* {item}' for item in transfer['notes']]
    lines.append('')
    write_once('reports/mechanism_v2/transfer_and_sensitivity.md', '\n'.join(lines).encode('utf-8'))

    status_lines = [f'| {name} | {record.get("status")} |' for name, record in sorted(table.items())]
    lines = ['# Mechanism-v2 final development verdict', '', header, '',
             f'## Verdict', '', f'**{verdict["verdict"]}**', '', verdict['rationale'], '',
             '## Pre-registered gate outcomes', '', '| gate | status |', '| --- | --- |',
             *status_lines, '',
             '## Boundaries preserved', '',
             f'* FinalShot: {verdict["finalshot_historical_result"]}.',
             f'* Astrocyte holdout: {verdict["astrocyte_holdout"]}. No Astrocyte sequence, label, '
             'outcome, feature row or metric was loaded at any point in this evaluation.',
             '* N-zip outcomes and quarantined TDP EV5 stability data were never accessed.',
             '* N10 is not applicable: independent stability admission failed and the block is '
             'absent, not zero-filled.',
             '', '## Evidence provenance', '',
             f'```json\n{json.dumps(digests, indent=2)}\n```', '',
             '## Honest scope', '',
             f'* {stages["development"]["reused_benchmark_caveat"]}',
             '* Predictive necessity tests do not establish that any RBP mediates localization.',
             '* A negative development result is a valid scientific outcome and is reported as such.',
             '']
    write_once('reports/mechanism_v2/final_verdict.md', '\n'.join(lines).encode('utf-8'))


def finalize():
    freeze = verify_outer_freeze()
    gates = frozen_gates()
    stages, digests = load_stages()
    table = collect_gates(stages, gates)
    verdict = determine_verdict(table, gates, stages)
    verdict['trans_clause'] = trans_clause(stages, gates)
    record = {'format': 'mechanism_v2_final_verdict_v1',
              'outer_freeze_git_commit': freeze['git_commit'],
              'gate_config_sha256': freeze['gate_config_sha256'],
              'evidence_sha256': digests, 'gates': table, **verdict}
    write_json(VERDICT, record)
    write_reports(stages, table, verdict, digests)
    print(json.dumps({'verdict': verdict['verdict'], 'gate_status': verdict['gate_status']}, indent=2),
          flush=True)
    return record
