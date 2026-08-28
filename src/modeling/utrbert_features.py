"""Frozen 3UTRBERT 3-mer features for RNAddress v3 development."""

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
MODEL_DIR = ROOT / "data/external/3utrbert/yangheng-3utrbert"
MODEL_SHA256 = "7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471"
HIDDEN_SIZE = 768
KMER = 3


def sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def overlapping_kmers(sequence: str, k: int = KMER) -> list[str]:
    normalized = normalize_sequence(sequence).replace("T", "U")
    if len(normalized) < k:
        raise ValueError(f"3UTRBERT requires at least {k} nucleotides")
    return [normalized[start : start + k] for start in range(len(normalized) - k + 1)]


def load_utrbert(model_dir: Path = MODEL_DIR):
    weight_path = model_dir / "pytorch_model.bin"
    if _sha256(weight_path) != MODEL_SHA256:
        raise ValueError("3UTRBERT checkpoint hash does not match the frozen manifest")
    local_runtime = ROOT / ".tf_runtime"
    if local_runtime.exists() and str(local_runtime) not in sys.path:
        sys.path.insert(0, str(local_runtime))
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(model_dir, local_files_only=True)
    model.eval()
    return tokenizer, model


def _token_hidden(tokenizer, model, sequences: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
    tokens = [" ".join(overlapping_kmers(sequence)) for sequence in sequences]
    encoded = tokenizer(tokens, return_tensors="pt", padding=True)
    observed = encoded["attention_mask"].sum(dim=1).tolist()
    expected = [len(normalize_sequence(sequence)) for sequence in sequences]
    if observed != expected:
        raise ValueError(f"3UTRBERT token alignment failed: {observed} != {expected}")
    with torch.inference_mode():
        hidden = model.bert(**encoded, return_dict=True).last_hidden_state
    if not bool(torch.isfinite(hidden).all()):
        raise ValueError("3UTRBERT produced non-finite hidden states")
    return hidden, encoded["attention_mask"]


def pool_absolute(hidden: torch.Tensor, sequence_length: int) -> np.ndarray:
    expected_tokens = sequence_length
    if hidden.shape != (1, expected_tokens, HIDDEN_SIZE):
        raise ValueError(f"Unexpected 3UTRBERT hidden shape: {tuple(hidden.shape)}")
    valid_kmers = hidden[:, 1 : expected_tokens - 1]
    pooled = torch.cat([hidden[:, 0], valid_kmers.mean(dim=1)], dim=1)
    return pooled.numpy().astype(np.float32)


def pool_contextual_delta(
    parent_hidden: torch.Tensor,
    mutant_hidden: torch.Tensor,
    parent_sequence: str,
    mutant_sequences: list[str],
    radius: int = 10,
) -> np.ndarray:
    """Pool CLS/global/affected-3-mer/local mutant-minus-parent deltas."""
    parent = normalize_sequence(parent_sequence)
    mutants = [normalize_sequence(sequence) for sequence in mutant_sequences]
    if any(len(mutant) != len(parent) for mutant in mutants):
        raise ValueError("3UTRBERT contextual deltas require length-preserving edits")
    expected_tokens = len(parent)
    if parent_hidden.shape != (1, expected_tokens, HIDDEN_SIZE):
        raise ValueError("Unexpected parent 3UTRBERT hidden-state shape")
    if mutant_hidden.shape != (len(mutants), expected_tokens, HIDDEN_SIZE):
        raise ValueError("Unexpected mutant 3UTRBERT hidden-state shape")

    delta = mutant_hidden - parent_hidden
    kmer_delta = delta[:, 1 : expected_tokens - 1]
    affected_mask = np.zeros((len(mutants), len(parent) - KMER + 1), dtype=bool)
    local_mask = np.zeros_like(affected_mask)
    for row, mutant in enumerate(mutants):
        changed = [index for index, (left, right) in enumerate(zip(parent, mutant)) if left != right]
        if not changed:
            raise ValueError("Every intervention must change at least one nucleotide")
        for position in changed:
            first = max(0, position - (KMER - 1))
            last = min(position, len(parent) - KMER)
            affected_mask[row, first : last + 1] = True
            left = max(0, position - radius)
            right = min(len(parent) - 1, position + radius)
            local_first = max(0, left - (KMER - 1))
            local_last = min(right, len(parent) - KMER)
            local_mask[row, local_first : local_last + 1] = True

    affected = torch.as_tensor(affected_mask, dtype=kmer_delta.dtype).unsqueeze(2)
    local = torch.as_tensor(local_mask, dtype=kmer_delta.dtype).unsqueeze(2)
    affected_mean = (kmer_delta * affected).sum(dim=1) / affected.sum(dim=1)
    local_mean = (kmer_delta * local).sum(dim=1) / local.sum(dim=1)
    pooled = torch.cat(
        [
            delta[:, 0],
            kmer_delta.mean(dim=1),
            affected_mean,
            local_mean,
        ],
        dim=1,
    )
    output = pooled.numpy().astype(np.float32)
    if output.shape != (len(mutants), HIDDEN_SIZE * 4) or not np.isfinite(output).all():
        raise ValueError("Invalid pooled 3UTRBERT contextual features")
    return output


def build_utrbert_delta_features(
    frame: pd.DataFrame,
    batch_size: int = 32,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return pair features and unique-sequence absolute feature caches."""
    tokenizer, model = load_utrbert()
    contextual = np.empty((len(frame), HIDDEN_SIZE * 4), dtype=np.float32)
    absolute_by_hash: dict[str, np.ndarray] = {}
    sequence_by_hash: dict[str, str] = {}

    for parent_number, (parent_id, indices) in enumerate(
        frame.groupby("parent_id", sort=True).indices.items(), start=1
    ):
        indices = np.asarray(indices, dtype=int)
        group = frame.iloc[indices]
        parents = group["parent_sequence"].map(normalize_sequence).unique()
        if len(parents) != 1:
            raise ValueError(f"Parent sequence changed within {parent_id}")
        parent = str(parents[0])
        parent_hidden, _ = _token_hidden(tokenizer, model, [parent])
        parent_hash = sha256_bytes(parent)
        absolute_by_hash[parent_hash] = pool_absolute(parent_hidden, len(parent))[0]
        sequence_by_hash[parent_hash] = parent

        for first in range(0, len(indices), batch_size):
            batch_indices = indices[first : first + batch_size]
            mutants = frame.iloc[batch_indices]["mutant_sequence"].map(normalize_sequence).tolist()
            mutant_hidden, _ = _token_hidden(tokenizer, model, mutants)
            contextual[batch_indices] = pool_contextual_delta(
                parent_hidden, mutant_hidden, parent, mutants
            )
            for offset, mutant in enumerate(mutants):
                sequence_hash = sha256_bytes(mutant)
                tokens = len(mutant)
                absolute_by_hash[sequence_hash] = pool_absolute(
                    mutant_hidden[offset : offset + 1, :tokens], len(mutant)
                )[0]
                sequence_by_hash[sequence_hash] = mutant
        print(f"embedded 3UTRBERT parent {parent_number}/15: {parent_id}", flush=True)

    edit = build_v2_features(frame).edit
    features = np.column_stack([contextual, edit]).astype(np.float32)
    hashes = np.asarray(sorted(absolute_by_hash), dtype="U64")
    absolute = np.vstack([absolute_by_hash[key] for key in hashes]).astype(np.float32)
    sequences = np.asarray([sequence_by_hash[key] for key in hashes])
    if len(hashes) != 4_410 or absolute.shape != (4_410, HIDDEN_SIZE * 2):
        raise ValueError(f"Unexpected 3UTRBERT absolute cache shape: {absolute.shape}")
    return features, hashes, sequences, absolute
