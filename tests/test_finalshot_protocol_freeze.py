"""Integrity checks for the outcome-blind FinalShot protocol checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "finalshot"
BUILDER = ROOT / "src" / "audit" / "build_finalshot_trans_context.py"
PROTOCOL = ROOT / "reports" / "finalshot_protocol.md"
PROTECTED = ROOT / "src" / "pairing" / "audit_astrocyte.py"


def test_context_builder_respects_protected_boundaries() -> None:
    code = BUILDER.read_text(encoding="utf-8").lower()
    assert "data/raw/astrocyte" not in code
    assert "data/processed/nzip" not in code
    assert "localization_effect" not in code
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
