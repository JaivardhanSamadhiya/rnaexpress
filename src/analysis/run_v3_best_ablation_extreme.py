"""Apply frozen C4 extreme stacking to the strongest grouped C3 ablation."""

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
    nested_extreme,
    selection_score,
)
from src.modeling.v3_stacking import add_extreme_head, rank_magnitude_stack


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
CONTEXT = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
STRUCTURE = ROOT / "data/interim/v3_nzip_structure_cache.json"
STABILITY = ROOT / "data/interim/v3_nzip_tdp_stability_prediction.npy"
ABLATION = ROOT / "data/interim/v3_mechanistic_ablations"
INTERIM = ROOT / "data/interim/v3_best_ablation_extreme.npz"
TUNING = ROOT / "data/interim/v3_best_ablation_extreme_tuning.csv"
OUT = ROOT / "results/v3_phase3"
NAME = "remove_motif_interactions_plus_extreme"


def _load_nested(component: str) -> NestedResult:
    arrays = np.load(
        ABLATION / f"remove_motif_interactions_{component}.npz", allow_pickle=False
    )
    return NestedResult(
        arrays["prediction"],
        pd.read_csv(ABLATION / f"remove_motif_interactions_{component}_tuning.csv"),
        arrays["inner_prediction"],
    )


def main() -> None:
    frame = pd.read_csv(SOURCE)
    context = np.load(CONTEXT, allow_pickle=False)
    stability = np.load(STABILITY, allow_pickle=False)
    mechanism = build_mechanistic_features(frame, STRUCTURE, stability)
    mask = mechanism.keep_without("motif_interaction")
    features = np.column_stack([context, mechanism.values[:, mask]]).astype(np.float32)
    base = rank_magnitude_stack(frame, _load_nested("rank"), _load_nested("magnitude"))
    if INTERIM.exists() and TUNING.exists():
        arrays = np.load(INTERIM, allow_pickle=False)
        extreme_increase = arrays["increase"]
        extreme_decrease = arrays["decrease"]
        inner_increase = arrays["inner_increase"]
        inner_decrease = arrays["inner_decrease"]
        extreme_tuning = pd.read_csv(TUNING)
    else:
        (
            extreme_increase,
            extreme_decrease,
            extreme_tuning,
            inner_increase,
            inner_decrease,
        ) = nested_extreme(frame, features, return_inner=True)
        np.savez(
            INTERIM,
            increase=extreme_increase,
            decrease=extreme_decrease,
            inner_increase=inner_increase,
            inner_decrease=inner_decrease,
        )
        extreme_tuning.to_csv(TUNING, index=False, lineterminator="\n")
    result = add_extreme_head(
        frame,
        base,
        extreme_increase,
        extreme_decrease,
        inner_increase,
        inner_decrease,
    )
    predictions = frame[["source_row", "parent_id", "delta_localization"]].copy()
    predictions["increase_score"] = result.increase
    predictions["decrease_score"] = result.decrease
    predictions.to_csv(
        OUT / "best_ablation_extreme_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    metrics = directional_metrics(frame, result.increase, result.decrease, model=NAME)
    metrics.to_csv(
        OUT / "best_ablation_extreme_parent_direction_metrics.csv",
        index=False,
        lineterminator="\n",
    )
    macro = macro_metrics(metrics)
    macro["candidate"] = NAME
    macro["feature_count"] = features.shape[1]
    macro["selection_score"] = selection_score(metrics)
    pd.DataFrame([macro]).to_csv(
        OUT / "best_ablation_extreme_macro_metrics.csv", index=False, lineterminator="\n"
    )
    tuning = result.tuning.copy()
    tuning.insert(0, "component", "extreme_stack")
    extreme_table = extreme_tuning.copy()
    extreme_table.insert(0, "component", "extreme")
    pd.concat([extreme_table, tuning], ignore_index=True).to_csv(
        OUT / "best_ablation_extreme_inner_selections.csv",
        index=False,
        lineterminator="\n",
    )
    manifest = {
        "phase": "v3_phase3_best_ablation_extreme",
        "candidate": NAME,
        "status": "prespecified_C4_applied_after_grouped_component_removal",
        "removed_family": "motif_interaction",
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "best_ablation_extreme_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(pd.DataFrame([macro]).to_string(index=False))


if __name__ == "__main__":
    main()
