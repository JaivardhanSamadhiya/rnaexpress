"""Reproduce the Phase 3.5 N-zip zero/missingness integrity incident."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.pairing.reconstruct_nzip import load_tables


ROOT = Path(__file__).resolve().parents[2]
PAIRS = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
V2 = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
V3 = ROOT / "results/v3_phase3/best_ablation_extreme_predictions.csv.gz"
FORWARD = ROOT / "results/v3_phase3/forward_outer_predictions.csv.gz"
SDRF = ROOT / "data/raw/nzip/E-MTAB-10902.sdrf.txt"
OUT = ROOT / "results/v3_5/historical_outcome_integrity_incident.json"


def _selected_bad(
    frame: pd.DataFrame,
    increase: np.ndarray,
    decrease: np.ndarray,
) -> int:
    count = 0
    for _, indices in frame.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        count += int(frame.iloc[indices[np.argmax(increase[indices])]]["unresolved"])
        count += int(frame.iloc[indices[np.argmax(decrease[indices])]]["unresolved"])
    return count


def main() -> None:
    _, outcomes = load_tables()
    ratio = outcomes["Mean_log2ratio_NeuriteSoma_WT"]
    padj = outcomes["Mean_padj_NeuriteSoma_WT"]
    pairs = pd.read_csv(PAIRS)
    pairs["mutant_unresolved"] = pairs["mutant_localization_padj"].isna()
    pairs["parent_unresolved"] = pairs["parent_localization_padj"].isna()
    pairs["unresolved"] = pairs["mutant_unresolved"] | pairs["parent_unresolved"]

    v2 = pd.read_csv(V2)
    if not np.array_equal(v2["source_row"].to_numpy(), pairs["source_row"].to_numpy()):
        raise ValueError("Historical prediction rows do not align with reconstructed pairs")
    v3 = pd.read_csv(V3).set_index("source_row").loc[pairs["source_row"]]
    forward = pd.read_csv(FORWARD).set_index("source_row").loc[pairs["source_row"]]
    oracle_mutant_unresolved = 0
    oracle_parent_unresolved = 0
    for _, indices in pairs.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        values = pairs.iloc[indices]["delta_localization"].to_numpy(float)
        for sign in (1.0, -1.0):
            oracle = pairs.iloc[indices[np.argmax(sign * values)]]
            oracle_mutant_unresolved += int(oracle["mutant_unresolved"])
            oracle_parent_unresolved += int(oracle["parent_unresolved"])

    sdrf = pd.read_csv(SDRF, sep="\t")
    raw_runs = sorted(
        sdrf.loc[
            sdrf["Source Name"].str.contains(
                "Nzip-mutation-reporter_WT", case=False, regex=False
            ),
            "Comment[ENA_RUN]",
        ].unique()
    )
    result = {
        "phase": "v3_5",
        "analysis_class": "POST-PHASE-3 DIAGNOSTIC / NEW-PROTOCOL DEVELOPMENT",
        "status": "IMMEDIATE_STOP_TRIGGERED",
        "incident": "filtered_or_unresolved_nzip_outcomes_mapped_to_numeric_zero",
        "source": {
            "doi": "10.1038/s41593-022-01243-x",
            "accession": "E-MTAB-10902",
            "ena_study": "ERP133202",
            "workbook": "data/raw/nzip/supplementary/41593_2022_1243_MOESM2_ESM.xlsx",
            "workbook_sha256": "15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9",
            "sheet": "Supp_Table_2b",
        },
        "all_secondary_library_rows": int(len(outcomes)),
        "source_zero_missingness_cross_tab": {
            "ratio_zero_and_padj_missing": int(((ratio == 0) & padj.isna()).sum()),
            "ratio_zero_and_padj_finite": int(((ratio == 0) & padj.notna()).sum()),
            "ratio_nonzero_and_padj_missing": int(((ratio != 0) & padj.isna()).sum()),
        },
        "historical_retained_snv_rows": int(len(pairs)),
        "historical_retained_impact": {
            "mutant_unresolved_as_zero": int(pairs["mutant_unresolved"].sum()),
            "parent_unresolved_as_zero": int(pairs["parent_unresolved"].sum()),
            "mutant_or_parent_unresolved": int(pairs["unresolved"].sum()),
            "both_unresolved": int(
                (pairs["mutant_unresolved"] & pairs["parent_unresolved"]).sum()
            ),
            "mutant_only_unresolved": int(
                (pairs["mutant_unresolved"] & ~pairs["parent_unresolved"]).sum()
            ),
            "parent_only_unresolved": int(
                (~pairs["mutant_unresolved"] & pairs["parent_unresolved"]).sum()
            ),
            "unresolved_parent_count": int(
                pairs.loc[pairs["parent_unresolved"], "parent_id"].nunique()
            ),
            "unresolved_parents": sorted(
                pairs.loc[pairs["parent_unresolved"], "parent_id"].unique()
            ),
        },
        "nominal_oracle_diagnostic": {
            "decisions": 30,
            "oracle_mutant_unresolved": oracle_mutant_unresolved,
            "oracle_parent_unresolved": oracle_parent_unresolved,
        },
        "frozen_selected_decisions_with_unresolved_mutant_or_parent": {
            "v2_6": _selected_bad(
                pairs,
                v2["pred_nested_context_external_stack"].to_numpy(float),
                -v2["pred_nested_context_external_stack"].to_numpy(float),
            ),
            "v3_phase3_development_best": _selected_bad(
                pairs,
                v3["increase_score"].to_numpy(float),
                v3["decrease_score"].to_numpy(float),
            ),
            "strongest_forward_3utrbert_absolute_ridge": _selected_bad(
                pairs,
                forward["forward_3utrbert_absolute_ridge_score"].to_numpy(float),
                -forward["forward_3utrbert_absolute_ridge_score"].to_numpy(float),
            ),
            "metadata": _selected_bad(
                pairs,
                v2["pred_metadata_only"].to_numpy(float),
                -v2["pred_metadata_only"].to_numpy(float),
            ),
        },
        "primary_raw_runs": raw_runs,
        "raw_fastq_total_compressed_bytes": 7_452_065_966,
        "raw_read_count": 164_832_486,
        "author_code_revision": "0e7118f1d4880884e6e99e4ba48a26d67f00338a",
        "raw_fastqs_downloaded": False,
        "historical_outputs_modified": False,
        "phase3_no_go_modified": False,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_listed": False,
            "moffatt_archive_opened": False,
            "moffatt_outcomes_opened": False,
        },
        "required_next_action": (
            "commit a correction and raw-reconstruction protocol before resuming Phase 3.5"
        ),
    }
    expected = {
        "ratio_zero_and_padj_missing": 491,
        "ratio_zero_and_padj_finite": 0,
        "ratio_nonzero_and_padj_missing": 0,
    }
    if result["source_zero_missingness_cross_tab"] != expected:
        raise ValueError("Source zero/missingness sentinel pattern changed")
    if result["historical_retained_impact"]["mutant_unresolved_as_zero"] != 406:
        raise ValueError("Historical affected-mutant count changed")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
