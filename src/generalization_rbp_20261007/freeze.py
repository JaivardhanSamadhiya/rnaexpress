"""Separate committed certificates for RBP-only feature production and fits."""
from .common import *
import sys


def run(stage):
    assert stage in ("production", "prefit")
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    from src.generalization_20261007.verify import preservation
    from src.generalization_next_20261007.common import production_check as next_check
    preservation(); next_check()
    tests = readj(OUT / "tests_receipt_final.json")
    assert tests["status"] == "PASS"
    for name, checksum in tests["source_hashes"].items():
        assert sha256(SRC / name) == checksum, name
    assert readj(OUT / "projection_receipt.json")["status"] == "PASS"
    assert readj(ART / "direct_human_manifest.json")["unique_normalized_pfms"] == 421
    paths = sorted(path for folder in (SRC, REP) for path in folder.glob("*") if path.is_file())
    paths += sorted(path for path in ART.glob("*") if path.is_file())
    paths += sorted(path for path in OUT.glob("*") if path.is_file()
                    and path.name not in ("feature_production_manifest.json", "prefit_manifest.json"))
    paths += [NEXT_ART / name for name in ("sequence_inventory.csv.gz", "encoded_sequence_inventory.csv.gz", "base_features.npz")]
    paths += [NEXT_OUT / name for name in ("feature_production_manifest.json", "short_feature_receipt.json", "structure_config_v2.json")]
    paths += [ROOT / "src/generalization_next_20261007/structure_cache.py",
              ROOT / "src/generalization_next_20261007/route_structure.py",
              ROOT / "src/generalization_20261007/route_scaling.py",
              ROOT / "src/generalization_20261007/common.py",
              ROOT / "src/cross_assay_20260927/models.py",
              ROOT / "src/generalization_next_20261007/bootstrap.py",
              ROOT / "artifacts/generalization_20261007/reporter_context_metadata.json",
              ROOT / "results/generalization_20261007/prefit_manifest.json",
              ROOT / "artifacts/cross_assay_20260927/model_comparison.csv",
              ROOT / "results/cross_assay_20260927/decision_metrics.csv"]
    if stage == "production":
        assert not (OUT / "raw_production_receipt.json").exists()
        assert not (OUT / "access_production_receipt.json").exists()
        filename = "feature_production_manifest.json"
    else:
        production_check()
        assert readj(OUT / "prepare_receipt.json")["status"] == "PASS"
        assert readj(OUT / "raw_production_receipt.json")["status"] == "PASS"
        assert readj(OUT / "access_production_receipt.json")["status"] == "PASS"
        assert readj(NEXT_OUT / "structure_cache_production_receipt.json")["status"] == "PASS"
        paths += [OUT / "feature_production_manifest.json", NEXT_OUT / "structure_cache_production_receipt.json"]
        filename = "prefit_manifest.json"
    assert not (OUT / filename).exists(), "Preserve completed freeze"
    jsave(OUT / filename, {
        "status": "FROZEN_" + stage.upper(),
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        "no_comparative_fits_exist": True, "protected_outcomes_opened": False,
        "independent_confirmation": False, "raw_scoring_numerical_threads": 1,
        "tracks": TRACKS, "expected_fit_checkpoints": 120,
        "root_start_signal_required": True,
    })
    print("Separate RBP freeze written; commit before", stage, "execution", flush=True)


if __name__ == "__main__":
    run(sys.argv[1])
