"""Independent direct-exon/base replay; no original v1 numerical imports."""
from __future__ import annotations
from collections import Counter
import sys
from . import common as c
from .transport import cached


def ordered_positions(record):
    left = [int(value) for value in record["exonStarts"].split(",") if value]
    right = [int(value) for value in record["exonEnds"].split(",") if value]
    assert len(left) == len(right) == record["exonCount"] and record["strand"] in ("+", "-")
    assert all(a < b for a, b in zip(left, right)) and all(right[i] <= left[i + 1] for i in range(len(left) - 1))
    assert record["txStart"] <= record["cdsStart"] < record["cdsEnd"] <= record["txEnd"]
    assert all(record["txStart"] <= a < b <= record["txEnd"] for a, b in zip(left, right))
    intervals = list(zip(left, right))
    if record["strand"] == "-":
        intervals.reverse()
    result = []
    for lo, hi in intervals:
        for position in range(lo, hi) if record["strand"] == "+" else range(hi - 1, lo - 1, -1):
            if (record["strand"] == "+" and position >= record["cdsEnd"]) or (record["strand"] == "-" and position < record["cdsStart"]):
                result.append(position)
    return result


def direct_bases(dna, region_start, positions, strand):
    assert strand in ("+", "-") and all(region_start <= p < region_start + len(dna) for p in positions)
    mapping = dict(zip("ACGTN", "TGCAN"))
    return "".join(dna[p - region_start] if strand == "+" else mapping[dna[p - region_start]] for p in positions)


