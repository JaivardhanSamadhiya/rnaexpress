"""Run the frozen RNAddress v2.5 Mikl-XGBoost transfer gate."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.analysis.hostile_internal_audit import metadata_features
from src.analysis.run_v2_2_splicebert import percentile_targets
from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.mikl_xgboost_heads import predict_frozen_heads


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
V2_2_PREDICTIONS = ROOT / "results" / "v2_2" / "nzip_splicebert_predictions.csv.gz"
OUT_DIR = ROOT / "results" / "v2_5"
OUT_PRED = OUT_DIR / "nzip_mikl_xgboost_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_mikl_xgboost_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_mikl_xgboost_macro.csv"
OUT_GATE = OUT_DIR / "nzip_mikl_xgboost_gate.json"
THRESHOLD = 0.6758642587586807
SEED = 20260826
FEATURES = 20


def mikl_delta_features(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    sequences = sorted(
        set(frame["parent_sequence"].astype(str))
        | set(frame["mutant_sequence"].astype(str))
    )
    if len(sequences) != 4_410:
        raise ValueError(f"Expected 4,410 unique N-zip sequences, observed {len(sequences)}")
    predictions = predict_frozen_heads(sequences)
    sequence_index = {sequence: index for index, sequence in enumerate(sequences)}
    parent = frame["parent_sequence"].map(sequence_index).to_numpy(int)
    mutant = frame["mutant_sequence"].map(sequence_index).to_numpy(int)
    deltas = predictions[mutant] - predictions[parent]
    if deltas.shape != (len(frame), 2) or not np.isfinite(deltas).all():
        raise ValueError("Frozen Mikl probability deltas changed")
    return deltas, deltas[:, 0] - deltas[:, 1]


def lopo_calibration(frame: pd.DataFrame, features: np.ndarray) -> np.ndarray:
    targets = percentile_targets(frame)
    predictions = np.full(len(frame), np.nan, dtype=float)
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        scaler = StandardScaler().fit(features[train])
        model = Ridge(
            alpha=float(FEATURES),
            fit_intercept=True,
            solver="lsqr",
            tol=1e-6,
            max_iter=10_000,
        )
        model.fit(scaler.transform(features[train]), targets[train])
        predictions[test] = model.predict(scaler.transform(features[test]))
        print(f"completed v2.5 Mikl-XGBoost fold {fold}/15: {parent_id}", flush=True)
    if not np.isfinite(predictions).all():
        raise ValueError("V2.5 Mikl-XGBoost predictions are incomplete or non-finite")
    return predictions


def evaluate_gate(
    frame: pd.DataFrame,
    include_control: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    columns = {
        "mikl_xgboost_calibrated": "pred_mikl_xgboost_calibrated",
        "mikl_xgboost_zero_shot": "pred_mikl_xgboost_zero_shot",
        "splicebert_percentile_ridge": "pred_splicebert_contextual_delta_ridge",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_v2_5_shuffled_edit",
    }
    if include_control:
        columns["shuffled_labels_mikl_xgboost"] = "pred_v2_5_shuffled_labels"
    metrics = evaluate_predictions(frame, columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    candidate = "mikl_xgboost_calibrated"
    strongest_forward = max(
        ["forward_lightgbm", "forward_extratrees"],
        key=lambda model: float(table.loc[model, "rank_percentile"]),
    )
    by_parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        "rank_percentile"
    ].mean()
    custom = by_parent[by_parent["model"] == candidate].set_index("parent_id")[
        "rank_percentile"
    ]
    forward = by_parent[by_parent["model"] == strongest_forward].set_index("parent_id")[
        "rank_percentile"
    ]
    difference = custom - forward
    checks = {
        "rank_percentile_at_least_0_630": bool(table.loc[candidate, "rank_percentile"] >= 0.630),
        "gain_over_strongest_forward_at_least_0_030": bool(
            table.loc[candidate, "rank_percentile"]
            - table.loc[strongest_forward, "rank_percentile"]
            >= 0.030
        ),
        "gain_over_metadata_at_least_0_020": bool(
            table.loc[candidate, "rank_percentile"]
            - table.loc["metadata_only", "rank_percentile"]
            >= 0.020
        ),
        "improves_at_least_9_of_15_parents": bool((difference > 0).sum() >= 9),
        "positive_after_removing_two_best_parents": bool(
            difference.drop(difference.nlargest(2).index).mean() > 0
        ),
        "shuffled_edit_at_most_0_540": bool(
            table.loc["shuffled_edit_identity", "rank_percentile"] <= 0.540
        ),
    }
    if include_control:
        checks["shuffled_labels_at_most_0_530"] = bool(
            table.loc["shuffled_labels_mikl_xgboost", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": candidate,
        "strongest_forward": strongest_forward,
        "features": FEATURES,
        "ridge_alpha": FEATURES,
        "gate_checks": checks,
        "primary_gate_pass": bool(all(list(checks.values())[:6])),
        "development_gate_pass": bool(include_control and all(checks.values())),
        "shuffled_label_control_run": include_control,
        "note": "TDP-43 locked outcomes and astrocyte outcomes remained sealed.",
    }
    return metrics, macro, gate


def save(frame: pd.DataFrame, metrics: pd.DataFrame, macro: pd.DataFrame, gate: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PRED, index=False, compression="gzip")
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(gate, indent=2), flush=True)


def main() -> None:
    frame = pd.read_csv(SOURCE)
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("N-zip v2.5 candidate set changed")
    v2_2 = pd.read_csv(
        V2_2_PREDICTIONS,
        usecols=["source_row", "pred_splicebert_contextual_delta_ridge"],
    )
    frame = frame.merge(v2_2, on="source_row", how="left", validate="one_to_one")
    if frame["pred_splicebert_contextual_delta_ridge"].isna().any():
        raise ValueError("Frozen v2.2 descriptive predictions are incomplete")
    mikl_deltas, zero_shot = mikl_delta_features(frame)
    features = np.column_stack([metadata_features(frame), mikl_deltas])
    if features.shape != (len(frame), FEATURES):
        raise ValueError(f"Frozen v2.5 feature shape changed: {features.shape}")
    frame["pred_mikl_xgboost_zero_shot"] = zero_shot
    frame["pred_mikl_xgboost_calibrated"] = lopo_calibration(frame, features)
    rng = np.random.default_rng(SEED)
    frame["pred_v2_5_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_mikl_xgboost_calibrated"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = evaluate_gate(frame, False)
    save(frame, metrics, macro, gate)
    if not gate["primary_gate_pass"]:
        print("Primary v2.5 checks failed; shuffled-label control was not run.", flush=True)
        return

    shuffled = frame.copy()
    shuffle_rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffle_rng.permutation(values.to_numpy()))
    frame["pred_v2_5_shuffled_labels"] = lopo_calibration(shuffled, features)
    metrics, macro, gate = evaluate_gate(frame, True)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
