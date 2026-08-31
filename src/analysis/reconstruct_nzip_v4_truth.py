"""Reconstruct the N-zip v4 experimental truth layer without model evaluation.

This module is intentionally independent of the historical pairing loader.  It
uses exact sequence identities, preserves missing values, and never overwrites
historical RNAddress artifacts.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "nzip"
    / "supplementary"
    / "41593_2022_1243_MOESM2_ESM.xlsx"
)
FASTQ_DIR = ROOT / "data" / "raw" / "nzip" / "fastq_v3_5r"
DESIGN_OUT = ROOT / "data" / "processed" / "nzip_mutagenesis_design_v1.csv.gz"
COUNTS_OUT = ROOT / "data" / "processed" / "nzip_mutagenesis_raw_counts_v1.csv.gz"
RESULTS_DIR = ROOT / "results" / "v3_5r"
IDENTITY_OUT = RESULTS_DIR / "sequence_identity_groups.csv"
AUTHOR_FASTA = ROOT / "data" / "interim" / "nzip_v3_5r_canonical_library.fa"
CPP_COUNT_DIR = ROOT / "data" / "interim" / "nzip_cpp_full"
CPP_EXACT_AUDIT_DIR = ROOT / "data" / "interim" / "nzip_cpp_exact"

WORKBOOK_SHA256 = "15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9"
PAPER_ADAPTER = "TTCGATATCCGCATGCTAGC"
MPRNA_DEFAULT_ADAPTER = "TTGATTCGATATCCGCATGCTAGC"
DNA_RE = re.compile(r"^[ACGT]+$")

RUNS = {
    "ERR7337821": (1, "neurite"),
    "ERR7337822": (2, "neurite"),
    "ERR7337823": (3, "neurite"),
    "ERR7337824": (1, "soma"),
    "ERR7337825": (2, "soma"),
    "ERR7337826": (3, "soma"),
}

ENA_EXPECTED = {
    "ERR7337821": (1_400_843_603, "fd80b90536363964701995c679a04df0", 31_033_728),
    "ERR7337822": (964_822_552, "6b3edb97bb7890f058f057552cf3801d", 21_444_343),
    "ERR7337823": (1_274_894_586, "0f33bdb125acedfa826b846cd9b97f6b", 28_271_727),
    "ERR7337824": (1_417_520_067, "edb6203f498f761cee58ba3ef4b6be0d", 31_333_875),
    "ERR7337825": (1_121_848_198, "a9123739f929ecacad57571d2e6aeb8e", 24_605_069),
    "ERR7337826": (1_272_136_960, "55b24196cc0418c1e804f889f7d1b695", 28_143_744),
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> tuple[str, str]:
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def normalize_sequence(value: object) -> str:
    """Apply the frozen sequence canonicalization rule."""

    if pd.isna(value):
        raise ValueError("Missing N-zip design sequence")
    sequence = str(value).strip().upper().replace("U", "T")
    if not sequence or DNA_RE.fullmatch(sequence) is None:
        raise ValueError(f"Invalid N-zip design sequence: {value!r}")
    return sequence


def stable_gzip_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a deterministic CSV gzip (fixed gzip timestamp)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )


def _text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


def _classify_design_row(mutation_type: str) -> str:
    return {
        "WT": "wt",
        "sgl": "exact_snv_candidate",
        "kmer2": "multi_base_replacement",
        "kmer5": "multi_base_replacement",
        "kmer10": "multi_base_replacement",
        "del": "deletion",
        "scr": "scramble",
        "mut": "other_documented_mutation",
    }.get(mutation_type, "other_documented_design")


def build_design_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build all 6,266 design rows and canonical sequence identity groups."""

    if sha256_file(WORKBOOK) != WORKBOOK_SHA256:
        raise ValueError("N-zip source workbook SHA-256 changed")
    source = pd.read_excel(WORKBOOK, sheet_name="Supp_Table_2a", skiprows=2)
    if len(source) != 6_266:
        raise ValueError(f"Expected 6,266 design rows, found {len(source)}")

    frame = pd.DataFrame()
    frame["design_row_id"] = [f"nzip2a_{i:04d}" for i in range(len(source))]
    frame["source_table"] = "Supp_Table_2a"
    frame["source_data_row_0based"] = range(len(source))
    frame["source_excel_row_1based"] = range(4, 4 + len(source))
    frame["source_gene_id"] = source["Source gene id"].map(_text)
    frame["source_gene_name"] = source["Source gene name"].map(_text)
    frame["source_tile_id"] = source["Source tile id"].map(_text)
    frame["original_size"] = pd.to_numeric(source["size"], errors="raise").astype(int)
    frame["mutation_type"] = source["Mutation type"].map(_text)
    frame["mutation_position"] = source["Mutation position"].map(_text)
    frame["original_sequence"] = source["Sequence"].astype(str)
    frame["normalized_sequence"] = source["Sequence"].map(normalize_sequence)
    frame["sequence_length"] = frame["normalized_sequence"].str.len().astype(int)
    frame["sequence_sha256"] = frame["normalized_sequence"].map(
        lambda value: hashlib.sha256(value.encode("ascii")).hexdigest()
    )
    frame["sequence_id"] = "nzipseq_" + frame["sequence_sha256"]
    frame["notes"] = source["notes"].map(_text)
    frame["intervention_class"] = frame["mutation_type"].map(_classify_design_row)
    frame["is_wt"] = frame["mutation_type"].eq("WT")
    frame["is_scramble"] = frame["mutation_type"].eq("scr")

    parent_key = ["source_gene_id", "source_gene_name", "source_tile_id"]
    wt = frame.loc[frame["is_wt"], parent_key + ["design_row_id", "normalized_sequence", "sequence_id"]]
    if wt.duplicated(parent_key).any():
        raise ValueError("WT parent key is not unique in Supplementary Table 2a")
    wt = wt.rename(
        columns={
            "design_row_id": "intended_parent_design_row_id",
            "normalized_sequence": "intended_parent_sequence",
            "sequence_id": "intended_parent_sequence_id",
        }
    )
    frame = frame.merge(wt, on=parent_key, how="left", validate="many_to_one", sort=False)

    exact_snv: list[bool] = []
    edit_position: list[object] = []
    reference: list[object] = []
    alternate: list[object] = []
    edit_size: list[object] = []
    for row in frame.itertuples(index=False):
        parent = row.intended_parent_sequence
        mutant = row.normalized_sequence
        if not isinstance(parent, str):
            diffs: list[int] = []
            size: object = pd.NA
        elif len(parent) == len(mutant):
            diffs = [i for i, (a, b) in enumerate(zip(parent, mutant)) if a != b]
            size = len(diffs)
        else:
            diffs = []
            size = abs(len(parent) - len(mutant))
        is_snv = row.mutation_type == "sgl" and len(diffs) == 1
        exact_snv.append(is_snv)
        edit_position.append(diffs[0] if is_snv else pd.NA)
        reference.append(parent[diffs[0]] if is_snv else pd.NA)
        alternate.append(mutant[diffs[0]] if is_snv else pd.NA)
        edit_size.append(size)
    frame["exact_snv"] = exact_snv
    frame["edit_position_0based"] = pd.array(edit_position, dtype="Int64")
    frame["edit_position_1based"] = frame["edit_position_0based"] + 1
    frame["reference_nt"] = reference
    frame["alternate_nt"] = alternate
    frame["observed_edit_size"] = pd.array(edit_size, dtype="Int64")

    sizes = frame.groupby("sequence_id", sort=True)["design_row_id"].transform("size")
    frame["number_design_ids_sharing_sequence"] = sizes.astype(int)
    duplicate_ids = sorted(frame.loc[sizes.gt(1), "sequence_id"].unique())
    group_number = {sequence_id: i + 1 for i, sequence_id in enumerate(duplicate_ids)}
    frame["duplicate_sequence_group"] = frame["sequence_id"].map(
        lambda value: f"dupseq_{group_number[value]:03d}" if value in group_number else ""
    )

    duplicate_rows: list[dict[str, object]] = []
    for sequence_id, group in frame.loc[sizes.gt(1)].groupby("sequence_id", sort=True):
        types = set(group["mutation_type"])
        if types == {"WT"}:
            duplicate_class = "wt_duplicate"
        elif "sgl" in types and len(types) > 1:
            duplicate_class = "convergent_snv_and_multibase_design"
        elif len(types) > 1:
            duplicate_class = "convergent_non_snv_designs"
        else:
            duplicate_class = "same_type_convergent_designs"
        duplicate_rows.append(
            {
                "duplicate_sequence_group": group["duplicate_sequence_group"].iloc[0],
                "sequence_id": sequence_id,
                "sequence_sha256": group["sequence_sha256"].iloc[0],
                "normalized_sequence": group["normalized_sequence"].iloc[0],
                "number_design_ids": len(group),
                "design_row_ids": ";".join(group["design_row_id"]),
                "source_constructs": ";".join(
                    group.apply(
                        lambda row: "|".join(
                            [
                                row["source_gene_name"],
                                row["source_tile_id"],
                                row["mutation_type"],
                                row["mutation_position"],
                            ]
                        ),
                        axis=1,
                    )
                ),
                "duplicate_class": duplicate_class,
                "measurement_policy": "one canonical sequence-level measurement",
            }
        )
    identities = pd.DataFrame(duplicate_rows)

    if int(frame["exact_snv"].sum()) != 4_695:
        raise ValueError("Not all 4,695 source-labelled sgl constructs are exact SNVs")
    if frame["sequence_id"].nunique() != 6_260 or len(identities) != 6:
        raise ValueError("Unexpected N-zip exact-sequence duplicate structure")
    if (frame["sequence_length"] != frame["original_size"]).any():
        raise ValueError("Source size and normalized sequence length disagree")

    stable_gzip_csv(frame, DESIGN_OUT)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    identities.to_csv(IDENTITY_OUT, index=False, lineterminator="\n")
    return frame, identities


