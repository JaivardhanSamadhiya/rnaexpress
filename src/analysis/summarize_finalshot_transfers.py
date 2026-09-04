"""Summarize frozen FinalShot transfer predictions and Gates D, E, J, and K."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_finalshot_m3_transfers import TASKS
from src.analysis.summarize_finalshot_direct_models import METRICS, inner_summary
from src.analysis.summarize_finalshot_m3 import choose_final_family, selected_m3_grid
from src.modeling.v4_decision_models import decision_set_metrics


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
DIRECT = ROOT / "results" / "finalshot" / "transfers_direct"
M3 = ROOT / "results" / "finalshot" / "transfers_m3"
OUT = ROOT / "results" / "finalshot"
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def load_result(task: str, family: str) -> tuple[np.ndarray, np.ndarray, dict[str, object], np.ndarray | None]:
    path = (M3 / f"{task}_M3.npz") if family == "M3" else (DIRECT / f"{task}_{family}.npz")
    if not path.exists():
        raise FileNotFoundError(f"Missing transfer result: {path}")
    with np.load(path, allow_pickle=False) as archive:
        indices = archive["test_indices"].astype(int)
        prediction = archive["prediction"].astype(np.float32)
        metadata = json.loads(str(archive["metadata_json"].item()))
        seeds = archive["seed_predictions"].astype(np.float32) if "seed_predictions" in archive else None
    if metadata["task"] != task or len(indices) != len(prediction) or not np.isfinite(prediction).all():
        raise RuntimeError(f"Invalid transfer archive: {path}")
    if seeds is not None and (seeds.shape != (3, len(indices)) or not np.isfinite(seeds).all()):
        raise RuntimeError(f"Invalid seed predictions: {path}")
    return indices, prediction, metadata, seeds


def aggregate(set_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    unit = (
        set_metrics.groupby(
            ["model", "task", "dataset", "requested_direction", "biological_unit"], sort=True
        )
        .agg(decision_sets=("decision_set_id", "size"), **{key: (key, "mean") for key in METRICS})
        .reset_index()
    )
    task = (
        unit.groupby(["model", "task", "dataset", "requested_direction"], sort=True)
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            **{key: (key, "mean") for key in METRICS},
        )
        .reset_index()
    )
    return unit, task


def gate_d(context: pd.DataFrame) -> dict[str, object]:
    group = context[
        context["model"].eq("M1_M2_M3_nested_selected")
        & context["task"].str.startswith("leave_")
    ].copy()
    contributions = (
        group.assign(positive=group["regret_context_value"].clip(lower=0))
        .groupby("dataset", sort=True)["positive"].sum()
    )
    total_positive = float(contributions.sum())
    maximum_share = float(contributions.max() / total_positive) if total_positive > 0 else 1.0
    result = {
        "positive_regret_tasks": int(group["regret_context_value"].gt(0).sum()),
        "task_count": int(len(group)),
        "mean_rank_context_value": float(group["rank_context_value"].mean()),
        "mean_regret_context_value": float(group["regret_context_value"].mean()),
        "maximum_source_share_of_positive_regret": maximum_share,
        "source_positive_regret_contributions": {key: float(value) for key, value in contributions.items()},
    }
    result["pass"] = bool(
        result["positive_regret_tasks"] >= 4
        and result["mean_rank_context_value"] > 0
        and result["mean_regret_context_value"] >= 0.010
        and maximum_share <= 0.75
    )
    return result


def gate_e_part(context: pd.DataFrame, tasks: tuple[str, ...]) -> dict[str, object]:
    group = context[
        context["model"].eq("M1_M2_M3_nested_selected") & context["task"].isin(tasks)
    ].copy()
    both = group["rank_context_value"].gt(0) & group["regret_context_value"].gt(0)
    result = {
        "positive_rank_and_regret_tasks": int(both.sum()),
        "task_count": int(len(group)),
        "mean_rank_context_value": float(group["rank_context_value"].mean()),
        "mean_regret_context_value": float(group["regret_context_value"].mean()),
    }
    result["pass"] = bool(
        result["positive_rank_and_regret_tasks"] >= 3
        and result["mean_regret_context_value"] >= 0.005
    )
    return result


def m3_vs_m2(task_metrics: pd.DataFrame, m3_model: str) -> dict[str, object]:
    leave = task_metrics[task_metrics["task"].str.startswith("leave_")]
    m3 = leave[leave["model"].eq(m3_model)]
    m2 = leave[leave["model"].eq("M2")]
    paired = m3.merge(
        m2,
        on=["task", "dataset", "requested_direction"],
        suffixes=("_m3", "_m2"),
        validate="one_to_one",
    )
    rank_difference = paired["directional_rank_percentile_m3"] - paired["directional_rank_percentile_m2"]
    regret_difference = paired["normalized_regret_m2"] - paired["normalized_regret_m3"]
    result = {
        "model": m3_model,
        "mean_rank_improvement": float(rank_difference.mean()),
        "mean_regret_improvement": float(regret_difference.mean()),
        "regret_worsened_by_more_than_0_020": int(regret_difference.lt(-0.020).sum()),
        "task_count": int(len(paired)),
    }
    result["pass"] = bool(
        (
            result["mean_regret_improvement"] >= 0.005
            or result["mean_rank_improvement"] >= 0.010
        )
        and result["regret_worsened_by_more_than_0_020"] <= 1
    )
    return result


def main() -> None:
    rows = pd.read_csv(ROWS)
    set_records = []
    selection_records = []
    for task in TASKS:
        loaded = {family: load_result(task, family) for family in ("M0", "R1", "M1", "M2", "M3")}
        reference_indices = loaded["M0"][0]
        if any(not np.array_equal(reference_indices, item[0]) for item in loaded.values()):
            raise RuntimeError(f"Transfer test indices differ across families for {task}")
        m1_meta = loaded["M1"][2]
        m2_meta = loaded["M2"][2]
        m3_meta = loaded["M3"][2]
        candidates = {
            "M1": inner_summary(m1_meta),
            "M2": inner_summary(m2_meta),
            "M3": selected_m3_grid(m3_meta),
        }
        selected_family = choose_final_family(candidates)
        selection_records.append({
            "task": task,
            "selected_family": selected_family,
            "test_rows": int(len(reference_indices)),
        })
        predictions = {
            "M0_geometry": loaded["M0"][1],
            "R1_3UTRBERT": loaded["R1"][1],
            "M1": loaded["M1"][1],
            "M2": loaded["M2"][1],
            "M3": loaded["M3"][1],
            "M1_M2_M3_nested_selected": loaded[selected_family][1],
        }
        for seed_index, seed in enumerate((17, 41, 89)):
            predictions[f"M3_seed{seed}"] = loaded["M3"][3][seed_index]
        frame = rows.iloc[reference_indices].reset_index(drop=True)
        for model, prediction in predictions.items():
            for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
                metric = decision_set_metrics(
                    frame, sign * prediction, model, direction, SEED, f"frozen_transfer_{task}"
                )
                metric["task"] = task
                set_records.append(metric)
    set_metrics = pd.concat(set_records, ignore_index=True)
    unit_metrics, task_metrics = aggregate(set_metrics)
    baseline = task_metrics[task_metrics["model"].eq("M0_geometry")]
    records = []
    for model in sorted(set(task_metrics["model"]) - {"M0_geometry"}):
        full = task_metrics[task_metrics["model"].eq(model)]
        paired = full.merge(
            baseline,
            on=["task", "dataset", "requested_direction"],
            suffixes=("_full", "_m0"),
            validate="one_to_one",
        )
        for row in paired.itertuples(index=False):
            records.append({
                "model": model,
                "task": row.task,
                "dataset": row.dataset,
                "requested_direction": row.requested_direction,
                "rank_context_value": row.directional_rank_percentile_full - row.directional_rank_percentile_m0,
                "regret_context_value": row.normalized_regret_m0 - row.normalized_regret_full,
                "good3_context_value": row.good_selection_at_3_full - row.good_selection_at_3_m0,
                "good5_context_value": row.good_selection_at_5_full - row.good_selection_at_5_m0,
            })
    context = pd.DataFrame(records)
    gate_j = m3_vs_m2(task_metrics, "M3")
    seed_j = [m3_vs_m2(task_metrics, f"M3_seed{seed}") for seed in (17, 41, 89)]
    result = {
        "phase": "FinalShot frozen zero-shot transfers",
        "task_family_selection": selection_records,
        "gate_D_leave_source": gate_d(context),
        "gate_E_cell": gate_e_part(context, ("CAD_to_N2A", "N2A_to_CAD")),
        "gate_E_reporter": gate_e_part(context, ("Firefly_to_GFP", "GFP_to_Firefly")),
        "gate_E_pass": False,
        "gate_J_measurement_process": gate_j,
        "gate_K_transfer_seed_conclusions": seed_j,
        "gate_K_all_seed_gate_J_agree": len({item["pass"] for item in seed_j}) == 1,
        "target_test_outcomes_used_for_fitting": False,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    result["gate_E_pass"] = bool(result["gate_E_cell"]["pass"] and result["gate_E_reporter"]["pass"])
    set_metrics.to_csv(OUT / "transfer_set_metrics.csv.gz", index=False, compression=GZIP)
    unit_metrics.to_csv(OUT / "transfer_unit_metrics.csv", index=False)
    task_metrics.to_csv(OUT / "transfer_task_metrics.csv", index=False)
    context.to_csv(OUT / "transfer_context_values.csv", index=False)
    (OUT / "transfer_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
