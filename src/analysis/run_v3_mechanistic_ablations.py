"""Run the frozen grouped mechanistic ablations for the C3 architecture."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.v3_mechanistic_features import build_mechanistic_features
from src.modeling.v3_nested import (
    NestedResult,
    directional_metrics,
    macro_metrics,
    nested_magnitude,
    nested_ridge,
    selection_score,
)
from src.modeling.v3_stacking import rank_magnitude_stack


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
CONTEXT = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
STRUCTURE = ROOT / "data/interim/v3_nzip_structure_cache.json"
STABILITY = ROOT / "data/interim/v3_nzip_tdp_stability_prediction.npy"
INTERIM = ROOT / "data/interim/v3_mechanistic_ablations"
CANDIDATE_INTERIM = ROOT / "data/interim/v3_candidate_nested"
OUT = ROOT / "results/v3_phase3"
SEED = 20260828


def _load_nested(directory: Path, name: str) -> NestedResult:
    arrays = np.load(directory / f"{name}.npz", allow_pickle=False)
    return NestedResult(
        arrays["prediction"],
        pd.read_csv(directory / f"{name}_tuning.csv"),
        arrays["inner_prediction"],
    )


def _run_or_load(name: str, component: str, frame: pd.DataFrame, features: np.ndarray):
    INTERIM.mkdir(parents=True, exist_ok=True)
    stem = f"{name}_{component}"
    path = INTERIM / f"{stem}.npz"
    tuning_path = INTERIM / f"{stem}_tuning.csv"
    if path.exists() and tuning_path.exists():
        print(f"loaded mechanistic ablation {name}/{component}", flush=True)
        arrays = np.load(path, allow_pickle=False)
        return NestedResult(
            arrays["prediction"], pd.read_csv(tuning_path), arrays["inner_prediction"]
        )
    result = (
        nested_ridge(frame, features, "rank")
        if component == "rank"
        else nested_magnitude(frame, features, SEED)
    )
    np.savez(path, prediction=result.prediction, inner_prediction=result.inner_prediction)
    result.tuning.to_csv(tuning_path, index=False, lineterminator="\n")
    return result


def main() -> None:
    frame = pd.read_csv(SOURCE)
    context = np.load(CONTEXT, allow_pickle=False)
    stability = np.load(STABILITY, allow_pickle=False)
    mechanism = build_mechanistic_features(frame, STRUCTURE, stability)
    masks = {
        "remove_motif_interactions": mechanism.keep_without("motif_interaction"),
        "remove_local_accessibility": mechanism.keep_without("accessibility"),
        "remove_stability_auxiliary": mechanism.keep_without("stability"),
        "remove_parent_state_interactions": mechanism.keep_without(
            "parent_state_interaction"
        ),
    }
    prediction_output = frame[["source_row", "parent_id", "delta_localization"]].copy()
    metric_tables = []
    summary_rows = []
    tuning_tables = []

    context_rank = _load_nested(CANDIDATE_INTERIM, "context_rank")
    context_magnitude = _load_nested(CANDIDATE_INTERIM, "context_magnitude")
    contextual_stack = rank_magnitude_stack(frame, context_rank, context_magnitude)
    complete_rank = _load_nested(CANDIDATE_INTERIM, "mechanism_rank")
    complete_magnitude = _load_nested(CANDIDATE_INTERIM, "mechanism_magnitude")
    complete_stack = rank_magnitude_stack(frame, complete_rank, complete_magnitude)
    stacks = {
        "contextual_only": contextual_stack,
        "complete_mechanism": complete_stack,
    }
    feature_counts = {
        "contextual_only": context.shape[1],
        "complete_mechanism": context.shape[1] + mechanism.values.shape[1],
    }
    for name, mask in masks.items():
        features = np.column_stack([context, mechanism.values[:, mask]]).astype(np.float32)
        rank = _run_or_load(name, "rank", frame, features)
        magnitude = _run_or_load(name, "magnitude", frame, features)
        stacks[name] = rank_magnitude_stack(frame, rank, magnitude)
        feature_counts[name] = features.shape[1]
        for component, table in (("rank", rank.tuning), ("magnitude", magnitude.tuning)):
            value = table.copy()
            value.insert(0, "component", component)
            value.insert(0, "ablation", name)
            tuning_tables.append(value)

    for name, stack in stacks.items():
        prediction_output[f"{name}_increase_score"] = stack.increase
        prediction_output[f"{name}_decrease_score"] = stack.decrease
        metrics = directional_metrics(frame, stack.increase, stack.decrease, model=name)
        metric_tables.append(metrics)
        row = macro_metrics(metrics)
        row["ablation"] = name
        row["feature_count"] = feature_counts[name]
        row["selection_score"] = selection_score(metrics)
        summary_rows.append(row)
        table = stack.tuning.copy()
        table.insert(0, "component", "stack")
        table.insert(0, "ablation", name)
        tuning_tables.append(table)

    prediction_output.to_csv(
        OUT / "mechanistic_ablation_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    pd.concat(metric_tables, ignore_index=True).to_csv(
        OUT / "mechanistic_ablation_parent_direction_metrics.csv",
        index=False,
        lineterminator="\n",
    )
    summary = pd.DataFrame(summary_rows).sort_values(
        "selection_score", ascending=False, kind="stable"
    )
    summary.to_csv(OUT / "mechanistic_ablation_macro_metrics.csv", index=False, lineterminator="\n")
    pd.concat(tuning_tables, ignore_index=True).to_csv(
        OUT / "mechanistic_ablation_inner_selections.csv", index=False, lineterminator="\n"
    )
    manifest = {
        "phase": "v3_phase3_mechanistic_ablations",
        "ablation_count_including_endpoints": len(stacks),
        "stability_survival_rule": {
            "selection_score_gain_at_least": 0.002,
            "maximum_regret_worsening": 0.005,
        },
        "selection_use": "prespecified_component_removal_only",
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "mechanistic_ablation_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
