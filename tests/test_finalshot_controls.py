"""Tests for frozen FinalShot mechanism-breaking feature controls."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.finalshot_controls import (
    FinalShotControlledFeatureStore,
    delta_shuffle_map,
)
from src.modeling.finalshot_models import FinalShotFeatureStore


ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
GATE_G = ROOT / "results" / "finalshot" / "gate_g_summary.json"
CONTROL_CONTEXT = ROOT / "results" / "finalshot" / "mechanism_control_context_values.csv"
GATE_H = ROOT / "results" / "finalshot" / "gate_h_summary.json"
HEAD_RANDOMIZATION = ROOT / "results" / "finalshot" / "measurement_head_randomization_summary.json"


def test_delta_shuffle_is_deterministic_cross_unit_and_fail_closed() -> None:
    rows = []
    for index in range(10):
        rows.append({
            "dataset": "source",
            "cell_type": "CAD",
            "substitution_count": 1,
            "insertion_length": 0,
            "deletion_length": 0,
            "replacement_length": 0,
            "edit_cost": 2,
            "motif_family": "motif",
            "biological_unit": "u1" if index < 6 else "u2",
            "candidate_id": f"eligible-{index}",
        })
    for index in range(4):
        rows.append({
            "dataset": "source",
            "cell_type": "CAD",
            "substitution_count": 1,
            "insertion_length": 0,
            "deletion_length": 0,
            "replacement_length": 0,
            "edit_cost": 2,
            "motif_family": "sparse",
            "biological_unit": "u1" if index < 2 else "u2",
            "candidate_id": f"sparse-{index}",
        })
    frame = pd.DataFrame(rows)
    first, eligible, audit = delta_shuffle_map(frame)
    second, second_eligible, _ = delta_shuffle_map(frame)
    assert np.array_equal(first, second)
    assert np.array_equal(eligible, second_eligible)
    assert eligible[:10].all() and not eligible[10:].any()
    assert (
        frame.loc[eligible, "biological_unit"].to_numpy()
        != frame.iloc[first[eligible]]["biological_unit"].to_numpy()
    ).all()
    assert audit["eligible"].sum() == 1


def test_control_feature_stores_preserve_frozen_invariants() -> None:
    rows = pd.read_csv(ROWS)
    paths = (RBP, DICTIONARY, EXPRESSION)
    indices = np.asarray([0, 1, 50_000])
    base = FinalShotFeatureStore(rows, *paths)
    base_m1, base_layout = base.materialize(indices, "M1")

    trans = FinalShotControlledFeatureStore(rows, *paths, "trans_interaction_knockout")
    trans_m2, trans_layout = trans.materialize(indices, "M2")
    assert trans_layout.feature_count == base_layout.feature_count
    assert np.array_equal(trans_m2, base_m1)

    parent = FinalShotControlledFeatureStore(rows, *paths, "parent_binding_knockout")
    parent_m1, parent_layout = parent.materialize(indices, "M1")
    assert np.array_equal(parent_m1[:, parent_layout.geometry], base_m1[:, base_layout.geometry])
    for columns in parent_layout.base_columns:
        assert np.all(parent_m1[:, columns[[6, 7]]] == 0)

    identity = FinalShotControlledFeatureStore(rows, *paths, "rbp_identity_permutation")
    identity_m1, identity_layout = identity.materialize(indices, "M1")
    original_blocks = base_m1[:, base_layout.geometry.stop:].reshape(len(indices), 103, 9)
    permuted_blocks = identity_m1[:, identity_layout.geometry.stop:].reshape(len(indices), 103, 9)
    assert np.array_equal(np.sort(original_blocks, axis=1), np.sort(permuted_blocks, axis=1))
    assert not np.array_equal(original_blocks, permuted_blocks)


def test_control_code_has_no_protected_data_path() -> None:
    paths = (
        ROOT / "src" / "modeling" / "finalshot_controls.py",
        ROOT / "src" / "analysis" / "run_finalshot_direct_controls.py",
        ROOT / "src" / "analysis" / "run_finalshot_m3_controls.py",
        ROOT / "src" / "analysis" / "run_finalshot_m3_trans_control.py",
        ROOT / "src" / "analysis" / "run_finalshot_head_randomization.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    assert "data/processed/nzip" not in source
    assert "data/raw/astrocyte" not in source
    assert "astrocyte_gse330741" not in source


def test_trans_control_wrapper_isolated_from_primary_transfer_outputs() -> None:
    from src.analysis import run_finalshot_m3_trans_control as control
    from src.analysis import run_finalshot_m3_transfers as primary

    assert control.CACHE != primary.CACHE
    assert control.OUT != primary.OUT
    assert control.IMPLEMENTATION != primary.IMPLEMENTATION
    rows = pd.read_csv(ROWS, nrows=10)
    store = control.TransKnockoutStore(rows, RBP, DICTIONARY, EXPRESSION)
    assert store.control == "trans_interaction_knockout"


def test_gate_g_summary_matches_frozen_context_values() -> None:
    summary = json.loads(GATE_G.read_text(encoding="utf-8"))
    context = pd.read_csv(CONTROL_CONTEXT)
    assert len(summary["controls"]) == 2
    assert set(context["control"]) == {"rbp_identity_permutation", "delta_rbp_shuffle"}
    assert set(context["model"]) == {"observed_nested", "broken_nested"}
    assert context.groupby(["control", "model"]).size().eq(6).all()
    for item in summary["controls"]:
        control = item["control"]
        observed = context[(context["control"] == control) & (context["model"] == "observed_nested")]
        broken = context[(context["control"] == control) & (context["model"] == "broken_nested")]
        assert np.isclose(observed["rank_context_value"].mean(), item["observed_rank_context_value"])
        assert np.isclose(observed["regret_context_value"].mean(), item["observed_regret_context_value"])
        assert np.isclose(broken["rank_context_value"].mean(), item["control_rank_context_value"])
        assert np.isclose(broken["regret_context_value"].mean(), item["control_regret_context_value"])
        assert np.isclose(
            item["mean_retained_fraction"],
            np.mean([item["rank_retained_fraction"], item["regret_retained_fraction"]]),
        )
        expected_pass = (
            item["eliminates_at_least_half_one_metric"]
            and item["mean_retained_at_most_half"]
            and not item["control_meets_gate_A"]
        )
        assert item["individual_pass"] is expected_pass
    assert summary["gate_G_pass"] is all(item["individual_pass"] for item in summary["controls"])
    assert summary["nzip_outcomes_accessed"] is False
    assert summary["astrocyte_data_accessed"] is False


def test_gate_h_uses_primary_m3_and_frozen_thresholds() -> None:
    summary = json.loads(GATE_H.read_text(encoding="utf-8"))
    assert summary["crossed_cell_primary_family"] == "M3"
    for key in ("M2_comparison", "M3_comparison"):
        item = summary[key]
        rank = item["mean_rank_improvement_over_knockout"]
        regret = item["mean_regret_improvement_over_knockout"]
        expected = (regret >= 0.005 or rank >= 0.010) and regret >= -0.002 and rank >= -0.002
        assert item["pass"] is expected
        assert item["directional_tasks"] == 4
    assert summary["gate_H_pass"] is summary["M3_comparison"]["pass"]
    assert summary["trans_context_retained"] is summary["gate_H_pass"]
    assert len(summary["control_archive_audit"]) == 2
    assert all(len(item["sha256"]) == 64 for item in summary["control_archive_audit"])
    assert summary["target_test_outcomes_used_for_fitting"] is False
    assert summary["nzip_outcomes_accessed"] is False
    assert summary["astrocyte_data_accessed"] is False


def test_measurement_head_randomization_preserves_latent_score() -> None:
    summary = json.loads(HEAD_RANDOMIZATION.read_text(encoding="utf-8"))
    calibration = summary["calibration"]
    assert summary["complete_derangement"] is True
    assert summary["baseline_calibration_reproduced"] is True
    assert summary["latent_ranking_bitwise_unchanged"] is True
    assert len(summary["head_block_permutation"]) == 5
    assert all(source != target for source, target in summary["head_block_permutation"].items())
    assert calibration["pooled_mse_degraded"] is True
    assert calibration["pooled_spearman_degraded"] is True
    assert summary["control_pass"] is (
        calibration["pooled_mse_degraded"]
        and calibration["pooled_spearman_degraded"]
        and calibration["equal_head_mse_degraded"]
        and calibration["equal_head_spearman_degraded"]
    )
    assert summary["nzip_outcomes_accessed"] is False
    assert summary["astrocyte_data_accessed"] is False