def pilot_audit():
    """Audit every preserved pilot vector/identity/edit before preparing expansion."""
    design = c.read(c.OLD_OUT / "pilot_design_manifest.json")
    c.committed(c.OLD_OUT / "pilot_design_manifest.json")
    for name, expected in design["files"].items():
        assert c.sha(c.ROOT / name) == expected, name
    completed = c.read(c.OLD_OUT / "pilot_mapping_receipt.json")
    prior = c.read(c.OLD_OUT / "independent_coordinate_replay_receipt.json")
    assert completed["status"] == "COMPLETED_COORDINATE_FEASIBILITY_ONLY" and prior["status"] == "PASS_COORDINATE_REPLAY_ONLY"
    assert prior["pilot_mapping_receipt_sha256"] == c.sha(c.OLD_OUT / "pilot_mapping_receipt.json")
    assert prior["replay_source_sha256"] == c.sha(c.OLD_SRC / "replay.py")
    for name, expected in completed["files"].items():
        assert c.sha(c.ROOT / name) == expected
    reference, response_pins = {}, {}
    for name, expected in completed["remote_reference_receipts"].items():
        receipt = c.ROOT / name
        assert c.sha(receipt) == expected
        item = c.read(receipt)
        path = receipt.with_name(receipt.name[:-len(".receipt.json")])
        assert item["http_status"] == 200 and c.sha(path) == item["sha256"] and path.stat().st_size == item["bytes"]
        response_pins[name], response_pins[path.relative_to(c.ROOT).as_posix()] = expected, item["sha256"]
        if not any(receipt.name.endswith("_" + kind + ".json.receipt.json") for kind in ("sequence", "knownGene")):
            continue
        data = c.read(path)
        key = (data["chrom"], data["start"], data["end"])
        reference.setdefault(key, {})["sequence" if "dna" in data else "knownGene"] = data
    original = {(p["dataset"], p["parent_id"]): p for p in c.read(c.OLD_OUT / "pilot_parent_metadata.json")}
    parents = c.read(c.OLD_OUT / "pilot_parent_mappings.json")
    lookup, checked_vectors = {}, 0
    for parent in parents:
        source = original[(parent["dataset"], parent["parent_id"])]
        assert source["parent_sequence"] == parent["parent_sequence"]
        for match in parent["matches"]:
            anchors = [ref for ref in source["reference_candidates"] if ref["transcript_id"].split(".")[0] == match["transcript"].split(".")[0]]
            found = False
            for anchor in anchors:
                key = c.region_key(anchor)
                if key not in reference:
                    continue
                records = [record for record in reference[key]["knownGene"]["knownGene"] if record["name"] == match["transcript"]]
                for record in records:
                    positions = ordered_positions(record)
                    if match["positions0"][0] not in positions:
                        continue
                    start = positions.index(match["positions0"][0])
                    if positions[start:start + len(match["positions0"])] != match["positions0"]:
                        continue
                    assert match["strand"] == record["strand"] and match["chrom"] == key[0] and match["assembly"] == "mm10"
                    assert direct_bases(reference[key]["sequence"]["dna"].upper(), key[1], match["positions0"], record["strand"]) == parent["parent_sequence"]
                    found = True
            assert found
            checked_vectors += 1
        vectors = c.vector_set(parent["matches"])
        status = "reference_site_vector_unique" if len(vectors) == 1 else "ambiguous_reference_site_vectors" if vectors else source["status"] if not source["reference_candidates"] else "no_exact_reference_vector"
        assert parent["mapping_status"] == status
        lookup[(parent["dataset"], parent["parent_id"])] = (parent, vectors)
    rows = c.read_columns(c.OLD_OUT / "pilot_candidate_metadata.csv.gz", c.ROW_COLS)
    edits = c.read(c.OLD_OUT / "pilot_edited_site_metadata.json")
    assert [r["intervention_id"] for r in edits] == [r["intervention_id"] for r in rows]
    checked_sites = 0
    for row, edited in zip(rows, edits):
        parent, vectors = lookup[(row["dataset"], row["parent_id"])]
        assert edited["dataset"] == row["dataset"] and edited["gene"] == row["gene_transcript"] and edited["parent_id"] == row["parent_id"]
        assert edited["mapping_status"] == parent["mapping_status"]
        changed = [i for i in range(len(row["parent_sequence"])) if row["parent_sequence"][i] != row["mutant_sequence"][i]]
        assert changed == edited["edit_positions0"]
        expected = []
        if len(vectors) == 1:
            chrom, strand, positions = next(iter(vectors))
            for i in changed:
                a, b = row["parent_sequence"][i], row["mutant_sequence"][i]
                expected.append({"insert_position0": i, "chrom": chrom, "genomic_position0": positions[i], "strand": strand,
                    "expressed_reference": a, "expressed_alternate": b,
                    "genomic_reference": a if strand == "+" else dict(zip("ACGT", "TGCA"))[a],
                    "genomic_alternate": b if strand == "+" else dict(zip("ACGT", "TGCA"))[b]})
        assert expected == edited["edited_site_coordinates"]
        checked_sites += len(expected)
    assert len(parents) == 13 and len(rows) == 5701 and checked_vectors == prior["transcript_match_vectors_checked"]
    assert checked_sites == prior["candidate_edited_site_records_checked"]
    return {"status": "PASS_PRESERVED_PILOT_DIRECT_REPLAY", "parents": len(parents), "rows": len(rows),
        "transcript_vectors": checked_vectors, "edited_site_records": checked_sites, "region_response_count": 8,
        "old_status_scope": "Unique among successfully observed v1 candidates; stricter full-candidate certification is separate",
        "old_completed_receipt_sha256": c.sha(c.OLD_OUT / "pilot_mapping_receipt.json"),
        "old_independent_replay_sha256": c.sha(c.OLD_OUT / "independent_coordinate_replay_receipt.json"),
        "response_pins": response_pins, "outcomes_read": False, "conservation_scores_read": False, "models_fit": 0, "new_requests": 0}


