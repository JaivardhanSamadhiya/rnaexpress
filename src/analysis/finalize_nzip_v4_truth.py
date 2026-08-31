"""Freeze the corrected N-zip truth tables without predictive analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.reconstruct_nzip_v4_truth import (
    DESIGN_OUT,
    COUNTS_OUT,
    RESULTS_DIR,
    stable_gzip_csv,
)
from src.pairing.reconstruct_nzip import load_tables


ROOT = Path(__file__).resolve().parents[2]
DESEQ_READ = ROOT / "data/processed/nzip_mutagenesis_deseq2_read_sensitivity_v1.csv.gz"
DESEQ_UMI = ROOT / "data/processed/nzip_mutagenesis_deseq2_umi_v1.csv.gz"
OUTCOMES_OUT = ROOT / "data/processed/nzip_mutagenesis_outcomes_v4_truth.csv.gz"
RECON_OUT = RESULTS_DIR / "nzip_6266_outcome_state_reconciliation.csv.gz"
CORRECTED_OUT = ROOT / "data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz"
EXCLUSIONS_OUT = RESULTS_DIR / "corrected_snv_exclusions.csv.gz"
HISTORICAL_MAP_OUT = RESULTS_DIR / "historical_to_corrected_snv_map.csv.gz"
RATIO_AUDIT_OUT = RESULTS_DIR / "localization_ratio_semantics_audit.json"
SUMMARY_OUT = RESULTS_DIR / "truth_reconstruction_summary.json"
HISTORICAL_PAIRS = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"


def _add_cpm_ratios(frame: pd.DataFrame, kind: str) -> pd.DataFrame:
    suffix = "read_count" if kind == "read" else "distinct_umi_count"
    coverage_column = "read_coverage_state" if kind == "read" else "coverage_state"
    eligible = frame[coverage_column].eq("coverage_pass")
    for replicate in (1, 2, 3):
        for compartment in ("neurite", "soma"):
            count = f"replicate{replicate}_{compartment}_{suffix}"
            cpm = f"replicate{replicate}_{compartment}_{kind}_cpm"
            # processTwist.R filters before calculating per-sample total-count
            # normalization factors.
            frame[cpm] = frame[count] * (1_000_000.0 / frame.loc[eligible, count].sum())
        frame[f"replicate{replicate}_{kind}_simple_log2ratio"] = np.log2(
            (frame[f"replicate{replicate}_neurite_{kind}_cpm"] + 0.5)
            / (frame[f"replicate{replicate}_soma_{kind}_cpm"] + 0.5)
        )
    ratio_columns = [f"replicate{replicate}_{kind}_simple_log2ratio" for replicate in (1, 2, 3)]
    frame[f"mean_replicate_{kind}_simple_log2ratio"] = frame[ratio_columns].mean(axis=1)
    neurite = frame[[f"replicate{x}_neurite_{kind}_cpm" for x in (1, 2, 3)]].mean(axis=1)
    soma = frame[[f"replicate{x}_soma_{kind}_cpm" for x in (1, 2, 3)]].mean(axis=1)
    frame[f"averaged_cpm_{kind}_log2ratio"] = np.log2((neurite + 0.5) / (soma + 0.5))
    return frame


def _add_exact_umi_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the predeclared exact-only sensitivity; never use it as primary truth."""

    coverage = frame["exact_umi_coverage_state_sensitivity"].eq("coverage_pass")
    ratios: list[str] = []
    for replicate in (1, 2, 3):
        cpm_names: dict[str, str] = {}
        for compartment in ("neurite", "soma"):
            count = f"replicate{replicate}_{compartment}_exact_distinct_umi_count"
            cpm = f"replicate{replicate}_{compartment}_exact_umi_cpm_sensitivity"
            frame[cpm] = frame[count] * (1_000_000.0 / frame.loc[coverage, count].sum())
            cpm_names[compartment] = cpm
        ratio = f"replicate{replicate}_exact_umi_simple_log2ratio_sensitivity"
        frame[ratio] = np.log2(
            (frame[cpm_names["neurite"]] + 0.5) / (frame[cpm_names["soma"]] + 0.5)
        )
        ratios.append(ratio)
    frame["mean_replicate_exact_umi_simple_log2ratio_sensitivity"] = frame[ratios].mean(axis=1)
    return frame


