"""One-time evaluation of committed predictions on the three locked N-zip parents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.development_benchmark import ALL_METHODS
from src.modeling.metrics import (
    bootstrap_parent_differences,
    evaluate_predictions,
    parent_macro,
)


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
SPLIT = ROOT / "data/manifests/nzip_parent_split.csv"
PREDICTIONS = ROOT / "results/internal/frozen_locked_predictions.csv.gz"
MANIFEST = ROOT / "results/internal/internal_freeze_manifest.json"
OUT_METRICS = ROOT / "results/internal/locked_parent_direction_metrics.csv"
OUT_MACRO = ROOT / "results/internal/locked_macro_metrics.csv"
OUT_PARENT = ROOT / "results/internal/locked_per_parent_results.csv"
OUT_BOOT = ROOT / "results/internal/locked_parent_bootstrap.csv"
OUT_REPORT = ROOT / "reports/locked_internal_results.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_random_rows(labels: pd.DataFrame, threshold: float) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for parent_id, parent in labels.groupby("parent_id", sort=True):
        measured = parent["delta_localization"].to_numpy(float)
        n = len(measured)
        for direction, sign in [("increase", 1.0), ("decrease", -1.0)]:
            utility = sign * measured
            best = float(np.max(utility))
            worst = float(np.min(utility))
            effect_range = best - worst
            successful = utility > threshold
            row = {
                "model": "random_exact",
                "parent_id": parent_id,
                "direction": direction,
                "n_candidates": n,
                "measured_effect": float("nan"),
                "measured_utility": float(np.mean(utility)),
                "best_measured_utility": best,
                "regret": float(best - np.mean(utility)),
                "normalized_regret": float((best - np.mean(utility)) / effect_range),
                "rank_percentile": 0.5,
                "spearman": 0.0,
            }
            from src.modeling.metrics import exact_random_success

            for k in [1, 3, 5]:
                row[f"success_at_{k}"] = exact_random_success(n, int(successful.sum()), k)
                row[f"precision_at_{k}"] = float(successful.mean())
            records.append(row)
    return pd.DataFrame(records)


def best_edit(parent: pd.DataFrame, direction: str) -> str:
    sign = 1.0 if direction == "increase" else -1.0
    row = parent.iloc[int(np.argmax(sign * parent["delta_localization"].to_numpy(float)))]
    return f"{row.reference_nt}{int(row.edit_position_1based)}{row.alternate_nt}"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if sha256(PREDICTIONS) != manifest["predictions_sha256"]:
        raise AssertionError("Frozen prediction hash changed before reveal")
    predictions = pd.read_csv(PREDICTIONS)
    forbidden = {
        "delta_localization",
        "parent_localization_log2_neurite_soma",
        "mutant_localization_log2_neurite_soma",
    }
    if forbidden & set(predictions):
        raise AssertionError("Frozen predictions already contain outcomes")

    split = pd.read_csv(SPLIT)
    lock_ids = set(split.loc[split["role"] == "locked_internal_test", "parent_id"])
    labels = pd.read_csv(
        NZIP,
        usecols=[
            "source_row",
            "parent_id",
            "delta_localization",
            "parent_localization_log2_neurite_soma",
            "mutant_localization_log2_neurite_soma",
        ],
    )
    labels = labels[labels["parent_id"].isin(lock_ids)].copy()
    revealed = predictions.merge(
        labels, on=["source_row", "parent_id"], how="left", validate="one_to_one"
    )
    if len(revealed) != 855 or revealed["delta_localization"].isna().any():
        raise AssertionError("Locked reveal is incomplete")

    prediction_columns = {method: f"pred_{method}" for method in ALL_METHODS}
    threshold = float(manifest["binary_threshold_log2"])
    metrics = evaluate_predictions(revealed, prediction_columns, threshold)
    random_rows = exact_random_rows(revealed, threshold)
    complete_metrics = pd.concat([metrics, random_rows], ignore_index=True, sort=False)
    macro = parent_macro(complete_metrics).sort_values(
        ["rank_percentile", "spearman"], ascending=[False, False]
    )
    complete_metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)

    selected_rows = metrics[metrics["model"] == "pairwise_rank"].copy()
    retrieval_rows = metrics[metrics["model"] == "retrieval"].copy()
    forward_rows = metrics[metrics["model"] == "forward_extratrees"].copy()
    per_parent = selected_rows.merge(
        retrieval_rows,
        on=["parent_id", "direction"],
        suffixes=("_rnaddress", "_retrieval"),
    )
    per_parent = per_parent.merge(
        forward_rows[
            [
                "parent_id",
                "direction",
                "selected_edit",
                "rank_percentile",
                "measured_effect",
            ]
        ],
        on=["parent_id", "direction"],
        suffixes=(None, "_forward"),
    ).rename(
        columns={
            "selected_edit": "selected_edit_forward",
            "rank_percentile": "rank_percentile_forward",
            "measured_effect": "measured_effect_forward",
        }
    )
    best_edits = []
    for row in per_parent.itertuples(index=False):
        best_edits.append(
            best_edit(revealed[revealed["parent_id"] == row.parent_id], row.direction)
        )
    per_parent["best_measured_edit"] = best_edits
    keep = [
        "parent_id",
        "direction",
        "n_candidates_rnaddress",
        "best_measured_edit",
        "selected_edit_rnaddress",
        "rank_percentile_rnaddress",
        "measured_effect_rnaddress",
        "regret_rnaddress",
        "normalized_regret_rnaddress",
        "success_at_1_rnaddress",
        "success_at_3_rnaddress",
        "success_at_5_rnaddress",
        "selected_edit_retrieval",
        "rank_percentile_retrieval",
        "measured_effect_retrieval",
        "selected_edit_forward",
        "rank_percentile_forward",
        "measured_effect_forward",
    ]
    per_parent[keep].to_csv(OUT_PARENT, index=False)

    bootstrap: list[dict[str, object]] = []
    for baseline in ["random_exact", "retrieval", "forward_extratrees"]:
        bootstrap.extend(
            bootstrap_parent_differences(
                complete_metrics,
                "pairwise_rank",
                baseline,
                [
                    "rank_percentile",
                    "normalized_regret",
                    "success_at_1",
                    "success_at_3",
                    "success_at_5",
                    "spearman",
                ],
                draws=10000,
            )
        )
    boot = pd.DataFrame(bootstrap)
    boot.to_csv(OUT_BOOT, index=False)

    table = macro.set_index("model")
    selected = table.loc["pairwise_rank"]
    retrieval = table.loc["retrieval"]
    forward = table.loc["forward_extratrees"]
    random = table.loc["random_exact"]
    same_direction = bool(
        selected["rank_percentile"] > retrieval["rank_percentile"]
        and selected["rank_percentile"] > forward["rank_percentile"]
    )
    gate_pass = bool(
        selected["rank_percentile"] > random["rank_percentile"]
        and selected["normalized_regret"] < random["normalized_regret"]
        and same_direction
    )

    lines = [
        "# RNAddress locked internal results",
        "",
        f"Frozen prediction hash verified before reveal: `{manifest['predictions_sha256']}`.",
        "",
        "## Macro results over three locked parents",
        "",
        "| Method | Rank percentile | Normalized regret | Spearman | Success@1 | Success@3 | Success@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in [
        "pairwise_rank",
        "retrieval",
        "forward_extratrees",
        "nzip_mikl_joint",
        "random_exact",
    ]:
        row = table.loc[model]
        lines.append(
            f"| {model} | {row['rank_percentile']:.3f} | "
            f"{row['normalized_regret']:.3f} | {row['spearman']:.3f} | "
            f"{row['success_at_1']:.3f} | {row['success_at_3']:.3f} | "
            f"{row['success_at_5']:.3f} |"
        )
    lines += [
        "",
        "## Gate decision",
        "",
        f"**{'PASS' if gate_pass else 'FAIL'}**.",
        "",
        f"Pairwise rank percentile is {selected['rank_percentile']:.3f}, compared with "
        f"{retrieval['rank_percentile']:.3f} for retrieval, {forward['rank_percentile']:.3f} "
        f"for strong forward search and {random['rank_percentile']:.3f} for exact random. "
        f"Normalized regret is {selected['normalized_regret']:.3f} versus "
        f"{random['normalized_regret']:.3f} for random.",
        "",
        "## Parent-level locked recommendations",
        "",
        "| Parent | Direction | RNAddress edit | Measured rank percentile | Forward edit | Forward rank percentile |",
        "|---|---|---|---:|---|---:|",
    ]
    for row in per_parent.itertuples(index=False):
        display_parent = str(row.parent_id).replace("|", "\\|")
        lines.append(
            f"| {display_parent} | {row.direction} | {row.selected_edit_rnaddress} | "
            f"{row.rank_percentile_rnaddress:.3f} | {row.selected_edit_forward} | "
            f"{row.rank_percentile_forward:.3f} |"
        )
    lines += [
        "",
        "## Parent-bootstrap uncertainty",
        "",
        "| Comparison (RNAddress minus baseline) | Rank-percentile difference | 95% CI |",
        "|---|---:|---:|",
    ]
    for baseline in ["random_exact", "retrieval", "forward_extratrees"]:
        row = boot[(boot["baseline_model"] == baseline) & (boot["metric"] == "rank_percentile")].iloc[0]
        lines.append(
            f"| {baseline} | {row['mean_difference']:.3f} | "
            f"[{row['ci95_low']:.3f}, {row['ci95_high']:.3f}] |"
        )
    lines += [
        "",
        "Only three parent units are available, so confidence intervals are necessarily "
        "wide and cannot establish population-level certainty. The external outcome reveal "
        + ("is authorized only after an external prediction freeze." if gate_pass else "is not authorized by the preregistered gate."),
        "",
        "The model was not modified after reveal. Astrocyte outcomes remain sealed.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
