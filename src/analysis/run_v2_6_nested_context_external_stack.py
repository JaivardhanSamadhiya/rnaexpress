"""Run the frozen RNAddress v2.6 nested contextual/external stack gate."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.analysis.hostile_internal_audit import metadata_features
from src.analysis.run_v2_2_splicebert import percentile_targets
from src.analysis.run_v2_4_external_transfer import load_context
from src.analysis.run_v2_5_mikl_xgboost_transfer import mikl_delta_features
from src.modeling.metrics import evaluate_predictions, parent_macro


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
V2_2_PREDICTIONS = ROOT / "results" / "v2_2" / "nzip_splicebert_predictions.csv.gz"
OUT_DIR = ROOT / "results" / "v2_6"
OUT_PRED = OUT_DIR / "nzip_nested_stack_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_nested_stack_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_nested_stack_macro.csv"
OUT_GATE = OUT_DIR / "nzip_nested_stack_gate.json"
THRESHOLD = 0.6758642587586807
SEED = 20260826
CONTEXT_DIM = 2_638
META_DIM = 21


def fit_contextual_base(
    train: np.ndarray,
    test: np.ndarray,
    context: np.ndarray,
    targets: np.ndarray,
) -> np.ndarray:
    scaler = StandardScaler().fit(context[train])
    model = Ridge(
        alpha=float(CONTEXT_DIM),
        fit_intercept=True,
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    )
    model.fit(scaler.transform(context[train]), targets[train])
    return model.predict(scaler.transform(context[test]))


def nested_stack(
    frame: pd.DataFrame,
    context: np.ndarray,
    mikl_deltas: np.ndarray,
) -> np.ndarray:
    targets = percentile_targets(frame)
    low_dimensional = np.column_stack([metadata_features(frame), mikl_deltas])
    if low_dimensional.shape != (len(frame), 20):
        raise ValueError(f"Frozen v2.6 low-dimensional feature shape changed: {low_dimensional.shape}")
    predictions = np.full(len(frame), np.nan, dtype=float)
    parents = frame["parent_id"].to_numpy()
    for outer_fold, outer_parent in enumerate(sorted(frame["parent_id"].unique()), start=1):
        outer_test = np.flatnonzero(parents == outer_parent)
        outer_train = np.flatnonzero(parents != outer_parent)
        crossfit = np.full(len(frame), np.nan, dtype=float)
        for inner_parent in sorted(frame.iloc[outer_train]["parent_id"].unique()):
            inner_test = np.flatnonzero((parents == inner_parent) & (parents != outer_parent))
            inner_train = np.flatnonzero(
                (parents != inner_parent) & (parents != outer_parent)
            )
            crossfit[inner_test] = fit_contextual_base(
                inner_train, inner_test, context, targets
            )
        if not np.isfinite(crossfit[outer_train]).all():
            raise ValueError(f"Incomplete inner cross-fit for outer parent {outer_parent}")
        outer_contextual = fit_contextual_base(
            outer_train, outer_test, context, targets
        )
        train_features = np.column_stack(
            [low_dimensional[outer_train], crossfit[outer_train]]
        )
        test_features = np.column_stack(
            [low_dimensional[outer_test], outer_contextual]
        )
        if train_features.shape[1] != META_DIM:
            raise ValueError(f"Frozen v2.6 meta-feature count changed: {train_features.shape[1]}")
        scaler = StandardScaler().fit(train_features)
        model = Ridge(
            alpha=float(META_DIM),
            fit_intercept=True,
            solver="lsqr",
            tol=1e-6,
            max_iter=10_000,
        )
        model.fit(scaler.transform(train_features), targets[outer_train])
        predictions[outer_test] = model.predict(scaler.transform(test_features))
        print(
            f"completed v2.6 nested stack fold {outer_fold}/15: {outer_parent}",
            flush=True,
        )
    if not np.isfinite(predictions).all():
        raise ValueError("V2.6 nested stack predictions are incomplete or non-finite")
    return predictions


def evaluate_gate(
    frame: pd.DataFrame,
    include_control: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    columns = {
        "nested_context_external_stack": "pred_nested_context_external_stack",
        "mikl_xgboost_calibrated": "pred_mikl_xgboost_calibrated",
        "splicebert_percentile_ridge": "pred_splicebert_contextual_delta_ridge",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_v2_6_shuffled_edit",
    }
    if include_control:
        columns["shuffled_labels_nested_stack"] = "pred_v2_6_shuffled_labels"
    metrics = evaluate_predictions(frame, columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    candidate = "nested_context_external_stack"
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
            table.loc["shuffled_labels_nested_stack", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": candidate,
        "strongest_forward": strongest_forward,
        "context_dim": CONTEXT_DIM,
        "meta_dim": META_DIM,
        "context_ridge_alpha": CONTEXT_DIM,
        "meta_ridge_alpha": META_DIM,
        "strict_inner_lopo": True,
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
        raise ValueError("N-zip v2.6 candidate set changed")
    v2_2 = pd.read_csv(
        V2_2_PREDICTIONS,
        usecols=["source_row", "pred_splicebert_contextual_delta_ridge"],
    )
    v2_5 = pd.read_csv(
        ROOT / "results" / "v2_5" / "nzip_mikl_xgboost_predictions.csv.gz",
        usecols=["source_row", "pred_mikl_xgboost_calibrated"],
    )
    frame = frame.merge(v2_2, on="source_row", how="left", validate="one_to_one")
    frame = frame.merge(v2_5, on="source_row", how="left", validate="one_to_one")
    if frame[["pred_splicebert_contextual_delta_ridge", "pred_mikl_xgboost_calibrated"]].isna().any().any():
        raise ValueError("Frozen descriptive base predictions are incomplete")
    context = load_context(frame)
    mikl_deltas, _ = mikl_delta_features(frame)
    frame["pred_nested_context_external_stack"] = nested_stack(
        frame, context, mikl_deltas
    )
    rng = np.random.default_rng(SEED)
    frame["pred_v2_6_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_nested_context_external_stack"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = evaluate_gate(frame, False)
    save(frame, metrics, macro, gate)
    if not gate["primary_gate_pass"]:
        print("Primary v2.6 checks failed; shuffled-label control was not run.", flush=True)
        return

    shuffled = frame.copy()
    shuffle_rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffle_rng.permutation(values.to_numpy()))
    frame["pred_v2_6_shuffled_labels"] = nested_stack(
        shuffled, context, mikl_deltas
    )
    metrics, macro, gate = evaluate_gate(frame, True)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
