"""Reconstruct the explicit Mikl motif-replacement intervention subset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "data"
    / "raw"
    / "mikl_gse173098"
    / "supplementary"
    / "files"
    / "SupplementaryData_NAR_Final"
    / "SupplementaryTables"
    / "TableS2.csv"
)
OUT_CSV = ROOT / "data" / "processed" / "mikl_motif_replacement_pairs.csv.gz"
OUT_AUDIT = ROOT / "data" / "processed" / "mikl_pairing_audit.json"
SEQ = "full library sequence (primers-barcode-test sequence)"


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b)) if len(a) == len(b) else 10**9


def reconstruct() -> tuple[pd.DataFrame, dict[str, object]]:
    data = pd.read_csv(SOURCE)
    wt = data[data["subset"] == "wt scanning 50"].copy()
    mutants = data[data["subset"] == "mut scanning 50"].copy()
    parent_groups = {
        key: rows for key, rows in wt.groupby(["gene name", "position in 3UTR"], dropna=False)
    }
    records: list[dict[str, object]] = []
    unresolved_examples: list[dict[str, object]] = []
    ambiguous = 0
    missing_parent = 0
    for source_row, row in mutants.iterrows():
        key = (row["gene name"], row["position in 3UTR"])
        candidates = parent_groups.get(key)
        if candidates is None or candidates.empty:
            missing_parent += 1
            if len(unresolved_examples) < 20:
                unresolved_examples.append(
                    {
                        "source_row": int(source_row),
                        "gene_name": row["gene name"],
                        "position_in_3utr": row["position in 3UTR"],
                        "reason": "missing_parent_key",
                    }
                )
            continue
        mutant_seq = str(row[SEQ]).upper().replace("U", "T")
        scored = []
        for parent_row, parent in candidates.iterrows():
            parent_seq = str(parent[SEQ]).upper().replace("U", "T")
            scored.append((hamming(parent_seq, mutant_seq), int(parent_row), parent, parent_seq))
        scored.sort(key=lambda x: (x[0], x[1]))
        best_distance = scored[0][0]
        tied = [item for item in scored if item[0] == best_distance]
        unique_sequences = {item[3] for item in tied}
        if len(unique_sequences) > 1:
            ambiguous += 1
            continue
        _, parent_row, parent, parent_seq = tied[0]
        diffs = [i for i, (a, b) in enumerate(zip(parent_seq, mutant_seq)) if a != b]
        records.append(
            {
                "dataset": "mikl_gse173098",
                "source_row": int(source_row),
                "parent_source_row": parent_row,
                "parent_id": f"{row['gene name']}|{row['position in 3UTR']}|{parent_row}",
                "gene_name": row["gene name"],
                "position_in_3utr": row["position in 3UTR"],
                "intervention_description": row["changes"],
                "parent_sequence": parent_seq,
                "mutant_sequence": mutant_seq,
                "edit_count": len(diffs),
                "edit_positions_0based": ";".join(map(str, diffs)),
                "parent_cad_localization": parent["logFC(neurite/soma) - CAD"],
                "mutant_cad_localization": row["logFC(neurite/soma) - CAD"],
                "delta_cad_localization": row["logFC(neurite/soma) - CAD"]
                - parent["logFC(neurite/soma) - CAD"],
                "parent_neuro2a_localization": parent["logFC(neurite/soma) - Neuro-2a"],
                "mutant_neuro2a_localization": row["logFC(neurite/soma) - Neuro-2a"],
                "delta_neuro2a_localization": row["logFC(neurite/soma) - Neuro-2a"]
                - parent["logFC(neurite/soma) - Neuro-2a"],
                "parent_stability_4h": parent["logFC(4h/0h ActD)"],
                "mutant_stability_4h": row["logFC(4h/0h ActD)"],
                "parent_stability_24h": parent["logFC(24h/0h ActD)"],
                "mutant_stability_24h": row["logFC(24h/0h ActD)"],
            }
        )
    pairs = pd.DataFrame.from_records(records)
    audit_record: dict[str, object] = {
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "total_analyzed_constructs": int(len(data)),
        "raw_geo_constructs": 47989,
        "wt_scanning_50_constructs": int(len(wt)),
        "mut_scanning_50_constructs": int(len(mutants)),
        "reconstructed_motif_replacement_pairs": int(len(pairs)),
        "unique_parent_rows_used": int(pairs["parent_source_row"].nunique()),
        "single_nucleotide_pairs": int((pairs["edit_count"] == 1).sum()),
        "multi_nucleotide_pairs": int((pairs["edit_count"] > 1).sum()),
        "ambiguous_parent_rows": ambiguous,
        "missing_parent_rows": missing_parent,
        "note": (
            "Rows with multiple equally close but sequence-distinct WT candidates are "
            "excluded rather than assigned by row order. Mikl interventions are motif "
            "replacements, not an exhaustive single-nucleotide benchmark."
        ),
        "unresolved_missing_parent_examples": unresolved_examples,
        "failures": [],
    }
    if pairs.empty:
        raise ValueError("No truth-safe Mikl intervention pairs were reconstructed")
    return pairs, audit_record


def main() -> None:
    pairs, audit_record = reconstruct()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUT_CSV, index=False, compression="gzip")
    OUT_AUDIT.write_text(json.dumps(audit_record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit_record, indent=2))


if __name__ == "__main__":
    main()
