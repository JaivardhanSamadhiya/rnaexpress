"""Reconstruct N-zip experimental SNV tuples with strict sequence checks."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "data"
    / "raw"
    / "nzip"
    / "supplementary"
    / "41593_2022_1243_MOESM2_ESM.xlsx"
)
OUT_CSV = ROOT / "data" / "processed" / "nzip_snv_intervention_pairs.csv.gz"
OUT_AUDIT = ROOT / "data" / "processed" / "nzip_pairing_audit.json"

KEY = ["Source gene id", "Source gene name", "Source tile id"]


def _normalize(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


JOIN_LEFT = ["Source gene id", "Source gene name", "Mutation type", "Mutation position"]
JOIN_RIGHT = ["source_gene_id", "source_gene_name", "mutation_type", "mutation_position"]


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    design = pd.read_excel(SOURCE, sheet_name="Supp_Table_2a", skiprows=2)
    outcomes = pd.read_excel(SOURCE, sheet_name="Supp_Table_2b", skiprows=2)
    if len(design) != len(outcomes):
        raise ValueError("N-zip design and outcome sheets have different row counts")

    # The two sheets use different global sort orders. Compare key multisets rather
    # than row positions, and only join keys that are unique in both sheets.
    left_keys = design[JOIN_LEFT].map(_normalize).agg("|".join, axis=1)
    right_keys = outcomes[JOIN_RIGHT].map(_normalize).agg("|".join, axis=1)
    if left_keys.value_counts().to_dict() != right_keys.value_counts().to_dict():
        raise ValueError("N-zip design/outcome construct-key multisets differ")
    design = design.assign(_join_key=left_keys)
    outcomes = outcomes.assign(_join_key=right_keys)
    return design, outcomes


def reconstruct() -> tuple[pd.DataFrame, dict[str, object]]:
    design, outcomes = load_tables()
    key_counts = design["_join_key"].value_counts()
    ambiguous_keys = set(key_counts[key_counts > 1].index)
    ambiguous_wt = design[
        (design["Mutation type"] == "WT") & design["_join_key"].isin(ambiguous_keys)
    ]
    unsafe_parent_identities = {
        (_normalize(row["Source gene id"]), _normalize(row["Source gene name"]))
        for _, row in ambiguous_wt.iterrows()
    }
    design_identity = design.apply(
        lambda row: (_normalize(row["Source gene id"]), _normalize(row["Source gene name"])),
        axis=1,
    )
    outcome_identity = outcomes.apply(
        lambda row: (_normalize(row["source_gene_id"]), _normalize(row["source_gene_name"])),
        axis=1,
    )
    unsafe_design = design_identity.isin(unsafe_parent_identities)
    unsafe_outcomes = outcome_identity.isin(unsafe_parent_identities)
    unique_design = design[
        ~design["_join_key"].isin(ambiguous_keys) & ~unsafe_design
    ].reset_index(
        names="source_row"
    )
    unique_outcomes = outcomes[
        ~outcomes["_join_key"].isin(ambiguous_keys) & ~unsafe_outcomes
    ].copy()
    joined = unique_design.merge(
        unique_outcomes.add_prefix("outcome_"),
        left_on="_join_key",
        right_on="outcome__join_key",
        validate="one_to_one",
    )

    wt = joined[joined["Mutation type"] == "WT"].copy()
    if wt.duplicated(KEY).any():
        raise ValueError("N-zip WT parent keys are not unique")
    parents = {tuple(row[k] for k in KEY): row for _, row in wt.iterrows()}

    snv = joined[joined["Mutation type"] == "sgl"].copy()
    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    covered_positions: dict[str, set[int]] = {}

    for _, row in snv.iterrows():
        key = tuple(row[k] for k in KEY)
        parent = parents.get(key)
        if parent is None:
            failures.append({"source_row": int(row["source_row"]), "reason": "missing_parent"})
            continue
        parent_seq = str(parent["Sequence"]).upper().replace("U", "T")
        mutant_seq = str(row["Sequence"]).upper().replace("U", "T")
        if len(parent_seq) != len(mutant_seq):
            failures.append({"source_row": int(row["source_row"]), "reason": "length_mismatch"})
            continue
        diffs = [i for i, (a, b) in enumerate(zip(parent_seq, mutant_seq)) if a != b]
        if len(diffs) != 1:
            failures.append(
                {
                    "source_row": int(row["source_row"]),
                    "reason": f"expected_one_difference_found_{len(diffs)}",
                }
            )
            continue
        pos0 = diffs[0]
        ref, alt = parent_seq[pos0], mutant_seq[pos0]
        parent_id = "|".join(map(str, key))
        covered_positions.setdefault(parent_id, set()).add(pos0)
        y_parent = float(parent["outcome_Mean_log2ratio_NeuriteSoma_WT"])
        y_mutant = float(row["outcome_Mean_log2ratio_NeuriteSoma_WT"])
        records.append(
            {
                "dataset": "nzip",
                "source_row": int(row["source_row"]),
                "parent_id": parent_id,
                "gene_id": row["Source gene id"],
                "gene_name": row["Source gene name"],
                "source_tile_id": row["Source tile id"],
                "parent_sequence": parent_seq,
                "edit_position_0based": pos0,
                "edit_position_1based": pos0 + 1,
                "reference_nt": ref,
                "alternate_nt": alt,
                "reported_mutation_position": row["Mutation position"],
                "mutant_sequence": mutant_seq,
                "parent_localization_log2_neurite_soma": y_parent,
                "mutant_localization_log2_neurite_soma": y_mutant,
                "delta_localization": y_mutant - y_parent,
                "parent_localization_padj": parent["outcome_Mean_padj_NeuriteSoma_WT"],
                "mutant_localization_padj": row["outcome_Mean_padj_NeuriteSoma_WT"],
                "mutant_shago2_localization": row["outcome_Median_log2ratio_NeuriteSoma_shAgo2"],
                "mutant_shhbs1l_localization": row["outcome_Median_log2ratio_NeuriteSoma_shHbs1l"],
                "mutant_shscramble_localization": row["outcome_Median_log2ratio_NeuriteSoma_shScramble"],
            }
        )

    pairs = pd.DataFrame.from_records(records)
    snv_parents = set(pairs["parent_id"])
    expected = int(
        pairs[["parent_id", "parent_sequence"]]
        .drop_duplicates()["parent_sequence"]
        .str.len()
        .sum()
    )
    # Each position must have all three non-reference alternatives.
    coverage = pairs.groupby(["parent_id", "edit_position_0based"])["alternate_nt"].nunique()
    complete_position_coverage = bool((coverage == 3).all())
    expected_snv_count = int(sum(len(v) for v in covered_positions.values()) * 3)

    audit: dict[str, object] = {
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "total_mutagenesis_constructs": int(len(design)),
        "mutation_type_counts": {
            str(k): int(v) for k, v in design["Mutation type"].value_counts().items()
        },
        "wt_parent_constructs": int(len(wt)),
        "snv_parent_constructs": int(len(snv_parents)),
        "snv_parent_total_length_nt": int(expected),
        "expected_snv_count_from_parent_lengths": int(expected * 3),
        "expected_snv_count_from_observed_positions": expected_snv_count,
        "reconstructed_snv_pairs": int(len(pairs)),
        "complete_three_alternates_per_position": complete_position_coverage,
        "complete_primary_localization_labels": int(
            pairs["mutant_localization_log2_neurite_soma"].notna().sum()
        ),
        "ambiguous_construct_keys": int(len(ambiguous_keys)),
        "ambiguous_design_rows_all_mutation_types": int(
            design["_join_key"].isin(ambiguous_keys).sum()
        ),
        "excluded_snv_rows_due_to_ambiguous_outcome_identity": int(
            ((design["Mutation type"] == "sgl") & unsafe_design).sum()
        ),
        "note": (
            "The outcome sheet omits Source tile id. Repeated Cflar_2 constructs "
            "therefore cannot be assigned to tile 107 versus tile 52 without an "
            "occurrence-order assumption; all such ambiguous keys are excluded."
        ),
        "failures": failures,
    }
    if failures:
        raise ValueError(f"N-zip reconstruction failures: {failures[:5]}")
    if len(pairs) != expected * 3 or not complete_position_coverage:
        raise ValueError("N-zip SNV library is not exhaustive after reconstruction")
    return pairs, audit


def main() -> None:
    pairs, audit = reconstruct()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUT_CSV, index=False, compression="gzip")
    OUT_AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
