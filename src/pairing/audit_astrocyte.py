"""Fail-closed access to the frozen, outcome-free Astrocyte SN-MPRA inputs.

The historical source-workbook reconstruction is retained for provenance but
requires an explicit reveal-stage environment token. Ordinary tests and v3
development must use :func:`audit`, which reads only committed frozen files.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "raw" / "astrocyte_gse330741" / "supplementary" / "media-1.xlsx"
OUT_FEATURES = ROOT / "data" / "frozen" / "astrocyte_external_features.csv.gz"
OUT_AUDIT = ROOT / "data" / "frozen" / "astrocyte_pairing_audit.json"
MANIFEST = ROOT / "data" / "frozen" / "external_manifest.json"

OUTCOME_COLUMNS = [
    "snin_ctxin_logFC",       # localization
    "ctxtrap_ctxin_logFC",    # ribosome occupancy
    "paptrap_ctxtrap_logFC",  # local translation
]

SAFE_COLUMNS = [
    "dataset",
    "element",
    "parent_id",
    "gene",
    "parent_sequence",
    "edit_position_0based",
    "edit_position_1based",
    "genomic_or_utr_position",
    "reference_nt",
    "alternate_nt",
    "mutant_sequence",
    "delta_g_kcal_per_mol",
    "rg4_prediction",
]
SOURCE_RECONSTRUCTION_TOKEN = "RNADDRESS_V3_REVEAL_STAGE_ONLY"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_outcome_free_features(features: pd.DataFrame) -> None:
    if features.columns.tolist() != SAFE_COLUMNS:
        unexpected = sorted(set(features.columns) - set(SAFE_COLUMNS))
        missing = sorted(set(SAFE_COLUMNS) - set(features.columns))
        raise ValueError(
            "Astrocyte feature schema is not the frozen outcome-free allowlist: "
            f"unexpected={unexpected}, missing={missing}"
        )
    protected_tokens = (
        "logfc",
        "localization",
        "translation",
        "ribosome",
        "expression",
        "rna_count",
        "dna_count",
    )
    normalized = [column.lower() for column in features.columns]
    leaked = [
        column
        for column, lowered in zip(features.columns, normalized)
        if any(token in lowered for token in protected_tokens)
    ]
    if leaked:
        raise ValueError(f"Protected Astrocyte outcome-like columns detected: {leaked}")


def audit() -> tuple[pd.DataFrame, dict[str, object]]:
    """Validate and load only the frozen outcome-free v3 feature artifact."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_hashes = {
        entry["path"]: entry["sha256"] for entry in manifest["files"]
    }
    for path in (OUT_FEATURES, OUT_AUDIT):
        relative = path.relative_to(ROOT).as_posix()
        if _sha256(path) != expected_hashes.get(relative):
            raise ValueError(f"Frozen Astrocyte artifact hash changed: {relative}")
    features = pd.read_csv(OUT_FEATURES)
    audit_record = json.loads(OUT_AUDIT.read_text(encoding="utf-8"))
    validate_outcome_free_features(features)
    if len(features) != 4_553 or features["parent_id"].nunique() != 8:
        raise ValueError("Frozen Astrocyte feature boundary changed")
    if features["element"].duplicated().any():
        raise ValueError("Frozen Astrocyte element identifiers must be unique")
    differences = [
        sum(left != right for left, right in zip(parent, mutant))
        for parent, mutant in zip(features["parent_sequence"], features["mutant_sequence"])
    ]
    if set(differences) != {1}:
        raise ValueError("Frozen Astrocyte artifact contains a non-SNV intervention")
    return features, audit_record