def audit_workbook_storage() -> dict[str, object]:
    """Distinguish literal XLSX values from dataframe missing-value parsing."""

    from openpyxl import load_workbook

    workbook = load_workbook(WORKBOOK, read_only=True, data_only=False)
    sheet = workbook["Supp_Table_2b"]
    rows = list(sheet.iter_rows(min_row=4, max_row=6_269, values_only=False))
    ratio_zero_padj_text_na = sum(
        row[4].value == 0 and row[4].data_type == "n" and row[5].value == "NA"
        for row in rows
    )
    ratio_zero_padj_blank = sum(row[4].value == 0 and row[5].value is None for row in rows)
    ratio_formula = sum(row[4].data_type == "f" for row in rows)
    padj_formula = sum(row[5].data_type == "f" for row in rows)
    result = {
        "workbook_sha256": sha256_file(WORKBOOK),
        "sheet": "Supp_Table_2b",
        "data_rows": len(rows),
        "literal_numeric_zero_ratio_with_literal_text_NA_padj": ratio_zero_padj_text_na,
        "numeric_zero_ratio_with_blank_padj": ratio_zero_padj_blank,
        "ratio_formula_cells": ratio_formula,
        "padj_formula_cells": padj_formula,
        "interpretation": (
            "The supplement stores numeric zero in the ratio cell and literal text NA "
            "in the adjusted-P cell; pandas parses the text NA as missing by default."
        ),
    }
    if ratio_zero_padj_text_na != 491 or ratio_zero_padj_blank != 0:
        raise ValueError("Unexpected workbook zero/NA storage pattern")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "workbook_cell_storage_audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def validate_fastq_sources() -> dict[str, object]:
    """Validate ENA bytes, MD5, gzip stream, read count, and local SHA-256."""

    runs: dict[str, object] = {}
    for run, (expected_bytes, expected_md5, expected_reads) in ENA_EXPECTED.items():
        path = FASTQ_DIR / f"{run}.fastq.gz"
        observed_bytes = path.stat().st_size
        observed_md5, observed_sha256 = md5_sha256_file(path)
        observed_reads = sum(1 for _ in _iter_fastq_sequences(path))
        valid = (
            observed_bytes == expected_bytes
            and observed_md5 == expected_md5
            and observed_reads == expected_reads
        )
        runs[run] = {
            "url": (
                "https://ftp.sra.ebi.ac.uk/vol1/fastq/"
                f"ERR733/{run[-3:]}/{run}/{run}.fastq.gz"
            ),
            "file": path.relative_to(ROOT).as_posix(),
            "expected_bytes": expected_bytes,
            "observed_bytes": observed_bytes,
            "ena_md5": expected_md5,
            "observed_md5": observed_md5,
            "local_sha256": observed_sha256,
            "expected_reads": expected_reads,
            "observed_reads": observed_reads,
            "gzip_integrity": True,
            "valid": valid,
        }
        if not valid:
            raise ValueError(f"ENA validation failed for {run}")
    result = {
        "accession": "E-MTAB-10902",
        "ena_study": "ERP133202",
        "processed_count_matrix_in_biostudies": False,
        "total_compressed_bytes": sum(value[0] for value in ENA_EXPECTED.values()),
        "total_reads": sum(value[2] for value in ENA_EXPECTED.values()),
        "runs": runs,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "source_acquisition_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def _iter_fastq_sequences(path: Path) -> Iterable[str]:
    with gzip.open(path, "rt", encoding="ascii", newline="") as handle:
        while True:
            header = handle.readline()
            if not header:
                return
            sequence = handle.readline().rstrip("\r\n").upper()
            plus = handle.readline()
            quality = handle.readline().rstrip("\r\n")
            if not header.startswith("@") or not plus.startswith("+"):
                raise ValueError(f"Malformed FASTQ record in {path}")
            if len(sequence) != len(quality):
                raise ValueError(f"Sequence/quality length mismatch in {path}")
            yield sequence


def _sequence_lookup(design: pd.DataFrame) -> tuple[dict[str, str], list[int]]:
    unique = design[["normalized_sequence", "sequence_id"]].drop_duplicates()
    lookup = dict(zip(unique["normalized_sequence"], unique["sequence_id"]))
    lengths = sorted({len(value) for value in lookup}, reverse=True)
    lexical = sorted(lookup)
    for first, second in zip(lexical, lexical[1:]):
        # Prefix-related strings are adjacent in lexical order.
        if second.startswith(first):
            raise ValueError("Canonical N-zip sequences contain a prefix collision")
    return lookup, lengths


def _prefix_match(payload: str, lookup: dict[str, str], lengths: list[int]) -> str | None:
    for length in lengths:
        if len(payload) >= length:
            sequence_id = lookup.get(payload[:length])
            if sequence_id is not None:
                return sequence_id
    return None


def _suffix_match(payload: str, lookup: dict[str, str], lengths: list[int]) -> str | None:
    for length in lengths:
        if len(payload) >= length:
            sequence_id = lookup.get(payload[-length:])
            if sequence_id is not None:
                return sequence_id
    return None


def _find_substitution_match(text: str, pattern: str, max_mismatches: int) -> int:
    """Return the first indel-free pattern placement within the mismatch limit."""

    stop = len(text) - len(pattern) + 1
    for offset in range(max(0, stop)):
        mismatches = 0
        for observed, expected in zip(text[offset : offset + len(pattern)], pattern):
            if observed != expected:
                mismatches += 1
                if mismatches > max_mismatches:
                    break
        if mismatches <= max_mismatches:
            return offset
    return -1


def _find_first_adapter(text: str) -> int:
    """Match the author's first <=2-substitution adapter occurrence exactly."""

    exact_offset = text.find(PAPER_ADAPTER)
    if exact_offset < 0:
        return _find_substitution_match(text, PAPER_ADAPTER, 2)
    # An earlier imperfect occurrence takes precedence over a later exact one.
    return _find_substitution_match(
        text[: exact_offset + len(PAPER_ADAPTER)], PAPER_ADAPTER, 2
    )


FIXED_HAMMING_BLOCKS = [(0, 16), (16, 32), (32, 48), (48, 64), (64, 80)]


def _hamming_block_candidates(
    payload: str,
    block_index: dict[tuple[int, str], set[tuple[int, int]]],
) -> dict[int, set[int]]:
    """Find all possible <=4-Hamming candidates by the pigeonhole principle."""

    candidates: dict[int, set[int]] = {}
    if len(payload) < 80:
        return candidates
    for block_number, (start, end) in enumerate(FIXED_HAMMING_BLOCKS):
        for sequence_length, row_index in block_index.get(
            (block_number, payload[start:end]), ()
        ):
            candidates.setdefault(sequence_length, set()).add(row_index)
    return candidates


def _best_source_match(
    payload: str,
    sequences_by_length: dict[int, tuple[list[str], np.ndarray]],
    block_index: dict[tuple[int, str], set[tuple[int, int]]],
    seed_index: dict[str, set[tuple[int, int]]],
) -> tuple[str | None, int | None, int]:
    """Implement the pinned author's unique-best-sequence rule."""

    candidates = _hamming_block_candidates(payload, block_index)
    observed = np.frombuffer(payload.encode("ascii"), dtype=np.uint8)
    best_distance = 5
    best_ids: list[str] = []
    # The fixed-block pigeonhole index is exact for payloads >=80 nt. For
    # truncated payloads reproduce the Java counter's actual 5-mer seeding:
    # sliding read 5-mers over the available first-15-nt window, against
    # sliding library 5-mers from positions 0..10. Payloads <5 retrieve none.
    if len(payload) < 80:
        short_candidates: dict[int, set[int]] = defaultdict(set)
        for start in range(max(0, min(len(payload), 15) - 5 + 1)):
            for sequence_length, row_index in seed_index.get(payload[start : start + 5], ()):
                short_candidates[sequence_length].add(row_index)
        candidates = short_candidates
    candidate_items = candidates.items()
    for sequence_length, row_indices in candidate_items:
        if not row_indices:
            continue
        sequence_ids, matrix = sequences_by_length[sequence_length]
        compare_length = min(len(payload), sequence_length)
        indices = np.fromiter(row_indices, dtype=np.int64)
        selected = matrix[indices, :compare_length]
        mismatch_matrix = selected != observed[:compare_length]
        first_15 = mismatch_matrix[:, :15].sum(axis=1)
        total = mismatch_matrix.sum(axis=1)
        valid_positions = np.flatnonzero((first_15 <= 2) & (total < 5))
        for position in valid_positions:
            mismatches = int(total[position])
            sequence_id = sequence_ids[int(indices[position])]
            if mismatches < best_distance:
                best_distance = mismatches
                best_ids = [sequence_id]
            elif mismatches == best_distance:
                best_ids.append(sequence_id)
    if len(best_ids) == 1:
        return best_ids[0], best_distance, 1
    if len(best_ids) > 1:
        return None, best_distance, len(best_ids)
    return None, None, 0


def write_author_library_fasta() -> Path:
    design = pd.read_csv(DESIGN_OUT)
    canonical = (
        design[["sequence_id", "normalized_sequence"]]
        .drop_duplicates()
        .sort_values("sequence_id")
    )
    AUTHOR_FASTA.parent.mkdir(parents=True, exist_ok=True)
    with AUTHOR_FASTA.open("w", encoding="ascii", newline="\n") as handle:
        for row in canonical.itertuples(index=False):
            handle.write(f">{row.sequence_id}\n{row.normalized_sequence}\n")
    return AUTHOR_FASTA


def inspect_read_structure(limit_per_run: int = 100_000) -> dict[str, object]:
    """Inspect adapters and exact library sequence placement without choosing labels."""

    design = pd.read_csv(DESIGN_OUT)
    lookup, lengths_desc = _sequence_lookup(design)
    lengths = sorted(lengths_desc)
    result: dict[str, object] = {"limit_per_run": limit_per_run, "runs": {}}
    for run in RUNS:
        path = FASTQ_DIR / f"{run}.fastq.gz"
        metrics: Counter[str] = Counter()
        adapter_offsets: Counter[int] = Counter()
        umi_lengths: Counter[int] = Counter()
        for i, read in enumerate(_iter_fastq_sequences(path)):
            if i >= limit_per_run:
                break
            metrics["reads"] += 1
            for label, adapter in (
                ("paper_adapter", PAPER_ADAPTER),
                ("mprna_default_adapter", MPRNA_DEFAULT_ADAPTER),
            ):
                offset = read.find(adapter)
                if offset >= 0:
                    metrics[f"{label}_positive"] += 1
                    if label == "paper_adapter":
                        adapter_offsets[offset] += 1
                        umi_lengths[offset] += 1
            paper_offset = read.find(PAPER_ADAPTER)
            if paper_offset >= 0:
                after = read[paper_offset + len(PAPER_ADAPTER) :]
                before = read[:paper_offset]
                if _prefix_match(after, lookup, lengths_desc) is not None:
                    metrics["exact_sequence_after_paper_adapter"] += 1
                if _suffix_match(before, lookup, lengths_desc) is not None:
                    metrics["exact_sequence_before_paper_adapter"] += 1
            if _prefix_match(read, lookup, lengths_desc) is not None:
                metrics["starts_with_library_sequence"] += 1
            if _suffix_match(read, lookup, lengths_desc) is not None:
                metrics["ends_with_library_sequence"] += 1
        result["runs"][run] = {
            **metrics,
            "paper_adapter_offset_counts": dict(sorted(adapter_offsets.items())),
            "candidate_umi_length_counts": dict(sorted(umi_lengths.items())),
            "library_sequence_lengths": lengths,
        }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "read_structure_sample_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _count_one_run(
    run: str, max_records: int | None = None
) -> tuple[str, dict[str, int], dict[str, int], dict[str, object]]:
    """Count one run using the source-proven substitution-tolerant rule."""

    design = pd.read_csv(DESIGN_OUT)
    lookup, _ = _sequence_lookup(design)
    entries_by_length: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for sequence, sequence_id in lookup.items():
        entries_by_length[len(sequence)].append((sequence, sequence_id))
    sequences_by_length: dict[int, tuple[list[str], np.ndarray]] = {}
    for length, entries in entries_by_length.items():
        sequence_ids = [entry[1] for entry in entries]
        matrix = np.vstack(
            [np.frombuffer(entry[0].encode("ascii"), dtype=np.uint8) for entry in entries]
        )
        sequences_by_length[length] = (sequence_ids, matrix)
    block_index: dict[tuple[int, str], set[tuple[int, int]]] = defaultdict(set)
    seed_index: dict[str, set[tuple[int, int]]] = defaultdict(set)
    for length, (sequence_ids, matrix) in sequences_by_length.items():
        for row_index in range(len(sequence_ids)):
            sequence = bytes(matrix[row_index]).decode("ascii")
            for block_number, (start, end) in enumerate(FIXED_HAMMING_BLOCKS):
                block_index[(block_number, sequence[start:end])].add((length, row_index))
            for start in range(11):
                seed_index[sequence[start : start + 5]].add((length, row_index))
    read_counts: Counter[str] = Counter()
    umi_sets: dict[str, set[str]] = defaultdict(set)
    metrics: Counter[str] = Counter()
    adapter_offsets: Counter[int] = Counter()
    umi_lengths: Counter[int] = Counter()
    path = FASTQ_DIR / f"{run}.fastq.gz"
    for record_index, read in enumerate(_iter_fastq_sequences(path)):
        if max_records is not None and record_index >= max_records:
            break
        metrics["fastq_reads"] += 1
        paper_offset = _find_first_adapter(read)
        if paper_offset < 0:
            metrics["adapter_absent"] += 1
            continue
        metrics["paper_adapter_positive"] += 1
        adapter_offsets[paper_offset] += 1
        umi = read[:paper_offset]
        umi_lengths[len(umi)] += 1
        if "N" in umi:
            metrics["umi_contains_n_skipped"] += 1
            continue
        payload = read[paper_offset + len(PAPER_ADAPTER) :]
        sequence_id, mismatches, tied_sequences = _best_source_match(
            payload, sequences_by_length, block_index, seed_index
        )
        if sequence_id is None:
            if tied_sequences > 1:
                metrics["ambiguous_best_sequence_tie"] += 1
            else:
                metrics["adapter_positive_unmapped"] += 1
            continue
        metrics["uniquely_mapped_reads"] += 1
        metrics[f"mapped_mismatches_{mismatches}"] += 1
        read_counts[sequence_id] += 1
        if umi and DNA_RE.fullmatch(umi) is not None:
            umi_sets[sequence_id].add(umi)
            metrics["mapped_reads_with_valid_umi"] += 1
        else:
            metrics["mapped_reads_without_valid_umi"] += 1
    umi_counts = {sequence_id: len(values) for sequence_id, values in umi_sets.items()}
    audit: dict[str, object] = {
        **metrics,
        "paper_adapter_offset_counts": dict(sorted(adapter_offsets.items())),
        "umi_length_counts": dict(sorted(umi_lengths.items())),
        "counting_rule": (
            "adapter <=2 substitutions; insert <=4 substitutions, <=2 in first 15 nt; "
            "unique best canonical sequence; no indels"
        ),
        "max_records": max_records,
    }
    return run, dict(read_counts), umi_counts, audit


