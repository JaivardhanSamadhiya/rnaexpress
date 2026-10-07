"""Deterministic direct-human PFM evidence manifest; no project data inputs."""

from collections import Counter
import csv
import io
import json
import zipfile

from src.research_20260921 import common as _runtime
import numpy as np

from .prepare_catalog import ART, OUT, REP, ROOT, digest, jsave, save

EVIDENCE_TYPES = frozenset(("RNAcompete", "RNA-Bind-n-Seq", "HTR-SELEX", "SELEX",
                           "RIP-chip", "PAR-clip", "yeast three-hybrid screen", "SEQRS", "CLIP-seq"))
EXPECTED_ARCHIVE_SHA = "5dba2f07d48b173d2309cde21e2309aa29473dfe8aa59402290849430a891030"
BASE_ORDER = "ACGU"


def parse_evidence(data):
    rows = list(csv.reader(io.StringIO(data.decode("utf-8")), delimiter="\t"))
    header = rows[0]
    assert len(header) == 26 and header[5] == header[13] == "DBID"
    header = list(header)
    header[5], header[13] = "RBP_DBID", "Motif_DBID"
    assert len(set(header)) == len(header)
    records = []
    for row in rows[1:]:
        if not row:
            continue
        assert len(row) == len(header)
        records.append(dict(zip(header, row)))
    return records


def direct_human(record):
    # RBP_Status describes the protein, not the experimental provenance of all
    # associated motifs. In particular, some D proteins also have JPLE motifs.
    return (record["RBP_Species"] == "Homo_sapiens"
            and record["RBP_Status"] == "D"
            and record["Motif_Type"] in EVIDENCE_TYPES)


def parse_pfm(data):
    rows = list(csv.reader(io.StringIO(data.decode("utf-8")), delimiter="\t"))
    if not rows:
        raise ValueError("No matrix supplied in empty official PFM member")
    assert rows[0] == ["Pos", "A", "C", "G", "U"], "Author strand/base order must be explicit"
    rows = [row for row in rows[1:] if row]
    assert rows and all(len(row) == 5 for row in rows)
    assert [int(row[0]) for row in rows] == list(range(1, len(rows) + 1))
    value = np.asarray([[float(x) for x in row[1:]] for row in rows], dtype="<f8")
    assert np.isfinite(value).all() and np.all(value >= 0)
    totals = value.sum(1)
    assert np.all(totals > 0) and np.allclose(totals, 1., atol=1e-6, rtol=0)
    return np.asarray(value / totals[:, None], dtype="<f8")


def matrix_digest(pfm):
    value = np.asarray(pfm, dtype="<f8")
    assert value.ndim == 2 and value.shape[1] == 4
    return digest(str(value.shape).encode("ascii") + b"\n" + value.tobytes(order="C"))


