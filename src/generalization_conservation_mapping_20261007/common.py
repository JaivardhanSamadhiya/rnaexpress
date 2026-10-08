"""Standard-library-only metadata identities and coordinate rules."""
from __future__ import annotations
from collections import Counter
import csv, gzip, hashlib, io, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = "generalization_conservation_mapping_20261007"
SRC, REP, OUT, ART = [ROOT / folder / NS for folder in ("src", "reports", "results", "artifacts")]
OLD_SRC = ROOT / "src/generalization_conservation_feasibility_20261007"
OLD_OUT = ROOT / "results/generalization_conservation_feasibility_20261007"
OLD_ART = ROOT / "artifacts/generalization_conservation_feasibility_20261007"
INVENTORY = ROOT / "artifacts/generalization_next_20261007/sequence_inventory.csv.gz"
CORE = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
FASTA = ROOT / "data/external/RNAloc_MPRA/Datasets/mouse_3utrs.txt"
COLS = ["intervention_id", "dataset", "biological_component", "parent_context_id", "parent_sequence", "mutant_sequence"]
IDENTITY = ["intervention_id", "gene_transcript", "parent_id", "mutant_id"]
ROW_COLS = COLS + IDENTITY[1:]
API = "https://api.genome.ucsc.edu/"
MAX_REGION, MAX_TOTAL, MAX_RESPONSE = 500_000, 100_000_000, 4_000_000
ANNOTATION_TIME = "2019-09-19T15:18:52"
DESIGN = OUT / "design_manifest.json"
MAPPED = "reference_site_vector_unique_complete_candidates"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, data):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (SRC, REP, OUT, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, "Preserve existing artifact: " + str(path)
    else:
        with path.open("xb") as stream:
            stream.write(data)


def jsave(path, data):
    save(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_columns(path, columns, exact=False):
    """Retain and interpret named metadata columns only; no outcome dictionaries."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        assert len(header) == len(set(header)) and set(columns) <= set(header)
        if exact:
            assert header == list(columns)
        indices = [header.index(name) for name in columns]
        return [{name: raw[index] for name, index in zip(columns, indices)} for raw in reader]


def csvsave(path, rows, columns):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = buffer.getvalue().encode()
    save(path, gzip.compress(payload, mtime=0) if str(path).endswith(".gz") else payload)


def committed(path):
    path = Path(path)
    assert subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes()


def certify():
    committed(DESIGN)
    manifest = read(DESIGN)
    assert manifest["status"] == "FROZEN_OUTCOME_BLIND_FULL_COORDINATE_MAPPING"
    for name, expected in manifest["files"].items():
        assert sha(ROOT / name) == expected, name
    return manifest


def occurrences(sequence, piece):
    assert piece
    found, offset = [], sequence.find(piece)
    while offset >= 0:
        found.append(offset)
        offset = sequence.find(piece, offset + 1)
    return found


def complement(base):
    return {"A": "T", "C": "G", "G": "C", "T": "A", "N": "N"}[base]


def region_key(ref):
    chromosome = str(ref["chromosome"])
    return ("chrM" if chromosome == "MT" else "chr" + chromosome, int(ref["gene_start1"]) - 1, int(ref["gene_end1"]))


def tag(key):
    return f"mm10_{key[0]}_{key[1]}_{key[2]}"


def urls(key):
    chrom, start, end = key
    return {"knownGene": API + f"getData/track?genome=mm10;track=knownGene;chrom={chrom};start={start};end={end};maxItemsOutput=10000",
            "sequence": API + f"getData/sequence?genome=mm10;chrom={chrom};start={start};end={end}"}


def transcript_utr(record, genomic, start):
    left = [int(value) for value in record["exonStarts"].split(",") if value]
    right = [int(value) for value in record["exonEnds"].split(",") if value]
    assert len(left) == len(right) == int(record["exonCount"])
    assert record["strand"] in ("+", "-") and left == sorted(left)
    assert all(a < b for a, b in zip(left, right)) and all(right[i] <= left[i + 1] for i in range(len(left) - 1))
    assert int(record["txStart"]) <= int(record["cdsStart"]) <= int(record["cdsEnd"]) <= int(record["txEnd"])
    assert all(int(record["txStart"]) <= a < b <= int(record["txEnd"]) for a, b in zip(left, right))
    if int(record["cdsStart"]) == int(record["cdsEnd"]):
        return None, None
    positions = []
    for a, b in zip(left, right):
        lo, hi = (max(a, int(record["cdsEnd"])), b) if record["strand"] == "+" else (a, min(b, int(record["cdsStart"])))
        positions.extend(range(lo, hi))
    if record["strand"] == "-":
        positions.reverse()
    assert all(start <= position < start + len(genomic) for position in positions)
    sequence = "".join(genomic[position - start] for position in positions)
    if record["strand"] == "-":
        sequence = "".join(complement(base) for base in sequence)
    return sequence, positions


def vector_set(matches):
    return {(item["chrom"], item["strand"], tuple(item["positions0"])) for item in matches}


def mapping_status(parent, matches, unresolved):
    if parent["dataset"] == "srle":
        assert not matches
        return "synthetic_no_native_coordinates"
    if not parent["reference_candidates"]:
        assert not matches
        return "no_exact_source_utr"
    if unresolved:
        return "unresolved_reference_candidates"
    count = len(vector_set(matches))
    return MAPPED if count == 1 else "ambiguous_reference_site_vectors" if count > 1 else "no_exact_reference_vector"


def edited_coordinates(row, parent):
    assert len(row["parent_sequence"]) == len(row["mutant_sequence"])
    changed = [i for i, (a, b) in enumerate(zip(row["parent_sequence"], row["mutant_sequence"])) if a != b]
    assert 0 < len(changed) <= 6
    coordinates = []
    if parent["mapping_status"] == MAPPED:
        assert parent["candidate_resolution_complete"] and not parent["unresolved_candidates"]
        vectors = vector_set(parent["matches"])
        assert len(vectors) == 1
        chrom, strand, positions = next(iter(vectors))
        assert len(positions) == len(row["parent_sequence"])
        for index in changed:
            ref, alt = row["parent_sequence"][index], row["mutant_sequence"][index]
            coordinates.append({"insert_position0": index, "chrom": chrom, "genomic_position0": positions[index], "strand": strand,
                "expressed_reference": ref, "expressed_alternate": alt,
                "genomic_reference": ref if strand == "+" else complement(ref),
                "genomic_alternate": alt if strand == "+" else complement(alt)})
    return changed, coordinates


def menu_counts(rows):
    return Counter((row["dataset"], row["parent_context_id"]) for row in rows)
