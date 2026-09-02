"""Fetch and freeze MGI human-to-mouse homology for RBPNet channels.

The source is the Mouse Genome Informatics homology report.  The script reads
only the RBP checkpoint manifest and never accesses assay or protected data.
"""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
INFILE = ROOT / "results" / "finalshot" / "rbpnet_checkpoint_manifest.csv"
RAW_REPORT = ROOT / "data" / "raw" / "finalshot_resource_audit" / "HOM_MouseHumanSequence.rpt"
OUTFILE = ROOT / "results" / "finalshot" / "rbp_orthology_mgi_2026-09-02.csv"
REPORT_URL = "https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt"
EXPECTED_SHA256 = "3d4bc89e71e57e10adf0139ba033786cb02e2e24e8d49cf0c357d1c2924afa0a"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download() -> None:
    if RAW_REPORT.exists() and sha256(RAW_REPORT) == EXPECTED_SHA256:
        return
    request = Request(REPORT_URL, headers={"User-Agent": "RNAddress-resource-audit"})
    with urlopen(request, timeout=120) as response:
        payload = response.read()
    RAW_REPORT.parent.mkdir(parents=True, exist_ok=True)
    RAW_REPORT.write_bytes(payload)
    if sha256(RAW_REPORT) != EXPECTED_SHA256:
        raise RuntimeError("MGI report changed from the 2026-09-02 audited snapshot")


def main() -> None:
    download()
    with INFILE.open("r", encoding="utf-8", newline="") as handle:
        human_rbps = sorted({row["rbp"] for row in csv.DictReader(handle)})

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with RAW_REPORT.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            groups[row["DB Class Key"]].append(row)

    human_index: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
    for group_key, records in groups.items():
        for record in records:
            if record["NCBI Taxon ID"] == "9606":
                human_index[record["Symbol"]].append((group_key, record))

    rows: list[dict[str, object]] = []
    for rbp in human_rbps:
        matches = human_index.get(rbp, [])
        if not matches:
            rows.append({
                "snapshot_date": "2026-09-02", "source_sha256": EXPECTED_SHA256,
                "human_rbp": rbp, "homology_group": "", "human_entrez": "", "human_hgnc": "",
                "mouse_symbol": "", "mouse_entrez": "", "mouse_mgi_id": "", "mouse_coordinates": "",
                "mapping_status": "missing",
            })
            continue
        for group_key, human in matches:
            mice = [record for record in groups[group_key] if record["NCBI Taxon ID"] == "10090"]
            if not mice:
                mice = [{}]
            group_humans = [record for record in groups[group_key] if record["NCBI Taxon ID"] == "9606"]
            status = "one_to_one" if len(group_humans) == 1 and len(mice) == 1 and mice[0] else "non_one_to_one"
            for mouse in mice:
                rows.append({
                    "snapshot_date": "2026-09-02",
                    "source_sha256": EXPECTED_SHA256,
                    "human_rbp": rbp,
                    "homology_group": group_key,
                    "human_entrez": human["EntrezGene ID"],
                    "human_hgnc": human["HGNC ID"],
                    "mouse_symbol": mouse.get("Symbol", ""),
                    "mouse_entrez": mouse.get("EntrezGene ID", ""),
                    "mouse_mgi_id": mouse.get("Mouse MGI ID", ""),
                    "mouse_coordinates": mouse.get("Genome Coordinates (mouse: GRCm39 human: GRCh38)", ""),
                    "mapping_status": status,
                })

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
