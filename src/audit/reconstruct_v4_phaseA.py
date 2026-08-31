"""Reconstruct the RNAddress v4 Phase A development foundation.

This module performs source-truth reconstruction only. It does not fit, tune,
select, or evaluate a predictive model and never reads Astrocyte outcomes.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import platform
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "v4_phaseA"
MIKL_TABLE = (
    ROOT
    / "data/raw/mikl_gse173098/supplementary/files/"
    "SupplementaryData_NAR_Final/SupplementaryTables/TableS2.csv"
)
MIKL_GENES = MIKL_TABLE.with_name("TableS1.csv")
MIKL_COUNTS = ROOT / "data/raw/mikl_gse173098/GSE173098_RNAloc_MPRA_counts.csv.gz"
TDP_PAIRS = ROOT / "data/processed/tdp43_motif_intervention_pairs.csv.gz"
TDP_AUDIT = ROOT / "reports/v3_tdp_source_data_audit.json"
MOFF_DIR = ROOT / "data/raw/moffatt_gse334718"
MOFF_FASTA = MOFF_DIR / "supplementary/supplementary_file_1.txt"
MOFF_TABLES = [MOFF_DIR / f"supplementary/supplementary_table_{i}.csv" for i in range(1, 6)]
MOFF_COUNT_DIR = MOFF_DIR / "processed_counts"
MOFF_SAMPLE_MANIFEST = OUT / "moffatt_geo_sample_manifest.csv"
MOFF_ARCHIVE = MOFF_DIR / "GSE334718_RAW.tar"
MOFF_ARCHIVE_SHA256 = "abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1"
ARORA_DIR = ROOT / "data/raw/arora_gse183192/supplementary/files"
ARORA_AUDIT = ROOT / "data/frozen/v2_4_external_forward_audit.json"
MOFF_CODE_REFERENCES = [
    MOFF_DIR / "code/sufficiency-mpra-analysis/by_position_l2fc.py",
    MOFF_DIR / "code/sufficiency-mpra-analysis/suff_fract_analysis.qmd",
    MOFF_DIR / "code/LE_SHAPE_Summary/shaped_based_oligo_design.qmd",
]
MIKL_FULL_SEQUENCE = "full library sequence (primers-barcode-test sequence)"
DNA = re.compile(r"^[ACGT]+$")
DETERMINISTIC_GZIP = {"method": "gzip", "mtime": 0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sequence_id(prefix: str, sequence: str) -> str:
    return f"{prefix}:{hashlib.sha256(sequence.encode()).hexdigest()[:16]}"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def standard_error(values: Iterable[float]) -> float:
    finite = np.asarray([v for v in values if math.isfinite(v)], dtype=float)
    if len(finite) < 2:
        return math.nan
    return float(finite.std(ddof=1) / math.sqrt(len(finite)))


def direction(value: float) -> str:
    if not math.isfinite(value):
        return "missing"
    if value > 0:
        return "increase"
    if value < 0:
        return "decrease"
    return "zero"


def edit_tier(edit_count: int, operation_class: str) -> str:
    """Empirical tiers anchored to assay modes, not effect outcomes."""
    if edit_count == 1:
        return "exact_snv"
    if 2 <= edit_count <= 5:
        return "small_local_edit"
    if 6 <= edit_count <= 12:
        return "motif_scale_edit"
    if 13 <= edit_count <= 99:
        return "regional_edit"
    if edit_count >= 100:
        return "large_element_edit"
    return f"unclassified_{operation_class}"


def motif_positions(sequence: str, motif: str) -> set[int]:
    starts = [m.start() for m in re.finditer(f"(?={re.escape(motif)})", sequence)]
    return {position for start in starts for position in range(start, start + len(motif))}


def raw_log_ratios(row: pd.Series, cell: str) -> list[float]:
    prefix = "CAD" if cell == "cad" else "Neuro-2a"
    values = []
    for replicate in range(1, 4):
        soma = float(row[f"{prefix} soma {replicate}"])
        neurite = float(row[f"{prefix} neurite {replicate}"])
        values.append(math.log2((neurite + 0.5) / (soma + 0.5)))
    return values


def reconstruct_mikl() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], list[dict[str, object]]]:
    table = pd.read_csv(MIKL_TABLE)
    counts = pd.read_csv(MIKL_COUNTS).rename(columns={"synthetic library sequence": MIKL_FULL_SEQUENCE})
    if len(table) != 47_347 or len(counts) != 47_989:
        raise ValueError("Unexpected Mikl source row count")
    if table[MIKL_FULL_SEQUENCE].duplicated().any() or counts[MIKL_FULL_SEQUENCE].duplicated().any():
        raise ValueError("Mikl complete construct sequences are not unique")
    if int(table[MIKL_FULL_SEQUENCE].isin(set(counts[MIKL_FULL_SEQUENCE])).sum()) != len(table):
        raise ValueError("Mikl analyzed constructs do not map one-to-one to GEO counts")
    table = table.merge(counts, on=MIKL_FULL_SEQUENCE, how="left", validate="one_to_one")
    lengths = table[MIKL_FULL_SEQUENCE].astype(str).str.len()
    if set(lengths) != {198}:
        raise ValueError(f"Unexpected Mikl construct lengths: {sorted(set(lengths))}")
    table["test_sequence"] = table[MIKL_FULL_SEQUENCE].str.upper().str.slice(30, 180)
    if not table["test_sequence"].map(lambda s: len(s) == 150 and bool(DNA.fullmatch(s))).all():
        raise ValueError("Mikl 150-nt test-sequence extraction failed")
    wt = table[table["subset"].eq("wt scanning 50")].copy()
    mutants = table[table["subset"].eq("mut scanning 50")].copy()
    groups = {
        key: rows for key, rows in wt.groupby(["gene name", "position in 3UTR"], dropna=False)
    }
    gene_table = pd.read_csv(MIKL_GENES)
    gene_ids = (
        gene_table.groupby("gene name")["gene ID"]
        .agg(lambda values: ";".join(sorted(set(map(str, values.dropna())))))
        .to_dict()
    )
    records: list[dict[str, object]] = []
    exclusions: list[dict[str, object]] = []
    for source_row, mutant in mutants.iterrows():
        key = (mutant["gene name"], mutant["position in 3UTR"])
        candidates = groups.get(key)
        if candidates is None or candidates.empty:
            exclusions.append(
                {
                    "dataset": "mikl_gse173098",
                    "source_id": int(source_row),
                    "reason": "missing_parent_gene_position_key",
                    "detail": f"{key[0]}|{key[1]}",
                }
            )
            continue
        description = str(mutant["changes"])
        motif = description.split(" replaced by random", 1)[0].upper()
        valid_parent_sequences: list[str] = []
        for parent_sequence in candidates["test_sequence"].unique():
            allowed = motif_positions(parent_sequence, motif)
            differences = {
                i
                for i, (parent_base, mutant_base) in enumerate(
                    zip(parent_sequence, mutant["test_sequence"])
                )
                if parent_base != mutant_base
            }
            if allowed and differences and differences <= allowed:
                valid_parent_sequences.append(parent_sequence)
        if len(valid_parent_sequences) != 1:
            exclusions.append(
                {
                    "dataset": "mikl_gse173098",
                    "source_id": int(source_row),
                    "reason": "no_semantic_parent" if not valid_parent_sequences else "ambiguous_parent",
                    "detail": f"valid_unique_parent_sequences={len(valid_parent_sequences)}",
                }
            )
            continue
        parent_sequence = valid_parent_sequences[0]
        parent_rows = candidates[candidates["test_sequence"].eq(parent_sequence)]
        differences = [
            i
            for i, (parent_base, mutant_base) in enumerate(
                zip(parent_sequence, mutant["test_sequence"])
            )
            if parent_base != mutant_base
        ]
        gene = str(mutant["gene name"])
        position = mutant["position in 3UTR"]
        parent_id = sequence_id(f"mikl:{gene}:{position}", parent_sequence)
        parent_raw = [raw_log_ratios(row, "cad") for _, row in parent_rows.iterrows()]
        parent_cad = np.asarray(parent_raw, dtype=float).mean(axis=0)
        parent_n2a = np.asarray(
            [raw_log_ratios(row, "n2a") for _, row in parent_rows.iterrows()], dtype=float
        ).mean(axis=0)
        mutant_cad = np.asarray(raw_log_ratios(mutant, "cad"), dtype=float)
        mutant_n2a = np.asarray(raw_log_ratios(mutant, "n2a"), dtype=float)
        delta_cad_replicates = mutant_cad - parent_cad
        delta_n2a_replicates = mutant_n2a - parent_n2a
        author_parent_cad = float(parent_rows["logFC(neurite/soma) - CAD"].mean())
        author_parent_n2a = float(parent_rows["logFC(neurite/soma) - Neuro-2a"].mean())
        author_delta_cad = float(mutant["logFC(neurite/soma) - CAD"] - author_parent_cad)
        author_delta_n2a = float(mutant["logFC(neurite/soma) - Neuro-2a"] - author_parent_n2a)
        edit_count = len(differences)
        records.append(
            {
                "dataset": "mikl_gse173098",
                "accession": "GSE173098",
                "source_row": int(source_row),
                "assay": "neurite_soma_mpra",
                "organism": "Mus musculus",
                "cell_type": "CAD;Neuro-2a",
                "gene_id": gene_ids.get(gene, "missing"),
                "gene_name": gene,
                "parent_id": parent_id,
                "parent_sequence": parent_sequence,
                "mutant_id": sequence_id(f"mikl:{source_row}", mutant["test_sequence"]),
                "mutant_sequence": mutant["test_sequence"],
                "edit_distance": edit_count,
                "edit_fraction": edit_count / 150.0,
                "substitution_count": edit_count,
                "insertion_length": 0,
                "deletion_length": 0,
                "edit_cost": edit_count,
                "intervention_class": "motif_random_replacement",
                "edit_tier": edit_tier(edit_count, "motif_random_replacement"),
                "motif_family": motif,
                "edit_positions_1based": ";".join(str(i + 1) for i in differences),
                "parent_barcode_construct_count": int(len(parent_rows)),
                "replicate_count_cad": 3,
                "replicate_count_n2a": 3,
                "localization_effect_cad": author_delta_cad,
                "localization_effect_n2a": author_delta_n2a,
                "effect_uncertainty_cad": standard_error(delta_cad_replicates),
                "effect_uncertainty_n2a": standard_error(delta_n2a_replicates),
                "raw_delta_cad_replicates": ";".join(f"{value:.12g}" for value in delta_cad_replicates),
                "raw_delta_n2a_replicates": ";".join(f"{value:.12g}" for value in delta_n2a_replicates),
                "uncertainty_semantics": "SE of three paired raw-count log2-ratio deltas; pseudocount=0.5",
                "stability_effect_4h": float(
                    mutant["logFC(4h/0h ActD)"] - parent_rows["logFC(4h/0h ActD)"].mean()
                ),
                "stability_effect_24h": float(
                    mutant["logFC(24h/0h ActD)"] - parent_rows["logFC(24h/0h ActD)"].mean()
                ),
                "outcome_valid": True,
                "group_id": parent_id,
                "mapping_method": "gene+position candidates; unique parent whose differences are confined to source-declared motif occurrences",
            }
        )
    interventions = pd.DataFrame.from_records(records)
    outcomes: list[dict[str, object]] = []
    for row in interventions.to_dict("records"):
        for cell, label in (("cad", "CAD"), ("n2a", "Neuro-2a")):
            outcomes.append(
                {
                    **{k: row[k] for k in (
                        "dataset", "accession", "assay", "organism", "gene_id", "gene_name",
                        "parent_id", "parent_sequence", "mutant_id", "mutant_sequence",
                        "edit_distance", "edit_fraction", "edit_cost", "intervention_class",
                        "edit_tier", "motif_family", "group_id", "outcome_valid",
                    )},
                    "cell_type": label,
                    "reporter": "GFP 3UTR MPRA",
                    "localization_effect": row[f"localization_effect_{cell}"],
                    "effect_uncertainty": row[f"effect_uncertainty_{cell}"],
                    "replicate_count": row[f"replicate_count_{cell}"],
                    "outcome_semantics": "mutant minus matched-WT author log2(neurite/soma)",
                    "uncertainty_semantics": row["uncertainty_semantics"],
                    "direction": direction(float(row[f"localization_effect_{cell}"])),
                }
            )
    summary = {
        "raw_geo_constructs": len(counts),
        "analyzed_constructs": len(table),
        "wt_scanning_constructs": len(wt),
        "mutant_scanning_constructs": len(mutants),
        "certified_interventions": len(interventions),
        "certified_genes": int(interventions["gene_name"].nunique()),
        "independent_parent_contexts": int(interventions["parent_id"].nunique()),
        "exact_snv_interventions": int(interventions["edit_distance"].eq(1).sum()),
        "exclusions": Counter(item["reason"] for item in exclusions),
        "direction_cad": Counter(direction(float(v)) for v in interventions["localization_effect_cad"]),
        "direction_n2a": Counter(direction(float(v)) for v in interventions["localization_effect_n2a"]),
        "replicates": {"CAD": 3, "Neuro-2a": 3},
        "test_sequence_definition": "bases 31-180 of 198-nt source oligo (18-nt primer + 12-nt barcode removed; 18-nt reverse primer removed)",
    }
    return interventions, pd.DataFrame(outcomes), summary, exclusions


def parse_fasta_like(path: Path) -> tuple[dict[str, str], dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) % 2:
        raise ValueError("Moffatt supplementary sequence dictionary has an odd line count")
    records: dict[str, str] = {}
    malformed = 0
    for i in range(0, len(lines), 2):
        if not lines[i].startswith(">"):
            raise ValueError(f"Malformed Moffatt FASTA header at line {i + 1}")
        identifier, sequence = lines[i][1:], lines[i + 1].upper()
        if identifier in records:
            raise ValueError(f"Duplicate Moffatt sequence identifier: {identifier}")
        if not DNA.fullmatch(sequence):
            malformed += 1
        records[identifier] = sequence
    audit = {
        "records": len(records),
        "unique_sequences": len(set(records.values())),
        "malformed_sequences": malformed,
        "ends_with_newline": path.read_bytes().endswith(b"\n"),
        "last_identifier": lines[-2][1:] if lines else None,
        "last_sequence_length": len(lines[-1]) if lines else None,
    }
    return records, audit


def reconstruct_moffatt_parents(sequences: dict[str, str]) -> tuple[dict[str, str], dict[str, object]]:
    inserts = {
        identifier: sequence[20:-20]
        for identifier, sequence in sequences.items()
        if len(sequence) == 300
    }
    parent_calls: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    # Sufficiency coordinates are 1-based inclusive; the preserved parent window is first.
    suff_pattern = re.compile(r"^(\w+)_(\d+)\|(\d+)\+suff$")
    for identifier, child in inserts.items():
        match = suff_pattern.fullmatch(identifier)
        if not match:
            continue
        gene, start, end = match.groups()
        start_i, end_i = int(start), int(end)
        for position, base in zip(range(start_i - 1, end_i), child[: end_i - start_i + 1]):
            parent_calls[gene.lower()][position].append(base)
    suff_parents: dict[str, str] = {}
    for gene, calls in parent_calls.items():
        if set(calls) != set(range(260)):
            raise ValueError(f"Incomplete Moffatt sufficiency parent reconstruction: {gene}")
        if any(len(set(calls[position])) != 1 for position in range(260)):
            raise ValueError(f"Conflicting Moffatt sufficiency parent bases: {gene}")
        suff_parents[gene] = "".join(calls[position][0] for position in range(260))
    # Necessity coordinates are 1-based half-open. The retained parent is followed by padding.
    parent_calls = defaultdict(lambda: defaultdict(list))
    ness_pattern = re.compile(r"^(\w+)_(\d+):(\d+)\+ness$")
    for identifier, child in inserts.items():
        match = ness_pattern.fullmatch(identifier)
        if not match:
            continue
        gene, start, end = match.groups()
        start_i, end_i = int(start) - 1, int(end) - 1
        retained = child[: 260 - (end_i - start_i)]
        original_positions = list(range(start_i)) + list(range(end_i, 260))
        for position, base in zip(original_positions, retained):
            parent_calls[gene.lower()][position].append(base)
    ness_parents: dict[str, str] = {}
    for gene, calls in parent_calls.items():
        if set(calls) != set(range(260)):
            raise ValueError(f"Incomplete Moffatt necessity parent reconstruction: {gene}")
        if any(len(set(calls[position])) != 1 for position in range(260)):
            raise ValueError(f"Conflicting Moffatt necessity parent bases: {gene}")
        ness_parents[gene] = "".join(calls[position][0] for position in range(260))
    # Mutation simple windows recover the same six parents without using outcomes.
    mutation_calls = defaultdict(lambda: defaultdict(list))
    mutation_pattern = re.compile(r"^(\w+)_(\d+):(\d+)_([123])\+mut$")
    for identifier, child in inserts.items():
        match = mutation_pattern.fullmatch(identifier)
        if not match:
            continue
        gene, start, end, _ = match.groups()
        start_i, end_i = int(start) - 1, int(end)
        for position, base in enumerate(child):
            if not start_i <= position < end_i:
                mutation_calls[gene.lower()][position].append(base)
    mutation_parents: dict[str, str] = {}
    for gene, calls in mutation_calls.items():
        if set(calls) != set(range(260)):
            raise ValueError(f"Incomplete Moffatt mutation parent reconstruction: {gene}")
        if any(len(set(calls[position])) != 1 for position in range(260)):
            raise ValueError(f"Conflicting Moffatt mutation parent bases: {gene}")
        mutation_parents[gene] = "".join(calls[position][0] for position in range(260))
    for gene in set(suff_parents) & set(mutation_parents):
        if suff_parents[gene] != mutation_parents[gene]:
            raise ValueError(f"Moffatt sufficiency/mutation parent disagreement: {gene}")
    for gene in set(ness_parents) & set(mutation_parents):
        if ness_parents[gene] != mutation_parents[gene]:
            raise ValueError(f"Moffatt necessity/mutation parent disagreement: {gene}")
    parents = dict(ness_parents)
    parents.update(mutation_parents)
    audit = {
        "sufficiency_parent_genes": sorted(suff_parents),
        "necessity_parent_genes": sorted(ness_parents),
        "mutation_parent_genes": sorted(mutation_parents),
        "unique_parent_sequences": len(set(parents.values())),
        "parent_genes": sorted(parents),
        "shared_parent_exact_matches": sorted(set(ness_parents) & set(mutation_parents)),
    }
    return parents, audit


def load_moffatt_counts() -> tuple[dict[tuple[str, str, str, int], pd.DataFrame], dict[str, object]]:
    manifest = pd.read_csv(MOFF_SAMPLE_MANIFEST)
    samples: dict[tuple[str, str, str, int], pd.DataFrame] = {}
    row_counts: dict[str, int] = {}
    duplicate_keys = 0
    for record in manifest.to_dict("records"):
        path = MOFF_COUNT_DIR / record["processed_count_filename"]
        frame = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=["oligo_key", "read_count", "umi_count"],
            dtype={"oligo_key": str, "read_count": int, "umi_count": int},
        )
        duplicate_keys += int(frame["oligo_key"].duplicated().sum())
        key = (
            str(record["assay_family"]),
            str(record["reporter"]),
            str(record["compartment"]),
            int(record["biological_replicate"]),
        )
        if key in samples:
            raise ValueError(f"Duplicate Moffatt sample design key: {key}")
        samples[key] = frame.set_index("oligo_key")
        row_counts[path.name] = len(frame)
    if len(samples) != 80 or duplicate_keys:
        raise ValueError(f"Moffatt count integrity failure: samples={len(samples)}, duplicates={duplicate_keys}")
    return samples, {
        "sample_files": len(samples),
        "duplicate_sample_oligo_keys": duplicate_keys,
        "minimum_rows_per_sample": min(row_counts.values()),
        "maximum_rows_per_sample": max(row_counts.values()),
    }


def moffatt_raw_ratios(
    samples: dict[tuple[str, str, str, int], pd.DataFrame],
    family: str,
    reporter: str,
    oligo_key: str,
) -> list[float]:
    values: list[float] = []
    for replicate in range(1, 5):
        soma = samples[(family, reporter, "soma", replicate)]
        neurite = samples[(family, reporter, "neurite", replicate)]
        if oligo_key not in soma.index or oligo_key not in neurite.index:
            continue
        soma_umi = float(soma.at[oligo_key, "umi_count"])
        neurite_umi = float(neurite.at[oligo_key, "umi_count"])
        values.append(math.log2((neurite_umi + 0.5) / (soma_umi + 0.5)))
    return values


def declared_ranges(identifier: str) -> list[tuple[int, int]]:
    core = identifier.split("+", 1)[0]
    return [(int(start), int(end)) for start, end in re.findall(r"(\d+):(\d+)", core)]


def reconstruct_moffatt() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], list[dict[str, object]]]:
    if sha256(MOFF_ARCHIVE) != MOFF_ARCHIVE_SHA256:
        raise ValueError("Moffatt archive hash changed after unseal")
    sequences, fasta_audit = parse_fasta_like(MOFF_FASTA)
    parents, parent_audit = reconstruct_moffatt_parents(sequences)
    samples, count_audit = load_moffatt_counts()
    table_specs = [
        ("sufficiency", MOFF_TABLES[0], "gfp_log2fc", "ff_log2fc"),
        ("necessity", MOFF_TABLES[1], "gfp_log2fc", "ff_log2fc"),
        ("mutation", MOFF_TABLES[2], "log2fc_gfp", "log2fc_ff"),
        ("shuffle", MOFF_TABLES[3], "log2fc_gfp", "log2fc_ff"),
        ("shape", MOFF_TABLES[4], "gfp_log2fc", "ff_log2fc"),
    ]
    suffixes = {
        "sufficiency": "suff",
        "necessity": "ness",
        "mutation": "mut",
        "shuffle": "shuff",
        "shape": "shape",
    }
    records: list[dict[str, object]] = []
    exclusions: list[dict[str, object]] = []
    source_rows = 0
    for family, path, gfp_column, firefly_column in table_specs:
        table = pd.read_csv(path)
        source_rows += len(table)
        if table["oligo"].duplicated().any():
            raise ValueError(f"Duplicate Moffatt outcome IDs in {path.name}")
        for source_row, row in table.iterrows():
            identifier = str(row["oligo"])
            sequence = sequences.get(identifier)
            if sequence is None:
                exclusions.append(
                    {
                        "dataset": "moffatt_gse334718",
                        "source_id": f"{path.name}:{source_row}",
                        "reason": "missing_sequence_dictionary_entry",
                        "detail": identifier,
                    }
                )
                continue
            if len(sequence) != 300 or not DNA.fullmatch(sequence):
                exclusions.append(
                    {
                        "dataset": "moffatt_gse334718",
                        "source_id": f"{path.name}:{source_row}",
                        "reason": "invalid_fixed_length_oligo",
                        "detail": f"{identifier}|length={len(sequence)}",
                    }
                )
                continue
            child = sequence[20:-20]
            gene = re.split(r"[_|]", identifier, maxsplit=1)[0].lower()
            parent = parents.get(gene)
            if parent is None:
                exclusions.append(
                    {
                        "dataset": "moffatt_gse334718",
                        "source_id": f"{path.name}:{source_row}",
                        "reason": "missing_reconstructable_parent",
                        "detail": identifier,
                    }
                )
                continue
            design_valid = True
            operation_size = 0
            deletion_length = 0
            insertion_length = 0
            operation_class = family
            ranges = declared_ranges(identifier)
            if family == "sufficiency":
                match = re.fullmatch(r"\w+_(\d+)\|(\d+)\+suff", identifier)
                if not match:
                    design_valid = False
                else:
                    start, end = map(int, match.groups())
                    preserved = end - start + 1
                    design_valid = child.startswith(parent[start - 1 : end])
                    operation_size = 260 - preserved
                    deletion_length = operation_size
                    insertion_length = operation_size
                    operation_class = "sufficiency_background_replacement"
            elif family == "necessity":
                match = re.fullmatch(r"\w+_(\d+):(\d+)\+ness", identifier)
                if not match:
                    design_valid = False
                else:
                    start, end = map(int, match.groups())
                    start_i, end_i = start - 1, end - 1
                    operation_size = end_i - start_i
                    expected = parent[:start_i] + parent[end_i:]
                    design_valid = child.startswith(expected)
                    deletion_length = operation_size
                    insertion_length = operation_size
                    operation_class = "necessity_deletion_with_inactive_padding"
            elif family in {"mutation", "shuffle"}:
                differences = {i + 1 for i, (a, b) in enumerate(zip(parent, child)) if a != b}
                allowed = {
                    position
                    for start, end in ranges
                    for position in range(start, end + 1)
                }
                design_valid = bool(differences) and (not allowed or differences <= allowed)
                operation_size = sum(end - start + 1 for start, end in ranges)
                operation_class = "random_substitution" if family == "mutation" else "regional_shuffle"
            elif family == "shape":
                operation_size = sum(a != b for a, b in zip(parent, child))
                design_valid = operation_size > 0 or "wt_" in identifier
                operation_class = "shape_structure_perturbation"
            if not design_valid:
                exclusions.append(
                    {
                        "dataset": "moffatt_gse334718",
                        "source_id": f"{path.name}:{source_row}",
                        "reason": "design_operation_mismatch",
                        "detail": identifier,
                    }
                )
                continue
            gfp_effect = float(row[gfp_column]) if pd.notna(row[gfp_column]) else math.nan
            firefly_effect = float(row[firefly_column]) if pd.notna(row[firefly_column]) else math.nan
            if not (math.isfinite(gfp_effect) or math.isfinite(firefly_effect)):
                exclusions.append(
                    {
                        "dataset": "moffatt_gse334718",
                        "source_id": f"{path.name}:{source_row}",
                        "reason": "both_reporter_outcomes_missing",
                        "detail": identifier,
                    }
                )
                continue
            differences = [i for i, (a, b) in enumerate(zip(parent, child)) if a != b]
            actual_edit = len(differences)
            # For deletion/replacement designs, cost counts removed and inserted bases.
            edit_cost = (
                deletion_length + insertion_length
                if family in {"sufficiency", "necessity"}
                else actual_edit
            )
            oligo_key = identifier.rsplit("+", 1)[0]
            gfp_ratios = moffatt_raw_ratios(samples, family, "gfp", oligo_key)
            firefly_ratios = moffatt_raw_ratios(samples, family, "firefly", oligo_key)
            gfp_raw_valid = len(gfp_ratios) >= 2
            firefly_raw_valid = len(firefly_ratios) >= 2
            parent_id = sequence_id(f"moffatt:{gene}", parent)
            records.append(
                {
                    "dataset": "moffatt_gse334718",
                    "accession": "GSE334718;PRJNA1476227",
                    "source_table": path.name,
                    "source_row": int(source_row),
                    "assay": f"{family}_neurite_soma_mpra",
                    "organism": "Mus musculus",
                    "cell_type": "CAD",
                    "gene_id": "missing",
                    "gene_name": gene,
                    "parent_id": parent_id,
                    "parent_sequence": parent,
                    "mutant_id": identifier,
                    "mutant_sequence": child,
                    "edit_distance": actual_edit,
                    "edit_fraction": actual_edit / 260.0,
                    "substitution_count": actual_edit,
                    "insertion_length": insertion_length,
                    "deletion_length": deletion_length,
                    "operation_size": operation_size,
                    "edit_cost": edit_cost,
                    "intervention_class": operation_class,
                    "edit_tier": edit_tier(edit_cost, operation_class),
                    "motif_family": "not_applicable" if family != "shape" else "source_shape_element",
                    "reporter": "GFP;Firefly",
                    "localization_effect_gfp": gfp_effect,
                    "localization_effect_firefly": firefly_effect,
                    "effect_uncertainty_gfp": standard_error(gfp_ratios) if gfp_raw_valid else math.nan,
                    "effect_uncertainty_firefly": standard_error(firefly_ratios) if firefly_raw_valid else math.nan,
                    "raw_ratio_mean_gfp": float(np.mean(gfp_ratios)) if gfp_raw_valid else math.nan,
                    "raw_ratio_mean_firefly": float(np.mean(firefly_ratios)) if firefly_raw_valid else math.nan,
                    "raw_ratio_min_gfp": min(gfp_ratios) if gfp_raw_valid else math.nan,
                    "raw_ratio_max_gfp": max(gfp_ratios) if gfp_raw_valid else math.nan,
                    "raw_ratio_min_firefly": min(firefly_ratios) if firefly_raw_valid else math.nan,
                    "raw_ratio_max_firefly": max(firefly_ratios) if firefly_raw_valid else math.nan,
                    "raw_ratio_replicates_gfp": ";".join(f"{value:.12g}" for value in gfp_ratios),
                    "raw_ratio_replicates_firefly": ";".join(f"{value:.12g}" for value in firefly_ratios),
                    "raw_ratio_status_gfp": "valid_diagnostic" if gfp_raw_valid else "insufficient_paired_replicates",
                    "raw_ratio_status_firefly": "valid_diagnostic" if firefly_raw_valid else "insufficient_paired_replicates",
                    "replicate_count_gfp": len(gfp_ratios),
                    "replicate_count_firefly": len(firefly_ratios),
                    "uncertainty_semantics": "SE/range of >=2 available unnormalized raw UMI log2(neurite/soma) ratios; pseudocount=0.5; diagnostic only because author effect is WT-normalized",
                    "outcome_valid": True,
                    "group_id": parent_id,
                    "mapping_method": "exact outcome oligo ID to supplementary sequence dictionary; operation validated against reconstructed 260-nt parent",
                }
            )
    interventions = pd.DataFrame.from_records(records)
    outcomes: list[dict[str, object]] = []
    for row in interventions.to_dict("records"):
        for reporter, label in (("gfp", "GFP"), ("firefly", "Firefly")):
            value = float(row[f"localization_effect_{reporter}"])
            if not math.isfinite(value):
                continue
            outcomes.append(
                {
                    **{k: row[k] for k in (
                        "dataset", "accession", "assay", "organism", "cell_type", "gene_id",
                        "gene_name", "parent_id", "parent_sequence", "mutant_id", "mutant_sequence",
                        "edit_distance", "edit_fraction", "edit_cost", "intervention_class",
                        "edit_tier", "motif_family", "group_id", "outcome_valid",
                    )},
                    "reporter": label,
                    "localization_effect": value,
                    "effect_uncertainty": row[f"effect_uncertainty_{reporter}"],
                    "replicate_count": row[f"replicate_count_{reporter}"],
                    "outcome_semantics": "author WT-normalized log2 neurite enrichment",
                    "uncertainty_semantics": row["uncertainty_semantics"],
                    "direction": direction(value),
                }
            )
    summary = {
        "source_outcome_rows": source_rows,
        "certified_interventions": len(interventions),
        "certified_parent_elements": int(interventions["parent_id"].nunique()),
        "certified_gene_labels": int(interventions["gene_name"].nunique()),
        "intervention_classes": Counter(interventions["intervention_class"]),
        "source_fasta": fasta_audit,
        "parent_reconstruction": parent_audit,
        "count_files": count_audit,
        "exclusions": Counter(item["reason"] for item in exclusions),
        "replicate_design": "four biological replicates per assay family × reporter × compartment",
        "reporter_finite_outcomes": {
            "gfp": int(interventions["localization_effect_gfp"].notna().sum()),
            "firefly": int(interventions["localization_effect_firefly"].notna().sum()),
        },
        "raw_ratio_diagnostics_with_at_least_two_paired_replicates": {
            "gfp": int(interventions["raw_ratio_status_gfp"].eq("valid_diagnostic").sum()),
            "firefly": int(interventions["raw_ratio_status_firefly"].eq("valid_diagnostic").sum()),
        },
        "direction_gfp": Counter(direction(float(v)) for v in interventions["localization_effect_gfp"]),
        "direction_firefly": Counter(
            direction(float(v)) for v in interventions["localization_effect_firefly"]
        ),
    }
    return interventions, pd.DataFrame(outcomes), summary, exclusions


def reconstruct_tdp() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], list[dict[str, object]]]:
    pairs = pd.read_csv(TDP_PAIRS)
    audit = json.loads(TDP_AUDIT.read_text(encoding="utf-8"))
    if len(pairs) != 4_566 or audit["historical_pairing_error_found"]:
        raise ValueError("TDP source audit no longer matches the frozen exact-ID reconstruction")
    computed = pairs.apply(
        lambda row: sum(a != b for a, b in zip(row["parent_sequence"], row["mutant_sequence"])),
        axis=1,
    )
    if not np.array_equal(computed.to_numpy(), pairs["edited_base_count"].to_numpy()):
        raise ValueError("TDP declared edit counts do not match exact sequences")
    records: list[dict[str, object]] = []
    outcomes: list[dict[str, object]] = []
    for row in pairs.to_dict("records"):
        edit_count = int(row["edited_base_count"])
        record = {
            "dataset": "tdp43_gse288185",
            "accession": "GSE288185;S-SCDT-10_1038-S44318-025-00653-4",
            "source_row": int(row["source_figure4e_row"]),
            "assay": "tdp43_motif_neurite_soma_mpra",
            "organism": "Mus musculus",
            "cell_type": "CAD",
            "gene_id": row["gene_id"],
            "gene_name": row["gene_name"],
            "parent_id": row["parent_id"],
            "parent_sequence": row["parent_sequence"],
            "mutant_id": row["mutant_id"],
            "mutant_sequence": row["mutant_sequence"],
            "edit_distance": edit_count,
            "edit_fraction": edit_count / len(row["parent_sequence"]),
            "substitution_count": edit_count,
            "insertion_length": 0,
            "deletion_length": 0,
            "edit_cost": edit_count,
            "intervention_class": "tdp43_motif_complement_replacement",
            "edit_tier": edit_tier(edit_count, "tdp43_motif_complement_replacement"),
            "motif_family": "TDP-43 UG-rich motif",
            "reporter": "MPRA reporter",
            "localization_effect": float(row["delta_localization"]),
            "effect_uncertainty": math.nan,
            "replicate_count": 4,
            "uncertainty_semantics": "missing at pair level in processed Figure 4E; EV3 contains four biological replicates",
            "outcome_valid": True,
            "group_id": row["parent_id"],
            "mapping_method": "exact parent_id and mutant_id; both exact 260-nt sequences verified against EV8",
        }
        records.append(record)
        outcomes.append(
            {
                **{k: record[k] for k in (
                    "dataset", "accession", "assay", "organism", "cell_type", "gene_id",
                    "gene_name", "parent_id", "parent_sequence", "mutant_id", "mutant_sequence",
                    "edit_distance", "edit_fraction", "edit_cost", "intervention_class",
                    "edit_tier", "motif_family", "group_id", "outcome_valid",
                )},
                "reporter": record["reporter"],
                "localization_effect": record["localization_effect"],
                "effect_uncertainty": math.nan,
                "replicate_count": 4,
                "outcome_semantics": "mutant minus WT author processed log2(neurite/soma)",
                "uncertainty_semantics": record["uncertainty_semantics"],
                "direction": direction(record["localization_effect"]),
            }
        )
    interventions = pd.DataFrame(records)
    summary = {
        "certified_interventions": len(interventions),
        "certified_genes": int(interventions["gene_id"].nunique()),
        "independent_parent_contexts": int(interventions["parent_id"].nunique()),
        "replicate_design": "four biological replicates in EV3",
        "pair_level_uncertainty": "not available in Figure 4E processed source",
        "direction": Counter(direction(float(v)) for v in interventions["localization_effect"]),
        "slamseq_quarantine_duplicate_keys": audit["slam_raw_duplicate_sample_oligo_keys"],
        "rbns_exact_pairs": audit["rbns_exact_both_construct_pairs"],
        "stability_exact_pairs": audit["stability_source_pairs"],
    }
    return interventions, pd.DataFrame(outcomes), summary, []


def json_safe(value: object) -> object:
    if isinstance(value, Counter):
        return dict(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    return value


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mikl, mikl_outcomes, mikl_summary, mikl_exclusions = reconstruct_mikl()
    tdp, tdp_outcomes, tdp_summary, tdp_exclusions = reconstruct_tdp()
    moffatt, moffatt_outcomes, moffatt_summary, moffatt_exclusions = reconstruct_moffatt()
    mikl.to_csv(OUT / "mikl_interventions.csv.gz", index=False, compression=DETERMINISTIC_GZIP)
    tdp.to_csv(OUT / "tdp_interventions.csv.gz", index=False, compression=DETERMINISTIC_GZIP)
    moffatt.to_csv(OUT / "moffatt_interventions.csv.gz", index=False, compression=DETERMINISTIC_GZIP)
    common = pd.concat([mikl_outcomes, tdp_outcomes, moffatt_outcomes], ignore_index=True)
    common.to_csv(
        OUT / "common_intervention_outcomes.csv.gz",
        index=False,
        compression=DETERMINISTIC_GZIP,
    )
    exclusions = pd.DataFrame(mikl_exclusions + tdp_exclusions + moffatt_exclusions)
    exclusions.to_csv(OUT / "exclusion_audit.csv", index=False)
    interventions = pd.concat(
        [
            mikl[["dataset", "mutant_id", "parent_id", "gene_name", "edit_tier", "edit_distance", "edit_cost"]],
            tdp[["dataset", "mutant_id", "parent_id", "gene_name", "edit_tier", "edit_distance", "edit_cost"]],
            moffatt[["dataset", "mutant_id", "parent_id", "gene_name", "edit_tier", "edit_distance", "edit_cost"]],
        ],
        ignore_index=True,
    )
    edit_distribution = (
        interventions.groupby(["dataset", "edit_tier"], dropna=False)
        .agg(
            intervention_count=("mutant_id", "size"),
            parent_contexts=("parent_id", "nunique"),
            minimum_edit_distance=("edit_distance", "min"),
            median_edit_distance=("edit_distance", "median"),
            maximum_edit_distance=("edit_distance", "max"),
            minimum_edit_cost=("edit_cost", "min"),
            median_edit_cost=("edit_cost", "median"),
            maximum_edit_cost=("edit_cost", "max"),
        )
        .reset_index()
    )
    edit_distribution.to_csv(OUT / "edit_distribution.csv", index=False)
    normalized_genes = set(interventions["gene_name"].astype(str).str.lower())
    summary = {
        "phase": "v4_phaseA",
        "generated_from_git_commit": git_commit(),
        "nzip_outcomes_used": False,
        "astrocyte_outcomes_opened": False,
        "historical_models_rerun": False,
        "mikl": mikl_summary,
        "tdp": tdp_summary,
        "moffatt": moffatt_summary,
        "arora_representation_support": {
            "accession": "GSE183192",
            "processed_constructs": 7360,
            "complete_four_assay_constructs": 7115,
            "biological_insert_length": 260,
            "independent_gene_groups": 14,
            "per_assay_nonmissing_range": [7217, 7326],
            "role": "forward representation support only; not a parent-mutant intervention source",
            "pooling_constraint": "retain GFP/Firefly and CAD/Neuro-2a assay-specific heads",
        },
        "development_totals": {
            "certified_interventions": len(interventions),
            "unique_gene_labels_casefolded": len(normalized_genes),
            "independent_parent_contexts": int(interventions["parent_id"].nunique()),
            "exact_snv": int(interventions["edit_tier"].eq("exact_snv").sum()),
            "small_local_edit": int(interventions["edit_tier"].eq("small_local_edit").sum()),
            "motif_scale_edit": int(interventions["edit_tier"].eq("motif_scale_edit").sum()),
            "regional_edit": int(interventions["edit_tier"].eq("regional_edit").sum()),
            "large_element_edit": int(interventions["edit_tier"].eq("large_element_edit").sum()),
            "common_outcome_rows": len(common),
            "exclusion_rows": len(exclusions),
        },
    }
    (OUT / "phaseA_summary.json").write_text(
        json.dumps(json_safe(summary), indent=2) + "\n", encoding="utf-8"
    )
    source_paths = [
        MIKL_TABLE,
        MIKL_GENES,
        MIKL_COUNTS,
        TDP_PAIRS,
        TDP_AUDIT,
        ARORA_AUDIT,
        ARORA_DIR / "SupplementaryFile1.txt",
        *(ARORA_DIR / f"TableS{i}.xlsx" for i in range(1, 5)),
        MOFF_ARCHIVE,
        MOFF_FASTA,
        *MOFF_TABLES,
        MOFF_SAMPLE_MANIFEST,
        Path(__file__),
        *(path for path in MOFF_CODE_REFERENCES if path.exists()),
        *sorted(MOFF_COUNT_DIR.glob("*.gz")),
    ]
    source_manifest = {
        "phase": "v4_phaseA",
        "git_commit_at_run": git_commit(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "dataset_records": {
            "mikl_gse173098": {
                "accession": "GSE173098",
                "doi": "10.1093/nar/gkac806",
                "mapping": "unique exact 198-nt construct join, biological bases 31-180, then gene+position and source-declared motif semantic parent reconstruction",
                "replicates": "three paired soma/neurite replicates in each of CAD and Neuro-2a",
                "duplicate_policy": "complete construct sequences must be unique in both analyzed table and GEO count matrix",
                "outcome_semantics": "mutant minus parent author logFC(neurite/soma), with raw-count paired-delta SE retained separately",
            },
            "tdp43_gse288185": {
                "accession": "GSE288185;S-SCDT-10_1038-S44318-025-00653-4",
                "doi": "10.64898/2025.05.30.656993",
                "mapping": "exact parent_id and mutant_id to exact 260-nt EV8 sequences",
                "replicates": "four biological replicates in EV3",
                "duplicate_policy": "SLAM-seq raw stability table remains quarantined because sample+oligo keys are non-unique",
                "outcome_semantics": "mutant minus WT processed Figure 4E log2(neurite/soma); pair-level uncertainty unavailable",
            },
            "moffatt_gse334718": {
                "accession": "GSE334718;PRJNA1476227",
                "doi": "10.64898/2026.06.09.731215",
                "mapping": "exact outcome oligo ID to sequence dictionary; outcome-blind parent reconstruction and operation validation",
                "replicates": "four biological replicates per assay family, reporter, and compartment",
                "duplicate_policy": "outcome IDs and each sample's oligo keys must be unique; unmapped or operation-inconsistent rows are excluded",
                "outcome_semantics": "author WT-normalized log2 neurite enrichment; raw UMI ratio SE is diagnostic and is not the author-effect SE",
            },
            "arora_gse183192": {
                "accession": "GSE183192",
                "doi": "10.1093/nar/gkac763",
                "mapping": "7,360 result IDs map one-to-one to labeled 260-nt inserts",
                "replicates": "quadruplicate soma/neurite fractions across reporter and cell-line assays",
                "duplicate_policy": "forward tiles only; no parent-mutant conversion attempted",
                "outcome_semantics": "forward localization activity; representation support only",
            },
        },
        "source_repositories": {
            "charliemoffatt/sufficiency-mpra-analysis": {
                "url": "https://github.com/charliemoffatt/sufficiency-mpra-analysis",
                "commit": "cb05e45d608b9ef51f22a25df8b14ebcbfec9c22",
            },
            "charliemoffatt/LE_SHAPE_Summary": {
                "url": "https://github.com/charliemoffatt/LE_SHAPE_Summary",
                "commit": "329ad93801587ed8c29053c2c36500fb9dd9cbec",
            },
            "TaliaferroLab/peak-oligo": {
                "url": "https://github.com/TaliaferroLab/peak-oligo",
                "status": "declared by manuscript but not publicly resolvable during the 2026-08-31 audit",
            },
        },
        "scope_guards": {
            "nzip_outcomes_used": False,
            "astrocyte_outcomes_opened": False,
            "historical_models_rerun": False,
            "model_fit_or_tuning_performed": False,
        },
        "sources": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in source_paths
        ],
        "outputs": {},
        "missing_values": "Preserved as blank/NaN with explicit semantics; no sentinel interpreted as an outcome.",
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "source_manifest.json":
            source_manifest["outputs"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    (OUT / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(json_safe(summary), indent=2))


if __name__ == "__main__":
    main()
