"""Build the final RNAddress v4 Phase B reproducibility manifest."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_embeddings import sha256


OUT = ROOT / "results/v4_phaseB"
INTERIM = ROOT / "data/interim"


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    rows = pd.read_csv(OUT / "model_candidate_rows.csv.gz")
    splits = (
        rows.groupby(["dataset", "biological_unit", "biological_fold"])
        .agg(
            decision_sets=("decision_set_id", "nunique"),
            candidate_rows=("candidate_id", "size"),
            parent_ids=("parent_id", "nunique"),
            gene_ids=("gene_id", "nunique"),
        )
        .reset_index()
    )
    splits.to_csv(OUT / "biological_split_manifest.csv", index=False)
    protected_loader = ROOT / "src/pairing/audit_astrocyte.py"
    data_inputs = [
        ROOT / "results/v4_phaseA/source_manifest.json",
        ROOT / "results/v4_phaseA/common_intervention_outcomes.csv.gz",
        OUT / "decision_set_manifest.json",
        OUT / "phaseB_candidates.csv.gz",
        OUT / "representation_benchmark_summary.json",
        OUT / "model_interventions.csv.gz",
    ]
    representation_caches = [
        INTERIM / "v4_phaseB_3utrbert_benchmark_features.npy",
        INTERIM / "v4_phaseB_splicebert_benchmark_features.npy",
        INTERIM / "v4_phaseB_3utrbert_full_features.npy",
    ]
    code = sorted(
        [
            *ROOT.glob("src/analysis/*v4_phaseB*.py"),
            *ROOT.glob("src/modeling/v4_*.py"),
            ROOT / "tests/test_v4_phaseB.py",
        ]
    )
    output_files = sorted(
        path
        for path in OUT.iterdir()
        if path.is_file() and path.name != "phaseB_reproducibility_manifest.json"
    )
    packages = [
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "torch",
        "transformers",
        "openvino",
    ]
    manifest = {
        "phase": "RNAddress v4 Phase B",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                package: importlib.metadata.version(package) for package in packages
            },
        },
        "data_inputs": [file_record(path) for path in data_inputs],
        "representation_caches": [file_record(path) for path in representation_caches],
        "code": [file_record(path) for path in code],
        "outputs": [file_record(path) for path in output_files],
        "protected_astrocyte_loader": file_record(protected_loader),
        "scope_guards": {
            "nzip_outcomes_used": False,
            "astrocyte_outcomes_opened": False,
            "astrocyte_predictions_generated": False,
        },
    }
    (OUT / "phaseB_reproducibility_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"outputs": len(output_files), "code": len(code)}, indent=2))


if __name__ == "__main__":
    main()
