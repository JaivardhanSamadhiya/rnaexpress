"""Additive thin entrypoint: admitted mean effects only, no replicate reader.

Reuse the committed canonical replay mathematics with a temporary in-memory
loader replacement. No source file, model, configuration or gate is changed.
"""
from pathlib import Path
import argparse
import importlib
from unittest.mock import patch
from . import canonical_inner_replay as replay

np, pd = replay.np, replay.pd
IDENTITY = ["intervention_id", "dataset", "biological_component", "parent_context_id", "parent_sequence", "mutant_sequence"]
CORE_NAME = "results/probabilistic_ranking_20260928/candidate_index.csv"
FOUNDATION_NAME = "results/generalization_20261007/prefit_manifest.json"
AUTHOR_ADMISSION_NAME = "results/probabilistic_ranking_20260928/prefit_manifest.json"


def read_admitted_frame(core_path, row_path, identity, expected_rows, studies):
    """Explicit columns only; preserve the original pandas default parser."""
    fields = list(dict.fromkeys(IDENTITY + ["endpoint_class", "measured_delta", "primary_eligible"]))
    frame = pd.read_csv(core_path, usecols=fields, low_memory=False)[fields]
    assert len(frame) == expected_rows and frame.intervention_id.is_unique
    assert set(frame.dataset) == set(studies)
    assert frame.primary_eligible.all() and np.isfinite(frame.measured_delta.to_numpy(float)).all()
    rows = pd.read_csv(row_path, usecols=identity, low_memory=False)[identity]
    pd.testing.assert_frame_equal(frame[identity].reset_index(drop=True), rows.reset_index(drop=True))
    return frame.reset_index(drop=True)


def certified_core(common, manifest):
    """Follow the target -> foundation -> admission immutable SHA chain."""
    foundation = common.ROOT / FOUNDATION_NAME
    assert common.sha256(foundation) == manifest["files"][FOUNDATION_NAME]
    original = common.ROOT / AUTHOR_ADMISSION_NAME
    assert common.sha256(original) == common.readj(foundation)["files"][AUTHOR_ADMISSION_NAME]
    core = common.ROOT / CORE_NAME
    assert common.sha256(core) == common.readj(original)["files"][CORE_NAME]
    if CORE_NAME in manifest["files"]:
        assert common.sha256(core) == manifest["files"][CORE_NAME]
    return core, [foundation, original, core]


def run(mode):
    assert mode in replay.NAMESPACES
    common = importlib.import_module("src." + replay.NAMESPACES[mode] + ".common")
    manifest = common.freeze_check()
    for track in common.TRACKS:
        complete = common.readj(common.OUT / track / "run_complete.json")
        assert complete["status"] == "PASS" and complete["prefit_manifest_sha256"] == common.sha256(common.OUT / "prefit_manifest.json")
    core, chain = certified_core(common, manifest)
    if mode == "alignment":
        rows, identity = common.OUT / "row_index.csv.gz", common.ROW_COLUMNS
    else:
        rows, identity = common.NEXT_ART / "sequence_inventory.csv.gz" if mode == "rbp" else common.ART / "sequence_inventory.csv.gz", IDENTITY
    assert common.sha256(rows) == manifest["files"][rows.relative_to(common.ROOT).as_posix()]
    frame = read_admitted_frame(core, rows, identity, 26258, common.STUDIES)
    source = Path(__file__).resolve()
    original_save = common.jsave
    output_path = common.OUT / "canonical_source_only_replay.json"
    def save_distinct(path, receipt):
        if Path(path).name == "canonical_inner_replay.json":
            receipt = {**receipt, "loader_role": "ADDITIVE_EXPLICIT_ADMITTED_MEAN_EFFECT_COLUMNS",
                "loader_source_sha256": common.sha256(source), "core_sha256": common.sha256(core),
                "row_identity_sha256": common.sha256(rows),
                "mean_effect_float64_sha256": replay.hashlib.sha256(np.asarray(frame.measured_delta, dtype="<f8").tobytes()).hexdigest(),
                "admission_manifest_chain": {p.relative_to(common.ROOT).as_posix(): common.sha256(p) for p in chain},
                "replicate_evidence_opened": False, "historical_data_npz_loaded": False,
                "loader_changes": "Temporary process-local common.load override; no frozen file edit; original default pandas parser"}
            return original_save(output_path, receipt)
        return original_save(path, receipt)
    with patch.object(common, "load", return_value=frame), patch.object(common, "jsave", side_effect=save_distinct):
        replay.run(mode)
    assert output_path.exists()
    print(mode, "source-only canonical replay receipt", output_path, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=sorted(replay.NAMESPACES))
    run(parser.parse_args().mode)