def _workbook_values(design: pd.DataFrame) -> pd.DataFrame:
    workbook_design, workbook_outcomes = load_tables()
    design_counts = workbook_design["_join_key"].value_counts()
    outcome_counts = workbook_outcomes["_join_key"].value_counts()
    unique_keys = set(design_counts[design_counts == 1].index) & set(
        outcome_counts[outcome_counts == 1].index
    )
    lookup = workbook_outcomes[workbook_outcomes["_join_key"].isin(unique_keys)].set_index(
        "_join_key"
    )
    keys = workbook_design.loc[design["source_data_row_0based"], "_join_key"].reset_index(drop=True)
    result = pd.DataFrame({"_join_key": keys})
    result["workbook_identity_state"] = np.where(
        result["_join_key"].isin(unique_keys), "unique", "ambiguous"
    )
    result["workbook_localization_ratio"] = result["_join_key"].map(
        lookup["Mean_log2ratio_NeuriteSoma_WT"]
    )
    result["workbook_padj"] = result["_join_key"].map(
        lookup["Mean_padj_NeuriteSoma_WT"]
    )
    return result.drop(columns="_join_key")


def _agreement(observed: pd.Series, reconstructed: pd.Series) -> dict[str, float | int]:
    valid = observed.notna() & reconstructed.notna() & np.isfinite(reconstructed)
    left = observed[valid].astype(float)
    right = reconstructed[valid].astype(float)
    error = right - left
    return {
        "n": int(valid.sum()),
        "pearson_r": float(left.corr(right, method="pearson")),
        "spearman_r": float(left.corr(right, method="spearman")),
        "mean_absolute_error": float(error.abs().mean()),
        "root_mean_squared_error": float(np.sqrt(np.mean(error**2))),
        "maximum_absolute_error": float(error.abs().max()),
    }


def build_outcomes() -> tuple[pd.DataFrame, dict[str, object]]:
    design = pd.read_csv(DESIGN_OUT)
    counts = pd.read_csv(COUNTS_OUT)
    read = pd.read_csv(DESEQ_READ).add_prefix("read_deseq_")
    umi = pd.read_csv(DESEQ_UMI).add_prefix("umi_deseq_")
    outcomes = counts.merge(
        read, left_on="sequence_id", right_on="read_deseq_sequence_id", validate="one_to_one"
    ).merge(umi, left_on="sequence_id", right_on="umi_deseq_sequence_id", validate="one_to_one")
    outcomes = _add_cpm_ratios(outcomes, "read")
    outcomes = _add_cpm_ratios(outcomes, "umi")
    outcomes = _add_exact_umi_sensitivity(outcomes)
    stable_gzip_csv(outcomes, OUTCOMES_OUT)

    expanded = design.merge(
        outcomes.drop(columns=["sequence_sha256", "normalized_sequence"]),
        on="sequence_id", validate="many_to_one",
    )
    expanded = pd.concat([expanded.reset_index(drop=True), _workbook_values(design)], axis=1)
    candidates = {
        "read_deseq2_log2FoldChange": expanded["read_deseq_log2FoldChange"],
        "umi_deseq2_log2FoldChange": expanded["umi_deseq_log2FoldChange"],
        "mean_replicate_read_simple_ratio": expanded["mean_replicate_read_simple_log2ratio"],
        "averaged_read_cpm_ratio": expanded["averaged_cpm_read_log2ratio"],
        "mean_replicate_umi_simple_ratio": expanded["mean_replicate_umi_simple_log2ratio"],
        "averaged_umi_cpm_ratio": expanded["averaged_cpm_umi_log2ratio"],
        "exact_only_mean_replicate_umi_ratio_rejected_sensitivity": expanded[
            "mean_replicate_exact_umi_simple_log2ratio_sensitivity"
        ],
    }
    finite_workbook = expanded["workbook_localization_ratio"].notna() & expanded[
        "workbook_padj"
    ].notna()
    agreement = {
        name: _agreement(
            expanded.loc[finite_workbook, "workbook_localization_ratio"],
            values.loc[finite_workbook],
        )
        for name, values in candidates.items()
    }
    best = min(agreement, key=lambda name: agreement[name]["mean_absolute_error"])
    audit: dict[str, object] = {
        "comparison_scope": "unique workbook identities with finite workbook ratio and padj",
        "candidate_agreement": agreement,
        "closest_numeric_semantics": best,
        "primary_truth_outcome": "mean_replicate_umi_simple_ratio",
        "primary_reason": (
            "the workbook column is labelled Mean_log2ratio and independently matches the "
            "source-defined UMI CPM replicate-ratio calculation best; DESeq2 statistics remain "
            "a separate inferential layer"
        ),
        "rejected_sensitivity_reason": (
            "exact-only matching produced 5,670 design-level coverage passes, not 5,679, "
            "and worsened global agreement; it is retained only to demonstrate that the "
            "publication count was not reverse-engineered"
        ),
    }
    RATIO_AUDIT_OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return expanded, audit


