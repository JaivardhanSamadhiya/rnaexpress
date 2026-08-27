"""Run the frozen RNAddress v2.2 SpliceBERT contextual-delta gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.splicebert_features import build_splicebert_delta_features


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
CACHE = ROOT / "data" / "interim" / "splicebert_v2_2_features.npy"
CACHE_ROWS = ROOT / "data" / "interim" / "splicebert_v2_2_source_rows.npy"
OUT_DIR = ROOT / "results" / "v2_2"
OUT_PRED = OUT_DIR / "nzip_splicebert_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_splicebert_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_splicebert_macro.csv"
OUT_GATE = OUT_DIR / "nzip_splicebert_gate.json"
THRESHOLD = 0.6758642587586807
SEED = 20260826


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile_targets(frame: pd.DataFrame) -> np.ndarray:
    targets = np.empty(len(frame), dtype=float)
    for _, indices in frame.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        values = frame.iloc[indices]["delta_localization"].to_numpy(float)
        if len(values) <= 1:
            targets[indices] = 1.0
        else:
            targets[indices] = (rankdata(values, method="average") - 1.0) / (
                len(values) - 1.0
            )
    return targets


def lopo_ridge(frame: pd.DataFrame, features: np.ndarray) -> np.ndarray:
    targets = percentile_targets(frame)
    predictions = np.full(len(frame), np.nan, dtype=float)
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        scaler = StandardScaler().fit(features[train])
        model = Ridge(
            alpha=float(features.shape[1]),
            fit_intercept=True,
            solver="lsqr",
            tol=1e-6,
            max_iter=10_000,
        )
        model.fit(scaler.transform(features[train]), targets[train])
        predictions[test] = model.predict(scaler.transform(features[test]))
        print(f"completed SpliceBERT ridge fold {fold}/15: {parent_id}", flush=True)
    if not np.isfinite(predictions).all():
        raise ValueError("SpliceBERT LOPO predictions are incomplete or non-finite")
    return predictions


def load_features(frame: pd.DataFrame) -> np.ndarray:
    rows = frame["source_row"].to_numpy(np.int64)
    if CACHE.exists() and CACHE_ROWS.exists():
        cached_rows = np.load(CACHE_ROWS)
        features = np.load(CACHE)
        if np.array_equal(cached_rows, rows) and features.shape[0] == len(frame):
            print(f"loaded cached SpliceBERT features {features.shape}", flush=True)
            return features
        raise ValueError("SpliceBERT cache does not match frozen source rows")
    features = build_splicebert_delta_features(frame)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(CACHE, features, allow_pickle=False)
    np.save(CACHE_ROWS, rows, allow_pickle=False)
    return features


def evaluate_gate(frame: pd.DataFrame, include_control: bool, feature_hash: str):
    columns = {
        "splicebert_contextual_delta_ridge": "pred_splicebert_contextual_delta_ridge",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_splicebert_shuffled_edit",
    }
    if include_control:
        columns["shuffled_labels_splicebert_ridge"] = "pred_splicebert_shuffled_labels"
    metrics = evaluate_predictions(frame, columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    candidate = "splicebert_contextual_delta_ridge"
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
            table.loc["shuffled_labels_splicebert_ridge", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": candidate,
        "strongest_forward": strongest_forward,
        "feature_sha256": feature_hash,
        "feature_shape": [int(value) for value in np.load(CACHE, mmap_mode="r").shape],
        "ridge_alpha_equals_feature_count": True,
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
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("N-zip v2.2 candidate set changed")
    features = load_features(frame)
    if features.shape != (len(frame), 2_638):
        raise ValueError(f"Frozen v2.2 feature shape changed: {features.shape}")
    feature_hash = file_sha256(CACHE)
    frame["pred_splicebert_contextual_delta_ridge"] = lopo_ridge(frame, features)
    rng = np.random.default_rng(SEED)
    frame["pred_splicebert_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_splicebert_contextual_delta_ridge"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = evaluate_gate(frame, False, feature_hash)
    save(frame, metrics, macro, gate)
    if not gate["primary_gate_pass"]:
        print("Primary v2.2 checks failed; shuffled-label control was not run.", flush=True)
        return

    shuffled = frame.copy()
    shuffle_rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffle_rng.permutation(values.to_numpy()))
    frame["pred_splicebert_shuffled_labels"] = lopo_ridge(shuffled, features)
    metrics, macro, gate = evaluate_gate(frame, True, feature_hash)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
