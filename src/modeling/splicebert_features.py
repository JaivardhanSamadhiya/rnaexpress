"""Frozen SpliceBERT contextual-delta features for RNAddress v2.2."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from .features import normalize_sequence
from .v2_features import build_v2_features


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "data" / "external" / "splicebert" / "models" / "SpliceBERT.1024nt"
MODEL_SHA256 = "2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d"
HIDDEN_SIZE = 512


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_splicebert(model_dir: Path = MODEL_DIR):
    weight_path = model_dir / "pytorch_model.bin"
    if _sha256(weight_path) != MODEL_SHA256:
        raise ValueError("SpliceBERT checkpoint hash does not match the frozen manifest")
    local_runtime = ROOT / ".tf_runtime"
    if local_runtime.exists():
        sys.path.insert(0, str(local_runtime))
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(model_dir, local_files_only=True)
    model.eval()
    return tokenizer, model


def _token_hidden(tokenizer, model, sequences: list[str]) -> torch.Tensor:
    normalized = [normalize_sequence(sequence) for sequence in sequences]
    encoded = tokenizer(
        [" ".join(sequence) for sequence in normalized],
        return_tensors="pt",
        padding=True,
    )
    observed = encoded["attention_mask"].sum(dim=1).tolist()
    expected = [len(sequence) + 2 for sequence in normalized]
    if observed != expected:
        raise ValueError(f"SpliceBERT token alignment failed: {observed} != {expected}")
    with torch.inference_mode():
        hidden = model.bert(**encoded, return_dict=True).last_hidden_state
    if not bool(torch.isfinite(hidden).all()):
        raise ValueError("SpliceBERT produced non-finite hidden states")
    return hidden


def pool_contextual_delta(
    parent_hidden: torch.Tensor,
    mutant_hidden: torch.Tensor,
    parent_sequence: str,
    mutant_sequences: list[str],
    radius: int = 10,
) -> np.ndarray:
    """Pool CLS/global/edit/window mutant-minus-parent hidden-state changes."""
    parent = normalize_sequence(parent_sequence)
    mutants = [normalize_sequence(sequence) for sequence in mutant_sequences]
    if any(len(sequence) != len(parent) for sequence in mutants):
        raise ValueError("SpliceBERT contextual deltas require length-preserving edits")
    if parent_hidden.shape != (1, len(parent) + 2, HIDDEN_SIZE):
        raise ValueError("Unexpected parent hidden-state shape")
    if mutant_hidden.shape != (len(mutants), len(parent) + 2, HIDDEN_SIZE):
        raise ValueError("Unexpected mutant hidden-state shape")

    delta = mutant_hidden - parent_hidden
    nucleotide_delta = delta[:, 1 : len(parent) + 1]
    changed_mask = np.asarray(
        [[left != right for left, right in zip(parent, mutant)] for mutant in mutants],
        dtype=bool,
    )
    if not changed_mask.any(axis=1).all():
        raise ValueError("Every intervention must change at least one nucleotide")
    window_mask = np.zeros_like(changed_mask)
    for row, changed in enumerate(changed_mask):
        positions = np.flatnonzero(changed)
        for position in positions:
            first = max(0, int(position) - radius)
            last = min(len(parent), int(position) + radius + 1)
            window_mask[row, first:last] = True

    changed = torch.as_tensor(changed_mask, dtype=nucleotide_delta.dtype).unsqueeze(2)
    window = torch.as_tensor(window_mask, dtype=nucleotide_delta.dtype).unsqueeze(2)
    changed_mean = (nucleotide_delta * changed).sum(dim=1) / changed.sum(dim=1)
    window_mean = (nucleotide_delta * window).sum(dim=1) / window.sum(dim=1)
    pooled = torch.cat(
        [
            delta[:, 0],
            nucleotide_delta.mean(dim=1),
            changed_mean,
            window_mean,
        ],
        dim=1,
    )
    return pooled.numpy().astype(np.float32)


def build_splicebert_delta_features(
    frame: pd.DataFrame,
    batch_size: int = 32,
) -> np.ndarray:
    tokenizer, model = load_splicebert()
    contextual = np.empty((len(frame), HIDDEN_SIZE * 4), dtype=np.float32)
    for parent_number, (parent_id, indices) in enumerate(
        frame.groupby("parent_id", sort=True).indices.items(), start=1
    ):
        indices = np.asarray(indices, dtype=int)
        group = frame.iloc[indices]
        parents = group["parent_sequence"].map(normalize_sequence).unique()
        if len(parents) != 1:
            raise ValueError(f"Parent sequence changed within {parent_id}")
        parent = str(parents[0])
        parent_hidden = _token_hidden(tokenizer, model, [parent])
        for first in range(0, len(indices), batch_size):
            batch_indices = indices[first : first + batch_size]
            mutants = frame.iloc[batch_indices]["mutant_sequence"].tolist()
            mutant_hidden = _token_hidden(tokenizer, model, mutants)
            contextual[batch_indices] = pool_contextual_delta(
                parent_hidden, mutant_hidden, parent, mutants
            )
        print(
            f"embedded SpliceBERT parent {parent_number}/15: {parent_id}",
            flush=True,
        )
    edit = build_v2_features(frame).edit
    return np.column_stack([contextual, edit]).astype(np.float32)


def build_splicebert_paired_delta_features(
    frame: pd.DataFrame,
    batch_size: int = 32,
) -> np.ndarray:
    """Build the same frozen delta vector for one parent/mutant pair per row.

    Unlike ``build_splicebert_delta_features``, this batches distinct parent
    sequences together. It is intended for assays such as the TDP-43 MPRA in
    which every oligo is its own parent context. The pooling operation and the
    appended v2 edit vector are otherwise identical.
    """
    tokenizer, model = load_splicebert()
    contextual = np.empty((len(frame), HIDDEN_SIZE * 4), dtype=np.float32)
    for first in range(0, len(frame), batch_size):
        last = min(len(frame), first + batch_size)
        batch = frame.iloc[first:last]
        parents = batch["parent_sequence"].map(normalize_sequence).tolist()
        mutants = batch["mutant_sequence"].map(normalize_sequence).tolist()
        if any(len(parent) != len(mutant) for parent, mutant in zip(parents, mutants)):
            raise ValueError("SpliceBERT contextual deltas require length-preserving edits")
        parent_hidden = _token_hidden(tokenizer, model, parents)
        mutant_hidden = _token_hidden(tokenizer, model, mutants)
        for offset, (parent, mutant) in enumerate(zip(parents, mutants)):
            tokens = len(parent) + 2
            contextual[first + offset] = pool_contextual_delta(
                parent_hidden[offset : offset + 1, :tokens],
                mutant_hidden[offset : offset + 1, :tokens],
                parent,
                [mutant],
            )[0]
        if last % (batch_size * 10) == 0 or last == len(frame):
            print(f"embedded SpliceBERT pairs {last}/{len(frame)}", flush=True)
    edit = build_v2_features(frame).edit
    return np.column_stack([contextual, edit]).astype(np.float32)
