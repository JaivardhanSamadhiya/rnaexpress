"""Write the immutable v3.5R N-zip audit/partial-reconstruction manifest."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import pandas as pd

from src.analysis.reconstruct_nzip_v4_truth import ROOT, sha256_file


OUT = ROOT / "data/frozen/nzip_v4_truth_manifest.json"


def _entry(relative: str) -> dict[str, object]:
    path = ROOT / relative
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_manifest() -> dict[str, object]:
    acquisition = json.loads(
        (ROOT / "results/v3_5r/source_acquisition_manifest.json").read_text(encoding="utf-8")
    )
    summary = json.loads(
        (ROOT / "results/v3_5r/truth_reconstruction_summary.json").read_text(encoding="utf-8")
    )
    raw_audit = json.loads(
        (ROOT / "results/v3_5r/raw_count_audit.json").read_text(encoding="utf-8")
    )
    corrected = pd.read_csv(
        ROOT / "data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz"
    )
    replicate_columns = [
        column
        for column in pd.read_csv(
            ROOT / "data/processed/nzip_mutagenesis_raw_counts_v1.csv.gz", nrows=1
        ).columns
        if column.startswith("replicate")
    ]

    artifact_paths = [
        "data/processed/nzip_mutagenesis_design_v1.csv.gz",
        "data/processed/nzip_mutagenesis_raw_counts_v1.csv.gz",
        "data/processed/nzip_mutagenesis_outcomes_v4_truth.csv.gz",
        "data/processed/nzip_mutagenesis_deseq2_umi_v1.csv.gz",
        "data/processed/nzip_mutagenesis_deseq2_read_sensitivity_v1.csv.gz",
        "data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz",
        "results/v3_5r/nzip_6266_outcome_state_reconciliation.csv.gz",
        "results/v3_5r/corrected_snv_exclusions.csv.gz",
        "results/v3_5r/historical_to_corrected_snv_map.csv.gz",
        "results/v3_5r/sequence_identity_groups.csv",
        "results/v3_5r/raw_count_audit.json",
        "results/v3_5r/localization_ratio_semantics_audit.json",
        "results/v3_5r/truth_reconstruction_summary.json",
        "results/v3_5r/source_acquisition_manifest.json",
        "results/v3_5r/author_independent_slice_concordance.json",
    ]
    script_paths = [
        "src/analysis/reconstruct_nzip_v4_truth.py",
        "src/analysis/nzip_fast_counter.cpp",
        "src/analysis/reconstruct_nzip_deseq2.R",
        "src/analysis/finalize_nzip_v4_truth.py",
        "src/analysis/freeze_nzip_v4_truth.py",
        "tests/test_nzip_v4_truth.py",
    ]

    manifest: dict[str, object] = {
        "schema": "rnaddress.nzip_v4_truth_manifest.v1",
        "frozen_date": "2026-08-30",
        "decision": "NO-GO — N-ZIP CANNOT BE RECOVERED RELIABLY FROM PUBLIC HISTORICAL MATERIALS",
        "dataset_status": "deterministic partial reconstruction; not a validated development benchmark",
        "phase_3_5_may_resume": False,
        "no_model_training_or_evaluation_performed": True,
        "source": {
            "publication_doi": "10.1038/s41593-022-01243-x",
            "pmcid": "PMC9991926",
            "experiment": "E-MTAB-10902",
            "ena_study": "ERP133202",
            "workbook_sha256": "15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9",
            "mprna_git_commit": "0e7118f1d4880884e6e99e4ba48a26d67f00338a",
            "mprna_processTwist": _entry("data/raw/nzip/MPRNA_v3_5/processTwist.R"),
            "mprna_compbio_jar": _entry("data/raw/nzip/MPRNA_v3_5/jar/compbio.jar"),
            "fastqs": acquisition["runs"],
        },
        "counts": {
            "design_rows": summary["design_rows"],
            "canonical_sequences": summary["canonical_sequences"],
            "reconstructed_umi_coverage_pass_design_rows": summary["design_coverage_pass"],
            "reconstructed_umi_coverage_fail_design_rows": summary["design_coverage_fail"],
            "publication_reported_pass_design_rows": 5_679,
            "unresolved_aggregate_pass_difference": raw_audit["publication_pass_count_difference"],
            "exact_only_rejected_sensitivity_pass": raw_audit[
                "exact_only_design_level_pass_rejected_sensitivity"
            ],
            "workbook_zero_missing_padj_rows": summary["workbook_zero_missing_padj"],
            "partial_valid_exact_snvs": summary["corrected_valid_snvs"],
            "excluded_exact_snvs": summary["excluded_snvs"],
            "retained_parents": summary["retained_parents"],
            "excluded_or_quarantined_parents": summary["candidate_parents"]
            - summary["retained_parents"],
            "historical_rows_removed": summary["historical_rows_removed"],
            "state_counts": summary["state_counts"],
        },
        "partial_cohort_parent_ids": sorted(corrected["parent_id"].unique().tolist()),
        "replicate_columns": replicate_columns,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "r": "4.5.1",
            "deseq2": "1.48.1",
            "deseq2_session_info": [
                "data/processed/nzip_mutagenesis_deseq2_umi_v1.csv.gz.sessionInfo.txt",
                "data/processed/nzip_mutagenesis_deseq2_read_sensitivity_v1.csv.gz.sessionInfo.txt",
            ],
        },
        "unresolved_state_definitions": {
            "coverage_filtered": "fewer than three samples have at least 20 distinct mapped UMIs",
            "sequence_ambiguous": "Cflar_2 workbook identity cannot be assigned safely between source tiles",
            "duplicate_sequence_collapsed": "secondary design ID shares one physical sequence measurement",
            "publication_coverage_identity_unresolved": (
                "public raw data/current source counter yield 5,787 passes versus reported 5,679; "
                "the 108 historical identities cannot be inferred without tuning"
            ),
            "finite_value_reproduction_failed": (
                "published finite values and deltas exceed prospectively frozen agreement tolerances"
            ),
        },
        "artifacts": [_entry(path) for path in artifact_paths],
        "processing": [_entry(path) for path in script_paths],
        "protected_boundaries": {
            "astrocyte_outcomes_inspected": False,
            "moffatt_archive_listed_opened_or_extracted": False,
            "historical_nzip_pairs_sha256": "0a9bd52f089694f6431ae9cb44782499f2249913ac17781b38052cf3a0319a10",
            "astrocyte_loader_sha256": "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78",
            "moffatt_guard_sha256": "b6a22b19f71a3800043fdbab29decf6fdfccb5ec0d0e9edeaa23617a577c4bb3",
        },
    }
    return manifest


def main() -> None:
    manifest = build_manifest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(OUT), "sha256": sha256_file(OUT)}, indent=2))


if __name__ == "__main__":
    main()
