"""Nested grouped selection for the factorized context ranker."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_models import fit_factorized_context_ranker


ROOT = Path(__file__).resolve().parents[2]
SCREEN = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
HOSTILE = ROOT / "results" / "v2" / "nzip_hostile_control_summary.json"
OUT_DIR = ROOT / "results" / "v2"
OUT_PRED = OUT_DIR / "nzip_nested_predictions.csv.gz"
OUT_SELECTION = OUT_DIR / "nzip_nested_hyperparameters.csv"
OUT_METRICS = OUT_DIR / "nzip_nested_parent_direction_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_nested_macro_metrics.csv"
OUT_GATE = OUT_DIR / "nzip_nested_gate.json"
OUT_REPORT = ROOT / "reports" / "v2_nested_development_results.md"
THRESHOLD = 0.6758642587586807
SEED = 20260826


GRID = [
    {
        "rank": rank,
        "hidden": hidden,
        "weight_decay": weight_decay,
        "learning_rate": learning_rate,
    }
    for rank, hidden, weight_decay, learning_rate in itertools.product(
        [4, 8, 16], [32, 64], [1e-4, 1e-3, 1e-2], [1e-3, 3e-4]
    )
]


def inner_parent_folds(parents: list[str], outer_parent: str) -> list[list[str]]:
    ordered = sorted(
        parents,
        key=lambda parent: hashlib.sha256(
            f"{SEED}|{outer_parent}|{parent}".encode()
        ).hexdigest(),
    )
    return [ordered[offset::3] for offset in range(3)]


def score_predictions(frame: pd.DataFrame, predictions: np.ndarray) -> tuple[float, float]:
    scored = frame.copy()
    scored["_prediction"] = predictions
    metrics = evaluate_predictions(scored, {"candidate": "_prediction"}, THRESHOLD)
    macro = parent_macro(metrics).iloc[0]
    return float(macro["rank_percentile"]), float(macro["normalized_regret"])


def main() -> None:
    frame = pd.read_csv(SCREEN)
    features = build_v2_features(frame)
    frame["pred_factorized_context_nested"] = np.nan
    selection_rows: list[dict[str, object]] = []

    all_parents = sorted(frame["parent_id"].unique())
    for outer_number, outer_parent in enumerate(all_parents, start=1):
        available = [parent for parent in all_parents if parent != outer_parent]
        folds = inner_parent_folds(available, outer_parent)
        config_scores: list[tuple[float, float, dict[str, object]]] = []
        for config_number, config in enumerate(GRID, start=1):
            fold_ranks: list[float] = []
            fold_regrets: list[float] = []
            for fold_parents in folds:
                validation = frame.index[frame["parent_id"].isin(fold_parents)].to_numpy(int)
                training = frame.index[
                    frame["parent_id"].isin(
                        [parent for parent in available if parent not in fold_parents]
                    )
                ].to_numpy(int)
                prediction = fit_factorized_context_ranker(
                    training,
                    validation,
                    frame,
                    features,
                    **config,
                    epochs=50,
                    pairs_per_parent=300,
                )
                rank_score, regret_score = score_predictions(
                    frame.iloc[validation], prediction
                )
                fold_ranks.append(rank_score)
                fold_regrets.append(regret_score)
            mean_rank = float(np.mean(fold_ranks))
            mean_regret = float(np.mean(fold_regrets))
            config_scores.append((mean_rank, mean_regret, config))
            selection_rows.append(
                {
                    "outer_parent": outer_parent,
                    **config,
                    "inner_rank_percentile": mean_rank,
                    "inner_normalized_regret": mean_regret,
                }
            )
            if config_number % 6 == 0:
                print(
                    f"outer {outer_number}/15 inner configs {config_number}/36: {outer_parent}",
                    flush=True,
                )
        best_rank = max(score[0] for score in config_scores)
        eligible = [score for score in config_scores if score[0] >= best_rank - 0.005]
        _, _, selected = min(
            eligible,
            key=lambda score: (
                score[1],
                score[2]["rank"],
                score[2]["hidden"],
                score[2]["weight_decay"],
                score[2]["learning_rate"],
            ),
        )
        test = frame.index[frame["parent_id"] == outer_parent].to_numpy(int)
        train = frame.index[frame["parent_id"] != outer_parent].to_numpy(int)
        frame.loc[test, "pred_factorized_context_nested"] = fit_factorized_context_ranker(
            train, test, frame, features, **selected, epochs=200, pairs_per_parent=600
        )
        for row in reversed(selection_rows):
            if row["outer_parent"] == outer_parent:
                row["selected"] = all(row[key] == value for key, value in selected.items())
        print(
            f"completed nested outer {outer_number}/15: {outer_parent}; selected {selected}",
            flush=True,
        )

    if frame["pred_factorized_context_nested"].isna().any():
        raise ValueError("Nested predictions are incomplete")
    prediction_columns = {
        "factorized_context_nested": "pred_factorized_context_nested",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_shuffled_edit_identity",
    }
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
    custom_parent = by_parent[by_parent["model"] == "factorized_context_nested"].set_index(
        "parent_id"
    )["rank_percentile"]
    forward_parent = by_parent[by_parent["model"] == strongest_forward].set_index("parent_id")[
        "rank_percentile"
    ]
    difference = custom_parent - forward_parent
    shuffled_labels = json.loads(HOSTILE.read_text())["shuffled_label_rank_percentile"]
    checks = {
        "rank_percentile_at_least_0_630": bool(
            table.loc["factorized_context_nested", "rank_percentile"] >= 0.630
        ),
        "gain_over_strongest_forward_at_least_0_030": bool(
            table.loc["factorized_context_nested", "rank_percentile"]
            - table.loc[strongest_forward, "rank_percentile"]
            >= 0.030
        ),
        "gain_over_metadata_at_least_0_020": bool(
            table.loc["factorized_context_nested", "rank_percentile"]
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
        "shuffled_labels_at_most_0_530": bool(shuffled_labels <= 0.530),
    }
    gate = {
        "selected_custom": "factorized_context_nested",
        "strongest_forward": strongest_forward,
        "shuffled_label_rank_percentile": shuffled_labels,
        "gate_checks": checks,
        "development_gate_pass": bool(all(checks.values())),
    }
    selection = pd.DataFrame(selection_rows)
    frame.to_csv(OUT_PRED, index=False, compression="gzip")
    selection.to_csv(OUT_SELECTION, index=False)
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")

    lines = [
        "# RNAddress v2 nested development results",
        "",
        "All 15 N-zip parents are development data because the original lock was spent. These are nested out-of-parent predictions, not a new confirmatory lock. TDP-43 locked outcomes and Astrocyte outcomes remained sealed.",
        "",
        "| Model | Rank percentile | Normalized regret | Spearman |",
        "|---|---:|---:|---:|",
    ]
    for _, row in macro.iterrows():
        lines.append(
            f"| {row['model']} | {row['rank_percentile']:.3f} | {row['normalized_regret']:.3f} | {row['spearman']:.3f} |"
        )
    lines += [
        "",
        f"Development gate: **{'PASS' if gate['development_gate_pass'] else 'FAIL'}**.",
        "",
        "The original three-parent result remains a FAIL and is not superseded.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
