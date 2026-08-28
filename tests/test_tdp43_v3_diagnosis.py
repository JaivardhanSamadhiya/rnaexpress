import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "v3_phase2"
MASTER = RESULTS / "tdp_diagnostic_master.csv.gz"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_phase2_master_preserves_truth_safe_interventions() -> None:
    frame = pd.read_csv(MASTER)

    assert len(frame) == 4566
    assert not frame[["parent_id", "mutant_id"]].duplicated().any()
    assert (frame["parent_sequence"].str.len() == frame["mutant_sequence"].str.len()).all()
    observed_changes = np.fromiter(
        (
            sum(left != right for left, right in zip(parent, mutant))
            for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])
        ),
        dtype=int,
        count=len(frame),
    )
    assert np.array_equal(observed_changes, frame["edited_base_count"].to_numpy())
    assert (frame["canonical_motif_count_mutant"] == 0).all()
    assert (frame["remaining_unedited_motif_count"] == 0).all()


def test_phase2_exact_mechanism_coverage_and_frozen_predictions() -> None:
    frame = pd.read_csv(MASTER)
    finite_stability = frame["stability_intervention_delta"].dropna()

    assert np.isfinite(finite_stability).all()
    assert len(finite_stability) == 3117
    assert frame["rbns_delta_r500"].notna().sum() == 3600
    assert frame["pred_nested_context_external_stack"].notna().sum() == 1006
    assert set(frame.loc[frame["pred_nested_context_external_stack"].notna(), "historical_status"]) == {
        "former_locked_post_lock_diagnostic"
    }


def test_phase2_manifest_hashes_and_protected_data_flags() -> None:
    manifest = json.loads((RESULTS / "analysis_manifest.json").read_text())

    assert manifest["historical_pairs_preserved"] == 4566
    assert manifest["historical_pairing_error_found"] is False
    assert manifest["protected_data_access"] == {
        "astrocyte_outcomes_opened": False,
        "moffatt_archive_opened": False,
    }
    for name, expected_hash in manifest["output_hashes"].items():
        assert _sha256(RESULTS / name) == expected_hash


def test_phase2_verdict_is_go_without_recasting_tdp_as_validation() -> None:
    verdict = json.loads((RESULTS / "phase2_verdict.json").read_text())

    assert verdict["decision"] == "GO"
    assert verdict["phase"] == "v3_phase2_post_lock_diagnostic"
    assert verdict["v3_changes"]["magnitude_aware_learning"] == "justified"
    assert verdict["phase3_started"] is False
    assert verdict["data_integrity"]["historical_pairing_error_found"] is False
    assert verdict["protected_data"]["moffatt_archive_listed_opened_extracted_or_used"] is False
