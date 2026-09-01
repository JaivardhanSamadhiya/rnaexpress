"""Apply the frozen numerical RNAddress v4 Phase B development gates."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "v4_phaseB"


def _model_name(kind: str, hierarchical: bool = True) -> str:
    if kind == "ptr":
        return "predict_then_rank_hierarchical" if hierarchical else "ptr_global"
    return f"{kind}_{'hierarchical' if hierarchical else 'global'}"


def _mean_rows(frame: pd.DataFrame, model: str) -> pd.DataFrame:
    return (
        frame[frame["model"].eq(model)]
        .groupby(["dataset", "requested_direction"])
        .agg(
            rank=("directional_rank_percentile", "mean"),
            regret=("normalized_regret", "mean"),
            utility=("selected_normalized_utility", "mean"),
            good1=("good_selection_at_1", "mean"),
            good3=("good_selection_at_3", "mean"),
            good5=("good_selection_at_5", "mean"),
            random_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )


def main() -> None:
    selection = json.loads((OUT / "model_selection.json").read_text(encoding="utf-8"))
    kind = str(selection["selected_model_kind"])
    selected_name = _model_name(kind)
    aggregate = pd.read_csv(OUT / "model_aggregate_metrics.csv")
    unit = pd.read_csv(OUT / "model_biological_unit_metrics.csv")
    transfer = pd.read_csv(OUT / "transfer_aggregate_metrics.csv")
    controls = pd.read_csv(OUT / "control_summary.csv")

    conventional = aggregate[
        ~aggregate["model"].str.startswith(("dfl_", "pairwise_", "random_"))
        & ~aggregate["model"].eq("edit_size_heuristic")
    ]
    conventional_means = conventional.groupby("model")["normalized_regret"].mean()
    strongest = str(conventional_means.idxmin())
    selected_source = _mean_rows(aggregate, selected_name)
    baseline_source = _mean_rows(aggregate, strongest)
    paired_source = selected_source.merge(
        baseline_source,
        on=["dataset", "requested_direction"],
        suffixes=("_selected", "_baseline"),
    )
    paired_source["rank_gain"] = paired_source["rank_selected"] - paired_source["rank_baseline"]
    paired_source["regret_gain"] = (
        paired_source["regret_baseline"] - paired_source["regret_selected"]
    )
    paired_source["utility_gain"] = (
        paired_source["utility_selected"] - paired_source["utility_baseline"]
    )
    source_gate_rows = (
        paired_source.groupby("dataset")
        .agg(rank_gain=("rank_gain", "mean"), regret_gain=("regret_gain", "mean"), utility_gain=("utility_gain", "mean"))
        .reset_index()
    )
    source_gate_rows["passes_gain"] = (
        source_gate_rows["rank_gain"].ge(0.01)
        & source_gate_rows["regret_gain"].ge(0.01)
        & source_gate_rows["utility_gain"].gt(0)
    )
    gate_a = bool(
        source_gate_rows["passes_gain"].sum() >= 2
        and source_gate_rows["rank_gain"].min() >= -0.03
        and source_gate_rows["regret_gain"].min() >= -0.03
    )

    selected_unit = (
        unit[unit["model"].eq(selected_name)]
        .groupby(["dataset", "biological_unit"])["normalized_regret"]
        .mean()
        .rename("selected")
    )
    baseline_unit = (
        unit[unit["model"].eq(strongest)]
        .groupby(["dataset", "biological_unit"])["normalized_regret"]
        .mean()
        .rename("baseline")
    )
    unit_gain = pd.concat([selected_unit, baseline_unit], axis=1).dropna()
    unit_gain["gain"] = unit_gain["baseline"] - unit_gain["selected"]
    gains = unit_gain["gain"].to_numpy(float)
    rng = np.random.default_rng(41_017)
    bootstrap = np.mean(rng.choice(gains, size=(10_000, len(gains)), replace=True), axis=1)
    best_index = int(np.argmax(gains))
    without_best = np.delete(gains, best_index)
    gate_b_detail = {
        "biological_units": len(gains),
        "median_gain": float(np.median(gains)),
        "fraction_improved": float(np.mean(gains > 0)),
        "leave_best_unit_out_mean_gain": float(np.mean(without_best)),
        "mean_gain": float(np.mean(gains)),
        "bootstrap_95_low": float(np.quantile(bootstrap, 0.025)),
        "bootstrap_95_high": float(np.quantile(bootstrap, 0.975)),
    }
    gate_b = bool(
        gate_b_detail["median_gain"] > 0
        and gate_b_detail["fraction_improved"] > 0.5
        and gate_b_detail["leave_best_unit_out_mean_gain"] > 0
        and gate_b_detail["mean_gain"] > 0
        and gate_b_detail["bootstrap_95_low"] > -0.005
    )

    selected_transfer_name = _model_name(kind, hierarchical=False)
    transfer_selected = transfer[transfer["model"].eq(selected_transfer_name)]

    def scenario_seed_rows(family: str) -> pd.DataFrame:
        target = transfer_selected[transfer_selected["scenario_family"].eq(family)]
        return (
            target.groupby(["scenario", "seed", "requested_direction"])
            .agg(
                rank=("directional_rank_percentile", "mean"),
                regret=("normalized_regret", "mean"),
                random_regret=("random_expected_regret", "mean"),
            )
            .reset_index()
        )

    source_transfer = scenario_seed_rows("leave_source_out")
    generic = transfer[
        transfer["scenario_family"].eq("leave_source_out")
        & transfer["model"].isin(["metadata_ridge", "edit_size_heuristic"])
    ]
    generic = (
        generic.groupby(["scenario", "requested_direction", "model"])["normalized_regret"]
        .mean()
        .groupby(["scenario", "requested_direction"])
        .min()
        .rename("strongest_generic_regret")
        .reset_index()
    )
    source_transfer = source_transfer.merge(
        generic, on=["scenario", "requested_direction"], how="left"
    )
    source_transfer["random_regret_gain"] = (
        source_transfer["random_regret"] - source_transfer["regret"]
    )
    source_transfer["generic_regret_gain"] = (
        source_transfer["strongest_generic_regret"] - source_transfer["regret"]
    )
    source_transfer["passes"] = (
        source_transfer["rank"].gt(0.52)
        & source_transfer["random_regret_gain"].ge(0.02)
        & source_transfer["generic_regret_gain"].ge(0.01)
    )
    source_by_scenario = source_transfer.groupby("scenario")["passes"].all()
    gate_c = bool(source_by_scenario.sum() >= 2)

    transfer_task_details: dict[str, list[dict[str, object]]] = {}
    gate_d_parts = {}
    for family in ("cell_transfer", "reporter_transfer"):
        tasks = scenario_seed_rows(family)
        tasks["random_regret_gain"] = tasks["random_regret"] - tasks["regret"]
        tasks["passes"] = tasks["rank"].gt(0.52) & tasks["random_regret_gain"].ge(0.02)
        transfer_task_details[family] = tasks.to_dict("records")
        per_task = tasks.groupby(["scenario", "requested_direction"])["passes"].all()
        gate_d_parts[family] = int(per_task.sum())
    gate_d = bool(
        gate_d_parts.get("cell_transfer", 0) >= 2
        and gate_d_parts.get("reporter_transfer", 0) >= 2
    )

    all_edit_rank = float(source_transfer["rank"].mean())
    small_targets = transfer_selected[
        transfer_selected["scenario"].isin(
            ["leave_edit_2-5_out", "train_excluding_1-10_test_1-10"]
        )
    ]
    small = (
        small_targets.groupby(["scenario", "seed"])
        .agg(
            rank=("directional_rank_percentile", "mean"),
            regret=("normalized_regret", "mean"),
            random_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )
    small["random_regret_gain"] = small["random_regret"] - small["regret"]
    small["rank_degradation"] = all_edit_rank - small["rank"]
    small["passes"] = (
        small["rank"].gt(0.52)
        & small["random_regret_gain"].ge(0.02)
        & small["rank_degradation"].le(0.10)
    )
    gate_e = bool(
        set(small["scenario"])
        == {"leave_edit_2-5_out", "train_excluding_1-10_test_1-10"}
        and small.groupby("scenario")["passes"].all().all()
    )

    direction_detail = []
    for direction in ("increase", "decrease"):
        within = selected_source[selected_source["requested_direction"].eq(direction)].copy()
        within["random_gain"] = within["random_regret"] - within["regret"]
        source_passes = int((within["rank"].gt(0.52) & within["random_gain"].ge(0.02)).sum())
        lso = source_transfer[source_transfer["requested_direction"].eq(direction)]
        lso_rank = float(lso["rank"].mean())
        lso_gain = float(lso["random_regret_gain"].mean())
        passed = source_passes >= 2 and lso_rank > 0.52 and lso_gain >= 0.02
        direction_detail.append(
            {
                "direction": direction,
                "within_sources_passing": source_passes,
                "leave_source_out_rank": lso_rank,
                "leave_source_out_random_regret_gain": lso_gain,
                "passed": bool(passed),
            }
        )
    gate_f = {item["direction"]: item["passed"] for item in direction_detail}

    gate_g = bool(selection["dfl_gate"]["passed"]) if kind == "dfl" else False
    gate_i = bool(controls["within_frozen_0_02_tolerance"].all())
    selected_seed_regret = (
        aggregate[aggregate["model"].eq(selected_name)].groupby("seed")["normalized_regret"].mean()
    )
    seed_sd = float(selected_seed_regret.std(ddof=0)) if len(selected_seed_regret) > 1 else 0.0
    core_seed_pass = []
    core = pd.concat(
        [
            source_transfer.assign(domain="source"),
            scenario_seed_rows("cell_transfer").assign(domain="cell"),
            scenario_seed_rows("reporter_transfer").assign(domain="reporter"),
            small.assign(domain="small"),
        ],
        ignore_index=True,
        sort=False,
    )
    for seed, group in core.groupby("seed"):
        if "random_regret_gain" not in group or group["random_regret_gain"].isna().any():
            group = group.copy()
            group["random_regret_gain"] = group["random_regret"] - group["regret"]
        core_seed_pass.append(
            {
                "seed": int(seed),
                "mean_rank": float(group["rank"].mean()),
                "mean_random_regret_gain": float(group["random_regret_gain"].mean()),
                "positive_signal": bool(
                    group["rank"].mean() > 0.52 and group["random_regret_gain"].mean() >= 0.02
                ),
            }
        )
    gate_j = bool(seed_sd <= 0.02 and all(item["positive_signal"] for item in core_seed_pass))

    output = {
        "selected_model_kind": kind,
        "selected_model_name": selected_name,
        "strongest_conventional_baseline": strongest,
        "gate_A_within_source": {"passed": gate_a, "per_source": source_gate_rows.to_dict("records")},
        "gate_B_unit_robustness": {"passed": gate_b, **gate_b_detail},
        "gate_C_leave_source_out": {"passed": gate_c, "tasks": source_transfer.to_dict("records")},
        "gate_D_cell_reporter": {"passed": gate_d, "counts": gate_d_parts, "tasks": transfer_task_details},
        "gate_E_small_edit": {"passed": gate_e, "all_edit_transfer_rank": all_edit_rank, "tasks": small.to_dict("records")},
        "gate_F_direction": {"passed_by_direction": gate_f, "details": direction_detail},
        "gate_G_dfl_value": {"passed": gate_g, "selection_record": selection["dfl_gate"]},
        "gate_H_robust_dfl": {"applicable": False, "passed": None},
        "gate_I_controls": {"passed": gate_i, "controls": controls.to_dict("records")},
        "gate_J_seed_stability": {"passed": gate_j, "within_source_regret_sd": seed_sd, "core_transfer": core_seed_pass},
        "scope_guards": {"nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
    }
    (OUT / "development_gates.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
