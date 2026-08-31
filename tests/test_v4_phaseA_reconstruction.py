"""Integrity gates for the RNAddress v4 Phase A source reconstruction."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "v4_phaseA"
SCRIPT = ROOT / "src" / "audit" / "reconstruct_v4_phaseA.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module():
    spec = importlib.util.spec_from_file_location("reconstruct_v4_phaseA", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_edit_tier_boundaries_are_predeclared_and_exhaustive() -> None:
    module = _load_module()
    expected = {
        1: "exact_snv",
        2: "small_local_edit",
        5: "small_local_edit",
        6: "motif_scale_edit",
        12: "motif_scale_edit",
        13: "regional_edit",
        99: "regional_edit",
        100: "large_element_edit",
        510: "large_element_edit",
    }
    assert {cost: module.edit_tier(cost, "test") for cost in expected} == expected


def test_phaseA_summary_scale_and_scope_guards() -> None:
    summary = json.loads((OUT / "phaseA_summary.json").read_text(encoding="utf-8"))
    assert summary["nzip_outcomes_used"] is False
    assert summary["astrocyte_outcomes_opened"] is False
    assert summary["historical_models_rerun"] is False
    assert summary["mikl"]["certified_interventions"] == 11_900
    assert summary["mikl"]["certified_genes"] == 224
    assert summary["mikl"]["independent_parent_contexts"] == 5_830
    assert summary["tdp"]["certified_interventions"] == 4_566
    assert summary["moffatt"]["certified_interventions"] == 46_292
    assert summary["development_totals"] == {
        "certified_interventions": 62_758,
        "unique_gene_labels_casefolded": 248,
        "independent_parent_contexts": 10_406,
        "exact_snv": 19,
        "small_local_edit": 15_993,
        "motif_scale_edit": 14_719,
        "regional_edit": 17_641,
        "large_element_edit": 14_386,
        "common_outcome_rows": 93_397,
        "exclusion_rows": 2_672,
    }


def test_mikl_certified_sequences_and_parent_groups_are_exact() -> None:
    frame = pd.read_csv(OUT / "mikl_interventions.csv.gz")
    assert len(frame) == 11_900
    assert frame["parent_id"].nunique() == 5_830
    assert frame["gene_name"].nunique() == 224
    assert frame["parent_sequence"].str.len().eq(150).all()
    assert frame["mutant_sequence"].str.len().eq(150).all()
    observed = np.fromiter(
        (
            sum(left != right for left, right in zip(parent, mutant))
            for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])
        ),
        dtype=int,
        count=len(frame),
    )
    assert np.array_equal(observed, frame["edit_distance"].to_numpy())
    assert frame["effect_uncertainty_cad"].notna().all()
    assert frame["effect_uncertainty_n2a"].notna().all()
    assert frame["raw_delta_cad_replicates"].str.count(";").eq(2).all()
    assert frame["raw_delta_n2a_replicates"].str.count(";").eq(2).all()


def test_tdp_common_schema_preserves_exact_sequences_and_missing_uncertainty() -> None:
    frame = pd.read_csv(OUT / "tdp_interventions.csv.gz")
    assert len(frame) == 4_566
    assert frame["parent_id"].nunique() == 4_566
    observed = np.fromiter(
        (
            sum(left != right for left, right in zip(parent, mutant))
            for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])
        ),
        dtype=int,
        count=len(frame),
    )
    assert np.array_equal(observed, frame["edit_distance"].to_numpy())
    assert frame["effect_uncertainty"].isna().all()
    assert frame["replicate_count"].eq(4).all()


def test_moffatt_certified_operations_and_raw_missingness_are_explicit() -> None:
    frame = pd.read_csv(OUT / "moffatt_interventions.csv.gz")
    assert len(frame) == 46_292
    assert frame["parent_id"].nunique() == 10
    assert frame["parent_sequence"].nunique() == 8
    assert frame["parent_sequence"].str.len().eq(260).all()
    assert frame["mutant_sequence"].str.len().eq(260).all()
    assert not frame["mutant_id"].duplicated().any()
    assert set(frame["raw_ratio_status_gfp"]) == {
        "valid_diagnostic",
        "insufficient_paired_replicates",
    }
    assert set(frame["raw_ratio_status_firefly"]) == {
        "valid_diagnostic",
        "insufficient_paired_replicates",
    }
    for reporter in ("gfp", "firefly"):
        insufficient = frame[f"raw_ratio_status_{reporter}"].eq("insufficient_paired_replicates")
        assert frame.loc[insufficient, f"effect_uncertainty_{reporter}"].isna().all()
        assert frame.loc[insufficient, f"raw_ratio_mean_{reporter}"].isna().all()


def test_exclusions_are_reasoned_and_never_enter_certified_outputs() -> None:
    exclusions = pd.read_csv(OUT / "exclusion_audit.csv")
    assert len(exclusions) == 2_672
    expected = {
        ("mikl_gse173098", "missing_parent_gene_position_key"): 770,
        ("mikl_gse173098", "no_semantic_parent"): 239,
        ("moffatt_gse334718", "missing_sequence_dictionary_entry"): 1_658,
        ("moffatt_gse334718", "design_operation_mismatch"): 5,
    }
    assert exclusions.groupby(["dataset", "reason"]).size().to_dict() == expected
    moffatt = pd.read_csv(OUT / "moffatt_interventions.csv.gz", usecols=["mutant_id"])
    excluded_ids = set(
        exclusions.loc[
            exclusions["dataset"].eq("moffatt_gse334718"), "detail"
        ].astype(str)
    )
    assert not set(moffatt["mutant_id"]) & excluded_ids


def test_long_common_schema_has_only_finite_certified_outcomes() -> None:
    common = pd.read_csv(OUT / "common_intervention_outcomes.csv.gz")
    assert len(common) == 93_397
    assert common["outcome_valid"].all()
    assert np.isfinite(common["localization_effect"]).all()
    assert set(common["dataset"]) == {
        "mikl_gse173098",
        "tdp43_gse288185",
        "moffatt_gse334718",
    }
    assert not common[["dataset", "mutant_id", "cell_type", "reporter"]].duplicated().any()


def test_source_manifest_hashes_and_scope_contract() -> None:
    manifest = json.loads((OUT / "source_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scope_guards"] == {
        "nzip_outcomes_used": False,
        "astrocyte_outcomes_opened": False,
        "historical_models_rerun": False,
        "model_fit_or_tuning_performed": False,
    }
    for record in manifest["sources"]:
        path = ROOT / record["path"]
        assert path.stat().st_size == record["bytes"]
        assert _sha256(path) == record["sha256"]
    for name, record in manifest["outputs"].items():
        path = OUT / name
        assert path.stat().st_size == record["bytes"]
        assert _sha256(path) == record["sha256"]


def test_compressed_outputs_have_reproducible_zero_mtime() -> None:
    for name in (
        "mikl_interventions.csv.gz",
        "tdp_interventions.csv.gz",
        "moffatt_interventions.csv.gz",
        "common_intervention_outcomes.csv.gz",
    ):
        raw = (OUT / name).read_bytes()
        assert raw[:2] == b"\x1f\x8b"
        assert raw[4:8] == b"\x00\x00\x00\x00"
        with gzip.open(OUT / name, "rt", encoding="utf-8") as handle:
            assert handle.readline().strip()


def test_protected_astrocyte_loader_is_unchanged_and_not_imported() -> None:
    assert _sha256(ROOT / "src/pairing/audit_astrocyte.py") == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )
    source = SCRIPT.read_text(encoding="utf-8").lower()
    assert "astrocyte_gse330741" not in source
    assert "data/raw/astrocyte" not in source
    assert "data/processed/nzip" not in source
