"""Run the frozen explanatory 3UTRBERT representation ablations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.features import normalize_sequence
from src.modeling.utrbert_features import sha256_bytes
from src.modeling.v3_nested import directional_metrics, macro_metrics, nested_ridge


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2/nzip_development_predictions.csv.gz"
INTERIM = ROOT / "data/interim"
OUT = ROOT / "results/v3_phase3"


def _absolute_rows(frame: pd.DataFrame, column: str) -> np.ndarray:
    features = np.load(INTERIM / "v3_3utrbert_absolute_features.npy", allow_pickle=False)
    sequences = np.load(INTERIM / "v3_3utrbert_absolute_sequences.npy", allow_pickle=False)
    lookup = {
        sha256_bytes(normalize_sequence(sequence)): features[index]
        for index, sequence in enumerate(sequences)
    }
    return np.vstack(
        [lookup[sha256_bytes(normalize_sequence(value))] for value in frame[column]]
    ).astype(np.float32)


def _run_or_load(name: str, target: str, frame: pd.DataFrame, features: np.ndarray):
    path = INTERIM / f"v3_representation_ablation_{name}_{target}.npy"
    tuning_path = INTERIM / f"v3_representation_ablation_{name}_{target}_tuning.csv"
    if path.exists() and tuning_path.exists():
        print(f"loaded representation ablation {name}/{target}", flush=True)
        return np.load(path, allow_pickle=False), pd.read_csv(tuning_path)
    result = nested_ridge(frame, features, target)
    np.save(path, result.prediction, allow_pickle=False)
    result.tuning.to_csv(tuning_path, index=False, lineterminator="\n")
    return result.prediction, result.tuning


def main() -> None:
    frame = pd.read_csv(SOURCE)
    context = np.load(INTERIM / "v3_3utrbert_delta_features.npy", allow_pickle=False)
    parent_absolute = _absolute_rows(frame, "parent_sequence")
    mutant_absolute = _absolute_rows(frame, "mutant_sequence")
    feature_sets = {
        "parent_absolute": parent_absolute,
        "mutant_absolute": mutant_absolute,
        "global_mutant_minus_parent_delta": context[:, :1536],
        "local_edited_region_delta": context[:, 1536:3072],
        "combined_delta_plus_edit": context,
    }
    prediction_output = frame[["source_row", "parent_id", "delta_localization"]].copy()
    metric_tables = []
    summary_rows = []
    tuning_tables = []
    for name, features in feature_sets.items():
        rank_prediction, rank_tuning = _run_or_load(name, "rank", frame, features)
        magnitude_prediction, magnitude_tuning = _run_or_load(
            name, "magnitude", frame, features
        )
        prediction_output[f"{name}_rank"] = rank_prediction
        prediction_output[f"{name}_magnitude"] = magnitude_prediction
        for target, prediction, tuning in (
            ("rank", rank_prediction, rank_tuning),
            ("magnitude", magnitude_prediction, magnitude_tuning),
        ):
            metrics = directional_metrics(frame, prediction, -prediction, model=name)
            metrics.insert(1, "target", target)
            metric_tables.append(metrics)
            row = macro_metrics(metrics)
            row["representation_ablation"] = name
            row["target"] = target
            row["feature_count"] = features.shape[1]
            summary_rows.append(row)
            table = tuning.copy()
            table.insert(0, "representation_ablation", name)
            tuning_tables.append(table)
    prediction_output.to_csv(
        OUT / "representation_ablation_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    pd.concat(metric_tables, ignore_index=True).to_csv(
        OUT / "representation_ablation_parent_direction_metrics.csv",
        index=False,
        lineterminator="\n",
    )
    pd.DataFrame(summary_rows).to_csv(
        OUT / "representation_ablation_macro_metrics.csv", index=False, lineterminator="\n"
    )
    pd.concat(tuning_tables, ignore_index=True).to_csv(
        OUT / "representation_ablation_inner_selections.csv",
        index=False,
        lineterminator="\n",
    )
    manifest = {
        "phase": "v3_phase3_representation_ablations",
        "representation": "3utrbert_3mer",
        "ablation_count": len(feature_sets),
        "targets": ["rank", "magnitude"],
        "selection_use": "explanatory_only_not_a_sixth_candidate",
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "representation_ablation_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
