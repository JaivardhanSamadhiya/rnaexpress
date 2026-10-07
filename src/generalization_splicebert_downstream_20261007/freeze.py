"""Separate post-production prefit freeze; does not start any fits."""
from .common import *
from .assemble import source_controls
from .producer import backend_check


def run():
    production_check(); backend_check(); source_controls(); receipt = input_check()
    assert not (OUT / "prefit_manifest.json").exists()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    tests = readj(OUT / "synthetic_tests_receipt_final_review.json")
    assert tests["status"] == "PASS" and tests["models_fit"] == 0
    for name, expected in tests["source_hashes"].items():
        assert sha256(SRC / name) == expected, name
    required = {"engine.py", "gate.py", "verify.py", "freeze.py", "routes.py", "producer.py", "assemble.py", "common.py", "prepare.py", "tests.py", "__init__.py"}
    assert required == set(tests["source_hashes"])
    frame = load()
    assert metadata_identity(frame) == receipt["original_metadata_identity_sha256"]
    paths = [path for folder in (SRC, REP, OUT) for path in folder.glob("*") if path.is_file()]
    paths += [ROOT / name for name in receipt["files"]]
    paths += [CORE, NEXT_ART / "sequence_inventory.csv.gz", NEXT_ART / "encoded_sequence_inventory.csv.gz",
        NEXT_OUT / "feature_production_manifest.json", NEXT_OUT / "prefit_manifest.json", NEXT_OUT / "short_feature_receipt.json", NEXT_OUT / "prepare_receipt.json",
        NEXT_OUT / "structure_cache_production_receipt.json", NEXT_OUT / "bert_features_receipt.json", NEXT_OUT / "assembly_integrity_receipt.json",
        NEXT_OUT / "structure_postproduction_audit_receipt.json", NEXT_ART / "structure_postproduction_sha256_index.json",
        ROOT / "src/generalization_next_20261007/bootstrap.py", ROOT / "src/generalization_20261007/common.py",
        ROOT / "src/generalization_20261007/route_scaling.py", ROOT / "src/cross_assay_20260927/models.py",
        ROOT / "src/cross_assay_20260927/common.py", ROOT / "results/generalization_20261007/prefit_manifest.json",
        ROOT / "artifacts/cross_assay_20260927/model_comparison.csv", ROOT / "results/cross_assay_20260927/decision_metrics.csv"]
    paths += [ROOT / name for name in readj(OUT / "feature_production_manifest.json")["files"]]
    producer_receipt = readj(OUT / "features_receipt.json")
    paths += [ART / "splicebert_features.npz", ART / "lookup_features.npz", ART / "compact_cache/index.json"]
    for shard in producer_receipt["compact_shards"]:
        paths += [ROOT / shard["path"], ROOT / shard["sidecar_path"]]
    jsave(OUT / "prefit_manifest.json", {"status": "FROZEN_PREFIT_SPLICEBERT_FOLLOWUP",
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        "tracks": TRACKS, "shapes": SHAPES, "fits_per_track": 40, "primary_fit_checkpoints": 240,
        "original_labels_sha256": label_hash(frame.measured_delta), "original_metadata_identity_sha256": metadata_identity(frame),
        "control_fitting_policy": "STANDALONE_ALL_SIX_NO_CHECKPOINT_REUSE",
        "control_rationale": "Old checkpoint metadata does not independently certify all parsed label/feature bytes and numerical thread identity; replicate matched controls under the same frozen parser and do not count them as independent evidence",
        "source_only_three_penalties": [.005, .05, .5], "numerical_threads": 1,
        "checkpoint_creation_SHA_sidecars_required": True, "all_inner_and_outer_replay_required": True,
        "no_fits_exist": True, "independent_confirmation": False, "observed_data_followup": True, "SRLE46nt_OOD": True,
        "new_encoder_GO_tracks_only": ["splicebert", "combined"], "root_commits_before_fitting": True})
    print("SpliceBERT separate prefit freeze written; root commits before engine", flush=True)


if __name__ == "__main__":
    run()
