"""Pin outcome-free preparation inputs before any backend loading/conversion."""
from pathlib import Path
import json
import sys
from .resources import ROOT, ART, OUT, REP, MODEL, digest, jsave


def run():
    assert not (OUT / "backend_synthetic_receipt.json").exists()
    path = OUT / "backend_preparation_manifest.json"
    assert not path.exists(), "Preserve completed preparation freeze"
    tests = json.loads((OUT / "backend_preparation_tests_receipt_final.json").read_text())
    assert tests["status"] == "PASS"
    assert tests["backend_probe_sha256"] == digest(ROOT / "src/generalization_splicebert_20261007/backend_probe.py")
    assert tests["test_source_sha256"] == digest(ROOT / "src/generalization_splicebert_20261007/test_backend_preparation.py")
    for name in ("cpu_wheel_download_receipt.json", "cpu_runtime_extraction_receipt.json",
                 "dependency_runtime_receipt.json", "reused_runtime_receipt.json", "resource_audit.json"):
        assert json.loads((OUT / name).read_text())["status"] == "PASS"
    sources = ROOT / "src/generalization_splicebert_20261007"
    paths = sorted(sources.glob("*.py")) + sorted(REP.glob("*.md"))
    paths += sorted(member for member in OUT.glob("*.json") if member.is_file())
    paths += sorted(member for member in ART.glob("*") if member.is_file())
    paths += sorted((ART / "dependency_metadata").glob("*.json"))
    paths += sorted((ART / "wheels").glob("*.whl"))
    paths += sorted(member for member in MODEL.glob("*") if member.is_file())
    paths += [ROOT / "results/generalization_next_20261007/bert_runtime_integrity.json",
              ROOT / "artifacts/generalization_20261007/reporter_context_metadata.json"]
    jsave(path, {"status": "FROZEN_SYNTHETIC_BACKEND_PREPARATION_ONLY",
                "files": {member.relative_to(ROOT).as_posix(): digest(member) for member in sorted(set(paths))},
                "synthetic_alleles": 16, "project_alleles_authorized": 0, "outcomes_used": False,
                "models_fit": 0, "root_start_required": True, "minimum_free_RAM_bytes": 3 * 1024**3,
                "full_feature_production_authorized": False})
    print("Backend preparation freeze written; root commits before synthetic start", flush=True)


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