def count_raw_reads(max_workers: int = 6) -> tuple[pd.DataFrame, dict[str, object]]:
    """Count all six runs and write one row per canonical measurable sequence."""

    design = pd.read_csv(DESIGN_OUT)
    canonical = (
        design[["sequence_id", "sequence_sha256", "normalized_sequence"]]
        .drop_duplicates()
        .sort_values("sequence_id")
        .reset_index(drop=True)
    )
    outputs: dict[str, tuple[dict[str, int], dict[str, int], dict[str, object]]] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_count_one_run, run): run for run in RUNS}
        for future in concurrent.futures.as_completed(futures):
            run, reads, umis, audit = future.result()
            outputs[run] = (reads, umis, audit)
    if set(outputs) != set(RUNS):
        raise ValueError("Not all six N-zip runs were counted")

    for run, (replicate, compartment) in RUNS.items():
        reads, umis, _ = outputs[run]
        stem = f"replicate{replicate}_{compartment}"
        canonical[f"{stem}_read_count"] = canonical["sequence_id"].map(reads).fillna(0).astype(int)
        canonical[f"{stem}_distinct_umi_count"] = canonical["sequence_id"].map(umis).fillna(0).astype(int)
    count_columns = [column for column in canonical if column.endswith("_read_count")]
    canonical["samples_with_at_least_20_reads"] = canonical[count_columns].ge(20).sum(axis=1)
    canonical["read_coverage_state"] = canonical["samples_with_at_least_20_reads"].map(
        lambda value: "coverage_pass" if value >= 3 else "coverage_fail"
    )
    umi_columns = [column for column in canonical if column.endswith("_distinct_umi_count")]
    canonical["samples_with_at_least_20_umis"] = canonical[umi_columns].ge(20).sum(axis=1)
    canonical["coverage_state"] = canonical["samples_with_at_least_20_umis"].map(
        lambda value: "coverage_pass" if value >= 3 else "coverage_fail"
    )
    canonical["umi_coverage_state"] = canonical["coverage_state"]
    stable_gzip_csv(canonical, COUNTS_OUT)
    audit = {
        "counting_rule": (
            "paper adapter <=2 substitutions; insert <=4 substitutions and <=2 in first 15 nt; "
            "unique best canonical sequence; indel-free; distinct UMIs are the quantitative layer"
        ),
        "coverage_rule": "at least three of six samples each have at least 20 distinct mapped UMIs",
        "canonical_sequences": len(canonical),
        "canonical_coverage_pass": int(canonical["coverage_state"].eq("coverage_pass").sum()),
        "canonical_read_coverage_pass_sensitivity": int(
            canonical["read_coverage_state"].eq("coverage_pass").sum()
        ),
        "design_level_coverage_pass": int(
            design.merge(canonical[["sequence_id", "coverage_state"]], on="sequence_id")[
                "coverage_state"
            ].eq("coverage_pass").sum()
        ),
        "runs": {run: outputs[run][2] for run in RUNS},
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "raw_count_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    return canonical, audit


def merge_compiled_counts() -> tuple[pd.DataFrame, dict[str, object]]:
    """Merge six outputs from the slice-validated compiled streaming counter."""

    design = pd.read_csv(DESIGN_OUT)
    canonical = (
        design[["sequence_id", "sequence_sha256", "normalized_sequence"]]
        .drop_duplicates()
        .sort_values("sequence_id")
        .reset_index(drop=True)
    )
    audits: dict[str, object] = {}
    for run, (replicate, compartment) in RUNS.items():
        path = CPP_COUNT_DIR / f"{run}.tsv"
        metrics_path = CPP_COUNT_DIR / f"{run}.metrics.json"
        counts = pd.read_csv(path, sep="\t")
        if len(counts) != len(canonical) or counts["sequence_id"].duplicated().any():
            raise ValueError(f"Invalid compiled count output for {run}")
        merged = canonical[["sequence_id"]].merge(
            counts, on="sequence_id", how="left", validate="one_to_one"
        )
        if merged[["read_count", "distinct_umi_count"]].isna().any().any():
            raise ValueError(f"Compiled count IDs do not cover the canonical library for {run}")
        stem = f"replicate{replicate}_{compartment}"
        canonical[f"{stem}_read_count"] = merged["read_count"].astype(int)
        canonical[f"{stem}_distinct_umi_count"] = merged["distinct_umi_count"].astype(int)
        exact_path = CPP_EXACT_AUDIT_DIR / f"{run}.tsv"
        if exact_path.exists():
            exact = pd.read_csv(exact_path, sep="\t")
            exact = canonical[["sequence_id"]].merge(
                exact[["sequence_id", "exact_read_count", "exact_distinct_umi_count"]],
                on="sequence_id", how="left", validate="one_to_one",
            )
            if exact.isna().any().any():
                raise ValueError(f"Exact-match sensitivity IDs do not cover the library for {run}")
            canonical[f"{stem}_exact_read_count"] = exact["exact_read_count"].astype(int)
            canonical[f"{stem}_exact_distinct_umi_count"] = exact[
                "exact_distinct_umi_count"
            ].astype(int)
        audits[run] = json.loads(metrics_path.read_text(encoding="utf-8"))

    count_columns = [
        column for column in canonical
        if column.endswith("_read_count") and "_exact_" not in column
    ]
    canonical["samples_with_at_least_20_reads"] = canonical[count_columns].ge(20).sum(axis=1)
    canonical["read_coverage_state"] = canonical["samples_with_at_least_20_reads"].map(
        lambda value: "coverage_pass" if value >= 3 else "coverage_fail"
    )
    umi_columns = [
        column for column in canonical
        if column.endswith("_distinct_umi_count") and "_exact_" not in column
    ]
    canonical["samples_with_at_least_20_umis"] = canonical[umi_columns].ge(20).sum(axis=1)
    canonical["coverage_state"] = canonical["samples_with_at_least_20_umis"].map(
        lambda value: "coverage_pass" if value >= 3 else "coverage_fail"
    )
    canonical["umi_coverage_state"] = canonical["coverage_state"]
    exact_umi_columns = [
        column for column in canonical if column.endswith("_exact_distinct_umi_count")
    ]
    if exact_umi_columns:
        canonical["exact_samples_with_at_least_20_umis"] = canonical[exact_umi_columns].ge(20).sum(axis=1)
        canonical["exact_umi_coverage_state_sensitivity"] = canonical[
            "exact_samples_with_at_least_20_umis"
        ].map(lambda value: "coverage_pass" if value >= 3 else "coverage_fail")
    stable_gzip_csv(canonical, COUNTS_OUT)
    design_states = design.merge(
        canonical[["sequence_id", "coverage_state"]], on="sequence_id", validate="many_to_one"
    )
    audit = {
        "implementation": "compiled source-equivalent counter",
        "validation": "exact per-sequence read and UMI agreement on pinned 100000-read author slice",
        "counting_rule": (
            "paper adapter <=2 substitutions; source 5-mer candidate seeding for truncated reads; "
            "insert <=4 substitutions and <=2 in first 15 nt; unique best exact sequence; "
            "indel-free; N-containing UMI skipped; distinct UMIs are the quantitative layer"
        ),
        "coverage_rule": "at least three of six samples each have at least 20 distinct mapped UMIs",
        "coverage_interpretation_evidence": (
            "the workbook mean localization ratio independently matches UMI-derived simple "
            "replicate ratios better than read-count or DESeq2 candidates"
        ),
        "canonical_sequences": len(canonical),
        "canonical_coverage_pass": int(canonical["coverage_state"].eq("coverage_pass").sum()),
        "canonical_read_coverage_pass_sensitivity": int(
            canonical["read_coverage_state"].eq("coverage_pass").sum()
        ),
        "design_level_coverage_pass": int(design_states["coverage_state"].eq("coverage_pass").sum()),
        "publication_reported_design_level_coverage_pass": 5_679,
        "publication_pass_count_difference": int(
            design_states["coverage_state"].eq("coverage_pass").sum() - 5_679
        ),
        "publication_pass_identity_reproduced": False,
        "historical_processing_state": (
            "aggregate mismatch unresolved; do not tune threshold or choose exact-only sensitivity"
        ),
        "runs": audits,
    }
    if exact_umi_columns:
        exact_states = design.merge(
            canonical[["sequence_id", "exact_umi_coverage_state_sensitivity"]],
            on="sequence_id", validate="many_to_one",
        )
        audit["exact_only_design_level_pass_rejected_sensitivity"] = int(
            exact_states["exact_umi_coverage_state_sensitivity"].eq("coverage_pass").sum()
        )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "raw_count_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    return canonical, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "design",
            "author-fasta",
            "workbook-audit",
            "validate-fastq",
            "inspect-reads",
            "count",
            "merge-compiled",
        ),
    )
    parser.add_argument("--limit-per-run", type=int, default=100_000)
    parser.add_argument("--max-workers", type=int, default=6)
    args = parser.parse_args()
    if args.command == "design":
        design, identities = build_design_table()
        print(
            json.dumps(
                {
                    "design_rows": len(design),
                    "unique_sequences": design["sequence_id"].nunique(),
                    "exact_snvs": int(design["exact_snv"].sum()),
                    "duplicate_sequence_groups": len(identities),
                },
                indent=2,
            )
        )
    elif args.command == "author-fasta":
        print(write_author_library_fasta())
    elif args.command == "workbook-audit":
        print(json.dumps(audit_workbook_storage(), indent=2))
    elif args.command == "validate-fastq":
        print(json.dumps(validate_fastq_sources(), indent=2))
    elif args.command == "inspect-reads":
        print(json.dumps(inspect_read_structure(args.limit_per_run), indent=2))
    elif args.command == "count":
        _, audit = count_raw_reads(args.max_workers)
        print(json.dumps(audit, indent=2))
    else:
        _, audit = merge_compiled_counts()
        print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
