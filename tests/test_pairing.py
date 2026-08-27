import pytest

from src.pairing.audit_astrocyte import audit as audit_astrocyte
from src.pairing.reconstruct_mikl import reconstruct as reconstruct_mikl
from src.pairing.reconstruct_nzip import reconstruct as reconstruct_nzip
from src.modeling.metrics import exact_random_success, expected_random_best


def test_nzip_reconstruction_is_exhaustive() -> None:
    pairs, audit = reconstruct_nzip()
    assert len(pairs) == 4395
    assert audit["snv_parent_constructs"] == 15
    assert audit["complete_three_alternates_per_position"] is True
    assert audit["excluded_snv_rows_due_to_ambiguous_outcome_identity"] == 300
    assert not audit["failures"]


def test_astrocyte_reconstruction_is_near_saturation_and_blinded() -> None:
    features, audit = audit_astrocyte()
    assert audit["biological_element_groups"] == 8
    assert len(features) == 4553
    assert audit["snv_positions"] == 1520
    assert audit["missing_alternate_substitutions_from_full_saturation"] == 7
    assert audit["outcome_values_exported"] is False
    assert not any("logFC" in column for column in features.columns)
    assert not audit["failures"]


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
