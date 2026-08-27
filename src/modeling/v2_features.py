"""Length-tolerant, outcome-independent RNAddress v2 sequence/edit features."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .features import BASE_INDEX, kmer_delta, kmer_frequencies, local_one_hot, normalize_sequence


FIXED_MOTIFS = (
    "ATATAT",  # AU repeat
    "TATATA",
    "TGTAT",  # let-7-family seed-related DNA spelling
    "GTGTG",  # TDP-43 canonical motifs
    "TGTGT",
    "GTATG",
    "ACTAA",  # compact QRE-like cores
    "CTAAC",
    "GATG",
    "GGAGG",  # purine-rich / G-quadruplex-adjacent summaries
)


@dataclass
class V2Features:
    parent: np.ndarray
    edit: np.ndarray
    joint: np.ndarray


def _changed_positions(parent: str, mutant: str) -> list[int]:
    return [index for index, (left, right) in enumerate(zip(parent, mutant)) if left != right]


def _motif_features(sequence: str) -> np.ndarray:
    length = max(1, len(sequence))
    fixed = [
        sum(1 for _ in re.finditer(f"(?={motif})", sequence)) / length
        for motif in FIXED_MOTIFS
    ]
    ag = np.fromiter((base in "AG" for base in sequence), dtype=float)
    max_ag_25 = max(
        (float(ag[start : start + 25].mean()) for start in range(max(1, length - 24))),
        default=float(ag.mean()),
    )
    g_runs = len(re.findall(r"G{3,}", sequence)) / length
    return np.asarray([*fixed, max_ag_25, g_runs], dtype=np.float32)


def _substitution_counts(parent: str, mutant: str, changed: list[int]) -> np.ndarray:
    output = np.zeros(16, dtype=np.float32)
    for position in changed:
        output[BASE_INDEX[parent[position]] * 4 + BASE_INDEX[mutant[position]]] += 1.0
    if changed:
        output /= len(changed)
    return output


def build_v2_features(frame: pd.DataFrame, radius: int = 10) -> V2Features:
    parent_rows: list[np.ndarray] = []
    edit_rows: list[np.ndarray] = []
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        if len(parent) != len(mutant):
            raise ValueError("v2 features require length-preserving interventions")
        changed = _changed_positions(parent, mutant)
        if not changed:
            raise ValueError("v2 intervention has no sequence change")
        center = int(round(float(np.mean(changed))))
        relative = np.asarray(changed, dtype=float) / max(1, len(parent) - 1)
        x = float(np.mean(relative))
        edge = min(float(np.min(relative)), float(1.0 - np.max(relative)))
        positional = [x, edge, float(np.ptp(relative)), len(changed) / len(parent)]
        for frequency in (1.0, 2.0, 4.0, 8.0):
            positional.extend(
                [np.sin(2 * np.pi * frequency * x), np.cos(2 * np.pi * frequency * x)]
            )

        parent_kmer = kmer_frequencies(parent, (1, 2, 3, 4))
        mutant_kmer = kmer_frequencies(mutant, (1, 2, 3, 4))
        parent_motif = _motif_features(parent)
        mutant_motif = _motif_features(mutant)
        parent_vector = np.concatenate(
            [
                parent_kmer,
                parent_motif,
                np.asarray(
                    [
                        len(parent) / 260.0,
                        (parent.count("G") + parent.count("C")) / len(parent),
                        (parent.count("A") + parent.count("G")) / len(parent),
                    ],
                    dtype=np.float32,
                ),
            ]
        )
        edit_vector = np.concatenate(
            [
                kmer_delta(parent, mutant, (1, 2, 3, 4)),
                local_one_hot(parent, center, radius),
                local_one_hot(mutant, center, radius),
                _substitution_counts(parent, mutant, changed),
                mutant_motif - parent_motif,
                np.asarray(positional, dtype=np.float32),
            ]
        )
        parent_rows.append(parent_vector)
        edit_rows.append(edit_vector)
    parent_array = np.vstack(parent_rows).astype(np.float32)
    edit_array = np.vstack(edit_rows).astype(np.float32)
    return V2Features(
        parent=parent_array,
        edit=edit_array,
        joint=np.column_stack([parent_array, edit_array]).astype(np.float32),
    )


def absolute_sequence_features(sequences: pd.Series | list[str]) -> np.ndarray:
    rows = []
    for raw in sequences:
        sequence = normalize_sequence(raw)
        rows.append(
            np.concatenate(
                [
                    kmer_frequencies(sequence, (1, 2, 3, 4)),
                    _motif_features(sequence),
                    np.asarray(
                        [
                            len(sequence) / 260.0,
                            (sequence.count("G") + sequence.count("C")) / len(sequence),
                            (sequence.count("A") + sequence.count("G")) / len(sequence),
                        ],
                        dtype=np.float32,
                    ),
                ]
            )
        )
    return np.vstack(rows).astype(np.float32)
