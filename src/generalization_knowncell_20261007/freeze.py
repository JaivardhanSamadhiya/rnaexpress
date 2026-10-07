"""Pin completed old predictors and prospective protocol before new evaluation."""
from .common import *


def run():
    from src.generalization_crosscell_20261007.common import freeze_check as source_freeze
    source_freeze()
    assert not (OUT / "evaluation_manifest.json").exists()
    assert not (OUT / "evaluation_complete.json").exists()
    assert readj(OUT / "metadata_receipt.json")["status"] == "PASS"
    tests = readj(OUT / "tests_receipt_reviewed_final.json"); assert tests["status"] == "PASS"
    for name, expected in tests["source_hashes"].items(): assert sha256(SRC / name) == expected, name
    source_check = readj(SOURCE_OUT / "verification_receipt.json")
    assert source_check["status"] == "PASS"
    assert source_check["inner_models_replayed"] == 252 and source_check["outer_models_replayed"] == 42
    assert source_check["source_only_selection_checked"] and source_check["gene_and_exact_allele_exclusions_checked"]
    paths = [p for directory in (SRC, REP, OUT) for p in directory.glob("*") if p.is_file()]
    paths += [CORE, SOURCE_OUT / "prefit_manifest.json", SOURCE_OUT / "verification_receipt.json",
        ROOT / "results/generalization_20261007/prefit_manifest.json",
        ROOT / "src/generalization_crosscell_20261007/common.py", ROOT / "src/generalization_crosscell_20261007/engine.py",
        ROOT / "src/generalization_crosscell_20261007/verify.py", ROOT / "src/generalization_crosscell_20261007/splits.py",
        ROOT / "src/generalization_crosscell_20261007/routes.py", ROOT / "src/generalization_crosscell_20261007/bootstrap.py",
        ROOT / "src/generalization_20261007/route_scaling.py", ROOT / "src/generalization_20261007/common.py",
        ROOT / "src/generalization_rbp_20261007/canonical_inner_replay.py",
        ROOT / "src/generalization_rbp_20261007/inner_replay.py", ROOT / "src/research_20260921/common.py"]
    for track in TRACKS:
        complete = readj(SOURCE_OUT / track / "run_complete.json")
        assert complete["status"] == "PASS" and complete["fit_files"] == 42
        assert complete["prefit_manifest_sha256"] == sha256(SOURCE_OUT / "prefit_manifest.json")
        paths += [SOURCE_ART / (track + "_model_features.npz")]
        paths += [p for p in (SOURCE_OUT / track).rglob("*") if p.is_file()]
    jsave(OUT / "evaluation_manifest.json", {"status": "FROZEN_EVALUATION_KNOWN_CELL",
        "files": {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(set(paths))},
        "new_fits": 0, "old_outer_predictors_reused": 42, "target_prediction_analysis_started": False,
        "configurations": "Unchanged source-only OOF choices in original crosscell folds",
        "numerical_threads": 1, "independent_confirmation": False,
        "post_fit_pin_scope": "Pins observed old checkpoint bytes; no retroactive creation-time certificate",
        "root_commits_before_evaluation": True})
    print("Known-cell evaluation freeze written; root commits before new target scoring", flush=True)


if __name__ == "__main__": run()