def independent_parent(parent, references):
    expected, unresolved = set(), False
    anchors = {(ref["transcript_id"].split(".")[0], c.region_key(ref)) for ref in parent["reference_candidates"]}
    for transcript, key in anchors:
        item = references[key]
        if item is None:
            unresolved = True
            continue
        ann, dna = item
        records = [record for record in ann["knownGene"] if record["name"].split(".")[0] == transcript]
        if not records:
            unresolved = True
        for record in records:
            try:
                assert record["chrom"] == key[0] and key[1] <= record["txStart"] < record["txEnd"] <= key[2]
                positions = ordered_positions(record)
                utr = direct_bases(dna, key[1], positions, record["strand"])
                offsets = [offset for offset in range(len(utr) - len(parent["parent_sequence"]) + 1) if utr.startswith(parent["parent_sequence"], offset)]
                assert offsets
                for offset in offsets:
                    vector = tuple(positions[offset:offset + len(parent["parent_sequence"])])
                    expected.add((record["name"], key, key[0], record["strand"], vector))
            except (AssertionError, KeyError, TypeError, ValueError):
                unresolved = True
    return expected, unresolved, len(anchors)


def admit_reference(ann, genome, key):
    """Independent schema/release admission; valid JSON is not sufficient."""
    if not isinstance(ann, dict) or not isinstance(genome, dict):
        return None
    if ann.get("genome") != "mm10" or ann.get("track") != "knownGene" or ann.get("dataTime") != c.ANNOTATION_TIME or ann.get("maxItemsLimit", False):
        return None
    if (ann.get("chrom"), ann.get("start"), ann.get("end")) != key or (genome.get("chrom"), genome.get("start"), genome.get("end")) != key or genome.get("genome") != "mm10":
        return None
    if not isinstance(genome.get("dna"), str):
        return None
    dna, records = genome["dna"].upper(), ann.get("knownGene")
    valid = isinstance(records, list) and len(records) < 10000 and ann.get("itemsReturned", len(records)) == len(records)
    if valid:
        valid = all(isinstance(record, dict) and all(isinstance(record.get(name), str) for name in ("name", "chrom", "strand", "exonStarts", "exonEnds"))
            and all(type(record.get(name)) is int for name in ("txStart", "txEnd", "cdsStart", "cdsEnd", "exonCount")) for record in records)
    return (ann, dna) if valid and len(dna) == key[2] - key[1] and set(dna) <= set("ACGTN") else None


def bind_public_responses(completed, plan):
    """Check complete request roster and mapping-time hashes before cache replay."""
    expected = {(tuple(region["key"]), kind): region for region in plan if region["planned_status"] == "eligible" for kind in ("knownGene", "sequence")}
    observed = completed["public_response_receipts"]
    assert len(observed) == len(expected)
    assert len({(tuple(item["region"]), item["kind"]) for item in observed}) == len(observed)
    assert {(tuple(item["region"]), item["kind"]) for item in observed} == set(expected)
    for item in observed:
        key, kind = tuple(item["region"]), item["kind"]
        region = expected[(key, kind)]
        path = c.ROOT / region["reuse"][kind]["response"] if kind in region["reuse"] else c.ART / "public_metadata" / (c.tag(key) + "_" + kind + ".json")
        receipt = path.with_name(path.name + ".receipt.json")
        assert item["response"] == path.relative_to(c.ROOT).as_posix() and item["receipt"] == receipt.relative_to(c.ROOT).as_posix()
        assert c.sha(receipt) == item["receipt_sha256"], "Response receipt changed since mapping"
        internal = c.read(receipt)
        assert internal["url"] == region["urls"][kind] and internal["http_status"] == item["http_status"]
        assert internal["sha256"] == item["response_sha256"]
        if item["response_sha256"] is None:
            assert not path.exists(), "Failed no-body response acquired a payload"
        else:
            assert c.sha(path) == item["response_sha256"] and path.stat().st_size == internal["bytes"]
        # Also binds any overflow prefix through its mapping-time receipt hash.
        cached(path, region["urls"][kind])


