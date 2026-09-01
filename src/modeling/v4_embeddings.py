"""Frozen, projected RNA-language-model features for RNAddress v4.

The module embeds exact aligned parent/mutant pairs and stores three equal-size
blocks: parent absolute, mutant absolute, and contextual intervention delta.
No outcome is accepted by this API.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from .features import normalize_sequence


ROOT = Path(__file__).resolve().parents[2]
PROJECTION_SIZE = 128
PROJECTION_SEED = 41_017
MODEL_SPECS = {
    "3utrbert": {
        "model_id": "yangheng/3utrbert",
        "revision": "220d80829deb077d1d640463a4267a96e9e70b1d",
        "checkpoint_sha256": "7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471",
        "hidden_size": 768,
    },
    "splicebert": {
        "model_id": "SpliceBERT.1024nt",
        "revision": "official Zenodo 7995778 archive",
        "checkpoint_sha256": "2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d",
        "hidden_size": 512,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sequence_hash(sequence: str) -> str:
    return hashlib.sha256(normalize_sequence(sequence).encode("ascii")).hexdigest()


def pair_row_hash(frame: pd.DataFrame) -> str:
    payload = "\n".join(
        f"{sequence_hash(parent)}>{sequence_hash(mutant)}"
        for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _projection(input_size: int, block: str) -> np.ndarray:
    block_seed = int(hashlib.sha256(block.encode("ascii")).hexdigest()[:8], 16)
    rng = np.random.default_rng(PROJECTION_SEED + block_seed)
    matrix = rng.standard_normal((input_size, PROJECTION_SIZE), dtype=np.float32)
    matrix /= np.float32(math.sqrt(PROJECTION_SIZE))
    return matrix


class FrozenEncoder:
    def __init__(self, name: str, backend: str = "torch"):
        if name not in MODEL_SPECS:
            raise ValueError(f"Unknown frozen representation: {name}")
        self.name = name
        self.backend = backend
        self.spec = MODEL_SPECS[name]
        self.hidden_size = int(self.spec["hidden_size"])
        if backend in {"openvino_gpu", "openvino_cpu"}:
            if name != "3utrbert":
                raise ValueError("The audited OpenVINO backend is only available for 3UTRBERT")
            import sys
            from .utrbert_features import MODEL_DIR

            local_runtime = ROOT / ".tf_runtime"
            if local_runtime.exists() and str(local_runtime) not in sys.path:
                sys.path.insert(0, str(local_runtime))
            from transformers import AutoTokenizer
            import openvino as ov

            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
            ir_path = ROOT / "data/interim/v4_phaseB_3utrbert_openvino.xml"
            if not ir_path.exists():
                raise FileNotFoundError("Missing audited 3UTRBERT OpenVINO IR")
            core = ov.Core()
            device = "GPU" if backend == "openvino_gpu" else "CPU"
            if device not in core.available_devices:
                raise RuntimeError(f"OpenVINO {device} backend is not available")
            ov_model = core.read_model(ir_path)
            self.compiled_model = core.compile_model(
                ov_model, device, {"INFERENCE_PRECISION_HINT": "f32"}
            )
            self.model = None
        elif name == "3utrbert":
            from .utrbert_features import load_utrbert

            self.tokenizer, self.model = load_utrbert()
        else:
            from .splicebert_features import load_splicebert

            self.tokenizer, self.model = load_splicebert()
        self.absolute_projection = _projection(self.hidden_size * 2, f"{name}:absolute")
        self.context_projection = _projection(self.hidden_size * 4, f"{name}:context")

    def hidden(self, sequences: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
        normalized = [normalize_sequence(value) for value in sequences]
        if self.name == "3utrbert":
            from .utrbert_features import overlapping_kmers

            tokens = [" ".join(overlapping_kmers(value)) for value in normalized]
            expected = [len(value) for value in normalized]
        else:
            tokens = [" ".join(value) for value in normalized]
            expected = [len(value) + 2 for value in normalized]
        encoded = self.tokenizer(tokens, return_tensors="pt", padding=True)
        observed = encoded["attention_mask"].sum(dim=1).tolist()
        if observed != expected:
            raise ValueError(f"{self.name} token alignment failed: {observed} != {expected}")
        if self.backend in {"openvino_gpu", "openvino_cpu"}:
            ordered = [
                encoded["input_ids"].numpy(),
                encoded["attention_mask"].numpy(),
                encoded["token_type_ids"].numpy(),
            ]
            hidden = torch.from_numpy(np.asarray(self.compiled_model(ordered)[0]))
        else:
            with torch.inference_mode():
                hidden = self.model.bert(**encoded, return_dict=True).last_hidden_state
        if not bool(torch.isfinite(hidden).all()):
            raise ValueError(f"{self.name} generated non-finite hidden states")
        return hidden, encoded["attention_mask"]

    def absolute_raw(self, hidden: torch.Tensor, sequence: str) -> np.ndarray:
        length = len(normalize_sequence(sequence))
        if self.name == "3utrbert":
            token_count = length
            nucleotide = hidden[0, 1 : token_count - 1]
        else:
            token_count = length + 2
            nucleotide = hidden[0, 1 : length + 1]
        if hidden.shape[1] < token_count or nucleotide.shape[0] == 0:
            raise ValueError("Absolute embedding token slice is invalid")
        pooled = torch.cat([hidden[0, 0], nucleotide.mean(dim=0)]).numpy().astype(np.float32)
        if pooled.shape != (self.hidden_size * 2,) or not np.isfinite(pooled).all():
            raise ValueError("Absolute embedding pooling failed")
        return pooled

    def context_raw(
        self,
        parent_hidden: torch.Tensor,
        mutant_hidden: torch.Tensor,
        parent_sequence: str,
        mutant_sequence: str,
        radius: int = 10,
    ) -> np.ndarray:
        parent = normalize_sequence(parent_sequence)
        mutant = normalize_sequence(mutant_sequence)
        if len(parent) != len(mutant):
            raise ValueError("Contextual deltas require aligned equal-length sequences")
        length = len(parent)
        token_count = length if self.name == "3utrbert" else length + 2
        delta = mutant_hidden[0, :token_count] - parent_hidden[0, :token_count]
        if self.name == "3utrbert":
            nucleotide = delta[1 : length - 1]
            changed_positions = [i for i, (left, right) in enumerate(zip(parent, mutant)) if left != right]
            affected_mask = np.zeros(length - 2, dtype=bool)
            local_mask = np.zeros(length - 2, dtype=bool)
            for position in changed_positions:
                affected_mask[max(0, position - 2) : min(position, length - 3) + 1] = True
                left = max(0, position - radius)
                right = min(length - 1, position + radius)
                local_mask[max(0, left - 2) : min(right, length - 3) + 1] = True
        else:
            nucleotide = delta[1 : length + 1]
            changed_mask = np.asarray(
                [left != right for left, right in zip(parent, mutant)], dtype=bool
            )
            changed_positions = np.flatnonzero(changed_mask).tolist()
            affected_mask = changed_mask
            local_mask = np.zeros(length, dtype=bool)
            for position in changed_positions:
                local_mask[max(0, position - radius) : min(length, position + radius + 1)] = True
        if not changed_positions or not affected_mask.any() or not local_mask.any():
            raise ValueError("Contextual delta has no aligned edited region")
        affected = nucleotide[torch.as_tensor(affected_mask)].mean(dim=0)
        local = nucleotide[torch.as_tensor(local_mask)].mean(dim=0)
        pooled = torch.cat([delta[0], nucleotide.mean(dim=0), affected, local]).numpy().astype(
            np.float32
        )
        if pooled.shape != (self.hidden_size * 4,) or not np.isfinite(pooled).all():
            raise ValueError("Contextual delta pooling failed")
        return pooled

    def project_absolute(self, raw: np.ndarray) -> np.ndarray:
        return (raw @ self.absolute_projection).astype(np.float32)

    def project_context(self, raw: np.ndarray) -> np.ndarray:
        return (raw @ self.context_projection).astype(np.float32)


def _embed_singleton_batch(
    encoder: FrozenEncoder,
    frame: pd.DataFrame,
    indices: list[int],
    output: np.memmap,
) -> None:
    parents = frame.iloc[indices]["parent_sequence"].tolist()
    mutants = frame.iloc[indices]["mutant_sequence"].tolist()
    parent_hidden, _ = encoder.hidden(parents)
    mutant_hidden, _ = encoder.hidden(mutants)
    for offset, index in enumerate(indices):
        parent = parents[offset]
        mutant = mutants[offset]
        parent_raw = encoder.absolute_raw(parent_hidden[offset : offset + 1], parent)
        mutant_raw = encoder.absolute_raw(mutant_hidden[offset : offset + 1], mutant)
        context_raw = encoder.context_raw(
            parent_hidden[offset : offset + 1],
            mutant_hidden[offset : offset + 1],
            parent,
            mutant,
        )
        output[index, :PROJECTION_SIZE] = encoder.project_absolute(parent_raw)
        output[index, PROJECTION_SIZE : PROJECTION_SIZE * 2] = encoder.project_absolute(mutant_raw)
        output[index, PROJECTION_SIZE * 2 :] = encoder.project_context(context_raw)


def embed_pairs_resumable(
    frame: pd.DataFrame,
    model_name: str,
    output_path: Path,
    metadata_path: Path,
    batch_size: int = 32,
    backend: str = "torch",
) -> np.ndarray:
    """Embed exact pair rows with restart-safe NaN sentinels.

    Groups with repeated parents reuse one parent forward pass. Singleton
    parents are batched together to avoid thousands of one-row model calls.
    """
    required = {"parent_id", "parent_sequence", "mutant_sequence"}
    if not required <= set(frame):
        raise ValueError(f"Embedding frame is missing {sorted(required - set(frame))}")
    if frame[["parent_sequence", "mutant_sequence"]].isna().any().any():
        raise ValueError("Embedding frame contains missing sequences")
    row_hash = pair_row_hash(frame)
    shape = (len(frame), PROJECTION_SIZE * 3)
    if output_path.exists() and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("row_hash") != row_hash or tuple(metadata.get("shape", [])) != shape:
            raise ValueError("Embedding cache row identity changed")
        output = np.lib.format.open_memmap(output_path, mode="r+")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output = np.lib.format.open_memmap(output_path, mode="w+", dtype=np.float32, shape=shape)
        output[:] = np.nan
        output.flush()
        metadata_path.write_text(
            json.dumps(
                {
                    "model": MODEL_SPECS[model_name],
                    "row_hash": row_hash,
                    "shape": list(shape),
                    "projection_size_per_block": PROJECTION_SIZE,
                    "projection_seed": PROJECTION_SEED,
                    "completed_rows": 0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    complete = np.isfinite(output[:, 0])
    if complete.all():
        return np.asarray(output)

    torch.set_num_threads(4)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    backends = list(metadata.get("inference_backends", []))
    if backend not in backends:
        backends.append(backend)
    metadata["inference_backends"] = backends
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    encoder = FrozenEncoder(model_name, backend=backend)
    groups = frame.groupby("parent_id", sort=True).indices
    singleton_indices: list[int] = []
    processed_groups = 0
    for _, raw_indices in groups.items():
        indices = np.asarray(raw_indices, dtype=int)
        pending = indices[~complete[indices]]
        if len(pending) == 0:
            processed_groups += 1
            continue
        if len(indices) == 1:
            singleton_indices.append(int(indices[0]))
            if len(singleton_indices) >= batch_size:
                _embed_singleton_batch(encoder, frame, singleton_indices, output)
                complete[singleton_indices] = True
                singleton_indices = []
                output.flush()
        else:
            parent_values = frame.iloc[indices]["parent_sequence"].map(normalize_sequence).unique()
            if len(parent_values) != 1:
                raise ValueError("One parent_id maps to multiple exact parent sequences")
            parent = str(parent_values[0])
            parent_hidden, _ = encoder.hidden([parent])
            parent_projected = encoder.project_absolute(encoder.absolute_raw(parent_hidden, parent))
            for first in range(0, len(pending), batch_size):
                batch_indices = pending[first : first + batch_size].tolist()
                mutants = frame.iloc[batch_indices]["mutant_sequence"].tolist()
                mutant_hidden, _ = encoder.hidden(mutants)
                for offset, index in enumerate(batch_indices):
                    mutant = mutants[offset]
                    mutant_row = mutant_hidden[offset : offset + 1]
                    mutant_projected = encoder.project_absolute(
                        encoder.absolute_raw(mutant_row, mutant)
                    )
                    context_projected = encoder.project_context(
                        encoder.context_raw(parent_hidden, mutant_row, parent, mutant)
                    )
                    output[index, :PROJECTION_SIZE] = parent_projected
                    output[index, PROJECTION_SIZE : PROJECTION_SIZE * 2] = mutant_projected
                    output[index, PROJECTION_SIZE * 2 :] = context_projected
                complete[batch_indices] = True
                output.flush()
        processed_groups += 1
        if processed_groups % 100 == 0 or processed_groups == len(groups):
            completed_rows = int(complete.sum())
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["completed_rows"] = completed_rows
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            print(
                f"{model_name}: embedded {completed_rows}/{len(frame)} pairs; "
                f"processed {processed_groups}/{len(groups)} parent groups",
                flush=True,
            )
    if singleton_indices:
        _embed_singleton_batch(encoder, frame, singleton_indices, output)
        complete[singleton_indices] = True
        output.flush()
    if not np.isfinite(output).all():
        raise ValueError(f"{model_name} embedding cache remains incomplete")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["completed_rows"] = len(frame)
    metadata["feature_sha256"] = sha256(output_path)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return np.asarray(output)