def reconstruct_from_source() -> tuple[pd.DataFrame, dict[str, object]]:
    """Historical reconstruction; prohibited during v3 development by default."""
    if os.environ.get("RNADDRESS_ASTROCYTE_SOURCE_ACCESS") != SOURCE_RECONSTRUCTION_TOKEN:
        raise PermissionError(
            "Raw Astrocyte workbook access is sealed during v3 development. "
            "Use audit() to read the frozen outcome-free feature artifact."
        )
    design = pd.read_excel(SOURCE, sheet_name="S6_mutagenesis_lib_seq_info")
    outcomes = pd.read_excel(SOURCE, sheet_name="S8_lib2_results_summary")
    if design["element"].duplicated().any() or outcomes["element"].duplicated().any():
        raise ValueError("Astrocyte element identifiers must be unique")

    biological = design[design["element_group"] != "control"].copy()
    wt = biological[biological["original_nt"].astype(str).str.lower() == "wt"].copy()
    snv = biological[biological["original_nt"].astype(str).str.lower() != "wt"].copy()

    parent_rows: dict[str, pd.Series] = {}
    for group, rows in wt.groupby("element_group"):
        exact = rows[(rows["element"] == group) & (rows["seq_length"] == 190)]
        if len(exact) != 1:
            raise ValueError(f"Expected one 190-nt WT parent for {group}, found {len(exact)}")
        parent_rows[str(group)] = exact.iloc[0]

    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for _, row in snv.iterrows():
        parent = parent_rows[str(row["element_group"])]
        parent_seq = str(parent["CRE"]).upper().replace("U", "T")
        mutant_seq = str(row["CRE"]).upper().replace("U", "T")
        diffs = [i for i, (a, b) in enumerate(zip(parent_seq, mutant_seq)) if a != b]
        if len(parent_seq) != len(mutant_seq) or len(diffs) != 1:
            failures.append(
                {
                    "element": row["element"],
                    "reason": f"lengths_{len(parent_seq)}_{len(mutant_seq)}_diffs_{len(diffs)}",
                }
            )
            continue
        pos0 = diffs[0]
        ref, alt = parent_seq[pos0], mutant_seq[pos0]
        if ref != str(row["original_nt"]).upper() or alt != str(row["mutant_nt"]).upper():
            failures.append({"element": row["element"], "reason": "reported_base_mismatch"})
            continue
        expected_pos1 = int(row["position_start"]) - int(parent["position_start"]) + 1
        if expected_pos1 != pos0 + 1:
            failures.append({"element": row["element"], "reason": "reported_position_mismatch"})
            continue
        records.append(
            {
                "dataset": "astrocyte_sn_mpra",
                "element": row["element"],
                "parent_id": row["element_group"],
                "gene": row["gene"],
                "parent_sequence": parent_seq,
                "edit_position_0based": pos0,
                "edit_position_1based": pos0 + 1,
                "genomic_or_utr_position": int(row["position_start"]),
                "reference_nt": ref,
                "alternate_nt": alt,
                "mutant_sequence": mutant_seq,
                "delta_g_kcal_per_mol": row["DeltaG_kcal_per_mol"],
                "rg4_prediction": row["rG4prediction"],
            }
        )

    features = pd.DataFrame.from_records(records)
    result_index = outcomes.set_index("element")
    missing_result_rows = ~features["element"].isin(result_index.index)
    completeness: dict[str, int] = {}
    for column in OUTCOME_COLUMNS:
        completeness[column] = int(
            result_index.reindex(features["element"])[column].notna().sum()
        )

    coverage = features.groupby(["parent_id", "edit_position_0based"])["alternate_nt"].nunique()
    coverage_counts = {str(k): int(v) for k, v in coverage.value_counts().sort_index().items()}
    audit_record: dict[str, object] = {
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "total_library_constructs": int(len(design)),
        "control_constructs": int((design["element_group"] == "control").sum()),
        "biological_element_groups": int(len(parent_rows)),
        "wt_constructs_in_biological_groups": int(len(wt)),
        "selected_190nt_parent_constructs": int(len(parent_rows)),
        "reconstructed_snv_pairs": int(len(features)),
        "complete_three_alternates_per_position": bool((coverage == 3).all()),
        "snv_positions": int(len(coverage)),
        "positions_by_number_of_assayed_alternates": coverage_counts,
        "missing_alternate_substitutions_from_full_saturation": int(
            (3 - coverage).clip(lower=0).sum()
        ),
        "snvs_missing_result_row": int(missing_result_rows.sum()),
        "complete_held_out_labels_by_field": completeness,
        "held_out_outcome_columns": OUTCOME_COLUMNS,
        "outcome_values_exported": False,
        "failures": failures,
    }
    if failures or missing_result_rows.any():
        raise ValueError(f"Astrocyte pairing audit failed: {audit_record}")
    return features, audit_record


def main() -> None:
    features, audit_record = audit()
    print(
        json.dumps(
            {
                "outcome_free_rows": len(features),
                "parents": int(features["parent_id"].nunique()),
                "feature_columns": features.columns.tolist(),
                "frozen_audit_sha256": _sha256(OUT_AUDIT),
                "source_workbook_opened": False,
                "historical_audit": audit_record,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