def full():
    c.certify()
    completed = c.read(c.OUT / "mapping_receipt.json")
    assert completed["status"] == "COMPLETED_FULL_COORDINATE_METADATA_ONLY"
    for name, expected in completed["files"].items():
        assert c.sha(c.ROOT / name) == expected
    plan = c.read(c.OUT / "region_plan.json")
    bind_public_responses(completed, plan)
    references = {}
    for region in plan:
        key = tuple(region["key"])
        if region["planned_status"] != "eligible":
            references[key] = None
            continue
        loaded = {}
        for kind in ("knownGene", "sequence"):
            path = c.ROOT / region["reuse"][kind]["response"] if kind in region["reuse"] else c.ART / "public_metadata" / (c.tag(key) + "_" + kind + ".json")
            loaded[kind], receipt = cached(path, region["urls"][kind])
            assert receipt is not None
        ann, genome = loaded["knownGene"], loaded["sequence"]
        references[key] = admit_reference(ann, genome, key)
    parents = c.read(c.OUT / "parent_reference_candidates.json")
    mapped = c.read(c.OUT / "parent_mappings.json")
    assert [(p["dataset"], p["parent_id"]) for p in mapped] == [(p["dataset"], p["parent_id"]) for p in parents]
    lookup, vectors_checked = {}, 0
    for parent, result in zip(parents, mapped):
        expected, unresolved, anchor_count = independent_parent(parent, references)
        actual = {(m["transcript"], tuple(m["region"]), m["chrom"], m["strand"], tuple(m["positions0"])) for m in result["matches"]}
        assert actual == expected and result["candidate_anchor_count"] == anchor_count
        assert result["candidate_resolution_complete"] == (bool(anchor_count) and not unresolved)
        assert bool(result["unresolved_candidates"]) == unresolved
        vectors = {(chrom, strand, vector) for transcript, region, chrom, strand, vector in expected}
        status = "synthetic_no_native_coordinates" if parent["dataset"] == "srle" else "no_exact_source_utr" if not parent["reference_candidates"] else "unresolved_reference_candidates" if unresolved else c.MAPPED if len(vectors) == 1 else "ambiguous_reference_site_vectors" if vectors else "no_exact_reference_vector"
        assert status == result["mapping_status"]
        vectors_checked += len(expected)
        lookup[(parent["dataset"], parent["parent_id"])] = (status, vectors)
    rows = c.read_columns(c.OUT / "candidate_metadata.csv.gz", c.ROW_COLS, exact=True)
    edited = c.read(c.OUT / "edited_site_metadata.json")
    assert len(rows) == len(edited) == 26258 and c.menu_counts(rows) == c.menu_counts(edited)
    checked_sites = 0
    for row, result in zip(rows, edited):
        assert all(result[name] == row[name] for name in c.ROW_COLS)
        status, vectors = lookup[(row["dataset"], row["parent_id"])]
        assert result["mapping_status"] == status
        changes = [i for i in range(len(row["parent_sequence"])) if row["parent_sequence"][i] != row["mutant_sequence"][i]]
        assert result["edit_positions0"] == changes
        expected = []
        if status == c.MAPPED:
            chrom, strand, vector = next(iter(vectors))
            for i in changes:
                a, b = row["parent_sequence"][i], row["mutant_sequence"][i]
                expected.append({"insert_position0": i, "chrom": chrom, "genomic_position0": vector[i], "strand": strand,
                    "expressed_reference": a, "expressed_alternate": b,
                    "genomic_reference": a if strand == "+" else dict(zip("ACGT", "TGCA"))[a],
                    "genomic_alternate": b if strand == "+" else dict(zip("ACGT", "TGCA"))[b]})
        assert result["edited_site_coordinates"] == expected
        checked_sites += len(expected)
    c.certify()
    c.jsave(c.OUT / "independent_mapping_replay_receipt.json", {"status": "PASS_FULL_DIRECT_COORDINATE_REPLAY_ONLY",
        "parents": len(parents), "original_candidate_rows": len(rows), "transcript_vectors": vectors_checked,
        "edited_site_records": checked_sites, "complete_original_menus_and_identity_replayed": True,
        "source_manifest_sha256": c.sha(c.DESIGN), "mapping_receipt_sha256": c.sha(c.OUT / "mapping_receipt.json"),
        "independent_reference_exon_strand_and_all_candidate_enumeration": True,
        "outcomes_read": False, "conservation_scores_read": False, "models_fit": 0, "genome_wide_uniqueness_or_actual_isoform_certified": False})
    print("Independent full coordinate replay PASS", len(rows), "rows", len(parents), "parents", flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] == ["full"]
    full()
