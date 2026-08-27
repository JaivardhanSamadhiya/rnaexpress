"""Run the frozen RNAddress v2.1 seven-seed stability ensemble gate."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_models import fit_factorized_context_ranker


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
OUT_DIR = ROOT / "results" / "v2_1"
OUT_PRED = OUT_DIR / "nzip_seed_ensemble_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_seed_ensemble_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_seed_ensemble_macro.csv"
OUT_GATE = OUT_DIR / "nzip_seed_ensemble_gate.json"
CHECKPOINT = ROOT / "data" / "interim" / "v2_1_seed_ensemble_checkpoint.csv.gz"
THRESHOLD = 0.6758642587586807
SHUFFLE_SEED = 20260826
SEEDS = [20260826, 124347, 910243, 451921, 778103, 330817, 602911]


def percentile_scores(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, float)
    if len(values) <= 1:
        return np.ones(len(values), dtype=float)
    return (rankdata(values, method="average") - 1.0) / (len(values) - 1.0)


def fit_ensemble(
    frame: pd.DataFrame,
    label_frame: pd.DataFrame,
    features,
    prefix: str,
    allow_resume: bool,
) -> None:
    columns = [f"{prefix}_{seed}" for seed in SEEDS]
    for column in columns:
        if column not in frame:
            frame[column] = np.nan

    parents = sorted(frame["parent_id"].unique())
    for fold, parent_id in enumerate(parents, start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        for seed_number, (seed, column) in enumerate(zip(SEEDS, columns), start=1):
            if allow_resume and frame.loc[test, column].notna().all():
                continue
            raw = fit_factorized_context_ranker(
                train,
                test,
                label_frame,
                features,
                rank=8,
                hidden=32,
                learning_rate=1e-3,
                weight_decay=1e-3,
                epochs=200,
                pairs_per_parent=600,
                seed=seed,
            )
            frame.loc[test, column] = percentile_scores(raw)
            print(
                f"completed {prefix} fold {fold}/15 seed {seed_number}/7: {parent_id}",
                flush=True,
            )
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(CHECKPOINT, index=False, compression="gzip")

    if frame[columns].isna().any().any():
        raise ValueError(f"Incomplete ensemble columns for {prefix}")
    frame[f"{prefix}_ensemble"] = frame[columns].mean(axis=1)


def gate_summary(frame: pd.DataFrame, include_control: bool) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    prediction_columns = {
        "factorized_context_seed_ensemble": "pred_factorized_context_seed_ensemble",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_seed_ensemble_shuffled_edit",
    }
    if include_control:
        prediction_columns["shuffled_labels_seed_ensemble"] = (
            "pred_shuffled_labels_seed_ensemble"
        )
    metrics = evaluate_predictions(frame, prediction_columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    strongest_forward = max(
        ["forward_lightgbm", "forward_extratrees"],
        key=lambda model: float(table.loc[model, "rank_percentile"]),
    )
    by_parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        "rank_percentile"
    ].mean()
    custom = by_parent[
        by_parent["model"] == "factorized_context_seed_ensemble"
    ].set_index("parent_id")["rank_percentile"]
    forward = by_parent[by_parent["model"] == strongest_forward].set_index("parent_id")[
        "rank_percentile"
    ]
    difference = custom - forward
    checks = {
        "rank_percentile_at_least_0_630": bool(
            table.loc["factorized_context_seed_ensemble", "rank_percentile"] >= 0.630
        ),
        "gain_over_strongest_forward_at_least_0_030": bool(
            table.loc["factorized_context_seed_ensemble", "rank_percentile"]
            - table.loc[strongest_forward, "rank_percentile"]
            >= 0.030
        ),
        "gain_over_metadata_at_least_0_020": bool(
            table.loc["factorized_context_seed_ensemble", "rank_percentile"]
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
            table.loc["shuffled_labels_seed_ensemble", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": "factorized_context_seed_ensemble",
        "strongest_forward": strongest_forward,
        "seeds": SEEDS,
        "gate_checks": checks,
        "primary_gate_pass": bool(all(list(checks.values())[:6])),
        "development_gate_pass": bool(include_control and all(checks.values())),
        "shuffled_label_control_run": include_control,
        "note": (
            "TDP-43 locked outcomes and Astrocyte outcomes remained sealed. "
            "All seeds were frozen before fitting; none were selected or weighted."
        ),
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
    source = pd.read_csv(SOURCE)
    if len(source) != 4_395 or source["parent_id"].nunique() != 15:
        raise ValueError("N-zip v2.1 candidate set changed")
    if CHECKPOINT.exists():
        frame = pd.read_csv(CHECKPOINT)
        if not frame["source_row"].equals(source["source_row"]):
            raise ValueError("v2.1 checkpoint does not match frozen source rows")
        for column in source.columns:
            if column not in frame:
                frame[column] = source[column]
    else:
        frame = source.copy()
    features = build_v2_features(source)

    fit_ensemble(
        frame,
        source,
        features,
        prefix="pred_factorized_context_seed",
        allow_resume=True,
    )
    rng = np.random.default_rng(SHUFFLE_SEED)
    frame["pred_seed_ensemble_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_factorized_context_ensemble"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = gate_summary(frame, include_control=False)
    save(frame, metrics, macro, gate)

    if not gate["primary_gate_pass"]:
        print("Primary v2.1 checks failed; shuffled-label ensemble was not run.", flush=True)
        return

    shuffled = source.copy()
    shuffled_rng = np.random.default_rng(SHUFFLE_SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffled_rng.permutation(values.to_numpy()))
    fit_ensemble(
        frame,
        shuffled,
        features,
        prefix="pred_shuffled_labels_seed",
        allow_resume=True,
    )
    metrics, macro, gate = gate_summary(frame, include_control=True)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
