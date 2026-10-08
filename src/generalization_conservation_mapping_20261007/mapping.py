"""All-candidate full-parent reference mapping; fixed menus and missingness."""
from __future__ import annotations
from collections import Counter
import json, re, sys
from . import common as c
from .transport import Client, cached


def validate_region(ann, genome, key):
    chrom, start, end = key
    if ann is None or genome is None:
        return None, "reference_response_missing"
    if not isinstance(ann, dict) or not isinstance(genome, dict):
        return None, "reference_top_level_schema_mismatch"
    if ann.get("genome") != "mm10" or ann.get("track") != "knownGene" or ann.get("dataTime") != c.ANNOTATION_TIME:
        return None, "annotation_source_version_or_schema_mismatch"
    if ann.get("chrom") != chrom or ann.get("start") != start or ann.get("end") != end or ann.get("maxItemsLimit", False):
        return None, "annotation_region_or_item_limit_mismatch"
    if genome.get("genome") != "mm10" or genome.get("chrom") != chrom or genome.get("start") != start or genome.get("end") != end:
        return None, "sequence_region_mismatch"
    if not isinstance(genome.get("dna"), str):
        return None, "sequence_DNA_schema_mismatch"
    dna = genome["dna"].upper()
    if len(dna) != end - start or not re.fullmatch("[ACGTN]+", dna):
        return None, "sequence_length_or_alphabet_mismatch"
    if not isinstance(ann.get("knownGene"), list):
        return None, "annotation_records_schema_mismatch"
    if len(ann["knownGene"]) >= 10000 or ann.get("itemsReturned", len(ann["knownGene"])) != len(ann["knownGene"]):
        return None, "annotation_item_limit_or_count_mismatch"
    string_fields = ("name", "chrom", "strand", "exonStarts", "exonEnds")
    numeric_fields = ("txStart", "txEnd", "cdsStart", "cdsEnd", "exonCount")
    if any(not isinstance(record, dict) or any(not isinstance(record.get(name), str) for name in string_fields)
           or any(type(record.get(name)) is not int for name in numeric_fields) for record in ann["knownGene"]):
        return None, "annotation_records_schema_mismatch"
    return (ann["knownGene"], dna), None


def resolve_parent(parent, regions):
    matches, unresolved, resolved = [], [], []
    anchors = sorted({(ref["transcript_id"].split(".")[0], c.region_key(ref)) for ref in parent["reference_candidates"]})
    for transcript, key in anchors:
        region = regions[key]
        if region["failure"]:
            unresolved.append({"transcript": transcript, "region": list(key), "reason": region["failure"]})
            continue
        records, dna = region["data"]
        eligible = [record for record in records if record["name"].split(".")[0] == transcript]
        if not eligible:
            unresolved.append({"transcript": transcript, "region": list(key), "reason": "stable_transcript_absent_from_fixed_annotation"})
            continue
        anchor_ok = True
        for record in eligible:
            reason = None
            if record.get("chrom") != key[0] or int(record["txStart"]) < key[1] or int(record["txEnd"]) > key[2]:
                reason = "annotation_outside_fixed_author_gene_region"
            else:
                try:
                    utr, positions = c.transcript_utr(record, dna, key[1])
                    if utr is None:
                        reason = "noncoding_or_uncertified_coding_3UTR"
                    else:
                        offsets = c.occurrences(utr, parent["parent_sequence"])
                        if not offsets:
                            reason = "source_parent_sequence_version_incompatible"
                        for offset in offsets:
                            matches.append({"transcript": record["name"], "chrom": key[0], "strand": record["strand"],
                                "positions0": positions[offset:offset + len(parent["parent_sequence"])], "utr_start0": offset,
                                "region": list(key), "assembly": "mm10", "annotation_data_time": c.ANNOTATION_TIME})
                except (AssertionError, KeyError, TypeError, ValueError):
                    reason = "exon_or_strand_metadata_not_certified"
            if reason:
                anchor_ok = False
                unresolved.append({"transcript": transcript, "annotation_record": record["name"], "region": list(key), "reason": reason})
        if anchor_ok:
            resolved.append({"transcript": transcript, "region": list(key)})
    status = c.mapping_status(parent, matches, unresolved)
    return {key: value for key, value in parent.items() if key != "reference_candidates"} | {
        "mapping_status": status, "matches": matches, "resolved_candidate_anchors": resolved,
        "candidate_anchor_count": len(anchors), "candidate_resolution_complete": bool(anchors) and not unresolved and len(resolved) == len(anchors),
        "unresolved_candidates": unresolved}


