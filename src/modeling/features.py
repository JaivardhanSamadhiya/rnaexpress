"""Sequence and edit feature construction with no outcome-dependent inputs."""

from __future__ import annotations

from functools import lru_cache
from itertools import product

import numpy as np
import pandas as pd


BASES = "ACGT"
BASE_INDEX = {base: i for i, base in enumerate(BASES)}


@lru_cache(maxsize=None)
def vocabulary(k: int) -> tuple[str, ...]:
    return tuple("".join(chars) for chars in product(BASES, repeat=k))


@lru_cache(maxsize=None)
def vocabulary_index(k: int) -> dict[str, int]:
    return {word: i for i, word in enumerate(vocabulary(k))}


def normalize_sequence(sequence: object) -> str:
    return str(sequence).upper().replace("U", "T")


def positional_one_hot(sequence: str, max_length: int) -> np.ndarray:
    output = np.zeros(max_length * 4, dtype=np.float32)
    for position, base in enumerate(sequence[:max_length]):
        if base in BASE_INDEX:
            output[position * 4 + BASE_INDEX[base]] = 1.0
    return output


@lru_cache(maxsize=200_000)
def kmer_frequencies(sequence: str, ks: tuple[int, ...] = (2, 3, 4)) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for k in ks:
        values = np.zeros(4**k, dtype=np.float32)
        index = vocabulary_index(k)
        denominator = max(1, len(sequence) - k + 1)
        for start in range(len(sequence) - k + 1):
            word = sequence[start : start + k]
            if word in index:
                values[index[word]] += 1.0 / denominator
        pieces.append(values)
    return np.concatenate(pieces)


@lru_cache(maxsize=200_000)
def _sequence_features_cached(seq: str, max_length: int) -> np.ndarray:
    gc = (seq.count("G") + seq.count("C")) / max(1, len(seq))
    return np.concatenate(
        [
            positional_one_hot(seq, max_length),
            kmer_frequencies(seq),
            np.array([len(seq) / max_length, gc], dtype=np.float32),
        ]
    )


def sequence_features(sequence: object, max_length: int = 100) -> np.ndarray:
    return _sequence_features_cached(normalize_sequence(sequence), max_length)


def local_one_hot(sequence: str, position: int, radius: int) -> np.ndarray:
    # A/C/G/T plus explicit padding channel.
    output = np.zeros((2 * radius + 1) * 5, dtype=np.float32)
    for offset in range(-radius, radius + 1):
        source = position + offset
        target = (offset + radius) * 5
        if source < 0 or source >= len(sequence):
            output[target + 4] = 1.0
        else:
            base = sequence[source]
            output[target + BASE_INDEX.get(base, 4)] = 1.0
    return output


def kmer_delta(parent: str, mutant: str, ks: tuple[int, ...] = (2, 3, 4)) -> np.ndarray:
    return kmer_frequencies(mutant, ks) - kmer_frequencies(parent, ks)


def compact_intervention_features(frame: pd.DataFrame) -> np.ndarray:
    """Length-tolerant features shared by N-zip SNVs and Mikl replacements."""
    rows: list[np.ndarray] = []
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        edit_count = float(getattr(row, "edit_count", sum(a != b for a, b in zip(parent, mutant))))
        rows.append(
            np.concatenate(
                [
                    kmer_frequencies(parent),
                    kmer_delta(parent, mutant),
                    np.array(
                        [
                            len(parent) / 200.0,
                            edit_count / max(1.0, len(parent)),
                            (parent.count("G") + parent.count("C")) / len(parent),
                            (mutant.count("G") + mutant.count("C")) / len(mutant),
                        ],
                        dtype=np.float32,
                    ),
                ]
            )
        )
    return np.vstack(rows)


def intervention_features(
    frame: pd.DataFrame,
    radius: int = 10,
    max_length: int = 100,
    extra_feature: np.ndarray | None = None,
) -> np.ndarray:
    rows: list[np.ndarray] = []
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        position = int(row.edit_position_0based)
        substitution = np.zeros(16, dtype=np.float32)
        substitution[BASE_INDEX[row.reference_nt] * 4 + BASE_INDEX[row.alternate_nt]] = 1.0
        local = parent[max(0, position - radius) : position + radius + 1]
        local_gc = (local.count("G") + local.count("C")) / max(1, len(local))
        edge = min(position, len(parent) - position - 1) / max(1, len(parent) - 1)
        pieces = [
            sequence_features(parent, max_length=max_length),
            local_one_hot(parent, position, radius),
            substitution,
            kmer_delta(parent, mutant),
            np.array(
                [position / max(1, len(parent) - 1), edge, local_gc], dtype=np.float32
            ),
        ]
        rows.append(np.concatenate(pieces))
    output = np.vstack(rows)
    if extra_feature is not None:
        output = np.column_stack([output, np.asarray(extra_feature, dtype=np.float32)])
    return output


def local_features(frame: pd.DataFrame, radius: int) -> np.ndarray:
    rows: list[np.ndarray] = []
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        position = int(row.edit_position_0based)
        substitution = np.zeros(16, dtype=np.float32)
        substitution[BASE_INDEX[row.reference_nt] * 4 + BASE_INDEX[row.alternate_nt]] = 1.0
        local = parent[max(0, position - radius) : position + radius + 1]
        rows.append(
            np.concatenate(
                [
                    local_one_hot(parent, position, radius),
                    substitution,
                    np.array(
                        [
                            position / max(1, len(parent) - 1),
                            (parent.count("G") + parent.count("C")) / len(parent),
                            (local.count("G") + local.count("C")) / max(1, len(local)),
                        ],
                        dtype=np.float32,
                    ),
                ]
            )
        )
    return np.vstack(rows)


def centered_context(sequence: str, position: int, radius: int) -> str:
    chars = []
    for offset in range(-radius, radius + 1):
        source = position + offset
        chars.append(sequence[source] if 0 <= source < len(sequence) else "N")
    return "".join(chars)
