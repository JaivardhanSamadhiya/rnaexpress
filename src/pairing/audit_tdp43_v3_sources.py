"""Deterministic source-data audit for the post-lock TDP-43 diagnosis.

This module is intentionally restricted to the TDP-43 study.  It does not
reference or open the protected Astrocyte workbook or the sealed Moffatt TAR.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SUPP = ROOT / "data" / "raw" / "PMC12864922_supplementary"
PAIRS = ROOT / "data" / "processed" / "tdp43_motif_intervention_pairs.csv.gz"
PAIR_AUDIT = ROOT / "data" / "processed" / "tdp43_pairing_audit.json"
PREDICTIONS = ROOT / "results" / "v2_tdp43_lock" / "tdp43_v2_frozen_predictions.csv.gz"
LOCK_OUTCOMES = ROOT / "data" / "frozen" / "outcomes" / "tdp43_v2_locked_outcomes.csv.gz"
GEO_FILELIST = ROOT / "data" / "raw" / "gse288185_metadata" / "filelist.txt"
FULLTEXT = ROOT / "data" / "raw" / "PMC12864922_fulltext.xml"
FIG4_ZIP = SUPP / "44318_2025_653_MOESM14_ESM.zip"
FIG6_ZIP = SUPP / "44318_2025_653_MOESM16_ESM.zip"
OUT = ROOT / "reports" / "v3_tdp_source_data_audit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    identifier: str | None = None
    pieces: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            if identifier is not None:
                if identifier in records:
                    raise ValueError("Duplicate reporter identifier in EV8 FASTA")
                records[identifier] = "".join(pieces).upper()
            identifier, pieces = line[1:], []
        elif identifier is not None:
            pieces.append(line)
    if identifier is not None:
        if identifier in records:
            raise ValueError("Duplicate reporter identifier in EV8 FASTA")
        records[identifier] = "".join(pieces).upper()
    return records


def _read_zip_table(archive: Path, member: str, sep: str = ",") -> pd.DataFrame:
    with zipfile.ZipFile(archive) as zipped:
        return pd.read_csv(zipped.open(member), sep=sep)


def _read_repaired_structure() -> pd.DataFrame:
    """Repair the publisher's unquoted newline inside the CLIP label."""
    member = "Figure4/4F/Fig4Fsource.txt"
    with zipfile.ZipFile(FIG4_ZIP) as zipped:
        text = zipped.read(member).decode("utf-8-sig")
    text = text.replace("No\nCLIP peak", "No CLIP peak")
    text = text.replace("Contains\nCLIP peak", "Contains CLIP peak")
    frame = pd.read_csv(io.StringIO(text))
    if frame.isna().all(axis=1).any() or len(frame) != 39_388:
        raise ValueError("Unexpected repaired Figure 4F structure table")
    return frame


def _source_record(
    *,
    source: str,
    accession: str,
    rows: int,
    identifier: str,
    reporter_sequence: bool,
    parent_gene: bool,
    localization: bool,
    stability: bool,
    binding: bool,
    clip: bool,
    structure: bool,
    exact_linked_interventions: int,
    linkage: str,
    ambiguity_count: int,
    exclusion_count: int,
) -> dict[str, object]:
    return {
        "source": source,
        "public_accession": accession,
        "rows": rows,
        "identifier_field": identifier,
        "reporter_sequence_available": reporter_sequence,
        "parent_or_gene_identity": parent_gene,
        "localization_fields": localization,
        "stability_fields": stability,
        "binding_fields": binding,
        "clip_fields": clip,
        "structure_fields": structure,
        "exact_linked_interventions": exact_linked_interventions,
        "linkage_method": linkage,
        "ambiguity_count": ambiguity_count,
        "exclusion_count": exclusion_count,
    }