def derive():
    archive_path = ART / "official_human_pfms_evidence.zip"
    archive_bytes = archive_path.read_bytes()
    assert digest(archive_bytes) == EXPECTED_ARCHIVE_SHA
    receipt = json.loads((ART / "resource_receipt.json").read_text())
    for name, checksum in receipt["saved_files"].items():
        assert digest((ROOT / name).read_bytes()) == checksum
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        # This main table lists motifs associated with the human protein itself;
        # all_motifs additionally expands motifs of related proteins.
        evidence_bytes = archive.read("RBP_Information.txt")
        records = parse_evidence(evidence_bytes)
        direct = sorted((r for r in records if direct_human(r)),
                        key=lambda r: (r["Motif_ID"], r["RBP_ID"], r["MSource_ID"]))
        available = set(archive.namelist())
        mappings, excluded, by_hash = [], [], {}
        for record in direct:
            member = "pwms_all_motifs/" + record["Motif_ID"] + ".txt"
            if member not in available:
                excluded.append({**record, "reason": "No PFM member in official export"})
                continue
            content = archive.read(member)
            if not content.strip():
                excluded.append({**record, "reason": "Empty PFM member in official export",
                                 "archive_member": member, "member_sha256": digest(content)})
                continue
            pfm = parse_pfm(content)
            matrix_sha = matrix_digest(pfm)
            mapping = {**record, "archive_member": member, "member_sha256": digest(content),
                       "width_nt": len(pfm), "normalized_pfm_sha256": matrix_sha}
            mappings.append(mapping)
            if matrix_sha not in by_hash:
                by_hash[matrix_sha] = {"representative_motif_id": record["Motif_ID"],
                    "normalized_pfm_sha256": matrix_sha, "width_nt": len(pfm),
                    "probabilities_ACGU": pfm.tolist(), "motif_ids": [], "rbp_ids": [],
                    "rbp_names": [], "experimental_types": []}
            group = by_hash[matrix_sha]
            group["motif_ids"].append(record["Motif_ID"])
            group["rbp_ids"].append(record["RBP_ID"])
            group["rbp_names"].append(record["RBP_Name"])
            group["experimental_types"].append(record["Motif_Type"])
    motifs = sorted(by_hash.values(), key=lambda m: m["representative_motif_id"])
    for motif in motifs:
        for key in ("motif_ids", "rbp_ids", "rbp_names", "experimental_types"):
            motif[key] = sorted(set(motif[key]))
    assert len({m["normalized_pfm_sha256"] for m in motifs}) == len(motifs)
    selected_ids = {m["Motif_ID"] for m in mappings}
    rejected = [r for r in records if not direct_human(r)]
    manifest = {
        "status": "DIRECT_HUMAN_EXPERIMENTAL_CATALOG_PREPARED_NO_BIOLOGICAL_FIT",
        "archive_sha256": EXPECTED_ARCHIVE_SHA,
        "resource_receipt_sha256": digest((ART / "resource_receipt.json").read_bytes()),
        "evidence_member": "RBP_Information.txt", "evidence_member_sha256": digest(evidence_bytes),
        "unused_homology_expansion_member": "RBP_Information_all_motifs.txt",
        "filter": {"species": "Homo_sapiens", "RBP_Status": "D",
                   "Motif_Type_whitelist": sorted(EVIDENCE_TYPES),
                   "JPLE_excluded_even_for_D_protein": True,
                   "empirical_provenance_scope": "Includes in-vitro assays and direct CLIP/RIP-derived motifs; not all intrinsic binding measurements"},
        "evidence_rows": len(records), "eligible_mappings_before_member_check": len(direct),
        "retained_evidence_mappings": len(mappings), "direct_motif_ids_before_dedup": len(selected_ids),
        "retained_human_rbp_ids": len({m["RBP_ID"] for m in mappings}),
        "unique_normalized_pfms": len(motifs),
        "duplicate_motif_ids_removed": len(selected_ids) - len(motifs),
        "duplicate_rule": "Exact SHA256 of shape plus little-endian float64 row-normalized ACGU matrix; retain lexical first motif ID; preserve all evidence mappings",
        "missing_pfm_mappings": excluded,
        "missing_pfm_reason_counts": dict(Counter(r["reason"] for r in excluded)),
        "excluded_mappings_by_status": dict(Counter(r["RBP_Status"] for r in rejected)),
        "excluded_mappings_by_motif_type": dict(Counter(r["Motif_Type"] for r in rejected)),
        "retained_mappings_by_experimental_type": dict(Counter(m["Motif_Type"] for m in mappings)),
        "width_counts": {str(k): v for k, v in sorted(Counter(m["width_nt"] for m in motifs).items())},
        "standalone_catalog_license": "No standalone license found on inspected pages or in archive; no redistribution certified",
        "use_policy": "Internal computational research only, cite official data provenance and source papers",
        "project_data_loaded": False, "project_features_computed": False,
        "supervised_models_fit": 0, "protected_outcomes_opened": False,
        "motifs": motifs,
    }
    jsave(ART / "direct_human_manifest.json", manifest)
    buffer = io.StringIO()
    fields = list(mappings[0])
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(mappings)
    save(ART / "direct_human_evidence.csv", buffer.getvalue().encode())
    jsave(OUT / "catalog_preparation_receipt.json", {
        key: manifest[key] for key in ("status", "evidence_rows", "eligible_mappings_before_member_check",
        "retained_evidence_mappings", "direct_motif_ids_before_dedup", "retained_human_rbp_ids",
        "unique_normalized_pfms", "duplicate_motif_ids_removed", "width_counts",
        "project_data_loaded", "project_features_computed", "supervised_models_fit", "protected_outcomes_opened")})
    print(json.dumps({key: manifest[key] for key in ("status", "retained_evidence_mappings",
        "retained_human_rbp_ids", "unique_normalized_pfms", "duplicate_motif_ids_removed")}, indent=2), flush=True)
    return manifest


if __name__ == "__main__":
    derive()
