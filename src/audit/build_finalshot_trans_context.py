"""Build the outcome-blind FinalShot RBP-expression context proxy.

Only public GSE67828 expression files, the frozen MGI orthology table, and the
UCSC mm9 RefGene table are read.  No localization outcome or protected data is
accessed.  The old Cufflinks files frequently lack gene symbols, so RBP genes
are resolved against the experiment's mm9 build by genomic interval overlap.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "finalshot_resource_audit" / "gse67828_context"
OUT = ROOT / "results" / "finalshot"
ORTHOLOGY = OUT / "rbp_orthology_mgi_2026-09-02.csv"

ARCHIVE_SHA256 = "e2bce64320274f7a81b87598235934f6c6af0636126d6deca14ecc5b42a488c2"
REFGENE_SHA256 = "7eb239607afa72581e1eebb9c90156e8d83d871953118357b93d39df88208ac4"
SAMPLES = {
    "GSM1656708_N2ASoma1_fpkm.txt.gz": ("N2A", "soma", 1, "0de28d55d8b84d441de6aba27faeaf24f8ed5f27f1f41528f4f3e9f7dbee76ed"),
    "GSM1656709_N2ASoma2_fpkm.txt.gz": ("N2A", "soma", 2, "93ba3fde19a588ea3f7c73c58fd4145e8703e7929102734e036a5c4cb8ab012e"),
    "GSM1656710_N2ASoma3_fpkm.txt.gz": ("N2A", "soma", 3, "210c8cf77d0ac9febe8d9980ba512f3b0f271921a6837b97b39fe7a8a65c1e73"),
    "GSM1656711_N2AAxon1_fpkm.txt.gz": ("N2A", "neurite", 1, "382206ec05800bff47e319cf20269dbd0df3465539111849032a0282c797709e"),
    "GSM1656712_N2AAxon2_fpkm.txt.gz": ("N2A", "neurite", 2, "fdf04bbe7253c7911f06bedf64c6d668c839ef1d84cbd8f79e4fdab8474d62f1"),
    "GSM1656713_N2AAxon3_fpkm.txt.gz": ("N2A", "neurite", 3, "d0ae05df2cd87f4cd576915f4dcbeadfb6f4eee45a0e69a0d1bacbb2ce82fba9"),
    "GSM1656714_CADSoma1_fpkm.txt.gz": ("CAD", "soma", 1, "304c5839009b6e038467636d836b8fc6555e219788fee7356e347d6e82323985"),
    "GSM1656715_CADSoma2_fpkm.txt.gz": ("CAD", "soma", 2, "5d11944dd1ae25eb7166fe5c77b858ed0fd91716c8b816d7733ecd9ea2e98feb"),
    "GSM1656716_CADSoma3_fpkm.txt.gz": ("CAD", "soma", 3, "4d0255ef7ddd42ff96482391709b06a31c5e726eb74e3aa586dfe4be029ef85f"),
    "GSM1656717_CADAxon1_fpkm.txt.gz": ("CAD", "neurite", 1, "0c379a472f5040c5afde39e1a9876fc9b0b8359fc9e2b246131a09bb864ac7f5"),
    "GSM1656718_CADAxon2_fpkm.txt.gz": ("CAD", "neurite", 2, "f098e0536284399018139a1daff68f39fd5520a223f81952b7d2e626cb6b4390"),
    "GSM1656719_CADAxon3_fpkm.txt.gz": ("CAD", "neurite", 3, "5aa769553da5e8624c8d004623e678b3bed4d00e5db479dd376ec01699965f3b"),
}

# Qki was named Qk in the mm9 RefGene snapshot used for coordinate recovery.
MM9_SYMBOL_ALIASES = {"Qki": "Qk"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_inputs() -> None:
    archive = RAW / "GSE67828_RAW.tar"
    refgene = RAW / "mm9_refGene.txt.gz"
    if sha256(archive) != ARCHIVE_SHA256:
        raise RuntimeError("GSE67828 archive differs from the frozen snapshot")
    if sha256(refgene) != REFGENE_SHA256:
        raise RuntimeError("UCSC mm9 RefGene differs from the frozen snapshot")
    for filename, (_, _, _, expected) in SAMPLES.items():
        if sha256(RAW / filename) != expected:
            raise RuntimeError(f"GSE67828 sample differs from frozen snapshot: {filename}")


def read_orthology() -> list[dict[str, str]]:
    with ORTHOLOGY.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_refgene_spans() -> dict[str, tuple[str, int, int, str]]:
    transcripts: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    with gzip.open(RAW / "mm9_refGene.txt.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            transcripts[fields[12]].append((fields[2], int(fields[4]), int(fields[5])))

    spans: dict[str, tuple[str, int, int, str]] = {}
    for symbol, records in transcripts.items():
        chromosome = Counter(record[0] for record in records).most_common(1)[0][0]
        same_chromosome = [record for record in records if record[0] == chromosome]
        spans[symbol] = (
            chromosome,
            min(record[1] for record in same_chromosome),
            max(record[2] for record in same_chromosome),
            symbol,
        )
    return spans


def parse_locus(value: str) -> tuple[str, int, int]:
    chromosome, interval = value.split(":", 1)
    start, end = interval.split("-", 1)
    return chromosome, int(start), int(end)


def read_sample(path: Path) -> dict[str, list[dict[str, object]]]:
    by_chromosome: dict[str, list[dict[str, object]]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["FPKM_status"] != "OK":
                continue
            chromosome, start, end = parse_locus(row["locus"])
            value = float(row["FPKM"])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid FPKM in {path.name}")
            by_chromosome[chromosome].append({
                "start": start,
                "end": end,
                "tracking_id": row["tracking_id"],
                "fpkm": value,
            })
    return by_chromosome


def resolve_interval(
    candidates: list[dict[str, object]], target_start: int, target_end: int, symbol: str
) -> dict[str, object]:
    scored: list[tuple[float, float, float, dict[str, object]]] = []
    target_length = target_end - target_start
    for candidate in candidates:
        start, end = int(candidate["start"]), int(candidate["end"])
        overlap = max(0, min(target_end, end) - max(target_start, start))
        if overlap == 0:
            continue
        union = max(target_end, end) - min(target_start, start)
        exact_name = float(str(candidate["tracking_id"]).lower() == symbol.lower())
        scored.append((exact_name, overlap / union, overlap / target_length, candidate))
    if not scored:
        raise RuntimeError(f"No expressed/zero-valued Cufflinks locus overlaps {symbol}")
    scored.sort(key=lambda item: item[:3], reverse=True)
    exact_name, jaccard, target_coverage, selected = scored[0]
    return {
        **selected,
        "exact_symbol_match": bool(exact_name),
        "interval_jaccard": jaccard,
        "target_coverage": target_coverage,
        "overlap_candidate_count": len(scored),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    verify_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    orthology = read_orthology()
    refgene = read_refgene_spans()

    human_to_mouse: dict[str, tuple[str, str]] = {}
    ineligible: dict[str, str] = {}
    orthology_by_human: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in orthology:
        orthology_by_human[row["human_rbp"]].append(row)
    for human, rows in orthology_by_human.items():
        usable = [row for row in rows if row["mapping_status"] == "one_to_one" and row["mouse_symbol"]]
        exact_symbol = [row for row in usable if row["mouse_symbol"].upper() == human.upper()]
        # MGI links human LARP7 both to protein-coding Larp7 and Larp7-ps.  The
        # unique exact-symbol match is the prospective, outcome-blind resolver.
        if len(exact_symbol) == 1:
            selected_row = exact_symbol[0]
        elif len(usable) == 1 and len(rows) == 1:
            selected_row = usable[0]
        else:
            statuses = sorted({row["mapping_status"] for row in rows})
            ineligible[human] = f"no unique canonical MGI mapping ({'/'.join(statuses)})"
            continue
        mouse = selected_row["mouse_symbol"]
        mm9_symbol = MM9_SYMBOL_ALIASES.get(mouse, mouse)
        if mm9_symbol not in refgene:
            ineligible[human] = f"no unambiguous mm9 RefGene span for {mouse}"
            continue
        human_to_mouse[human] = (mouse, mm9_symbol)

    sample_rows: list[dict[str, object]] = []
    values: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for filename, (cell_line, compartment, replicate, expected_hash) in SAMPLES.items():
        sample = read_sample(RAW / filename)
        for human, (mouse, mm9_symbol) in sorted(human_to_mouse.items()):
            chromosome, target_start, target_end, _ = refgene[mm9_symbol]
            selected = resolve_interval(sample[chromosome], target_start, target_end, mm9_symbol)
            log1p_fpkm = math.log1p(float(selected["fpkm"]))
            values[(human, cell_line, compartment)].append(log1p_fpkm)
            sample_rows.append({
                "human_rbp": human,
                "mouse_symbol": mouse,
                "mm9_refgene_symbol": mm9_symbol,
                "cell_line": cell_line,
                "compartment": compartment,
                "replicate": replicate,
                "geo_sample": filename.split("_", 1)[0],
                "source_file": filename,
                "source_sha256": expected_hash,
                "fpkm": selected["fpkm"],
                "log1p_fpkm": log1p_fpkm,
                "matched_tracking_id": selected["tracking_id"],
                "matched_locus": f"{chromosome}:{selected['start']}-{selected['end']}",
                "exact_symbol_match": selected["exact_symbol_match"],
                "interval_jaccard": selected["interval_jaccard"],
                "target_coverage": selected["target_coverage"],
                "overlap_candidate_count": selected["overlap_candidate_count"],
            })

    proxy_rows: list[dict[str, object]] = []
    all_human = sorted({row["human_rbp"] for row in orthology})
    for human in all_human:
        mouse = human_to_mouse.get(human, ("", ""))[0]
        for cell_line in ("CAD", "N2A"):
            eligible = human in human_to_mouse
            soma = values.get((human, cell_line, "soma"), [])
            neurite = values.get((human, cell_line, "neurite"), [])
            soma_median = statistics.median(soma) if eligible else ""
            neurite_median = statistics.median(neurite) if eligible else ""
            proxy = (float(soma_median) + float(neurite_median)) / 2 if eligible else ""
            proxy_rows.append({
                "human_rbp": human,
                "mouse_symbol": mouse,
                "cell_line": cell_line,
                "context_eligible": eligible,
                "ineligibility_reason": "" if eligible else ineligible[human],
                "soma_replicates": len(soma),
                "neurite_replicates": len(neurite),
                "soma_median_log1p_fpkm": soma_median,
                "neurite_median_log1p_fpkm": neurite_median,
                "compartment_balanced_expression_proxy": proxy,
            })

    write_csv(OUT / "rbp_expression_proxy_samples.csv", sample_rows)
    write_csv(OUT / "rbp_expression_proxy.csv", proxy_rows)
    manifest = {
        "accession": "GSE67828",
        "paper_doi": "10.1016/j.molcel.2016.01.020",
        "organism": "Mus musculus",
        "genome_build": "mm9 supplemented with alternative isoforms",
        "processing": "TopHat 2.0.12 or STAR 2.0.4d; Cufflinks 2.1.1",
        "archive": {"bytes": (RAW / "GSE67828_RAW.tar").stat().st_size, "sha256": ARCHIVE_SHA256},
        "mm9_refgene": {"source": "UCSC refGene table", "sha256": REFGENE_SHA256},
        "samples": [
            {"file": filename, "cell_line": metadata[0], "compartment": metadata[1],
             "replicate": metadata[2], "sha256": metadata[3]}
            for filename, metadata in SAMPLES.items()
        ],
        "proxy_definition": "mean of the soma and neurite medians of log1p(FPKM), three replicates per compartment",
        "eligible_rbp_channels": len(human_to_mouse),
        "ineligible_rbp_channels": ineligible,
        "limitations": [
            "RNA abundance is an imperfect proxy for active RBP protein abundance.",
            "RBPNet is human HepG2-trained whereas the context proxy and development assays are mouse neural cell lines.",
            "GSE67828 is the closest public matching CAD/N2A state, not an exact batch match to every development assay.",
            "Gene identities absent from Cufflinks symbols are recovered outcome-blind by overlap with the experiment's mm9 RefGene coordinates.",
        ],
        "protected_data_accessed": False,
        "localization_outcomes_accessed": False,
    }
    (OUT / "context_source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
