import pytest

from src.pairing.audit_astrocyte import (
    audit as audit_astrocyte,
    reconstruct_from_source as reconstruct_astrocyte_from_source,
    validate_outcome_free_features,
)
from src.pairing.reconstruct_mikl import reconstruct as reconstruct_mikl
from src.pairing.reconstruct_nzip import reconstruct as reconstruct_nzip
from src.pairing.reconstruct_tdp43 import motif_suffix, mutate_by_suffix
from src.pairing.freeze_tdp43_v2 import choose_locked_genes
from src.modeling.metrics import exact_random_success, expected_random_best
import pandas as pd


def test_nzip_reconstruction_is_exhaustive() -> None:
    pairs, audit = reconstruct_nzip()
    assert len(pairs) == 4395
    assert audit["snv_parent_constructs"] == 15
    assert audit["complete_three_alternates_per_position"] is True
    assert audit["excluded_snv_rows_due_to_ambiguous_outcome_identity"] == 300
    assert not audit["failures"]


def test_astrocyte_frozen_features_are_near_saturation_and_blinded(monkeypatch) -> None:
    monkeypatch.setattr(
        pd,
        "read_excel",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Ordinary tests must not open the Astrocyte source workbook")
        ),
    )
    features, audit = audit_astrocyte()
    assert audit["biological_element_groups"] == 8
    assert len(features) == 4553
    assert audit["snv_positions"] == 1520
    assert audit["missing_alternate_substitutions_from_full_saturation"] == 7
    assert audit["outcome_values_exported"] is False
    assert not any("logFC" in column for column in features.columns)
    assert not audit["failures"]


def test_astrocyte_source_reconstruction_is_fail_closed() -> None:
    with pytest.raises(PermissionError, match="sealed during v3 development"):
        reconstruct_astrocyte_from_source()


def test_astrocyte_feature_allowlist_rejects_outcomes() -> None:
    features, _ = audit_astrocyte()
    features["snin_ctxin_logFC"] = 0.0
    with pytest.raises(ValueError, match="outcome-free allowlist"):
        validate_outcome_free_features(features)


def test_mikl_reconstruction_excludes_unsafe_parent_assignments() -> None:
    pairs, audit = reconstruct_mikl()
    assert len(pairs) > 0
    assert len(pairs) + audit["ambiguous_parent_rows"] + audit["missing_parent_rows"] == 12909
    assert (pairs["parent_sequence"].str.len() == pairs["mutant_sequence"].str.len()).all()
    assert not audit["failures"]


def test_exact_random_metrics() -> None:
    assert exact_random_success(10, 2, 1) == pytest.approx(0.2)
    assert exact_random_success(10, 2, 10) == 1.0
    assert expected_random_best([1.0, 2.0, 3.0], 1) == 2.0
    assert expected_random_best([1.0, 2.0, 3.0], 3) == 3.0


def test_tdp43_overlapping_motifs_and_complement_mutation() -> None:
    sequence = "AACGTGTGTAA"
    assert motif_suffix(sequence) == "4:9"
    mutant = mutate_by_suffix(sequence, "4:9")
    assert mutant == "AACCACACAAA"
    assert sum(left != right for left, right in zip(sequence, mutant)) == 6


def test_tdp43_lock_selection_is_deterministic_and_quartile_balanced() -> None:
    rows = []
    for index, count in enumerate(range(10, 170, 10)):
        rows.extend({"gene_id": f"gene{index:02d}"} for _ in range(count))
    pairs = pd.DataFrame(rows)
    first = choose_locked_genes(pairs)
    second = choose_locked_genes(pairs.sample(frac=1, random_state=7))
    assert first == second
    assert len(first) == 4
