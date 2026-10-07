"""Freeze only after source-array production/assembly PASS; no fitting."""
from .common import *


def run():
    from src.generalization_20261007.verify import preservation
    preservation(); source_arrays_check()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    assert not (OUT / "prefit_manifest.json").exists()
    assert readj(OUT / "input_receipt.json")["status"] == readj(OUT / "tests_receipt_final.json")["status"] == "PASS"
    tests = readj(OUT / "tests_receipt_final.json")
    for name, expected in tests["source_hashes"].items():
        assert sha256(SRC / name) == expected, name
    paths = [path for folder in (SRC, REP, OUT) for path in folder.glob("*") if path.is_file()]
    paths += [NEXT_ART / (track + "_model_features.npz") for track in TRACKS]
    paths += [CORE, NEXT_ART / "sequence_inventory.csv.gz", NEXT_ART / "encoded_sequence_inventory.csv.gz",
        NEXT_OUT / "feature_production_manifest.json", NEXT_OUT / "prepare_receipt.json", NEXT_OUT / "row_index.csv.gz",
        NEXT_OUT / "structure_cache_production_receipt.json", NEXT_OUT / "bert_features_receipt.json",
        NEXT_OUT / "assembly_integrity_receipt.json", NEXT_OUT / "short_feature_receipt.json",
        ROOT / "src/generalization_polarity_20261007/routes.py", ROOT / "reports/generalization_polarity_20261007/protocol.md",
        ROOT / "results/generalization_polarity_20261007/prefit_manifest.json", ROOT / "results/generalization_polarity_20261007/gate_verdict.json",
        ROOT / "src/generalization_next_20261007/bootstrap.py", ROOT / "src/generalization_next_20261007/routes.py",
        ROOT / "src/generalization_20261007/common.py", ROOT / "src/generalization_20261007/route_scaling.py",
        ROOT / "src/cross_assay_20260927/models.py", ROOT / "results/generalization_20261007/prefit_manifest.json",
        ROOT / "artifacts/cross_assay_20260927/model_comparison.csv", ROOT / "results/cross_assay_20260927/decision_metrics.csv"]
    jsave(OUT / "prefit_manifest.json", {"status":"FROZEN_PREFIT_ALIGNMENT_FOLLOWUP",
        "files":{path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(set(paths))},
        "tracks":TRACKS, "fits":240, "numerical_threads":1, "source_arrays_shared_with_unflipped":True,
        "observed_data_followup":True, "prior_polarity_NO_GO_retained":True,
        "no_alignment_fits_exist":True, "independent_confirmation":False, "root_start_required":True})
    print("Alignment prefit freeze written; commit before fitting", flush=True)


if __name__ == "__main__":
    run()
