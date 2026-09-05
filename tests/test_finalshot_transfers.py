"""Integrity checks for the completed frozen FinalShot transfer evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / "results" / "finalshot" / "transfers_direct"
M3 = ROOT / "results" / "finalshot" / "transfers_m3"
OUT = ROOT / "results" / "finalshot"
TASKS = (
    "CAD_to_N2A",
    "N2A_to_CAD",
    "Firefly_to_GFP",
    "GFP_to_Firefly",
    "leave_Mikl",
    "leave_TDP",
    "leave_Moffatt",
)


def _archive(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    with np.load(path, allow_pickle=False) as item:
        indices = item["test_indices"].astype(int)
        prediction = item["prediction"].astype(float)
        metadata = json.loads(str(item["metadata_json"].item()))
    return indices, prediction, metadata


def test_transfer_runners_do_not_reference_protected_sources() -> None:
    paths = (
        ROOT / "src" / "analysis" / "run_finalshot_direct_transfers.py",
        ROOT / "src" / "analysis" / "run_finalshot_m3_transfers.py",
        ROOT / "src" / "analysis" / "summarize_finalshot_transfers.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    assert "data/processed/nzip" not in source
    assert "data/raw/astrocyte" not in source
    assert "astrocyte_gse330741" not in source


def test_all_transfer_archives_are_complete_aligned_and_protected() -> None:
    assert len(list(DIRECT.glob("*.npz"))) == 28
    assert len(list(M3.glob("*.npz"))) == 7
    for task in TASKS:
        archives = {
            family: _archive(
                M3 / f"{task}_M3.npz" if family == "M3" else DIRECT / f"{task}_{family}.npz"
            )
            for family in ("M0", "R1", "M1", "M2", "M3")
        }
        reference = archives["M0"][0]
        for family, (indices, prediction, metadata) in archives.items():
            assert np.array_equal(indices, reference), (task, family)
            assert len(prediction) == len(indices)
            assert np.isfinite(prediction).all()
            assert metadata["task"] == task
            assert metadata["target_test_outcomes_used_for_fitting"] is False
            assert metadata["nzip_outcomes_accessed"] is False
            assert metadata["astrocyte_data_accessed"] is False
        with np.load(M3 / f"{task}_M3.npz", allow_pickle=False) as item:
            assert item["seed_predictions"].shape == (3, len(reference))
            assert np.isfinite(item["seed_predictions"]).all()


def test_frozen_transfer_gate_summary_matches_completed_evaluation() -> None:
    summary = json.loads((OUT / "transfer_summary.json").read_text(encoding="utf-8"))
    selected = {row["task"]: row["selected_family"] for row in summary["task_family_selection"]}
    assert selected == {
        "CAD_to_N2A": "M3",
        "N2A_to_CAD": "M3",
        "Firefly_to_GFP": "M3",
        "GFP_to_Firefly": "M3",
        "leave_Mikl": "M2",
        "leave_TDP": "M2",
        "leave_Moffatt": "M3",
    }
    gate_d = summary["gate_D_leave_source"]
    assert gate_d["pass"] is True
    assert gate_d["positive_regret_tasks"] == 6
    assert gate_d["mean_rank_context_value"] > 0
    assert gate_d["mean_regret_context_value"] >= 0.010
    assert gate_d["maximum_source_share_of_positive_regret"] <= 0.75
    assert summary["gate_E_pass"] is False
    assert summary["gate_E_cell"]["positive_rank_and_regret_tasks"] == 1
    assert summary["gate_E_reporter"]["positive_rank_and_regret_tasks"] == 2
    assert summary["gate_J_measurement_process"]["pass"] is False
    assert summary["gate_J_measurement_process"]["regret_worsened_by_more_than_0_020"] == 2
    assert summary["gate_K_all_seed_gate_J_agree"] is True
    assert {row["pass"] for row in summary["gate_K_transfer_seed_conclusions"]} == {False}
    assert summary["target_test_outcomes_used_for_fitting"] is False
    assert summary["nzip_outcomes_accessed"] is False
    assert summary["astrocyte_data_accessed"] is False
