"""Create the provenance manifest and lock the external astrocyte benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACQUISITION_OUT = ROOT / "data" / "manifests" / "acquisition_manifest.csv"
EXTERNAL_OUT = ROOT / "data" / "frozen" / "external_manifest.json"


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def source(
    dataset: str,
    paper: str,
    doi: str,
    accession: str,
    url: str,
    relative_file: str,
    organism: str,
    cell_type: str,
    assay: str,
    license_name: str,
    level: str,
    notes: str,
) -> dict[str, object]:
    path = ROOT / relative_file
    return {
        "dataset": dataset,
        "paper": paper,
        "DOI": doi,
        "accession": accession,
        "URL": url,
        "file": relative_file,
        "checksum": f"sha256:{sha256(path)}" if path.exists() else "",
        "size": path.stat().st_size if path.exists() else "",
        "downloaded": "yes" if path.exists() else "no",
        "organism": organism,
        "cell type": cell_type,
        "assay": assay,
        "public status": "public",
        "license": license_name,
        "raw/processed": level,
        "notes": notes,
    }


def repository(
    dataset: str,
    paper: str,
    doi: str,
    accession: str,
    url: str,
    relative_directory: str,
    commit: str,
    organism: str,
    cell_type: str,
    assay: str,
    license_name: str,
    notes: str,
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "paper": paper,
        "DOI": doi,
        "accession": accession,
        "URL": url,
        "file": f"{relative_directory}@{commit}",
        "checksum": f"git:{commit}",
        "size": "directory",
        "downloaded": "yes",
        "organism": organism,
        "cell type": cell_type,
        "assay": assay,
        "public status": "public",
        "license": license_name,
        "raw/processed": "code",
        "notes": notes,
    }


def build_acquisition_manifest() -> list[dict[str, object]]:
    rows = [
        source("Mikl", "Systematic analysis of RNA localization elements", "10.1093/nar/gkac806", "GSE173098", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE173nnn/GSE173098/suppl/GSE173098_RNAloc_MPRA_counts.csv.gz", "data/raw/mikl_gse173098/GSE173098_RNAloc_MPRA_counts.csv.gz", "Mus musculus", "CAD and Neuro-2a neuronal cell lines", "RNA localization MPRA", "GEO terms; article CC BY", "processed", "Raw per-replicate compartment counts for 47,989 library sequences."),
        source("Mikl", "Systematic analysis of RNA localization elements", "10.1093/nar/gkac806", "GSE173098", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/bin/gkac806_supplemental_files.zip", "data/raw/mikl_gse173098/supplementary/gkac806_supplemental_files.zip", "Mus musculus", "CAD and Neuro-2a neuronal cell lines", "RNA localization MPRA and ActD stability", "CC BY", "processed", "Supplementary tables, including analyzed construct-level outcomes and full library sequences."),
        source("N-zip", "Massively parallel functional dissection of 3' UTRs in neurons", "10.1038/s41593-022-01243-x", "E-MTAB-10902; E-MTAB-11572; E-MTAB-11575", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/bin/41593_2022_1243_MOESM2_ESM.xlsx", "data/raw/nzip/supplementary/41593_2022_1243_MOESM2_ESM.xlsx", "Mus musculus", "primary cortical neurons", "neurite/soma MPRA, knockdown MPRA and SLAM-seq", "CC BY", "processed", "Initial library and mutagenesis library sequence/outcome tables."),
        source("N-zip", "Massively parallel functional dissection of 3' UTRs in neurons", "10.1038/s41593-022-01243-x", "E-MTAB-10902", "https://www.ebi.ac.uk/biostudies/files/E-MTAB-10902/E-MTAB-10902.sdrf.txt", "data/raw/nzip/E-MTAB-10902.sdrf.txt", "Mus musculus", "primary cortical neurons", "neurite/soma MPRA", "BioStudies record", "metadata", "Public sample and raw-file metadata; processed workbook is sufficient for tuple reconstruction."),
        source("N-zip", "Massively parallel functional dissection of 3' UTRs in neurons", "10.1038/s41593-022-01243-x", "E-MTAB-11572", "https://www.ebi.ac.uk/biostudies/files/E-MTAB-11572/E-MTAB-11572.sdrf.txt", "data/raw/nzip/E-MTAB-11572.sdrf.txt", "Mus musculus", "primary cortical neurons", "compartment RNA-seq after degradation-machinery perturbation", "BioStudies record", "metadata", "Public sample and raw-file metadata."),
        source("N-zip", "Massively parallel functional dissection of 3' UTRs in neurons", "10.1038/s41593-022-01243-x", "E-MTAB-11575", "https://www.ebi.ac.uk/biostudies/files/E-MTAB-11575/E-MTAB-11575.sdrf.txt", "data/raw/nzip/E-MTAB-11575.sdrf.txt", "Mus musculus", "primary cortical neurons", "SLAM-seq after degradation-machinery perturbation", "BioStudies record", "metadata", "Public sample and raw-file metadata."),
        source("Astrocyte SN-MPRA", "Massively parallel dissection of RNA localization elements in vivo", "10.1101/2026.04.27.721172", "GSE330741", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE330nnn/GSE330741/suppl/GSE330741_RAW.tar", "data/raw/astrocyte_gse330741/GSE330741_RAW.tar", "Mus musculus", "adult astrocytes in vivo", "AAV SN-MPRA with synaptoneurosome and TRAP fractions", "GEO terms; preprint", "processed counts", "Complete GEO count-file archive; outcome values remain quarantined."),
        source("Astrocyte SN-MPRA", "Massively parallel dissection of RNA localization elements in vivo", "10.1101/2026.04.27.721172", "GSE330741", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/bin/media-1.xlsx", "data/raw/astrocyte_gse330741/supplementary/media-1.xlsx", "Mus musculus", "adult astrocytes in vivo", "AAV SN-MPRA with synaptoneurosome and TRAP fractions", "preprint", "processed", "Design and result workbook; SHA-locked before model development."),
        repository("Astrocyte SN-MPRA", "Massively parallel dissection of RNA localization elements in vivo", "10.1101/2026.04.27.721172", "GSE330741", "https://github.com/Dougherty-Lab/astrocyte_sn-mpra", "data/raw/astrocyte_gse330741/code", "94651f5ffc19d818c194bc4f56d3e5f2459349cc", "Mus musculus", "adult astrocytes in vivo", "AAV SN-MPRA", "repository terms", "Public analysis code pinned to an exact commit."),
        source("SRLE-seq", "High-throughput Screening of Sequence Elements Associated with RNA Localization", "10.34133/csbj.0107", "HRA016642", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/bin/csbj.0107.f1.zip", "data/raw/srle_seq/supplementary/csbj.0107.f1.zip", "Homo sapiens", "HEK293T", "fixed-backbone nuclear/cytoplasmic gain-of-function screen", "CC BY-NC-ND", "processed", "Supplementary tables include the complete 4,096 6-mer screen."),
        source("SRLE-seq", "High-throughput Screening of Sequence Elements Associated with RNA Localization", "10.34133/csbj.0107", "HRA016642", "https://download.cncb.ac.cn/gsa-human/HRA016642/Rawdata/md5sum.txt", "data/raw/srle_seq/md5sum.txt", "Homo sapiens", "HEK293T", "SRLE-seq", "GSA-Human controlled terms", "raw checksums", "Checksums for 60 public FASTQ files; FASTQs intentionally deferred because processed tables satisfy Phase E."),
        repository("SRLE-seq", "High-throughput Screening of Sequence Elements Associated with RNA Localization", "10.34133/csbj.0107", "HRA016642", "https://github.com/lysovosyl/SRLE-seq", "data/raw/srle_seq/code", "a65b8d3d26258647d41611cf1656c08ea34e9196", "Homo sapiens", "HEK293T", "SRLE-seq", "repository terms", "Public processing and prediction code pinned to an exact commit."),
        source("Arora", "A massively parallel reporter assay of 3' UTR sequence effects", "10.1093/nar/gkac763", "GSE183192", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9561290/bin/gkac763_supplemental_files.zip", "data/raw/arora_gse183192/supplementary/gkac763_supplemental_files.zip", "Mus musculus", "neuronal cells", "3' UTR MPRA", "CC BY", "processed", "Optional forward-model development source; not an intervention benchmark."),
        source("Moffatt 2026 candidate lock", "Robust mammalian RNA localization elements are complex and multipartite", "10.64898/2026.06.09.731215", "GSE334718; PRJNA1476227", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE334nnn/GSE334718/suppl/GSE334718_RAW.tar", "data/raw/moffatt_gse334718/GSE334718_RAW.tar", "Mus musculus", "CAD neuronal cells", "neurite/soma MPRA across mutation, necessity, SHAPE, shuffle and sufficiency libraries", "GEO terms; preprint CC BY-NC-ND", "sealed processed counts", "Downloaded and SHA-frozen during v3 Phase 1; archive not opened and outcomes not inspected. Exact parent-mutant reconstruction remains unverified."),
    ]
    ACQUISITION_OUT.parent.mkdir(parents=True, exist_ok=True)
    with ACQUISITION_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_external_manifest() -> dict[str, object]:
    if EXTERNAL_OUT.exists():
        return json.loads(EXTERNAL_OUT.read_text(encoding="utf-8"))
    workbook = ROOT / "data/raw/astrocyte_gse330741/supplementary/media-1.xlsx"
    raw_archive = ROOT / "data/raw/astrocyte_gse330741/GSE330741_RAW.tar"
    features = ROOT / "data/frozen/astrocyte_external_features.csv.gz"
    pairing_audit = ROOT / "data/frozen/astrocyte_pairing_audit.json"
    manifest = {
        "dataset": "GSE330741 astrocyte SN-MPRA",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "role": "locked external validation only",
        "files": [
            {"path": workbook.relative_to(ROOT).as_posix(), "size_bytes": workbook.stat().st_size, "sha256": sha256(workbook)},
            {"path": raw_archive.relative_to(ROOT).as_posix(), "size_bytes": raw_archive.stat().st_size, "sha256": sha256(raw_archive)},
            {"path": features.relative_to(ROOT).as_posix(), "size_bytes": features.stat().st_size, "sha256": sha256(features)},
            {"path": pairing_audit.relative_to(ROOT).as_posix(), "size_bytes": pairing_audit.stat().st_size, "sha256": sha256(pairing_audit)},
        ],
        "design": {
            "parents": 8,
            "parent_length_nt": 190,
            "snv_constructs": 4553,
            "positions": 1520,
            "missing_substitutions_from_full_saturation": 7,
            "feature_artifact_contains_outcome_values": False,
        },
        "sealed_outcome_fields": [
            "snin_ctxin_logFC (localization)",
            "ctxtrap_ctxin_logFC (ribosome occupancy)",
            "paptrap_ctxtrap_logFC (local translation)",
            "replicate count columns used to derive expression contrasts",
        ],
        "policy": [
            "No external outcome values may be used for feature design, threshold selection, model selection, hyperparameter selection or stopping rules.",
            "Outcome unsealing requires a committed model, immutable prediction artifact and prespecified evaluation configuration.",
            "All eight parents are evaluated as an external group; no mutation-level splitting is permitted.",
        ],
        "known_deviation": "Three result-sheet rows were printed during schema discovery before this manifest was created. No aggregate distribution, ranking, threshold or model result was inspected. This benchmark is outcome-blinded from freeze onward but must not be called perfectly never-seen.",
    }
    EXTERNAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    EXTERNAL_OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    rows = build_acquisition_manifest()
    external = build_external_manifest()
    print(f"Wrote {ACQUISITION_OUT.relative_to(ROOT)} with {len(rows)} source rows")
    print(json.dumps(external, indent=2))


if __name__ == "__main__":
    main()
