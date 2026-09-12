"""Frozen zipcode-grammar scoring: no localization_effect labels enter this module."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .io import ROOT, sha256

GRAMMAR_CONFIG = 'configs/mechanism_v3/grammar_design.json'


def load_grammar(path: str | Path = GRAMMAR_CONFIG):
    record = json.loads((ROOT / path).read_text())
    if record['version'] != 'mechanism_v3_zipcode_grammar_v1':
        raise ValueError('Unknown grammar design version')
    elements = record['elements']
    if not elements:
        raise ValueError('Grammar dictionary is empty')
    for element in elements:
        motif = str(element['motif']).upper().replace('U', 'T')
        if not motif or set(motif) - set('ACGT'):
            raise ValueError(f'Illegal motif alphabet for {element["id"]}')
        if int(element['polarity']) not in {-1, 1}:
            raise ValueError(f'Polarity must be ±1 for {element["id"]}')
        element = dict(element)
        element['motif'] = motif
    # rewrite normalized motifs into a working copy
    normalized = []
    for element in elements:
        item = dict(element)
        item['motif'] = str(element['motif']).upper().replace('U', 'T')
        item['polarity'] = int(element['polarity'])
        normalized.append(item)
    record = dict(record)
    record['elements'] = normalized
    record['config_sha256'] = sha256(ROOT / path)
    return record


def normalize_sequence(sequence: str) -> str:
    if sequence is None:
        raise ValueError('Missing sequence')
    text = str(sequence).upper().replace('U', 'T')
    if not text or set(text) - set('ACGT'):
        raise ValueError('Only ACGT/U sequences are accepted')
    return text


def count_motif(sequence: str, motif: str) -> int:
    """Non-overlapping left-to-right counts."""
    if not motif:
        return 0
    count = 0
    start = 0
    while True:
        index = sequence.find(motif, start)
        if index < 0:
            return count
        count += 1
        start = index + len(motif)


def grammar_value(sequence: str, elements) -> float:
    sequence = normalize_sequence(sequence)
    total = 0.0
    for element in elements:
        total += element['polarity'] * count_motif(sequence, element['motif'])
    return float(total)


def grammar_delta(reference: str, mutant: str, elements) -> float:
    return grammar_value(mutant, elements) - grammar_value(reference, elements)


def scrambled_elements(elements):
    """Deterministic null: reversed motifs and flipped polarities."""
    out = []
    for element in elements:
        item = dict(element)
        item['id'] = element['id'] + '_scrambled'
        item['motif'] = element['motif'][::-1]
        item['polarity'] = -int(element['polarity'])
        out.append(item)
    return out


def score_rows(rows, elements):
    """Vector of outcome-free grammar deltas aligned to candidate rows."""
    refs = rows.parent_sequence.astype(str).to_numpy()
    muts = rows.mutant_sequence.astype(str).to_numpy()
    return np.asarray([grammar_delta(a, b, elements) for a, b in zip(refs, muts)], float)


def size_baseline(rows):
    costs = rows.edit_cost.to_numpy(float)
    if not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError('Invalid edit_cost for size baseline')
    return -np.log1p(costs)
