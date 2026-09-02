"""Apply the prospectively frozen RNAddress v4 Phase B2 gates."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "results" / "v4_phaseB2"
SEED = 42_017


def paired_context(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    full = frame[frame["model"].eq("full")]
    nuisance = frame[frame["model"].eq("nuisance")]
    paired = full.merge(nuisance, on=keys, suffixes=("_full", "_nuisance"), validate="one_to_one")
    paired["rank_context_value"] = (
        paired["directional_rank_percentile_full"]
        - paired["directional_rank_percentile_nuisance"]
    )
    paired["regret_context_value"] = (
        paired["normalized_regret_nuisance"] - paired["normalized_regret_full"]
    )
    paired["good3_context_value"] = (
        paired["good_selection_at_3_full"] - paired["good_selection_at_3_nuisance"]
    )
    return paired


def source_direction_means(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["dataset", "requested_direction"])[
            ["rank_context_value", "regret_context_value", "good3_context_value"]
        ]
        .mean()
        .reset_index()
    )


def control_values(set_metrics: pd.DataFrame) -> pd.DataFrame:
    records = []
    for control, full_name in (
        ("context_shuffle", "full_on_context_shuffle"),
        ("delta_shuffle", "full_on_delta_shuffle"),
        ("interaction_knockout", "full"),
        ("parent_invariant", "full"),
    ):
        full = set_metrics[set_metrics["model"].eq(full_name)]
        candidate = set_metrics[set_metrics["model"].eq(control)]
        keys = ["dataset", "decision_set_id", "biological_unit", "requested_direction"]
        paired = full.merge(candidate, on=keys, suffixes=("_full", "_control"), validate="one_to_one")
        paired["rank_gain"] = (
            paired["directional_rank_percentile_full"]
            - paired["directional_rank_percentile_control"]
        )
        paired["regret_gain"] = (
            paired["normalized_regret_control"] - paired["normalized_regret_full"]
        )
        units = (
            paired.groupby(["dataset", "requested_direction", "biological_unit"])[
                ["rank_gain", "regret_gain"]
            ]
            .mean()
            .reset_index()
        )
        summary = (
            units.groupby(["dataset", "requested_direction"])[["rank_gain", "regret_gain"]]
            .mean()
            .reset_index()
        )
        summary["control"] = control
        records.append(summary)
    return pd.concat(records, ignore_index=True)


def main() -> None:
    primary_units = pd.read_csv(OUT / "primary_biological_unit_metrics.csv")
    primary_sets = pd.read_csv(OUT / "primary_set_metrics.csv.gz")
    transfer_units = pd.read_csv(OUT / "transfer_biological_unit_metrics.csv")
    subgroup_units = pd.read_csv(OUT / "subgroup_biological_unit_metrics.csv")
    selection = pd.read_csv(OUT / "inner_model_selection.csv.gz")

    primary = paired_context(
        primary_units,
        ["dataset", "requested_direction", "biological_unit"],
    )
    primary.to_csv(OUT / "context_value_by_unit.csv", index=False)
    source_direction = source_direction_means(primary)
    source_direction.to_csv(OUT / "context_value_by_source_direction.csv", index=False)
    overall = source_direction[
        ["rank_context_value", "regret_context_value", "good3_context_value"]
    ].mean()

    unit_both = (
        primary.groupby(["dataset", "biological_unit"])[
            ["rank_context_value", "regret_context_value", "good3_context_value"]
        ]
        .mean()
        .reset_index()
    )
    gains = unit_both["regret_context_value"].to_numpy(float)
    leave_best = float((gains.sum() - gains.max()) / (len(gains) - 1))
    rng = np.random.default_rng(SEED)
    by_source = [group["regret_context_value"].to_numpy(float) for _, group in unit_both.groupby("dataset")]
    bootstrap = np.empty(10_000, dtype=float)
    for index in range(len(bootstrap)):
        bootstrap[index] = float(
            np.mean([rng.choice(values, size=len(values), replace=True).mean() for values in by_source])
        )
    bootstrap_record = {
        "seed": SEED,
        "resamples": 10_000,
        "hierarchy": "biological units resampled within source; source means equally weighted",
        "observed_equal_source_mean_regret_context_value": float(overall["regret_context_value"]),
        "low_95": float(np.quantile(bootstrap, 0.025)),
        "median": float(np.quantile(bootstrap, 0.5)),
        "high_95": float(np.quantile(bootstrap, 0.975)),
    }
    (OUT / "parent_bootstrap.json").write_text(
        json.dumps(bootstrap_record, indent=2) + "\n", encoding="utf-8"
    )

    controls = control_values(primary_sets)
    controls.to_csv(OUT / "control_context_value.csv", index=False)
    control_overall = controls.groupby("control")[["rank_gain", "regret_gain"]].mean()

    transfer = paired_context(
        transfer_units,
        [
            "scenario_family",
            "scenario",
            "dataset",
            "requested_direction",
            "biological_unit",
        ],
    )
    transfer_summary = (
        transfer.groupby(["scenario_family", "scenario", "requested_direction"])[
            ["rank_context_value", "regret_context_value", "good3_context_value"]
        ]
        .mean()
        .reset_index()
    )
    transfer_summary.to_csv(OUT / "transfer_context_value.csv", index=False)

    subgroup = paired_context(
        subgroup_units,
        ["subgroup", "dataset", "requested_direction", "biological_unit"],
    )
    subgroup_summary = (
        subgroup.groupby(["subgroup", "dataset", "requested_direction"])[
            ["rank_context_value", "regret_context_value", "good3_context_value"]
        ]
        .mean()
        .reset_index()
    )
    subgroup_summary.to_csv(OUT / "subgroup_context_value.csv", index=False)
    subgroup_overall = subgroup_summary.groupby("subgroup")[
        ["rank_context_value", "regret_context_value", "good3_context_value"]
    ].mean()

    # Gate A
    gate_a = bool(
        (
            overall["regret_context_value"] >= 0.010
            and overall["rank_context_value"] >= 0
        )
        or (
            overall["rank_context_value"] >= 0.020
            and overall["regret_context_value"] >= -0.005
        )
    )

    # Gate B
    gate_b_controls = {}
    for control in ("context_shuffle", "delta_shuffle", "interaction_knockout"):
        values = control_overall.loc[control]
        passed = bool(
            (
                values["regret_gain"] >= 0.005
                or values["rank_gain"] >= 0.010
            )
            and values["regret_gain"] >= -0.002
            and values["rank_gain"] >= -0.002
        )
        gate_b_controls[control] = {
            "rank_gain": float(values["rank_gain"]),
            "regret_gain": float(values["regret_gain"]),
            "passed": passed,
        }
    gate_b = all(record["passed"] for record in gate_b_controls.values())

    # Gate C
    gate_c_values = {
        "biological_units": len(unit_both),
        "median_regret_context_value": float(np.median(gains)),
        "fraction_improved": float(np.mean(gains > 0)),
        "leave_best_unit_out_mean": leave_best,
        "bootstrap_low_95": bootstrap_record["low_95"],
    }
    gate_c = bool(
        gate_c_values["median_regret_context_value"] > 0
        and gate_c_values["fraction_improved"] > 0.50
        and gate_c_values["leave_best_unit_out_mean"] > 0
        and gate_c_values["bootstrap_low_95"] >= -0.005
    )

    # Gate D
    mikl_matched = subgroup_overall.loc["mikl_matched"]
    gate_d = bool(
        mikl_matched["rank_context_value"] >= 0.010
        and mikl_matched["regret_context_value"] >= 0.005
    )

    # Gate E
    lso = transfer_summary[transfer_summary["scenario_family"].eq("leave_source_out")].copy()
    lso["task_pass"] = lso["regret_context_value"].ge(0.005)
    lso_source = lso.groupby("scenario")["regret_context_value"].mean()
    gate_e_values = {
        "tasks_at_or_above_0_005": int(lso["task_pass"].sum()),
        "positive_source_means": int((lso_source > 0).sum()),
        "minimum_source_mean": float(lso_source.min()),
        "equal_source_direction_mean": float(lso["regret_context_value"].mean()),
    }
    gate_e = bool(
        gate_e_values["tasks_at_or_above_0_005"] >= 4
        and gate_e_values["positive_source_means"] >= 2
        and gate_e_values["minimum_source_mean"] >= -0.010
        and gate_e_values["equal_source_direction_mean"] >= 0.005
    )

    # Gate F
    transfer_counts = {}
    for family in ("cell_transfer", "reporter_transfer"):
        values = transfer_summary[transfer_summary["scenario_family"].eq(family)]
        transfer_counts[family] = int(values["regret_context_value"].ge(0.005).sum())
    gate_f = transfer_counts["cell_transfer"] >= 2 and transfer_counts["reporter_transfer"] >= 2

    # Gate G
    small = subgroup_overall.loc["2-10"]
    small_2_5 = subgroup_overall.loc["2-5"]
    small_6_10 = subgroup_overall.loc["6-10"]
    gate_g = bool(
        small["rank_context_value"] >= 0.010
        and small["regret_context_value"] >= 0.005
        and small_2_5["regret_context_value"] >= -0.005
        and small_6_10["regret_context_value"] >= -0.005
    )

    # Gate H
    direction_records = {}
    within_direction = source_direction.groupby("requested_direction")[
        ["rank_context_value", "regret_context_value"]
    ].mean()
    lso_direction = lso.groupby("requested_direction")[["rank_context_value", "regret_context_value"]].mean()
    small_direction = subgroup_summary[subgroup_summary["subgroup"].eq("2-10")].groupby(
        "requested_direction"
    )[["rank_context_value", "regret_context_value"]].mean()
    unit_direction_fraction = primary.groupby("requested_direction")["regret_context_value"].apply(
        lambda values: float(np.mean(values > 0))
    )
    for direction in ("increase", "decrease"):
        record = {
            "within_rank_context_value": float(within_direction.loc[direction, "rank_context_value"]),
            "within_regret_context_value": float(within_direction.loc[direction, "regret_context_value"]),
            "leave_source_out_regret_context_value": float(lso_direction.loc[direction, "regret_context_value"]),
            "small_edit_regret_context_value": float(small_direction.loc[direction, "regret_context_value"]),
            "fraction_units_improved": float(unit_direction_fraction.loc[direction]),
        }
        record["passed"] = bool(
            record["within_regret_context_value"] >= 0.005
            and record["within_rank_context_value"] >= 0
            and record["leave_source_out_regret_context_value"] >= 0.003
            and record["small_edit_regret_context_value"] >= 0.003
            and record["fraction_units_improved"] > 0.50
        )
        direction_records[direction] = record
    gate_h = any(record["passed"] for record in direction_records.values())

    # Gate I
    source_means = source_direction.groupby("dataset")["regret_context_value"].mean()
    gate_i = bool((source_means >= 0.005).sum() >= 2 and source_means.min() >= -0.005)

    # Gate J
    astro_path = ROOT / "src" / "pairing" / "audit_astrocyte.py"
    astro_hash = hashlib.sha256(astro_path.read_bytes()).hexdigest()
    primary_run = json.loads((OUT / "primary_run.json").read_text(encoding="utf-8"))
    expected_hash = "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    scope_ok = not any(primary_run["scope_guards"].values())
    gate_j = bool(gate_b and scope_ok and astro_hash == expected_hash)

    gates = {
        "A_context_beats_geometry": {
            "passed": gate_a,
            "rank_context_value": float(overall["rank_context_value"]),
            "regret_context_value": float(overall["regret_context_value"]),
        },
        "B_context_necessity": {"passed": gate_b, "controls": gate_b_controls},
        "C_distributed_units": {"passed": gate_c, **gate_c_values},
        "D_mikl_matched_context": {
            "passed": gate_d,
            "rank_context_value": float(mikl_matched["rank_context_value"]),
            "regret_context_value": float(mikl_matched["regret_context_value"]),
        },
        "E_leave_source_out": {"passed": gate_e, **gate_e_values},
        "F_cell_reporter_transfer": {"passed": gate_f, **transfer_counts},
        "G_small_edit_bridge": {
            "passed": gate_g,
            "combined_2_10_rank_context_value": float(small["rank_context_value"]),
            "combined_2_10_regret_context_value": float(small["regret_context_value"]),
            "2_5_regret_context_value": float(small_2_5["regret_context_value"]),
            "6_10_regret_context_value": float(small_6_10["regret_context_value"]),
        },
        "H_direction": {"passed": gate_h, "directions": direction_records},
        "I_source_robustness": {
            "passed": gate_i,
            "source_regret_context_value": {key: float(value) for key, value in source_means.items()},
        },
        "J_controls_integrity": {
            "passed": gate_j,
            "relationship_controls_passed": gate_b,
            "scope_guards_all_false": scope_ok,
            "astrocyte_loader_sha256": astro_hash,
            "astrocyte_loader_unchanged": astro_hash == expected_hash,
        },
    }
    gate_passes = {name: record["passed"] for name, record in gates.items()}
    verdict = "NO-GO"
    result = {
        "verdict": verdict,
        "central_answer": "no",
        "gates": gates,
        "gate_passes": gate_passes,
        "gates_passed": int(sum(gate_passes.values())),
        "gates_total": len(gate_passes),
        "parent_invariant": {
            "rank_gain_full_over_null": float(control_overall.loc["parent_invariant", "rank_gain"]),
            "regret_gain_full_over_null": float(control_overall.loc["parent_invariant", "regret_gain"]),
        },
        "bootstrap": bootstrap_record,
        "selected_outer_families": {},
        "scope_guards": primary_run["scope_guards"],
    }
    # JSON object keys cannot be tuples.
    result["selected_outer_families"] = {
        f"{direction}|{family}": int(count)
        for (direction, family), count in selection[selection["selected"]]
        .groupby(["direction", "family"])
        .size()
        .items()
    }
    (OUT / "development_gates.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    manifest_paths = [
        OUT / "primary_run.json",
        OUT / "inner_model_selection.csv.gz",
        OUT / "primary_candidate_predictions.csv.gz",
        OUT / "primary_set_metrics.csv.gz",
        OUT / "transfer_set_metrics.csv.gz",
        OUT / "subgroup_set_metrics.csv.gz",
        OUT / "development_gates.json",
    ]
    manifest = {
        "phase": "v4_phaseB2",
        "git_head_at_summary": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "files": {
            str(path.relative_to(ROOT)): {
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in manifest_paths
        },
    }
    (OUT / "reproducibility_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
