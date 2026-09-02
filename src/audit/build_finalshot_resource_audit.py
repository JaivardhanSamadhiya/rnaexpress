"""Build machine-readable FinalShot resource-audit artifacts.

This is an outcome-blind resource/provenance audit.  It reads only the certified
development sequence columns for exact-overlap checks and never discovers or
opens protected Astrocyte data.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "finalshot_resource_audit"
OUT = ROOT / "results" / "finalshot"
PHASE_A = ROOT / "results" / "v4_phaseA"
PROTECTED_LOADER = ROOT / "src" / "pairing" / "audit_astrocyte.py"
EXPECTED_PROTECTED_LOADER_SHA256 = "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fasta_sequences(path: Path) -> set[str]:
    sequences: set[str] = set()
    pieces: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                if pieces:
                    sequences.add("".join(pieces).upper().replace("U", "T"))
                    pieces = []
            elif line:
                pieces.append(line)
    if pieces:
        sequences.add("".join(pieces).upper().replace("U", "T"))
    return sequences


def development_sequences() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for source in ("mikl", "tdp", "moffatt"):
        path = PHASE_A / f"{source}_interventions.csv.gz"
        frame = pd.read_csv(path, usecols=["parent_sequence", "mutant_sequence"])
        values = pd.concat([frame["parent_sequence"], frame["mutant_sequence"]], ignore_index=True)
        result[source] = {str(value).upper().replace("U", "T") for value in values.dropna()}
    return result


def build_rbpnet_manifest() -> tuple[list[dict[str, object]], dict[str, list[str]]]:
    model_dir = RAW / "RBPNet_models" / "models"
    models = sorted(model_dir.glob("*.h5"))
    if len(models) != 103:
        raise RuntimeError(f"Expected 103 RBPNet checkpoints, found {len(models)}")
    rows: list[dict[str, object]] = []
    by_rbp: dict[str, list[str]] = {}
    for path in models:
        task = path.name.removesuffix(".model.h5")
        rbp, cell = task.rsplit("_", 1)
        row = {
            "task": task,
            "rbp": rbp,
            "cell_line": cell,
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": file_hash(path),
        }
        rows.append(row)
        by_rbp.setdefault(rbp, []).append(cell)
    return rows, by_rbp


def parnet_tasks() -> tuple[dict[int, tuple[str, str]], dict[str, list[str]]]:
    mapping_path = RAW / "parnet" / "parnet" / "assets" / "ENCODE.idx2symbol-cell.pt"
    mapping = torch.load(mapping_path, map_location="cpu")
    normalized = {int(index): (str(value[0]), str(value[1])) for index, value in mapping.items()}
    if len(normalized) != 223 or len({value[0] for value in normalized.values()}) != 150:
        raise RuntimeError("Parnet task mapping is not the declared 223 tracks / 150 unique RBPs")
    by_rbp: dict[str, list[str]] = {}
    for rbp, cell in normalized.values():
        by_rbp.setdefault(rbp, []).append(cell)
    return normalized, by_rbp


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if file_hash(PROTECTED_LOADER) != EXPECTED_PROTECTED_LOADER_SHA256:
        raise RuntimeError("Protected Astrocyte loader hash changed")

    rbpnet_rows, rbpnet_by_rbp = build_rbpnet_manifest()
    write_csv(OUT / "rbpnet_checkpoint_manifest.csv", rbpnet_rows)

    parnet_mapping, parnet_by_rbp = parnet_tasks()
    targets = [
        ("ELAVL/Hu", "ELAVL1"), ("ELAVL/Hu", "ELAVL2"), ("ELAVL/Hu", "ELAVL3"),
        ("ELAVL/Hu", "ELAVL4"), ("MBNL", "MBNL1"), ("MBNL", "MBNL2"),
        ("MBNL", "MBNL3"), ("TDP-43", "TARDBP"), ("SFPQ", "SFPQ"),
        ("FMRP/FXR", "FMR1"), ("FMRP/FXR", "FXR1"), ("FMRP/FXR", "FXR2"),
        ("IGF2BP", "IGF2BP1"), ("IGF2BP", "IGF2BP2"), ("IGF2BP", "IGF2BP3"),
        ("PUM", "PUM1"), ("PUM", "PUM2"), ("other", "QKI"),
        ("other", "STAU1"), ("other", "STAU2"), ("other", "FUS"),
        ("other", "HNRNPK"), ("other", "PTBP1"), ("other", "TIA1"),
        ("other", "TIAL1"), ("other", "RBFOX2"),
    ]
    coverage_rows = []
    for family, rbp in targets:
        p_cells = sorted(parnet_by_rbp.get(rbp, []))
        r_cells = sorted(rbpnet_by_rbp.get(rbp, []))
        coverage_rows.append({
            "family": family,
            "human_rbp": rbp,
            "parnet_declared_cells": ";".join(p_cells),
            "parnet_declared_channel_count": len(p_cells),
            "parnet_preprint_checkpoint_usable": False,
            "rbpnet_cells": ";".join(r_cells),
            "rbpnet_checkpoint_count": len(r_cells),
            "finalshot_usable_via_rbpnet": bool(r_cells),
            "mouse_support": "sequence inference only; human HepG2-trained, no validated mouse model",
            "orthology_note": "human-symbol channel; one-to-one mouse orthology must not be called mouse training",
        })
    write_csv(OUT / "rbp_coverage.csv", coverage_rows)

    dev = development_sequences()
    fasta_paths = sorted((RAW / "DeepLocRNA" / "DeepLocRNA" / "data").rglob("*.fasta"))
    overlap_rows: list[dict[str, object]] = []
    for path in fasta_paths:
        external = fasta_sequences(path)
        for source, sequences in dev.items():
            overlap_rows.append({
                "external_resource": "DeepLocRNA",
                "external_file": path.relative_to(RAW).as_posix(),
                "external_unique_sequences": len(external),
                "development_source": source,
                "development_unique_sequences": len(sequences),
                "exact_full_sequence_overlap": len(external & sequences),
            })
    write_csv(OUT / "external_sequence_overlap.csv", overlap_rows)

    rbpnet_zip = RAW / "RBPNet_models.zip"
    parnet_main_models = sorted((RAW / "parnet" / "models").glob("*.pt"))
    deep_checkpoints = sorted((RAW / "DeepLocRNA" / "DeepLocRNA" / "Result").rglob("*.ckpt"))
    orthology_path = OUT / "rbp_orthology_mgi_2026-09-02.csv"
    orthology = pd.read_csv(orthology_path)
    orthology_counts = {str(key): int(value) for key, value in orthology["mapping_status"].value_counts().items()}
    manifest = {
        "schema_version": 1,
        "audit_date": "2026-09-02",
        "starting_commit": "f5bf28ee85a75c03ffc8f116dc5677a48aa01efd",
        "branch": "rnaddress-final-zero-shot",
        "data_boundaries": {
            "nzip_outcomes": "prohibited and not accessed",
            "astrocyte": "sealed; no sequence identities or outcomes accessed",
            "protected_loader_sha256": EXPECTED_PROTECTED_LOADER_SHA256,
        },
        "parnet": {
            "paper": "bioRxiv 2026.08.08.743506v1",
            "doi": "10.64898/2026.08.08.743506",
            "status": "preprint; not peer reviewed; CC BY 4.0",
            "code_commit": "2f0570cf47d8bb927415a71f853a97eb7e94005c",
            "paper_repo_commit": "0f3dd29a9e3a3add7db175555721cbf001372199",
            "package_tag": "0.5.0",
            "package_metadata_version": "0.0.1",
            "imported_version": "0.1.1",
            "license": "Apache-2.0",
            "declared_tracks": len(parnet_mapping),
            "declared_unique_rbps": len({value[0] for value in parnet_mapping.values()}),
            "task_mapping_sha256": file_hash(RAW / "parnet" / "parnet" / "assets" / "ENCODE.idx2symbol-cell.pt"),
            "main_branch_model_files": [
                {"filename": p.name, "bytes": p.stat().st_size, "sha256": file_hash(p)}
                for p in parnet_main_models
            ],
            "develop_checkpoint": {
                "commit": "5aabae3181199c69ac70525a20f7cbf4feaec45b",
                "filename": "0.5.0_RBPNet-11M.pt",
                "bytes": 47059137,
                "sha256": "2620a1c9b838fd28fcefb3c8cc695fa7a4889fb18a67c21694c097248aa64869",
                "inference_smoke_test": "pass",
                "parameter_count": 11736799,
                "paper_architecture_match": False,
            },
            "preprint_checkpoint_available": False,
            "decision": "exclude: exact 21M preprint model is not released; repository checkpoints do not match paper architecture",
        },
        "rbpnet": {
            "paper_doi": "10.1186/s13059-023-03015-7",
            "status": "peer reviewed",
            "code_commit": "8ee000dcdb897e0eeed6a46a855604299e914ca7",
            "package_version": "0.10.0",
            "license": "MIT",
            "archive": {
                "filename": rbpnet_zip.name,
                "bytes": rbpnet_zip.stat().st_size,
                "md5": file_hash(rbpnet_zip, "md5"),
                "sha256": file_hash(rbpnet_zip),
            },
            "checkpoint_count": len(rbpnet_rows),
            "cell_lines": ["HepG2"],
            "species_training": "human",
            "cpu_inference_smoke_test": "pass; QKI parent/SNV delta L1=0.08078941702842712",
            "runtime": {"python": "3.11.9", "tensorflow": "2.15.1", "tensorflow_probability": "0.23.0"},
            "mouse_orthology_snapshot": {
                "source": "Mouse Genome Informatics HOM_MouseHumanSequence.rpt",
                "url": "https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt",
                "snapshot_date": "2026-09-02",
                "source_sha256": "3d4bc89e71e57e10adf0139ba033786cb02e2e24e8d49cf0c357d1c2924afa0a",
                "mapping_status_counts": orthology_counts,
            },
            "decision": "only authorized frozen output-space fallback",
        },
        "deeplocrna": {
            "paper_doi": "10.1093/bioinformatics/btae065",
            "status": "peer reviewed",
            "code_commit": "5e426b2de872e8c3b269a9e7efb6f6894648ef8f",
            "release": "0.0.2 (repository setup.py reports 0.0.4)",
            "declared_license": "MIT; repository root lacks a LICENSE file",
            "checkpoints": [
                {"filename": p.relative_to(RAW / "DeepLocRNA").as_posix(), "bytes": p.stat().st_size, "sha256": file_hash(p)}
                for p in deep_checkpoints
            ],
            "exact_development_sequence_overlap": 0,
            "decision": "precedent only; broad compartments do not identify neurite-versus-soma effects",
        },
        "bridge": {
            "paper_doi": "10.1038/s41467-026-73086-0",
            "status": "peer reviewed",
            "code_commit": "b5d886557e58f896c975ab290ad77a38df629658",
            "license": "MIT",
            "figshare_doi": "10.6084/m9.figshare.29819843.v6",
            "decision": "methodology only: human fixed 101-nt windows and unavailable matched structural/cell inputs",
        },
        "spatial_nt_seq": {
            "paper_doi": "10.1038/s41593-026-02420-y",
            "geo": "GSE249405",
            "status": "peer reviewed; GEO public 2026-06-12",
            "code_commit": "1401d941559d84c4be9a3241bb72839434f44e04",
            "kinetics_package_commit": "b5cd23a475e9fa9d988514b0ea65694e08b90594",
            "license": "no LICENSE file in either audited repository",
            "decision": "exclude; turnover observations are not a released sequence-to-mutant stability model; no astrocyte subset accessed",
        },
        "rnalocate_v3": {
            "paper_doi": "10.1093/nar/gkae872",
            "status": "peer reviewed",
            "license": "paper CC BY-NC 4.0; no versioned predictor code/checkpoint found",
            "decision": "exclude; broad localization labels, unresolved study-level overlap, and no pinned checkpoint",
        },
        "mavenn": {
            "paper_doi": "10.1186/s13059-022-02661-7",
            "status": "peer reviewed",
            "code_commit_audited": "95b5ff4913b961ac172fbc23c22be986f9f671d7",
            "release_1_1_4_commit": "d4c9f3759c2ef0dbb1046feabe0d5062c14b0ad3",
            "license": "MIT",
            "decision": "methodology only; latent genotype-phenotype map plus measurement process",
        },
        "perturbation_response_decomposition": {
            "paper_doi": "10.64898/2026.07.24.740459",
            "status": "preprint; not peer reviewed; CC BY 4.0",
            "code_commit": "a15214780619736d393f40240e56ba992fd416a3",
            "license": "README says MIT; repository lacks LICENSE file",
            "decision": "methodology only; no RNA-localization model or data",
        },
    }
    (OUT / "resource_audit_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
