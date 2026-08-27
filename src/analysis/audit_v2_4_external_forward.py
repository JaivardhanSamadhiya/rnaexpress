"""Audit sequence-level external localization sources for a v2.4 forward prior.

This script intentionally reads no TDP-43 or astrocyte outcome lock.  From the
N-zip development table it reads only identifiers and parent sequences.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data" / "processed" / "nzip_snv_intervention_pairs.csv.gz"
MIKL = (
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
ARORA_DIR = (
    ROOT
    / "data"
    / "raw"
    / "arora_gse183192"
    / "supplementary"
    / "files"
)
ARORA_FASTA = ARORA_DIR / "SupplementaryFile1.txt"
OUT = ROOT / "data" / "frozen" / "v2_4_external_forward_audit.json"

ARORA_ASSAYS = {
    "TableS1.xlsx": "GFP_CAD",
    "TableS2.xlsx": "firefly_CAD",
    "TableS3.xlsx": "GFP_N2A",
    "TableS4.xlsx": "firefly_N2A",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fasta(path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    records: dict[str, dict[str, str]] = {}
    header: str | None = None
    sequence: str | None = None
    unlabeled_sequences: list[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                oligo_id, gene = header.split("|", 1)
                if sequence is None:
                    raise ValueError(f"Arora FASTA record {header} has no sequence")
                records[oligo_id] = {"gene": gene, "sequence": sequence}
            header = line[1:]
            sequence = None
        else:
            if header is None:
                raise ValueError("Arora FASTA starts with sequence rather than header")
            normalized = line.upper().replace("U", "T")
            if len(normalized) != 260:
                raise ValueError(f"Arora sequence line has length {len(normalized)}, not 260")
            if sequence is None:
                sequence = normalized
            else:
                # The source places 750 unlabeled random-control oligos after one
                # labeled record. Every biological record and control occupies a
                # complete 260-nt line, rather than wrapped FASTA sequence lines.
                unlabeled_sequences.append(normalized)
    if header is not None:
        oligo_id, gene = header.split("|", 1)
        if sequence is None:
            raise ValueError(f"Arora FASTA record {header} has no sequence")
        records[oligo_id] = {"gene": gene, "sequence": sequence}
    return records, unlabeled_sequences


def base_gene(value: object) -> str:
    return str(value).strip().split("_", 1)[0].casefold()


def overlap_summary(
    parents: pd.DataFrame,
    external: pd.DataFrame,
    k: int = 31,
) -> list[dict[str, object]]:
    external_sequences = external["sequence"].astype(str).tolist()
    summary: list[dict[str, object]] = []
    for row in parents.itertuples(index=False):
        parent = str(row.parent_sequence)
        kmers = {parent[i : i + k] for i in range(len(parent) - k + 1)}
        exact = sum(parent in sequence for sequence in external_sequences)
        any_kmer = sum(any(kmer in sequence for kmer in kmers) for sequence in external_sequences)
        summary.append(
            {
                "parent_id": str(row.parent_id),
                "gene_name": str(row.gene_name),
                "parent_length": len(parent),
                "external_rows_containing_full_parent": int(exact),
                f"external_rows_sharing_any_exact_{k}mer": int(any_kmer),
            }
        )
    return summary


def arora_frame() -> tuple[pd.DataFrame, dict[str, object]]:
    records, unlabeled_sequences = parse_fasta(ARORA_FASTA)
    assays: list[pd.DataFrame] = []
    source_hashes = {ARORA_FASTA.name: sha256(ARORA_FASTA)}
    for filename, assay in ARORA_ASSAYS.items():
        path = ARORA_DIR / filename
        source_hashes[filename] = sha256(path)
        frame = pd.read_excel(path, usecols=["oligoid", "genename", "neuritelog2FC"])
        frame = frame.rename(columns={"neuritelog2FC": assay})
        assays.append(frame)
    merged = assays[0]
    for frame in assays[1:]:
        merged = merged.merge(frame, on=["oligoid", "genename"], how="outer", validate="one_to_one")
    result_ids = set(merged["oligoid"].astype(str))
    fasta_ids = set(records)
    sequence_frame = pd.DataFrame(
        [
            {"oligoid": oligo_id, "fasta_gene": item["gene"], "sequence": item["sequence"]}
            for oligo_id, item in records.items()
        ]
    )
    merged = merged.merge(sequence_frame, on="oligoid", how="left", validate="one_to_one")
    assay_columns = list(ARORA_ASSAYS.values())
    merged[assay_columns] = merged[assay_columns].apply(pd.to_numeric, errors="coerce")
    correlation = merged[assay_columns].corr(method="spearman")
    audit = {
        "source_sha256": source_hashes,
        "result_rows": int(len(merged)),
        "fasta_records": int(len(records)),
        "unlabeled_260nt_control_sequences": int(len(unlabeled_sequences)),
        "fasta_length_counts": {
            str(key): int(value)
            for key, value in sequence_frame["sequence"].str.len().value_counts().sort_index().items()
        },
        "fasta_controls_without_result": sorted(fasta_ids - result_ids),
        "results_missing_from_fasta": sorted(result_ids - fasta_ids),
        "complete_outcome_rows": int(merged[assay_columns].notna().all(axis=1).sum()),
        "assay_nonmissing_rows": {
            column: int(merged[column].notna().sum()) for column in assay_columns
        },
        "assay_spearman": {
            left: {right: float(correlation.loc[left, right]) for right in assay_columns}
            for left in assay_columns
        },
        "genes": sorted(merged["genename"].dropna().astype(str).unique()),
    }
    return merged, audit


def main() -> None:
    parents = pd.read_csv(
        NZIP,
        usecols=["parent_id", "gene_id", "gene_name", "parent_sequence"],
    ).drop_duplicates("parent_id")
    if len(parents) != 15:
        raise ValueError("N-zip development parents changed")

    mikl = pd.read_csv(
        MIKL,
        usecols=[
            "gene name",
            "subset",
            "full library sequence (primers-barcode-test sequence)",
        ],
    )
    mikl["sequence"] = mikl[
        "full library sequence (primers-barcode-test sequence)"
    ].str.slice(30, 180)
    if not mikl["sequence"].str.len().eq(150).all():
        raise ValueError("Mikl insert extraction no longer yields 150 nt")
    nzip_base_genes = {base_gene(value) for value in parents["gene_name"]}
    mikl_base_genes = {base_gene(value) for value in mikl["gene name"].dropna()}
    mikl_wt = mikl[mikl["subset"].eq("wt scanning 50")].copy()
    mikl_wt_decontaminated = mikl_wt[
        ~mikl_wt["gene name"].map(base_gene).isin(nzip_base_genes)
    ].copy()

    arora, arora_audit = arora_frame()
    arora_base_genes = {base_gene(value) for value in arora["genename"].dropna()}
    arora_audit["nzip_gene_overlap"] = sorted(nzip_base_genes & arora_base_genes)
    arora_audit["nzip_sequence_overlap"] = overlap_summary(parents, arora)

    output = {
        "purpose": "Outcome-blind source, construct, reliability, and leakage audit before v2.4 preregistration.",
        "locks": "TDP-43 locked outcomes and astrocyte outcomes were not read.",
        "nzip": {
            "source_sha256": sha256(NZIP),
            "parents": int(len(parents)),
            "base_genes": sorted(nzip_base_genes),
            "parent_length_counts": {
                str(key): int(value)
                for key, value in parents["parent_sequence"].str.len().value_counts().sort_index().items()
            },
        },
        "mikl": {
            "source_sha256": sha256(MIKL),
            "constructs": int(len(mikl)),
            "insert_length": 150,
            "wt_scanning_50_rows": int(len(mikl_wt)),
            "nzip_gene_overlap": sorted(nzip_base_genes & mikl_base_genes),
            "nzip_sequence_overlap_all_constructs": overlap_summary(parents, mikl),
            "wt_rows_after_global_nzip_gene_exclusion": int(len(mikl_wt_decontaminated)),
            "nzip_sequence_overlap_after_wt_and_gene_exclusion": overlap_summary(
                parents, mikl_wt_decontaminated
            ),
        },
        "arora": arora_audit,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
