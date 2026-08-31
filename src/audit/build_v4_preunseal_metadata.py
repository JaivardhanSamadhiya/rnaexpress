"""Freeze outcome-blind Phase A metadata before the Moffatt development unseal."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "v4_phaseA"
URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE334nnn/GSE334718/"
    "miniml/GSE334718_family.xml.tgz"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = urllib.request.urlopen(URL, timeout=60).read()  # noqa: S310
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if m.isfile() and m.name.endswith(".xml")]
        if len(members) != 1:
            raise ValueError(f"Expected one MINiML XML member, found {len(members)}")
        xml_bytes = archive.extractfile(members[0]).read()
    root = ET.fromstring(xml_bytes)
    rows: list[dict[str, object]] = []
    for sample in root.findall("{*}Sample"):
        accession = sample.findtext("{*}Accession", default="").strip()
        title = sample.findtext("{*}Title", default="").strip()
        supplementary = sample.findtext("{*}Supplementary-Data", default="").strip()
        match = re.fullmatch(
            r"(Mutation|Necessity|SHAPE|Shuffle|Sufficiency) MPRA, "
            r"(Firefly|GFP), (Neurite|Soma) Rep([1-4])",
            title,
        )
        if not match:
            raise ValueError(f"Unexpected Moffatt sample title: {title!r}")
        assay, reporter, compartment, replicate = match.groups()
        filename = supplementary.rsplit("/", 1)[-1]
        rows.append(
            {
                "geo_accession": accession,
                "title": title,
                "assay_family": assay.lower(),
                "reporter": reporter.lower(),
                "compartment": compartment.lower(),
                "biological_replicate": int(replicate),
                "processed_count_filename": filename,
                "processed_count_url": supplementary.replace("ftp://", "https://"),
            }
        )
    rows.sort(key=lambda row: str(row["geo_accession"]))
    if len(rows) != 80:
        raise ValueError(f"Expected 80 samples, found {len(rows)}")
    keys = [(r["assay_family"], r["reporter"], r["compartment"], r["biological_replicate"]) for r in rows]
    if len(set(keys)) != 80:
        raise ValueError("Moffatt outcome-blind sample design keys are not unique")
    csv_path = OUT / "moffatt_geo_sample_manifest.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "phase": "v4_phaseA_preunseal",
        "outcome_blind": True,
        "source_url": URL,
        "miniml_tgz_sha256": sha256(payload),
        "miniml_xml_sha256": sha256(xml_bytes),
        "sample_count": len(rows),
        "assay_families": sorted({str(r["assay_family"]) for r in rows}),
        "reporters": sorted({str(r["reporter"]) for r in rows}),
        "compartments": sorted({str(r["compartment"]) for r in rows}),
        "replicates": sorted({int(r["biological_replicate"]) for r in rows}),
        "csv_sha256": sha256(csv_path.read_bytes()),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    (OUT / "moffatt_preunseal_metadata_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
