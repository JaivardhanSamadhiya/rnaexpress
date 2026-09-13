"""Length-invariant, outcome-free sequence features.

Every column is a function of sequence alone. v4 used raw k-mer counts on a
uniform 260 nt source; v5 must score a 150 nt source with a model trained on a
260 nt source, so all features here are FREQUENCIES normalized by the number of
windows of that k.
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


def kmer_frequency(sequences, ks=(1, 2, 3)) -> np.ndarray:
    """Per-k normalized k-mer frequencies. Windows with non-ACGT are skipped."""
    ks = tuple(ks)
    index = {name: i for i, name in enumerate(kmer_names(ks))}
    offsets, cursor = {}, 0
    for k in ks:
        offsets[k] = (cursor, cursor + 4 ** k)
        cursor += 4 ** k
    out = np.zeros((len(sequences), len(index)), dtype=np.float64)
    for row, raw in enumerate(sequences):
        seq = normalize(raw)
        for k in ks:
            start_slot, end_slot = offsets[k]
            counted = 0
            for start in range(len(seq) - k + 1):
                slot = index.get(seq[start:start + k])
                if slot is not None:
                    out[row, slot] += 1.0
                    counted += 1
            if counted:
                out[row, start_slot:end_slot] /= counted
    return out


def delta_frequency(mutants, parents, ks=(1, 2, 3)) -> np.ndarray:
    """Finite difference in k-mer frequency space: mutant minus parent."""
    return kmer_frequency(mutants, ks) - kmer_frequency(parents, ks)


def au_fraction(sequence: str) -> float:
    seq = normalize(sequence)
    if not seq:
        return 0.0
    return (seq.count('A') + seq.count('T')) / len(seq)


def au_delta(mutants, parents) -> np.ndarray:
    """Single-column control: change in AU fraction."""
    return np.array([[au_fraction(m) - au_fraction(p)]
                     for m, p in zip(mutants, parents)], dtype=np.float64)


def random_projection(features: np.ndarray, seed: int, width: int) -> np.ndarray:
    """Seeded random projection reproducing the v2/N4 null that beat the real stack."""
    rng = np.random.default_rng(seed)
    basis = rng.normal(size=(features.shape[1], width))
    return features @ basis
