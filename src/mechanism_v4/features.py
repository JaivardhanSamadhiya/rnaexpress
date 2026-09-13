"""Outcome-free sequence featurization: k-mer counts only.

No feature may depend on an outcome, a parent identity, a gene name, a source
label or a split index. Every column is a function of the ACGT-normalized
sequence alone.
"""
from __future__ import annotations

import itertools

import numpy as np

ALPHABET = 'ACGT'


def normalize(sequence: str) -> str:
    return str(sequence).upper().replace('U', 'T')


def kmer_names(ks) -> list[str]:
    names: list[str] = []
    for k in ks:
        names.extend(''.join(p) for p in itertools.product(ALPHABET, repeat=k))
    return names


def _index(ks) -> dict[str, int]:
    return {name: i for i, name in enumerate(kmer_names(ks))}


def kmer_matrix(sequences, ks=(1, 2, 3, 4, 5)) -> np.ndarray:
    """Sliding-window k-mer counts. Windows containing non-ACGT are skipped."""
    ks = tuple(ks)
    index = _index(ks)
    out = np.zeros((len(sequences), len(index)), dtype=np.float32)
    for row, raw in enumerate(sequences):
        seq = normalize(raw)
        for k in ks:
            for start in range(len(seq) - k + 1):
                slot = index.get(seq[start:start + k])
                if slot is not None:
                    out[row, slot] += 1.0
    return out
