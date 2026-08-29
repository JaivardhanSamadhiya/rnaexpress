"""Parent-level statistics and preliminary frozen-gate evaluation for Phase 3."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling.v3_nested import directional_metrics, macro_metrics, selection_score
from src.modeling.v3_statistics import (
    MEANINGFUL_EFFECT,
    bootstrap_macro_intervals,
    exact_random_expectations,
    paired_parent_robustness,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/v3_phase3"
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"


def _complexity_pass(macros: pd.DataFrame, candidate: str) -> dict[str, object]:
    indexed = macros.set_index("candidate")
    if candidate == "mechanistic_rank_magnitude":
        reference = "rank_magnitude_stack"
    elif candidate == "mechanistic_rank_magnitude_extreme":
        reference = "mechanistic_rank_magnitude"
    else:
        return {"applicable": False, "pass": True}
    current = indexed.loc[candidate]
    baseline = indexed.loc[reference]
    score_gain = float(current["selection_score"] - baseline["selection_score"])
    rank_gain = float(current["rank_percentile"] - baseline["rank_percentile"])
    regret_gain = float(baseline["normalized_regret"] - current["normalized_regret"])
    top5_gain = float(current["oracle_top5"] - baseline["oracle_top5"])
    passed = score_gain >= 0.005 and (
        rank_gain >= 0.005 or regret_gain >= 0.010 or top5_gain >= 1.0 / 30.0
    )
    return {
        "applicable": True,
        "reference": reference,
        "selection_score_gain": score_gain,
        "rank_gain": rank_gain,
        "regret_improvement": regret_gain,
        "top5_gain": top5_gain,
        "pass": bool(passed),
    }


def main() -> None:
    frame = pd.read_csv(SOURCE)
    metrics = pd.read_csv(OUT / "candidate_parent_direction_metrics.csv")
    macros = pd.read_csv(OUT / "candidate_macro_metrics.csv")
    forward = pd.read_csv(OUT / "forward_macro_metrics.csv")
    forward_selection = json.loads((OUT / "forward_selection.json").read_text(encoding="utf-8"))
    strongest_forward = forward.set_index("model").loc[forward_selection["strongest_fair_forward"]]

    metadata_metrics = directional_metrics(
        frame,
        frame["pred_metadata_only"].to_numpy(float),
        -frame["pred_metadata_only"].to_numpy(float),
        model="metadata_only",
    )
    metadata_macro = macro_metrics(metadata_metrics)
    metadata_macro["selection_score"] = selection_score(metadata_metrics)
    metadata_metrics.to_csv(
        OUT / "metadata_parent_direction_metrics.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame([metadata_macro]).to_csv(
        OUT / "metadata_macro_metrics.csv", index=False, lineterminator="\n"
    )

    random = exact_random_expectations(frame)
    (OUT / "exact_random_expectations.json").write_text(
        json.dumps(random, indent=2) + "\n", encoding="utf-8"
    )
    bootstrap = []
    robustness_rows = []
    robustness_summary = {}
    baseline_metrics = metrics[metrics["model"] == "v2_6_historical"]
    for candidate in macros["candidate"]:
        table = metrics[metrics["model"] == candidate]
        intervals = bootstrap_macro_intervals(table)
        intervals.insert(0, "candidate", candidate)
        bootstrap.append(intervals)
        paired, summary = paired_parent_robustness(table, baseline_metrics)
        paired.insert(0, "candidate", candidate)
        robustness_rows.append(paired)
        robustness_summary[candidate] = summary
    pd.concat(bootstrap, ignore_index=True).to_csv(
        OUT / "candidate_parent_bootstrap_ci.csv", index=False, lineterminator="\n"
    )
    pd.concat(robustness_rows, ignore_index=True).to_csv(
        OUT / "candidate_parent_improvement.csv", index=False, lineterminator="\n"
    )
    (OUT / "candidate_parent_robustness.json").write_text(
        json.dumps(robustness_summary, indent=2) + "\n", encoding="utf-8"
    )

    indexed = macros.set_index("candidate")
    v2 = indexed.loc["v2_6_historical"]
    gate = {}
    for candidate in macros["candidate"]:
        row = indexed.loc[candidate]
        distribution = robustness_summary[candidate]
        criteria = {
            "A_rank_preservation": {
                "rank_at_least_0_630": bool(row["rank_percentile"] >= 0.630),
                "within_0_005_of_v2_6": bool(
                    row["rank_percentile"] >= v2["rank_percentile"] - 0.005
                ),
            },
            "B_regret_improvement": {
                "regret_at_most_0_397": bool(row["normalized_regret"] <= 0.397),
                "improvement_at_least_0_030": bool(
                    v2["normalized_regret"] - row["normalized_regret"] >= 0.030
                ),
            },
            "C_strongest_forward": {
                "rank_gain_at_least_0_030": bool(
                    row["rank_percentile"] - strongest_forward["rank_percentile"] >= 0.030
                ),
                "regret_improvement_at_least_0_020": bool(
                    strongest_forward["normalized_regret"] - row["normalized_regret"] >= 0.020
                ),
                "utility_gain_at_least_0_020": bool(
                    row["selected_utility"] - strongest_forward["selected_utility"] >= 0.020
                ),
            },
            "D_metadata": {
                "rank_gain_at_least_0_020": bool(
                    row["rank_percentile"] - metadata_macro["rank_percentile"] >= 0.020
                ),
                "regret_improvement_at_least_0_020": bool(
                    metadata_macro["normalized_regret"] - row["normalized_regret"] >= 0.020
                ),
            },
            "E_extreme_recovery": {
                "top5_at_least_0_10": bool(row["oracle_top5"] >= 0.10),
                "near_oracle_at_least_0_20": bool(row["near_oracle"] >= 0.20),
                "mean_oracle_rank_at_most_90": bool(row["mean_oracle_rank"] <= 90.0),
            },
            "F_distribution": {
                "median_gain_positive": bool(distribution["median_parent_gain"] > 0),
                "at_least_9_of_15_improve": bool(distribution["improved_parent_count"] >= 9),
                "leave_best_one_positive": bool(distribution["leave_best_one_mean_gain"] > 0),
                "leave_best_two_positive": bool(distribution["leave_best_two_mean_gain"] > 0),
            },
            "I_complexity": _complexity_pass(macros, candidate),
        }
        for section in criteria.values():
            if section.get("applicable") is False:
                continue
            section["pass"] = bool(
                section.get("pass", True)
                and all(value for key, value in section.items() if key not in {"pass", "applicable", "reference"} and isinstance(value, bool))
            )
        gate[candidate] = {
            "criteria": criteria,
            "core_A_to_F_pass": bool(
                all(criteria[key]["pass"] for key in criteria if key[0] in "ABCDEF")
            ),
        }
    (OUT / "candidate_gate_preliminary.json").write_text(
        json.dumps(
            {
                "strongest_fair_forward": forward_selection["strongest_fair_forward"],
                "meaningful_effect_threshold": MEANINGFUL_EFFECT,
                "candidates": gate,
                "controls_seeds_uncertainty_pending": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(macros.to_string(index=False))
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
