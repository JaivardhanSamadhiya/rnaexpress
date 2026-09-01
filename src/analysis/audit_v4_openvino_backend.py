"""Build and numerically audit the FP32 OpenVINO 3UTRBERT backend."""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.utrbert_features import overlapping_kmers
from src.modeling.v4_embeddings import FrozenEncoder, sha256


IR = ROOT / "data/interim/v4_phaseB_3utrbert_openvino.xml"
OUT = ROOT / "results/v4_phaseB/openvino_backend_equivalence.json"
BENCHMARK = ROOT / "results/v4_phaseB/representation_benchmark_interventions.csv.gz"


def build_ir() -> None:
    if IR.exists() and IR.with_suffix(".bin").exists():
        return
    import openvino as ov
    from src.modeling.utrbert_features import load_utrbert

    tokenizer, masked_model = load_utrbert()

    class BertWrapper(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                return_dict=False,
            )[0]

    sequence = "ACGT" * 37 + "AC"
    encoded = tokenizer(
        [" ".join(overlapping_kmers(sequence))] * 2,
        return_tensors="pt",
        padding=True,
    )
    example = (
        encoded["input_ids"],
        encoded["attention_mask"],
        encoded["token_type_ids"],
    )
    converted = ov.convert_model(BertWrapper(masked_model.bert).eval(), example_input=example)
    ov.save_model(converted, IR, compress_to_fp16=False)


def pair_feature(encoder: FrozenEncoder, row: pd.Series) -> np.ndarray:
    parent = str(row["parent_sequence"])
    mutant = str(row["mutant_sequence"])
    parent_hidden, _ = encoder.hidden([parent])
    mutant_hidden, _ = encoder.hidden([mutant])
    return np.concatenate(
        [
            encoder.project_absolute(encoder.absolute_raw(parent_hidden, parent)),
            encoder.project_absolute(encoder.absolute_raw(mutant_hidden, mutant)),
            encoder.project_context(
                encoder.context_raw(parent_hidden, mutant_hidden, parent, mutant)
            ),
        ]
    )


def main() -> None:
    build_ir()
    frame = pd.read_csv(BENCHMARK)
    sample_indices = np.linspace(0, len(frame) - 1, 12, dtype=int)
    sample = frame.iloc[sample_indices].reset_index(drop=True)
    start = time.perf_counter()
    torch_encoder = FrozenEncoder("3utrbert", backend="torch")
    torch_features = np.row_stack(
        [pair_feature(torch_encoder, row) for _, row in sample.iterrows()]
    )
    torch_seconds = time.perf_counter() - start
    del torch_encoder
    gc.collect()
    backend_results = {}
    accepted = True
    for backend in ("openvino_gpu", "openvino_cpu"):
        start = time.perf_counter()
        encoder = FrozenEncoder("3utrbert", backend=backend)
        features = np.row_stack([pair_feature(encoder, row) for _, row in sample.iterrows()])
        seconds = time.perf_counter() - start
        difference = np.abs(torch_features - features)
        cosine = np.sum(torch_features * features, axis=1) / (
            np.linalg.norm(torch_features, axis=1) * np.linalg.norm(features, axis=1)
        )
        backend_accepted = bool(
            difference.max() <= 0.001
            and difference.mean() <= 0.0001
            and cosine.min() >= 0.999999
        )
        accepted = accepted and backend_accepted
        backend_results[backend] = {
            "maximum_projected_feature_absolute_difference": float(difference.max()),
            "mean_projected_feature_absolute_difference": float(difference.mean()),
            "minimum_pair_feature_cosine_similarity": float(cosine.min()),
            "seconds_including_compile": seconds,
            "accepted": backend_accepted,
        }
    audit = {
        "backend": "OpenVINO 2026.3.1 FP32",
        "devices": ["Intel Iris Xe integrated GPU", "Intel CPU"],
        "sample_pairs": len(sample),
        "sample_pair_row_indices": sample_indices.tolist(),
        "torch_seconds": torch_seconds,
        "backend_results": backend_results,
        "acceptance_thresholds": {
            "maximum_absolute_difference_lte": 0.001,
            "mean_absolute_difference_lte": 0.0001,
            "minimum_cosine_similarity_gte": 0.999999,
        },
        "accepted": accepted,
        "ir_xml_sha256": sha256(IR),
        "ir_bin_sha256": sha256(IR.with_suffix(".bin")),
        "scope_guards": {"outcomes_opened": False, "nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
    }
    OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if not audit["accepted"]:
        raise ValueError("OpenVINO backend did not pass the frozen numerical equivalence tolerance")


if __name__ == "__main__":
    main()
