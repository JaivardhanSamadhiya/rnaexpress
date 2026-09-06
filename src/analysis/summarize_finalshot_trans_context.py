"""Evaluate frozen Gate H on crossed CAD/N2A cell transfers."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.summarize_finalshot_transfers import aggregate
from src.modeling.v4_decision_models import decision_set_metrics


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
DIRECT = ROOT / "results" / "finalshot" / "transfers_direct"
M3 = ROOT / "results" / "finalshot" / "transfers_m3"
CONTROL = ROOT / "results" / "finalshot" / "transfers_m3_trans_control"
OUT = ROOT / "results" / "finalshot"
TASKS = ("CAD_to_N2A", "N2A_to_CAD")
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    with np.load(path, allow_pickle=False) as archive:
        indices = archive["test_indices"].astype(int)
        prediction = archive["prediction"].astype(np.float32)
        metadata = json.loads(str(archive["metadata_json"].item()))
    if len(indices) != len(prediction) or not np.isfinite(prediction).all():
        raise RuntimeError(f"Invalid transfer archive: {path}")
    return indices, prediction, metadata


def comparison(task_metrics: pd.DataFrame, full: str, knockout: str) -> dict[str, object]:
    selected = task_metrics[task_metrics["model"].eq(full)]
    control = task_metrics[task_metrics["model"].eq(knockout)]
    paired = selected.merge(
        control,
        on=["task", "dataset", "requested_direction"],
        suffixes=("_full", "_knockout"),
        validate="one_to_one",
    )
    rank = paired["directional_rank_percentile_full"] - paired["directional_rank_percentile_knockout"]
    regret = paired["normalized_regret_knockout"] - paired["normalized_regret_full"]
    mean_rank = float(rank.mean())
    mean_regret = float(regret.mean())
    passed = bool(
        (mean_regret >= 0.005 or mean_rank >= 0.010)
        and mean_regret >= -0.002
        and mean_rank >= -0.002
    )
    return {
        "full_model": full,
        "knockout_model": knockout,
        "directional_tasks": int(len(paired)),
        "mean_rank_improvement_over_knockout": mean_rank,
        "mean_regret_improvement_over_knockout": mean_regret,
        "rank_threshold_met": bool(mean_rank >= 0.010),
        "regret_threshold_met": bool(mean_regret >= 0.005),
        "companion_floor_met": bool(mean_rank >= -0.002 and mean_regret >= -0.002),
        "pass": passed,
    }


def main() -> None:
    rows = pd.read_csv(ROWS)
    records = []
    archive_audit = []
    for task in TASKS:
        archives = {
            "M1_trans_knockout": load(DIRECT / f"{task}_M1.npz"),
            "M2": load(DIRECT / f"{task}_M2.npz"),
            "M3": load(M3 / f"{task}_M3.npz"),
            "M3_trans_knockout": load(CONTROL / f"{task}_M3.npz"),
        }
        reference = archives["M2"][0]
        if any(not np.array_equal(reference, item[0]) for item in archives.values()):
            raise RuntimeError(f"Crossed-cell test indices differ for {task}")
        control_metadata = archives["M3_trans_knockout"][2]
        if (
            control_metadata.get("control") != "trans_interaction_knockout"
            or control_metadata.get("target_test_outcomes_used_for_fitting") is not False
            or control_metadata.get("nzip_outcomes_accessed") is not False
            or control_metadata.get("astrocyte_data_accessed") is not False
        ):
            raise RuntimeError(f"Invalid trans-control provenance for {task}")
        path = CONTROL / f"{task}_M3.npz"
        archive_audit.append({
            "task": task,
            "rows": int(len(reference)),
            "sha256": sha256(path),
            "selected_penalty": control_metadata["selected_penalty"],
            "selected_group_fraction": control_metadata["selected_group_fraction"],
            "selected_head_form": control_metadata["selected_head_form"],
        })
        frame = rows.iloc[reference].reset_index(drop=True)
        for model, (_, prediction, _) in archives.items():
            for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
                metric = decision_set_metrics(
                    frame, sign * prediction, model, direction, SEED,
                    f"frozen_trans_context_{task}",
                )
                metric["task"] = task
                records.append(metric)
    set_metrics = pd.concat(records, ignore_index=True)
    unit_metrics, task_metrics = aggregate(set_metrics)
    m2 = comparison(task_metrics, "M2", "M1_trans_knockout")
    m3 = comparison(task_metrics, "M3", "M3_trans_knockout")
    summary = {
        "phase": "FinalShot Gate H trans context",
        "crossed_cell_primary_family": "M3",
        "M2_comparison": m2,
        "M3_comparison": m3,
        "gate_H_pass": m3["pass"],
        "trans_context_retained": m3["pass"],
        "control_archive_audit": archive_audit,
        "target_test_outcomes_used_for_fitting": False,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    set_metrics.to_csv(OUT / "trans_context_set_metrics.csv.gz", index=False, compression=GZIP)
    unit_metrics.to_csv(OUT / "trans_context_unit_metrics.csv", index=False)
    task_metrics.to_csv(OUT / "trans_context_task_metrics.csv", index=False)
    (OUT / "gate_h_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