def audit() -> dict[str, object]:
    pairs = pd.read_csv(PAIRS)
    pairing = json.loads(PAIR_AUDIT.read_text())
    if len(pairs) != 4_566 or pairs["gene_id"].nunique() != 16:
        raise ValueError("Historical 4,566-pair reconstruction changed")
    if pairs[["parent_id", "mutant_id"]].isna().any().any():
        raise ValueError("Historical pair identifiers are incomplete")
    if pairs["parent_id"].duplicated().any() or pairs["mutant_id"].duplicated().any():
        raise ValueError("Historical pair identifiers are not unique")
    if pairing["design_mismatches_quarantined"] != 0:
        raise ValueError("Historical pairing audit now reports mismatches")

    ev8_path = SUPP / "44318_2025_653_MOESM9_ESM.txt"
    fasta = _read_fasta(ev8_path)
    if len(fasta) != 11_955 or {len(sequence) for sequence in fasta.values()} != {300}:
        raise ValueError("Unexpected EV8 reporter FASTA")
    parent_match = sum(
        fasta[identifier][20:-20] == sequence
        for identifier, sequence in pairs[["parent_id", "parent_sequence"]].itertuples(index=False)
    )
    mutant_match = sum(
        fasta[identifier][20:-20] == sequence
        for identifier, sequence in pairs[["mutant_id", "mutant_sequence"]].itertuples(index=False)
    )
    if parent_match != 4_566 or mutant_match != 4_566:
        raise ValueError("Published EV8 FASTA contradicts historical reconstruction")

    ev3 = pd.read_excel(
        SUPP / "44318_2025_653_MOESM4_ESM.xlsx", sheet_name="allcounts"
    )
    if len(ev3) != 191_075 or ev3["oligo"].nunique() != 11_955:
        raise ValueError("Unexpected EV3 MPRA count table")
    ev3_ids = set(ev3["oligo"].astype(str))

    ev4 = pd.read_excel(
        SUPP / "44318_2025_653_MOESM5_ESM.xlsx", sheet_name="allcounts"
    )
    ev4_ids = set(ev4["oligo"].astype(str))
    rbns_parent = pairs["parent_id"].isin(ev4_ids)
    rbns_mutant = pairs["mutant_id"].isin(ev4_ids)
    rbns_both = rbns_parent & rbns_mutant

    ev5 = pd.read_excel(
        SUPP / "44318_2025_653_MOESM6_ESM.xlsx", sheet_name="tt_tc_counts (1)"
    )
    duplicate_slam_keys = int(ev5.duplicated(["sample", "oligo"]).sum())
    if duplicate_slam_keys != 10_935 or "WT_t0_3" in set(ev5["sample"]):
        raise ValueError("Unexpected EV5 duplicate-label profile")

    fig4d = _read_zip_table(FIG4_ZIP, "Figure4/4D/Fig4Dsource.txt")
    fig4d_ids = set(fig4d["oligo"].astype(str))
    structure = _read_repaired_structure()
    structure_ids = set(structure["oligo"].astype(str))

    stability = _read_zip_table(
        FIG6_ZIP, "Figure6/6C/paired_mut_clip_vs_stab_6c.tsv", sep="\t"
    )
    stability_names = set(stability["name"].astype(str))
    base_ids = pairs["parent_id"].str.split("|", regex=False).str[0]
    stability_pivot = stability.pivot(
        index="name", columns="oligotype", values="log_ko_wt_stb_delta"
    )
    stability_both_finite = int(
        np.isfinite(stability_pivot.to_numpy(float)).all(axis=1).sum()
    )

    predictions = pd.read_csv(PREDICTIONS)
    outcomes = pd.read_csv(LOCK_OUTCOMES)
    prediction_keys = ["parent_id", "mutant_id"]
    joined = predictions.merge(outcomes, on=prediction_keys, validate="one_to_one")
    if len(joined) != 1_006 or joined["gene_id"].nunique() != 4:
        raise ValueError("Frozen historical prediction/outcome linkage changed")

    geo = pd.read_csv(GEO_FILELIST, sep="\t")
    geo_names = geo["Name"].astype(str)
    gff_path = SUPP / "44318_2025_653_MOESM10_ESM.txt"
    gff_rows = sum(
        1
        for line in gff_path.read_text().splitlines()
        if line and not line.startswith("#")
    )

    source_records = [
        _source_record(
            source="Dataset EV3 / 44318_2025_653_MOESM4_ESM.xlsx",
            accession="GSE288185; PMCID PMC12864922",
            rows=len(ev3),
            identifier="oligo",
            reporter_sequence=False,
            parent_gene=True,
            localization=True,
            stability=False,
            binding=False,
            clip=False,
            structure=False,
            exact_linked_interventions=int(
                (pairs["parent_id"].isin(ev3_ids) & pairs["mutant_id"].isin(ev3_ids)).sum()
            ),
            linkage="exact parent_id and mutant_id",
            ambiguity_count=0,
            exclusion_count=0,
        ),
        _source_record(
            source="Dataset EV8 / 44318_2025_653_MOESM9_ESM.txt",
            accession="PMCID PMC12864922",
            rows=len(fasta),
            identifier="FASTA header",
            reporter_sequence=True,
            parent_gene=True,
            localization=False,
            stability=False,
            binding=False,
            clip=False,
            structure=False,
            exact_linked_interventions=4_566,
            linkage="exact construct ID; exact 260-nt insert after trimming 20-nt handles",
            ambiguity_count=0,
            exclusion_count=0,
        ),
        _source_record(
            source="Dataset EV9 / 44318_2025_653_MOESM10_ESM.txt",
            accession="PMCID PMC12864922",
            rows=gff_rows,
            identifier="GFF ID/oligo_id",
            reporter_sequence=False,
            parent_gene=True,
            localization=False,
            stability=False,
            binding=False,
            clip=False,
            structure=False,
            exact_linked_interventions=4_566,
            linkage="exact natural construct ID plus EV8 mutation suffix",
            ambiguity_count=0,
            exclusion_count=0,
        ),
        _source_record(
            source="Dataset EV4 / 44318_2025_653_MOESM5_ESM.xlsx",
            accession="GSE288185; PMCID PMC12864922",
            rows=len(ev4),
            identifier="oligo",
            reporter_sequence=False,
            parent_gene=True,
            localization=False,
            stability=False,
            binding=True,
            clip=False,
            structure=False,
            exact_linked_interventions=int(rbns_both.sum()),
            linkage="exact parent_id and mutant_id",
            ambiguity_count=0,
            exclusion_count=int((~rbns_both).sum()),
        ),
        _source_record(
            source="Dataset EV5 / 44318_2025_653_MOESM6_ESM.xlsx",
            accession="GSE288185; PMCID PMC12864922",
            rows=len(ev5),
            identifier="sample + oligo",
            reporter_sequence=False,
            parent_gene=True,
            localization=False,
            stability=True,
            binding=False,
            clip=False,
            structure=False,
            exact_linked_interventions=0,
            linkage="raw reconstruction quarantined because sample+oligo keys are duplicated",
            ambiguity_count=duplicate_slam_keys,
            exclusion_count=len(pairs),
        ),
        _source_record(
            source="Figure 6C source / paired_mut_clip_vs_stab_6c.tsv",
            accession="BioStudies S-SCDT-10_1038-S44318-025-00653-4",
            rows=len(stability),
            identifier="name + oligotype",
            reporter_sequence=False,
            parent_gene=True,
            localization=False,
            stability=True,
            binding=False,
            clip=True,
            structure=False,
            exact_linked_interventions=int(base_ids.isin(stability_names).sum()),
            linkage="exact natural oligo ID plus explicit TDP-43 motif/Mutant motif label",
            ambiguity_count=0,
            exclusion_count=int((~base_ids.isin(stability_names)).sum()),
        ),
        _source_record(
            source="Figure 4D source / Fig4Dsource.txt",
            accession="BioStudies S-SCDT-10_1038-S44318-025-00653-4",
            rows=len(fig4d),
            identifier="oligo",
            reporter_sequence=False,
            parent_gene=True,
            localization=True,
            stability=False,
            binding=False,
            clip=True,
            structure=False,
            exact_linked_interventions=int(pairs["parent_id"].isin(fig4d_ids).sum()),
            linkage="exact parent_id",
            ambiguity_count=0,
            exclusion_count=0,
        ),
        _source_record(
            source="Figure 4F source / Fig4Fsource.txt",
            accession="BioStudies S-SCDT-10_1038-S44318-025-00653-4",
            rows=len(structure),
            identifier="oligo + kmerpos + motifid",
            reporter_sequence=False,
            parent_gene=True,
            localization=True,
            stability=False,
            binding=False,
            clip=True,
            structure=True,
            exact_linked_interventions=int(pairs["parent_id"].isin(structure_ids).sum()),
            linkage="exact construct ID and zero-based motif start",
            ambiguity_count=0,
            exclusion_count=int((~pairs["parent_id"].isin(structure_ids)).sum()),
        ),
        _source_record(
            source="Frozen v2.6 lock predictions and outcomes",
            accession="RNAddress commit cf98954",
            rows=len(joined),
            identifier="gene_id + parent_id + mutant_id + source_figure4e_row",
            reporter_sequence=True,
            parent_gene=True,
            localization=True,
            stability=False,
            binding=False,
            clip=True,
            structure=False,
            exact_linked_interventions=len(joined),
            linkage="four-column one-to-one historical frozen key",
            ambiguity_count=0,
            exclusion_count=len(pairs) - len(joined),
        ),
    ]

    hash_paths = [
        FULLTEXT,
        PAIRS,
        PAIR_AUDIT,
        PREDICTIONS,
        LOCK_OUTCOMES,
        GEO_FILELIST,
        *(SUPP / f"44318_2025_653_MOESM{i}_ESM.xlsx" for i in range(2, 9)),
        ev8_path,
        gff_path,
        FIG4_ZIP,
        SUPP / "44318_2025_653_MOESM15_ESM.zip",
        FIG6_ZIP,
    ]
    result = {
        "phase": "v3_phase2_post_lock_diagnostic",
        "historical_pairing_error_found": False,
        "historical_pairs": len(pairs),
        "genes": int(pairs["gene_id"].nunique()),
        "ev8_parent_sequence_exact_matches": parent_match,
        "ev8_mutant_sequence_exact_matches": mutant_match,
        "ev3_samples": int(ev3["sample"].nunique()),
        "ev3_unique_oligos": int(ev3["oligo"].nunique()),
        "rbns_exact_both_construct_pairs": int(rbns_both.sum()),
        "stability_source_pairs": int(stability_pivot.shape[0]),
        "stability_pairs_both_finite": stability_both_finite,
        "slam_raw_duplicate_sample_oligo_keys": duplicate_slam_keys,
        "slam_distinct_sample_labels": sorted(ev5["sample"].astype(str).unique()),
        "geo_public_file_categories": {
            "all_records_including_archive": len(geo),
            "mpra": int(geo_names.str.contains("MPRA").sum()),
            "rbns": int(geo_names.str.contains("RBNS").sum()),
            "slamseq": int(geo_names.str.contains("SLAMseq").sum()),
        },
        "source_records": source_records,
        "source_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in hash_paths
        },
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    return result


def main() -> None:
    result = audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
