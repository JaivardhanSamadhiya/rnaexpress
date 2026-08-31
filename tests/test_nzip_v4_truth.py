"""Truth-layer invariants for the corrected N-zip reconstruction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/processed/nzip_mutagenesis_design_v1.csv.gz"
COUNTS = ROOT / "data/processed/nzip_mutagenesis_raw_counts_v1.csv.gz"
OUTCOMES = ROOT / "data/processed/nzip_mutagenesis_outcomes_v4_truth.csv.gz"
RECON = ROOT / "results/v3_5r/nzip_6266_outcome_state_reconciliation.csv.gz"
CORRECTED = ROOT / "data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz"
HISTORY_MAP = ROOT / "results/v3_5r/historical_to_corrected_snv_map.csv.gz"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_unresolved_outcomes_are_not_numeric_zero() -> None:
    table = pd.read_csv(RECON)
    invalid = ~table["quantitative_valid"]
    assert table.loc[invalid, "primary_localization_log2ratio"].isna().all()


def test_missing_deseq_results_remain_na() -> None:
    table = pd.read_csv(OUTCOMES)
    excluded = ~table["umi_deseq_deseq_included"]
    assert table.loc[excluded, "umi_deseq_log2FoldChange"].isna().all()
    assert table.loc[excluded, "umi_deseq_padj"].isna().all()


def test_invalid_wt_prevents_delta_generation() -> None:
    table = pd.read_csv(HISTORY_MAP)
    invalid = table["parent_status"].ne("measured_valid")
    assert table.loc[invalid, "corrected_delta"].isna().all()


def test_invalid_mutant_prevents_delta_generation() -> None:
    table = pd.read_csv(HISTORY_MAP)
    invalid = table["mutant_status"].ne("measured_valid")
    assert table.loc[invalid, "corrected_delta"].isna().all()


def test_duplicate_sequences_are_not_independent_measurements() -> None:
    table = pd.read_csv(RECON)
    duplicates = table[table["number_design_ids_sharing_sequence"] > 1]
    assert duplicates["sequence_id"].nunique() * 2 == len(duplicates)
    assert (duplicates.groupby("sequence_id")["outcome_state"].apply(
        lambda values: (values == "duplicate_sequence_collapsed").sum()
    ) == 1).all()


def test_sequence_mapping_is_deterministic() -> None:
    design = pd.read_csv(DESIGN)
    expected = design["normalized_sequence"].map(
        lambda value: "nzipseq_" + hashlib.sha256(value.encode("ascii")).hexdigest()
    )
    assert expected.equals(design["sequence_id"])


def test_all_exact_snvs_have_one_difference() -> None:
    corrected = pd.read_csv(CORRECTED)
    differences = [
        sum(left != right for left, right in zip(parent, mutant))
        for parent, mutant in zip(corrected["intended_parent_sequence"], corrected["normalized_sequence"])
    ]
    assert set(differences) == {1}


def test_parent_reference_allele_matches() -> None:
    corrected = pd.read_csv(CORRECTED)
    observed = [
        sequence[int(position)]
        for sequence, position in zip(
            corrected["intended_parent_sequence"], corrected["edit_position_0based"]
        )
    ]
    assert observed == corrected["reference_nt"].tolist()


def test_ambiguous_cflar2_does_not_reenter() -> None:
    corrected = pd.read_csv(CORRECTED)
    assert not corrected["source_gene_name"].eq("Cflar_2").any()


def test_coverage_filter_is_deterministic() -> None:
    counts = pd.read_csv(COUNTS)
    columns = [
        column for column in counts
        if column.endswith("_distinct_umi_count") and "_exact_" not in column
    ]
    samples = counts[columns].ge(20).sum(axis=1)
    expected = np.where(samples >= 3, "coverage_pass", "coverage_fail")
    assert np.array_equal(samples, counts["samples_with_at_least_20_umis"])
    assert np.array_equal(expected, counts["coverage_state"])


def test_raw_count_reconstruction_matches_run_audit() -> None:
    counts = pd.read_csv(COUNTS)
    audit = json.loads((ROOT / "results/v3_5r/raw_count_audit.json").read_text())
    run_map = {
        "ERR7337821": "replicate1_neurite_read_count",
        "ERR7337822": "replicate2_neurite_read_count",
        "ERR7337823": "replicate3_neurite_read_count",
        "ERR7337824": "replicate1_soma_read_count",
        "ERR7337825": "replicate2_soma_read_count",
        "ERR7337826": "replicate3_soma_read_count",
    }
    for run, column in run_map.items():
        assert int(counts[column].sum()) == audit["runs"][run]["uniquely_mapped_reads"]


def test_ratio_calculation_matches_source_logic() -> None:
    table = pd.read_csv(OUTCOMES)
    expected = np.log2(
        (table["replicate1_neurite_umi_cpm"] + 0.5)
        / (table["replicate1_soma_umi_cpm"] + 0.5)
    )
    assert np.allclose(expected, table["replicate1_umi_simple_log2ratio"], rtol=0, atol=1e-12)


def test_historical_nzip_files_are_unchanged() -> None:
    assert _sha256(ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz") == (
        "0a9bd52f089694f6431ae9cb44782499f2249913ac17781b38052cf3a0319a10"
    )
    assert _sha256(ROOT / "data/processed/nzip_pairing_audit.json") == (
        "b92bfc3972195bc73f12781291d121c7bb6bfa61b51d1410f01a133efb121046"
    )


def test_astrocyte_loader_protection_is_unchanged() -> None:
    assert _sha256(ROOT / "src/pairing/audit_astrocyte.py") == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )


def test_moffatt_archive_guard_is_unchanged() -> None:
    assert _sha256(ROOT / "src/pairing/audit_moffatt_candidate.py") == (
        "b6a22b19f71a3800043fdbab29decf6fdfccb5ec0d0e9edeaa23617a577c4bb3"
    )
