"""Fixed complete metadata roster/regions and design freeze; no new requests."""
from __future__ import annotations
from collections import defaultdict, Counter
import hashlib, re, sys
from . import common as c
from . import replay
from .transport import cached


def author_references(genes):
    result = defaultdict(list)
    header, chunks = None, []
    def emit():
        if header is None:
            return
        pieces = header.split("|")
        assert len(pieces) == 6
        if pieces[2].casefold() not in genes:
            return
        sequence = "".join(chunks).upper()
        if not re.fullmatch("[ACGT]+", sequence):
            return
        assert re.fullmatch("ENSMUSG[0-9]+", pieces[0]) and re.fullmatch("ENSMUST[0-9]+", pieces[1])
        result[pieces[2].casefold()].append({"header": header, "gene_id": pieces[0], "transcript_id": pieces[1], "gene": pieces[2],
            "chromosome": pieces[3], "gene_start1": int(pieces[4]), "gene_end1": int(pieces[5]),
            "sequence": sequence, "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest()})
    with c.FASTA.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith(">"):
                emit()
                header, chunks = line[1:].strip(), []
            else:
                chunks.append(line.strip())
        emit()
    return result


def make_region_plan(parents, cached_paths=None):
    cached_paths = {} if cached_paths is None else cached_paths
    keys = sorted({c.region_key(ref) for parent in parents for ref in parent["reference_candidates"]})
    used, records = 0, []
    allowed_chromosomes = {"chr" + str(i) for i in range(1, 20)} | {"chrX", "chrY", "chrM"}
    for key in keys:
        chrom, start, end = key
        if chrom not in allowed_chromosomes:
            status = "unsupported_fixed_author_chromosome"
        elif start < 0 or end <= start or end - start > c.MAX_REGION:
            status = "fixed_region_cap_or_invalid_interval"
        elif used + end - start > c.MAX_TOTAL:
            status = "fixed_total_region_cap"
        else:
            status = "eligible"
            used += end - start
        records.append({"key": list(key), "planned_status": status, "region_bases": end - start,
            "urls": c.urls(key) if status == "eligible" else {}, "reuse": cached_paths.get(key, {}) if status == "eligible" else {}})
    return records


def local():
    assert not (c.OUT / "metadata_preparation_receipt.json").exists()
    prior = c.read(c.OLD_OUT / "metadata_receipt.json")
    assert prior["status"] == "PASS_METADATA_ONLY" and not prior["outcomes_read"]
    for name, expected in prior["files"].items():
        assert c.sha(c.ROOT / name) == expected, name
    pilot = replay.pilot_audit()
    c.jsave(c.OUT / "preserved_pilot_audit_receipt.json", pilot)
    prefit = c.ROOT / "results/generalization_next_20261007/prefit_manifest.json"
    c.committed(prefit)
    assert c.read(prefit)["files"][c.INVENTORY.relative_to(c.ROOT).as_posix()] == c.sha(c.INVENTORY)
    inventory = c.read_columns(c.INVENTORY, c.COLS, exact=True)
    identity = c.read_columns(c.CORE, c.IDENTITY)
    assert len(inventory) == len(identity) == 26258
    assert [r["intervention_id"] for r in inventory] == [r["intervention_id"] for r in identity]
    assert len({r["intervention_id"] for r in inventory}) == len(inventory)
    rows = [row | {name: item[name] for name in c.IDENTITY[1:]} for row, item in zip(inventory, identity)]
    parents = c.read(c.OLD_OUT / "parent_reference_candidates.json")
    parent_index = {(p["dataset"], p["parent_id"]): p for p in parents}
    assert len(parents) == len(parent_index) == 3022
    for row in rows:
        parent = parent_index[(row["dataset"], row["parent_id"])]
        assert parent["gene"] == row["gene_transcript"] and parent["parent_sequence"] == row["parent_sequence"]
        assert set(row["parent_sequence"] + row["mutant_sequence"]) <= set("ACGT")
        assert len(row["parent_sequence"]) == len(row["mutant_sequence"])
        assert 0 < sum(a != b for a, b in zip(row["parent_sequence"], row["mutant_sequence"])) <= 6
    assert set(parent_index) == {(r["dataset"], r["parent_id"]) for r in rows}
    refs = author_references({p["gene"].casefold() for p in parents})
    for parent in parents:
        matches = []
        if parent["dataset"] != "srle":
            for ref in refs[parent["gene"].casefold()]:
                for offset in c.occurrences(ref["sequence"], parent["parent_sequence"]):
                    matches.append({name: value for name, value in ref.items() if name != "sequence"} |
                        {"utr_insert_start0": offset, "utr_insert_end0": offset + len(parent["parent_sequence"])})
        assert matches == parent["reference_candidates"], "Full author candidate roster changed"
    reused = {}
    for path in sorted((c.OLD_ART / "public_metadata").glob("*_*.json")):
        if path.name.endswith(".receipt.json") or not any(path.name.endswith("_" + kind + ".json") for kind in ("knownGene", "sequence")):
            continue
        value = c.read(path)
        key = (value["chrom"], value["start"], value["end"])
        kind = "sequence" if "dna" in value else "knownGene"
        data, item = cached(path, c.urls(key)[kind])
        assert data is not None and item["http_status"] == 200
        receipt_path = path.with_name(path.name + ".receipt.json")
        reused.setdefault(key, {})[kind] = {"response": path.relative_to(c.ROOT).as_posix(), "response_sha256": c.sha(path),
            "receipt": receipt_path.relative_to(c.ROOT).as_posix(), "receipt_sha256": c.sha(receipt_path)}
    assert len(reused) == 4 and sum(len(pair) for pair in reused.values()) == 8
    regions = make_region_plan(parents, reused)
    schema_path = c.OLD_ART / "public_metadata/mm10_knownGene_schema.json"
    schema = c.read(schema_path)
    assert schema["genome"] == "mm10" and schema["track"] == "knownGene" and schema["shortLabel"] == "GENCODE VM23" and schema["dataTime"] == c.ANNOTATION_TIME
    c.csvsave(c.OUT / "candidate_metadata.csv.gz", rows, c.ROW_COLS)
    c.jsave(c.OUT / "parent_reference_candidates.json", parents)
    c.jsave(c.OUT / "region_plan.json", regions)
    c.jsave(c.OUT / "metadata_preparation_receipt.json", {"status": "PASS_COMPLETE_METADATA_ONLY_PREPARATION", "original_rows": len(rows), "original_parents": len(parents),
        "full_parent_context_menus": len(c.menu_counts(rows)), "parent_status_by_dataset": {d: dict(Counter(p["status"] for p in parents if p["dataset"] == d)) for d in sorted({p["dataset"] for p in parents})},
        "regions": len(regions), "region_status_counts": dict(Counter(r["planned_status"] for r in regions)),
        "eligible_region_bases": sum(r["region_bases"] for r in regions if r["planned_status"] == "eligible"),
        "new_requests_planned": sum(2 - len(r["reuse"]) for r in regions if r["planned_status"] == "eligible"), "pilot_responses_reused": 8,
        "files": prior["files"] | {prefit.relative_to(c.ROOT).as_posix(): c.sha(prefit)},
        "canonical_identity_fields_only": c.IDENTITY, "sequence_fields_only": c.COLS,
        "full_author_transcript_candidates_recomputed_exactly": True, "new_remote_requests": 0,
        "outcomes_read": False, "conservation_values_read": False, "features_loaded": False, "models_fit": 0})
    print("Complete metadata preparation PASS", len(rows), "rows", len(parents), "parents; new requests0", flush=True)
    print("Fixed regions", len(regions), "eligible bases", sum(r["region_bases"] for r in regions if r["planned_status"] == "eligible"), "planned HTTP requests", sum(2 - len(r["reuse"]) for r in regions if r["planned_status"] == "eligible"), flush=True)


def freeze():
    assert not c.DESIGN.exists() and not (c.OUT / "mapping_receipt.json").exists()
    tests = c.read(c.OUT / "synthetic_tests_receipt_v4.json")
    sources = {p.relative_to(c.ROOT).as_posix(): c.sha(p) for p in sorted(c.SRC.glob("*.py"))}
    assert tests["status"] == "PASS" and tests["source_hashes"] == sources
    metadata = c.read(c.OUT / "metadata_preparation_receipt.json")
    assert metadata["status"] == "PASS_COMPLETE_METADATA_ONLY_PREPARATION"
    assert (c.REP / "plan.md").is_file()
    paths = [p for home in (c.SRC, c.OUT, c.REP, c.ART) for p in home.rglob("*") if p.is_file()]
    paths += [c.ROOT / name for name in metadata["files"]]
    paths += [p for home in (c.OLD_SRC, c.OLD_OUT, c.OLD_ART, c.ROOT / "reports/generalization_conservation_feasibility_20261007") for p in home.rglob("*") if p.is_file()]
    for name, expected in metadata["files"].items():
        assert c.sha(c.ROOT / name) == expected
    c.jsave(c.DESIGN, {"status": "FROZEN_OUTCOME_BLIND_FULL_COORDINATE_MAPPING", "files": {p.relative_to(c.ROOT).as_posix(): c.sha(p) for p in sorted(set(paths))},
        "original_rows": 26258, "original_parents": 3022, "region_cap_bases": c.MAX_REGION, "total_region_cap_bases": c.MAX_TOTAL,
        "response_byte_cap": c.MAX_RESPONSE, "one_overflow_detection_byte_only": True, "request_spacing_seconds": 1.05,
        "fixed_region_roster_sha256": c.sha(c.OUT / "region_plan.json"), "assembly": "mm10/GRCm38", "annotation": "knownGene GENCODE VM23", "annotation_data_time": c.ANNOTATION_TIME,
        "complete_candidate_rule": "Any unresolved anchored transcript/region prevents complete unique certification; all original rows and menus remain; missing coordinates never mean zero conservation",
        "root_review_commit_and_explicit_start_required": True, "new_region_requests_run": False,
        "outcomes_read": False, "conservation_values_read": False, "models_fit": 0, "old_freezes_modified": False})
    print("Full coordinate design freeze", len(c.read(c.DESIGN)["files"]), c.sha(c.DESIGN), flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["local"], ["freeze"])
    {"local": local, "freeze": freeze}[sys.argv[1]]()
