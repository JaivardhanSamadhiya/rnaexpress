"""Integrity checks for the outcome-blind FinalShot protocol checkpoint."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "finalshot"
BUILDER = ROOT / "src" / "audit" / "build_finalshot_trans_context.py"
PROTOCOL = ROOT / "reports" / "finalshot_protocol.md"
PROTECTED = ROOT / "src" / "pairing" / "audit_astrocyte.py"
SIGNATURE_BUILDER = ROOT / "src" / "features" / "build_finalshot_rbpnet_signatures.py"
SIGNATURE_MANIFEST = OUT / "rbp_signature_manifest.json"
ASSEMBLER = ROOT / "src" / "features" / "assemble_finalshot_features.py"
REPRESENTATION_RUNNER = ROOT / "src" / "analysis" / "run_finalshot_representation_benchmark.py"


def test_context_builder_respects_protected_boundaries() -> None:
    outcome_blind_code = (
        BUILDER.read_text(encoding="utf-8")
        + SIGNATURE_BUILDER.read_text(encoding="utf-8")
        + ASSEMBLER.read_text(encoding="utf-8")
    ).lower()
    all_code = outcome_blind_code + REPRESENTATION_RUNNER.read_text(encoding="utf-8").lower()
    assert "data/raw/astrocyte" not in all_code
    assert "data/processed/nzip" not in all_code
    assert "localization_effect" not in outcome_blind_code
    assert hashlib.sha256(PROTECTED.read_bytes()).hexdigest() == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )


def test_context_manifest_is_exact_and_outcome_blind() -> None:
    manifest = json.loads((OUT / "context_source_manifest.json").read_text(encoding="utf-8"))
    assert manifest["accession"] == "GSE67828"
    assert manifest["archive"]["bytes"] == 74_485_760
    assert manifest["archive"]["sha256"] == (
        "e2bce64320274f7a81b87598235934f6c6af0636126d6deca14ecc5b42a488c2"
    )
    assert len(manifest["samples"]) == 12
    assert manifest["eligible_rbp_channels"] == 98
    assert set(manifest["ineligible_rbp_channels"]) == {
        "HNRNPA1", "HNRNPC", "NCBP2", "TROVE2", "ZC3H11A"
    }
    assert manifest["protected_data_accessed"] is False
    assert manifest["localization_outcomes_accessed"] is False


def test_context_proxy_has_complete_prespecified_shape() -> None:
    proxy = pd.read_csv(OUT / "rbp_expression_proxy.csv").fillna("")
    samples = pd.read_csv(OUT / "rbp_expression_proxy_samples.csv")
    checkpoints = pd.read_csv(OUT / "rbpnet_checkpoint_manifest.csv")
    assert len(proxy) == 2 * len(checkpoints) == 206
    assert set(proxy["cell_line"]) == {"CAD", "N2A"}
    assert proxy.groupby("human_rbp")["cell_line"].nunique().eq(2).all()
    assert len(samples) == 98 * 12
    assert samples.groupby(["human_rbp", "cell_line", "compartment"]).size().eq(3).all()
    assert samples["fpkm"].ge(0).all()
    assert samples["interval_jaccard"].gt(0).all()
    assert samples["target_coverage"].gt(0).all()
    assert samples.select_dtypes("number").notna().all().all()


def test_protocol_freezes_small_family_features_controls_and_gates() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    compact = " ".join(protocol.split())
    for token in ("R0 — geometry", "R1 — 3UTRBERT", "R2 — RBPNet", "M0 —", "M1 —", "M2 —", "M3 —"):
        assert token in protocol
    assert "Exactly nine modeled summaries" in protocol
    assert "official `rbpnet.prediction._to_probs`" in protocol
    assert "sigmoid-transformed value" in protocol
    assert "RBP identity permutation" in protocol
    assert "Delta-RBP intervention permutation" in protocol
    assert "Cell-context permutation" in protocol
    assert "Parent-binding knockout" in protocol
    assert "Trans-interaction knockout" in protocol
    assert "Measurement-head randomization" in protocol
    assert "Gate I and stability permutation are not applicable" in protocol
    assert "rank ContextValue at least `+0.020`" in compact
    assert "normalized-regret ContextValue at least `+0.010`" in compact
    assert "Astrocyte remains sealed" in protocol
    assert "NO-GO — END ZERO-SHOT RNADDRESS" in protocol


def test_rbp_signature_summary_obeys_conservation_and_feature_order() -> None:
    spec = importlib.util.spec_from_file_location("finalshot_signatures", SIGNATURE_BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    profiles = np.asarray([[0.1, 0.2, 0.3, 0.4], [0.2, 0.1, 0.25, 0.45]], dtype=np.float32)
    mixing = np.asarray([0.3, 0.4], dtype=np.float32)
    lengths = np.asarray([4, 4], dtype=np.int16)
    pairs = np.asarray([[0, 1, 0, 2]], dtype=np.int32)
    values, diagnostics = module.summarize_interventions(profiles, mixing, lengths, pairs)
    assert module.FEATURE_NAMES.tolist() == [
        "delta_mass_radius10", "delta_mass_radius25", "delta_mass_radius50",
        "max_abs_delta_radius25", "binding_gained_global", "binding_lost_global",
        "parent_mass_radius25", "parent_mixing_coefficient", "delta_mixing_coefficient",
    ]
    np.testing.assert_allclose(values[0], [0, 0, 0, 0.1, 0.15, 0.15, 1, 0.3, 0.1], atol=1e-6)
    assert diagnostics["max_abs_global_signed_delta"] < 1e-6
    assert diagnostics["max_abs_gain_loss_difference"] < 1e-6


def test_completed_rbp_cache_manifest_is_consistent() -> None:
    manifest = json.loads(SIGNATURE_MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["checkpoint_caches"]
    assert manifest["protocol_commit"] == "30c89a3"
    assert manifest["checkpoint_count"] == len(entries) == 103
    assert manifest["sequence_index"]["unique_sequences"] == 72_998
    assert manifest["source_interventions"]["interventions"] == 62_665
    assert manifest["sequence_index"]["length_counts"] == {"150": 17_567, "260": 55_431}
    assert manifest["localization_outcomes_accessed"] is False
    assert manifest["nzip_outcomes_accessed"] is False
    assert manifest["astrocyte_data_accessed"] is False
    assert len({entry["task"] for entry in entries}) == 103
    assert max(entry["inference"]["profile_sum_max_abs_error"] for entry in entries) < 1e-6
    assert max(entry["signature"]["max_abs_global_signed_delta"] for entry in entries) < 1e-6
    assert max(entry["signature"]["max_abs_gain_loss_difference"] for entry in entries) < 1e-6
    for entry in entries:
        profile = ROOT / entry["profile_file"]
        features = ROOT / entry["feature_file"]
        assert profile.is_file() and profile.stat().st_size > 80_000_000
        assert features.is_file() and features.stat().st_size > 2_000_000


def test_assembled_rbp_matrix_and_dictionary_are_frozen() -> None:
    metadata = json.loads((OUT / "rbp_feature_matrix_manifest.json").read_text(encoding="utf-8"))
    dictionary = pd.read_csv(OUT / "rbp_feature_dictionary.csv")
    matrix = np.load(ROOT / metadata["matrix_path"], mmap_mode="r")
    assert matrix.shape == (62_665, 927)
    assert matrix.dtype == np.float32
    assert np.isfinite(matrix[[0, 10_000, 62_664]]).all()
    assert len(dictionary) == 927
    assert dictionary["group_index"].nunique() == 103
    assert dictionary.groupby("group_index").size().eq(9).all()
    assert metadata["localization_outcomes_accessed"] is False
    assert metadata["nzip_outcomes_accessed"] is False
    assert metadata["astrocyte_data_accessed"] is False
