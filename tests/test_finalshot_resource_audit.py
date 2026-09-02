"""Integrity tests for the audit-only FinalShot resource checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "finalshot"
AUDIT_SCRIPT = ROOT / "src" / "audit" / "build_finalshot_resource_audit.py"
ORTHOLOGY_SCRIPT = ROOT / "src" / "audit" / "fetch_finalshot_orthology.py"
PROTECTED = ROOT / "src" / "pairing" / "audit_astrocyte.py"


def test_protected_data_boundaries_and_loader_hash() -> None:
    combined = (AUDIT_SCRIPT.read_text(encoding="utf-8") + ORTHOLOGY_SCRIPT.read_text(encoding="utf-8")).lower()
    assert "data/raw/astrocyte" not in combined
    assert "data/processed/nzip" not in combined
    assert hashlib.sha256(PROTECTED.read_bytes()).hexdigest() == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )


def test_resource_manifest_is_pinned_and_excludes_unreleased_parnet() -> None:
    manifest = json.loads((OUT / "resource_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["starting_commit"].startswith("f5bf28e")
    assert manifest["parnet"]["declared_tracks"] == 223
    assert manifest["parnet"]["declared_unique_rbps"] == 150
    assert manifest["parnet"]["preprint_checkpoint_available"] is False
    assert manifest["parnet"]["develop_checkpoint"]["paper_architecture_match"] is False
    assert manifest["rbpnet"]["checkpoint_count"] == 103
    assert manifest["rbpnet"]["archive"]["md5"] == "e88fb57483ba9a3d81b842cc5aa140fb"
    assert manifest["data_boundaries"]["astrocyte"].startswith("sealed")


def test_all_rbpnet_checkpoints_are_individually_hashed() -> None:
    checkpoints = pd.read_csv(OUT / "rbpnet_checkpoint_manifest.csv")
    assert len(checkpoints) == 103
    assert checkpoints["task"].is_unique
    assert checkpoints["filename"].is_unique
    assert checkpoints["cell_line"].eq("HepG2").all()
    assert checkpoints["sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert checkpoints["bytes"].gt(10_000_000).all()


def test_absent_rbps_are_not_fabricated() -> None:
    coverage = pd.read_csv(OUT / "rbp_coverage.csv").fillna("")
    absent = {"ELAVL1", "ELAVL2", "ELAVL3", "ELAVL4", "MBNL1", "MBNL2", "MBNL3", "TARDBP", "PUM1", "PUM2"}
    rows = coverage.set_index("human_rbp").loc[sorted(absent)]
    assert rows["rbpnet_checkpoint_count"].eq(0).all()
    assert (~rows["finalshot_usable_via_rbpnet"].astype(bool)).all()
    assert (~coverage["parnet_preprint_checkpoint_usable"].astype(bool)).all()


def test_deeplocrna_exact_sequence_overlap_is_zero() -> None:
    overlap = pd.read_csv(OUT / "external_sequence_overlap.csv")
    assert len(overlap) == 15
    assert set(overlap["development_source"]) == {"mikl", "tdp", "moffatt"}
    assert overlap["exact_full_sequence_overlap"].eq(0).all()


def test_mouse_homology_snapshot_covers_all_rbpnet_symbols() -> None:
    orthology = pd.read_csv(OUT / "rbp_orthology_mgi_2026-09-02.csv").fillna("")
    checkpoints = pd.read_csv(OUT / "rbpnet_checkpoint_manifest.csv")
    assert set(orthology["human_rbp"]) == set(checkpoints["rbp"])
    counts = orthology["mapping_status"].value_counts().to_dict()
    assert counts == {"one_to_one": 99, "non_one_to_one": 4, "missing": 1}
    assert orthology["source_sha256"].eq(
        "3d4bc89e71e57e10adf0139ba033786cb02e2e24e8d49cf0c357d1c2924afa0a"
    ).all()


def test_audit_report_records_conditional_protocol_only_decision() -> None:
    report = (ROOT / "reports" / "finalshot_resource_audit.md").read_text(encoding="utf-8")
    assert "conditional pass for protocol freezing" in report
    assert "No localization performance model was trained" in report
    assert "Parnet is excluded" in report
    assert "Astrocyte" in report