def load_regions(plan):
    allowed = [url for region in plan if region["planned_status"] == "eligible" for url in region["urls"].values()]
    client = Client(allowed) if allowed else None
    result, records = {}, []
    for region in plan:
        key = tuple(region["key"])
        if region["planned_status"] != "eligible":
            result[key] = {"failure": region["planned_status"], "data": None}
            continue
        values = {}
        for kind in ("knownGene", "sequence"):
            if kind in region["reuse"]:
                path = c.ROOT / region["reuse"][kind]["response"]
                value, receipt = cached(path, region["urls"][kind])
            else:
                path = c.ART / "public_metadata" / (c.tag(key) + "_" + kind + ".json")
                value, receipt = client.get(region["urls"][kind], path)
            values[kind] = value
            receipt_path = path.with_name(path.name + ".receipt.json")
            records.append({"region": list(key), "kind": kind, "response": path.relative_to(c.ROOT).as_posix(),
                "receipt": receipt_path.relative_to(c.ROOT).as_posix(), "receipt_sha256": c.sha(receipt_path),
                "http_status": receipt["http_status"], "response_sha256": receipt.get("sha256"),
                "reused_immutable_pilot": kind in region["reuse"]})
        data, failure = validate_region(values["knownGene"], values["sequence"], key)
        result[key] = {"data": data, "failure": failure}
        print("Coordinate metadata region", c.tag(key), "missing:" + failure if failure else "reference bytes admitted", flush=True)
    return result, records, client.new_requests if client else 0


def run():
    c.certify()
    assert not (c.OUT / "mapping_receipt.json").exists(), "Preserve completed mapping"
    rows = c.read_columns(c.OUT / "candidate_metadata.csv.gz", c.ROW_COLS, exact=True)
    parents = c.read(c.OUT / "parent_reference_candidates.json")
    regions, response_receipts, requests = load_regions(c.read(c.OUT / "region_plan.json"))
    mapped = [resolve_parent(parent, regions) for parent in parents]
    lookup = {(item["dataset"], item["parent_id"]): item for item in mapped}
    sites = []
    for row in rows:
        parent = lookup[(row["dataset"], row["parent_id"])]
        assert parent["parent_sequence"] == row["parent_sequence"] and parent["gene"] == row["gene_transcript"]
        changed, coordinates = c.edited_coordinates(row, parent)
        sites.append({name: row[name] for name in c.ROW_COLS} | {"mapping_status": parent["mapping_status"],
            "edit_positions0": changed, "edited_site_coordinates": coordinates})
    assert [item["intervention_id"] for item in sites] == [item["intervention_id"] for item in rows]
    assert len(sites) == 26258 and c.menu_counts(sites) == c.menu_counts(rows)
    c.jsave(c.OUT / "parent_mappings.json", mapped)
    c.jsave(c.OUT / "edited_site_metadata.json", sites)
    c.certify()
    c.jsave(c.OUT / "mapping_receipt.json", {"status": "COMPLETED_FULL_COORDINATE_METADATA_ONLY",
        "parents": len(mapped), "original_candidate_rows": len(sites), "all_original_rows_and_full_menus_retained": True,
        "parent_status_by_dataset": {dataset: dict(Counter(item["mapping_status"] for item in mapped if item["dataset"] == dataset)) for dataset in sorted({item["dataset"] for item in mapped})},
        "row_status_by_dataset": {dataset: dict(Counter(item["mapping_status"] for item in sites if item["dataset"] == dataset)) for dataset in sorted({item["dataset"] for item in sites})},
        "files": {path.relative_to(c.ROOT).as_posix(): c.sha(path) for path in (c.OUT / "parent_mappings.json", c.OUT / "edited_site_metadata.json")},
        "new_region_requests": requests, "public_response_receipts": response_receipts,
        "design_manifest_sha256": c.sha(c.DESIGN), "preservation_before_and_after": True,
        "conservation_values_read": False, "outcomes_read": False, "features_loaded": False, "models_fit": 0,
        "genome_wide_uniqueness_or_actual_isoform_certified": False,
        "stricter_than_pilot": "Any unresolved anchored candidate prevents complete unique certification; v1 pilot statuses remain unchanged"})
    print("Full coordinate-only mapping completed; rows retained", len(sites), "parents", len(mapped), flush=True)


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
