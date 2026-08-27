"""Run the frozen RNAddress v2.3 SpliceBERT extreme-contrast gate."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.analysis.run_v2_2_splicebert import file_sha256
from src.modeling.metrics import evaluate_predictions, parent_macro


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
CACHE = ROOT / "data" / "interim" / "splicebert_v2_2_features.npy"
CACHE_ROWS = ROOT / "data" / "interim" / "splicebert_v2_2_source_rows.npy"
EXPECTED_FEATURE_SHA256 = "eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74"
OUT_DIR = ROOT / "results" / "v2_3"
OUT_PRED = OUT_DIR / "nzip_splicebert_extreme_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_splicebert_extreme_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_splicebert_extreme_macro.csv"
OUT_GATE = OUT_DIR / "nzip_splicebert_extreme_gate.json"
THRESHOLD = 0.6758642587586807
SEED = 20260826


def extreme_training_targets(
    frame: pd.DataFrame, train_indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    selected: list[int] = []
    targets: list[float] = []
    train_indices = np.asarray(train_indices, dtype=int)
    parent_values = frame.iloc[train_indices]["parent_id"].to_numpy(str)
    for parent_id in sorted(set(parent_values)):
        indices = train_indices[parent_values == parent_id]
        ordered = (
            frame.iloc[indices]
            .assign(_global_index=indices)
            .sort_values(["delta_localization", "source_row"], kind="stable")[
                "_global_index"
            ]
            .to_numpy(int)
        )
        quartile = len(ordered) // 4
        if quartile < 1:
            raise ValueError(f"Too few candidates for extreme contrast: {parent_id}")
        selected.extend(ordered[:quartile])
        targets.extend([-1.0] * quartile)
        selected.extend(ordered[-quartile:])
        targets.extend([1.0] * quartile)
    return np.asarray(selected, dtype=int), np.asarray(targets, dtype=float)


def lopo_extreme_ridge(frame: pd.DataFrame, features: np.ndarray) -> np.ndarray:
    predictions = np.full(len(frame), np.nan, dtype=float)
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        extreme, targets = extreme_training_targets(frame, train)
        scaler = StandardScaler().fit(features[train])
        model = Ridge(
            alpha=float(features.shape[1]),
            fit_intercept=True,
            solver="lsqr",
            tol=1e-6,
            max_iter=10_000,
        )
        model.fit(scaler.transform(features[extreme]), targets)
        predictions[test] = model.predict(scaler.transform(features[test]))
        print(f"completed extreme-contrast fold {fold}/15: {parent_id}", flush=True)
    if not np.isfinite(predictions).all():
        raise ValueError("Extreme-contrast LOPO predictions are incomplete or non-finite")
    return predictions


def evaluate_gate(frame: pd.DataFrame, include_control: bool):
    columns = {
        "splicebert_extreme_contrast_ridge": "pred_splicebert_extreme_contrast",
        "splicebert_percentile_ridge": "pred_splicebert_contextual_delta_ridge",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_splicebert_extreme_shuffled_edit",
    }
    if include_control:
        columns["shuffled_labels_extreme_ridge"] = "pred_splicebert_extreme_shuffled_labels"
    metrics = evaluate_predictions(frame, columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    candidate = "splicebert_extreme_contrast_ridge"
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
            table.loc["shuffled_labels_extreme_ridge", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": candidate,
        "strongest_forward": strongest_forward,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "feature_shape": [4_395, 2_638],
        "gate_checks": checks,
        "primary_gate_pass": bool(all(list(checks.values())[:6])),
        "development_gate_pass": bool(include_control and all(checks.values())),
        "shuffled_label_control_run": include_control,
        "note": "TDP-43 locked outcomes and Astrocyte outcomes remained sealed.",
    }
    return metrics, macro, gate


def save(frame: pd.DataFrame, metrics: pd.DataFrame, macro: pd.DataFrame, gate: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PRED, index=False, compression="gzip")
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(gate, indent=2), flush=True)


def main() -> None:
    frame = pd.read_csv(SOURCE)
    prior = pd.read_csv(ROOT / "results" / "v2_2" / "nzip_splicebert_predictions.csv.gz")
    if not prior["source_row"].equals(frame["source_row"]):
        raise ValueError("V2.2 predictions do not match frozen v2.3 source rows")
    frame["pred_splicebert_contextual_delta_ridge"] = prior[
        "pred_splicebert_contextual_delta_ridge"
    ]
    features = np.load(CACHE)
    rows = np.load(CACHE_ROWS)
    if features.shape != (4_395, 2_638):
        raise ValueError(f"Frozen v2.3 feature shape changed: {features.shape}")
    if not np.array_equal(rows, frame["source_row"].to_numpy(np.int64)):
        raise ValueError("Frozen v2.3 feature source rows changed")
    if file_sha256(CACHE) != EXPECTED_FEATURE_SHA256:
        raise ValueError("Frozen v2.3 feature hash changed")

    frame["pred_splicebert_extreme_contrast"] = lopo_extreme_ridge(frame, features)
    rng = np.random.default_rng(SEED)
    frame["pred_splicebert_extreme_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_splicebert_extreme_contrast"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = evaluate_gate(frame, False)
    save(frame, metrics, macro, gate)
    if not gate["primary_gate_pass"]:
        print("Primary v2.3 checks failed; shuffled-label control was not run.", flush=True)
        return

    shuffled = frame.copy()
    shuffle_rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffle_rng.permutation(values.to_numpy()))
    frame["pred_splicebert_extreme_shuffled_labels"] = lopo_extreme_ridge(
        shuffled, features
    )
    metrics, macro, gate = evaluate_gate(frame, True)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