def finalize() -> dict[str, object]:
    expanded, ratio_audit = build_outcomes()
    representative = expanded.groupby("sequence_id")["design_row_id"].transform("min")
    duplicate_secondary = (expanded["number_design_ids_sharing_sequence"] > 1) & (
        expanded["design_row_id"] != representative
    )
    cflar_quarantine = expanded["source_gene_name"].eq("Cflar_2")
    quantitative = (
        expanded["coverage_state"].eq("coverage_pass")
        & np.isfinite(expanded["mean_replicate_umi_simple_log2ratio"])
        & ~cflar_quarantine
    )
    expanded["primary_localization_log2ratio"] = np.where(
        quantitative, expanded["mean_replicate_umi_simple_log2ratio"], np.nan
    )
    expanded["outcome_state"] = np.select(
        [
            duplicate_secondary,
            cflar_quarantine,
            expanded["coverage_state"].eq("coverage_fail"),
            ~np.isfinite(expanded["umi_deseq_log2FoldChange"]),
        ],
        ["duplicate_sequence_collapsed", "sequence_ambiguous", "coverage_filtered", "deseq_unresolved"],
        default="measured_valid",
    )
    expanded["quantitative_valid"] = quantitative
    expanded["state_reason"] = np.select(
        [
            duplicate_secondary,
            cflar_quarantine,
            expanded["coverage_state"].eq("coverage_fail"),
            ~np.isfinite(expanded["umi_deseq_log2FoldChange"]),
        ],
        [
            "exact sequence shares one measurement; secondary design ID is not independent",
            "Cflar_2 outcome identities cannot be assigned uniquely to source tiles 107 and 52",
            "fewer than three of six samples have at least 20 distinct mapped UMIs",
            "coverage passed but the replicate-aware DESeq2 effect is not finite",
        ],
        default="coverage-valid canonical sequence with finite source-defined UMI localization ratio",
    )
    stable_gzip_csv(expanded, RECON_OUT)

    sequence = expanded.drop_duplicates("sequence_id").set_index("sequence_id")
    snv = expanded[expanded["exact_snv"]].copy()
    snv["parent_id"] = snv[["source_gene_id", "source_gene_name", "source_tile_id"]].astype(str).agg(
        "|".join, axis=1
    )
    snv["mutant_status"] = snv["sequence_id"].map(sequence["outcome_state"])
    snv["parent_status"] = snv["intended_parent_sequence_id"].map(sequence["outcome_state"])
    snv["mutant_outcome"] = snv["sequence_id"].map(sequence["primary_localization_log2ratio"])
    snv["parent_outcome"] = snv["intended_parent_sequence_id"].map(
        sequence["primary_localization_log2ratio"]
    )
    snv["cflar_identity_quarantine"] = snv["source_gene_name"].eq("Cflar_2")
    snv["outcome_valid"] = (
        snv["sequence_id"].map(sequence["quantitative_valid"]).fillna(False)
        & snv["intended_parent_sequence_id"].map(sequence["quantitative_valid"]).fillna(False)
        & ~snv["cflar_identity_quarantine"]
    )
    snv["corrected_delta"] = np.where(
        snv["outcome_valid"], snv["mutant_outcome"] - snv["parent_outcome"], np.nan
    )
    snv["exclusion_reason"] = np.select(
        [
            snv["cflar_identity_quarantine"],
            ~snv["sequence_id"].map(sequence["quantitative_valid"]).fillna(False),
            ~snv["intended_parent_sequence_id"].map(sequence["quantitative_valid"]).fillna(False),
        ],
        [
            "Cflar_2 workbook identity is ambiguous across tiles 107 and 52",
            "mutant outcome is not coverage-valid and finite",
            "WT parent outcome is not coverage-valid and finite",
        ],
        default="",
    )
    corrected = snv[snv["outcome_valid"]].copy()
    stable_gzip_csv(corrected, CORRECTED_OUT)
    stable_gzip_csv(snv[~snv["outcome_valid"]], EXCLUSIONS_OUT)

    historical = pd.read_csv(HISTORICAL_PAIRS)
    map_columns = [
        "source_data_row_0based", "mutant_status", "parent_status", "mutant_outcome",
        "parent_outcome", "corrected_delta", "outcome_valid", "exclusion_reason",
    ]
    mapping = historical.merge(
        snv[map_columns], left_on="source_row", right_on="source_data_row_0based",
        how="left", validate="one_to_one",
    )
    mapping = mapping.rename(
        columns={
            "mutant_localization_log2_neurite_soma": "historical_mutant_outcome",
            "parent_localization_log2_neurite_soma": "historical_parent_outcome",
            "delta_localization": "historical_delta",
        }
    )
    mapping["absolute_delta_change"] = (
        mapping["corrected_delta"] - mapping["historical_delta"]
    ).abs()
    stable_gzip_csv(mapping, HISTORICAL_MAP_OUT)

    parent_status = snv.groupby("parent_id", sort=True).agg(
        candidate_snvs=("design_row_id", "size"), valid_snvs=("outcome_valid", "sum")
    )
    retained_parents = int((parent_status["valid_snvs"] > 0).sum())
    states = {str(k): int(v) for k, v in expanded["outcome_state"].value_counts().items()}
    workbook_zero = (expanded["workbook_localization_ratio"] == 0) & expanded["workbook_padj"].isna()
    zero_coverage = pd.crosstab(workbook_zero, expanded["coverage_state"]).to_dict()
    finite_source = mapping["parent_localization_padj"].notna() & mapping[
        "mutant_localization_padj"
    ].notna() & mapping["outcome_valid"].fillna(False)
    finite_errors = mapping.loc[finite_source, "absolute_delta_change"]
    summary: dict[str, object] = {
        "design_rows": len(expanded),
        "canonical_sequences": int(expanded["sequence_id"].nunique()),
        "state_counts": states,
        "design_coverage_pass": int(expanded["coverage_state"].eq("coverage_pass").sum()),
        "design_coverage_fail": int(expanded["coverage_state"].eq("coverage_fail").sum()),
        "workbook_zero_missing_padj": int(workbook_zero.sum()),
        "workbook_zero_by_reconstructed_coverage": zero_coverage,
        "corrected_valid_snvs": len(corrected),
        "excluded_snvs": int((~snv["outcome_valid"]).sum()),
        "retained_parents": retained_parents,
        "candidate_parents": int(len(parent_status)),
        "map2_valid_snvs": int(parent_status.loc[parent_status.index.str.contains(r"\|Map2\|"), "valid_snvs"].sum()),
        "cox5b_valid_snvs": int(parent_status.loc[parent_status.index.str.contains(r"\|Cox5b\|"), "valid_snvs"].sum()),
        "historical_rows_mapped": int(mapping["source_data_row_0based"].notna().sum()),
        "historical_rows_removed": int((~mapping["outcome_valid"].fillna(False)).sum()),
        "historical_numeric_delta_changes_gt_1e_6": int((mapping["absolute_delta_change"] > 1e-6).sum()),
        "historical_numeric_delta_changes_gt_0_05": int((mapping["absolute_delta_change"] > 0.05).sum()),
        "finite_source_valid_delta_comparison_n": int(finite_source.sum()),
        "finite_source_valid_delta_mae": float(finite_errors.mean()),
        "finite_source_valid_delta_max_abs": float(finite_errors.max()),
        "ratio_semantics": ratio_audit,
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(finalize(), indent=2))
