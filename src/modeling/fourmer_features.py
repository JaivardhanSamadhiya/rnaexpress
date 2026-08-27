"""Fixed 4-mer features used by the Mikl published-model reconstruction."""

from __future__ import annotations

from itertools import product
from collections.abc import Sequence

import numpy as np

from .features import normalize_sequence


FOURMER_ORDER = tuple("".join(value) for value in product("ACGT", repeat=4))
FOURMER_INDEX = {value: index for index, value in enumerate(FOURMER_ORDER)}
TRAINING_POSITIONS = 147.0


def fourmer_counts(sequences: Sequence[str], equivalent_150nt: bool = False) -> np.ndarray:
    output = np.zeros((len(sequences), len(FOURMER_ORDER)), dtype=np.float32)
    for row, raw in enumerate(sequences):
        sequence = normalize_sequence(raw)
        positions = len(sequence) - 3
        if positions <= 0:
            raise ValueError("4-mer features require sequences of at least four nucleotides")
        for index in range(positions):
            output[row, FOURMER_INDEX[sequence[index : index + 4]]] += 1.0
        if equivalent_150nt:
            output[row] *= TRAINING_POSITIONS / positions
    return output
