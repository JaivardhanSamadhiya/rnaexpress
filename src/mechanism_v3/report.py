"""Status report writer for Mechanism-v3 checkpoints."""
from __future__ import annotations

import json

from .io import ROOT, write_once


def write_status_report():
    evidence_path = ROOT / 'results/mechanism_v3/outer/development_evidence.json'
    if not evidence_path.exists():
        raise FileNotFoundError('Run evaluate before report')
    evidence = json.loads(evidence_path.read_text())
    lines = [
        '# Mechanism-v3 status report',
        '',
        'Mechanism-v2 verdict preserved: '
        f'**{evidence["mechanism_v2_verdict_preserved"]}**.',
        '',
        'FinalShot preserved: '
        f'**{evidence["finalshot_preserved"]}**.',
        '',
        'Primary selector: outcome-free zipcode-grammar finite difference '
        '(`learned_from_localization_effect=false`).',
        '',
        '## Gate checkpoint (partial executable surface)',
        '',
        '| gate | status |',
        '| --- | --- |',
    ]
    for name, record in sorted(evidence['gates'].items()):
        lines.append(f'| {name} | {record.get("status")} |')
    lines += [
        '',
        '## Honest limit',
        '',
        evidence.get('note', ''),
        '',
        'Astrocyte holdout opened: '
        f'{evidence.get("holdout_opened", False)}.',
        '',
    ]
    write_once('reports/mechanism_v3/status.md', ('\n'.join(lines)).encode('utf-8'))
    print('Wrote reports/mechanism_v3/status.md', flush=True)
