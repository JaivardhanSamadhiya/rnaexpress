"""Run the preregistered RNAddress v2 15-parent development evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.hostile_internal_audit import gc_features, metadata_features, lopo_ridge
from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_models import (
    fit_context_lambdamart,
    fit_factorized_context_ranker,
    fit_forward_lightgbm,
)


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data" / "processed" / "nzip_snv_intervention_pairs.csv.gz"
OLD_DEV = ROOT / "results" / "internal" / "development_predictions.csv.gz"
OLD_LOCK = ROOT / "results" / "internal" / "frozen_locked_predictions.csv.gz"
OUT_DIR = ROOT / "results" / "v2"
OUT_PRED = OUT_DIR / "nzip_development_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_parent_direction_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_macro_metrics.csv"
OUT_GATE = OUT_DIR / "nzip_development_gate.json"
THRESHOLD = 0.6758642587586807


def old_predictions(labels: pd.DataFrame) -> pd.DataFrame:
    old = pd.concat([pd.read_csv(OLD_DEV), pd.read_csv(OLD_LOCK)], ignore_index=True)
    columns = [
        "source_row",
        "pred_pairwise_rank",
        "pred_forward_extratrees",
        "pred_retrieval",
    ]
    return labels.merge(old[columns], on="source_row", validate="one_to_one")


def main() -> None:
    labels = pd.read_csv(NZIP).sort_values(["parent_id", "source_row"]).reset_index(drop=True)
    frame = old_predictions(labels)
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("N-zip v2 candidate set changed")
    features = build_v2_features(frame)
    frame["pred_metadata_only"] = lopo_ridge(frame, metadata_features(frame))
    frame["pred_gc_only"] = lopo_ridge(frame, gc_features(frame))
    for column in [
        "pred_context_lambdamart",
        "pred_factorized_context_ranker",
        "pred_forward_lightgbm",
    ]:
        frame[column] = np.nan

    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test_indices = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train_indices = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        frame.loc[test_indices, "pred_context_lambdamart"] = fit_context_lambdamart(
            train_indices, test_indices, frame, features
        )
        frame.loc[test_indices, "pred_factorized_context_ranker"] = (
            fit_factorized_context_ranker(train_indices, test_indices, frame, features)
        )
        frame.loc[test_indices, "pred_forward_lightgbm"] = fit_forward_lightgbm(
            train_indices, test_indices, frame
        )
        print(f"completed v2 N-zip outer fold {fold}/15: {parent_id}", flush=True)

    if frame.filter(like="pred_").isna().any().any():
        raise ValueError("Missing v2 development predictions")
    rng = np.random.default_rng(20260826)
    frame["pred_shuffled_edit_identity"] = frame.groupby("parent_id")[
        "pred_factorized_context_ranker"
    ].transform(lambda values: rng.permutation(values.to_numpy()))

    prediction_columns = {
        "factorized_context_ranker": "pred_factorized_context_ranker",
        "context_lambdamart": "pred_context_lambdamart",
        "forward_lightgbm": "pred_forward_lightgbm",
        "old_pairwise_rank": "pred_pairwise_rank",
        "forward_extratrees": "pred_forward_extratrees",
        "retrieval": "pred_retrieval",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_shuffled_edit_identity",
    }
    metrics = evaluate_predictions(frame, prediction_columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    by_parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        ["rank_percentile", "normalized_regret", "spearman"]
    ].mean()
    custom_name = max(
        ["factorized_context_ranker", "context_lambdamart"],
        key=lambda name: float(macro.set_index("model").loc[name, "rank_percentile"]),
    )
    strongest_forward = max(
        ["forward_lightgbm", "forward_extratrees"],
        key=lambda name: float(macro.set_index("model").loc[name, "rank_percentile"]),
    )
    table = macro.set_index("model")
    custom_parent = by_parent[by_parent["model"] == custom_name].set_index("parent_id")
    forward_parent = by_parent[by_parent["model"] == strongest_forward].set_index("parent_id")
    differences = custom_parent["rank_percentile"] - forward_parent["rank_percentile"]
    gate_checks = {
        "rank_percentile_at_least_0_630": bool(table.loc[custom_name, "rank_percentile"] >= 0.630),
        "gain_over_strongest_forward_at_least_0_030": bool(
            table.loc[custom_name, "rank_percentile"]
            - table.loc[strongest_forward, "rank_percentile"]
            >= 0.030
        ),
        "gain_over_metadata_at_least_0_020": bool(
            table.loc[custom_name, "rank_percentile"]
            - table.loc["metadata_only", "rank_percentile"]
            >= 0.020
        ),
        "improves_at_least_9_of_15_parents": bool((differences > 0).sum() >= 9),
        "positive_after_removing_two_best_parents": bool(
            differences.drop(differences.nlargest(2).index).mean() > 0
        ),
        "shuffled_edit_at_most_0_540": bool(
            table.loc["shuffled_edit_identity", "rank_percentile"] <= 0.540
        ),
    }
    gate = {
        "selected_custom": custom_name,
        "strongest_forward": strongest_forward,
        "gate_checks": gate_checks,
        "partial_gate_pass": bool(all(gate_checks.values())),
        "note": "The preregistered shuffled-label check is run in the hostile-control stage if all other checks pass.",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PRED, index=False, compression="gzip")
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
