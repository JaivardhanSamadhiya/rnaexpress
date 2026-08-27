"""Absolute sequence embeddings from the frozen official SpliceBERT checkpoint."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import torch

from .features import normalize_sequence
from .splicebert_features import HIDDEN_SIZE, load_splicebert


def pool_absolute_hidden(
    hidden: torch.Tensor,
    attention_mask: torch.Tensor,
) -> np.ndarray:
    """Return concatenated CLS and nucleotide-mean embeddings."""
    if hidden.ndim != 3 or hidden.shape[2] != HIDDEN_SIZE:
        raise ValueError("Unexpected SpliceBERT hidden-state shape")
    if attention_mask.shape != hidden.shape[:2]:
        raise ValueError("SpliceBERT hidden states and attention mask are misaligned")
    nucleotide_mask = attention_mask.clone()
    nucleotide_mask[:, 0] = 0
    lengths = attention_mask.sum(dim=1)
    for row, length in enumerate(lengths.tolist()):
        nucleotide_mask[row, int(length) - 1] = 0
    weights = nucleotide_mask.to(hidden.dtype).unsqueeze(2)
    if not bool((weights.sum(dim=1) > 0).all()):
        raise ValueError("SpliceBERT sequence has no nucleotide tokens")
    nucleotide_mean = (hidden * weights).sum(dim=1) / weights.sum(dim=1)
    pooled = torch.cat([hidden[:, 0], nucleotide_mean], dim=1)
    if not bool(torch.isfinite(pooled).all()):
        raise ValueError("SpliceBERT absolute pooling produced non-finite values")
    return pooled.numpy().astype(np.float32)


def build_splicebert_absolute_features(
    sequences: Sequence[str],
    batch_size: int = 32,
    progress_label: str = "sequences",
) -> np.ndarray:
    tokenizer, model = load_splicebert()
    output = np.empty((len(sequences), HIDDEN_SIZE * 2), dtype=np.float32)
    for first in range(0, len(sequences), batch_size):
        batch = [normalize_sequence(value) for value in sequences[first : first + batch_size]]
        encoded = tokenizer(
            [" ".join(sequence) for sequence in batch],
            return_tensors="pt",
            padding=True,
        )
        observed = encoded["attention_mask"].sum(dim=1).tolist()
        expected = [len(sequence) + 2 for sequence in batch]
        if observed != expected:
            raise ValueError(f"SpliceBERT token alignment failed: {observed} != {expected}")
        with torch.inference_mode():
            hidden = model.bert(**encoded, return_dict=True).last_hidden_state
        output[first : first + len(batch)] = pool_absolute_hidden(
            hidden, encoded["attention_mask"]
        )
        completed = first + len(batch)
        if completed == len(sequences) or completed % (batch_size * 20) == 0:
            print(f"embedded {completed}/{len(sequences)} {progress_label}", flush=True)
    return output
