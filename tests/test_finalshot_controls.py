"""Tests for frozen FinalShot mechanism-breaking feature controls."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.finalshot_controls import (
    FinalShotControlledFeatureStore,
    delta_shuffle_map,
)
from src.modeling.finalshot_models import FinalShotFeatureStore


ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"


def test_delta_shuffle_is_deterministic_cross_unit_and_fail_closed() -> None:
    rows = []
    for index in range(10):
        rows.append({
            "dataset": "source",
            "cell_type": "CAD",
            "substitution_count": 1,
            "insertion_length": 0,
            "deletion_length": 0,
            "replacement_length": 0,
            "edit_cost": 2,
            "motif_family": "motif",
            "biological_unit": "u1" if index < 6 else "u2",
            "candidate_id": f"eligible-{index}",
        })
    for index in range(4):
        rows.append({
            "dataset": "source",
            "cell_type": "CAD",
            "substitution_count": 1,
            "insertion_length": 0,
            "deletion_length": 0,
            "replacement_length": 0,
            "edit_cost": 2,
            "motif_family": "sparse",
            "biological_unit": "u1" if index < 2 else "u2",
            "candidate_id": f"sparse-{index}",
        })
    frame = pd.DataFrame(rows)
    first, eligible, audit = delta_shuffle_map(frame)
    second, second_eligible, _ = delta_shuffle_map(frame)
    assert np.array_equal(first, second)
    assert np.array_equal(eligible, second_eligible)
    assert eligible[:10].all() and not eligible[10:].any()
    assert (
        frame.loc[eligible, "biological_unit"].to_numpy()
        != frame.iloc[first[eligible]]["biological_unit"].to_numpy()
    ).all()
    assert audit["eligible"].sum() == 1


def test_control_feature_stores_preserve_frozen_invariants() -> None:
    rows = pd.read_csv(ROWS)
    paths = (RBP, DICTIONARY, EXPRESSION)
    indices = np.asarray([0, 1, 50_000])
    base = FinalShotFeatureStore(rows, *paths)
    base_m1, base_layout = base.materialize(indices, "M1")

    trans = FinalShotControlledFeatureStore(rows, *paths, "trans_interaction_knockout")
    trans_m2, trans_layout = trans.materialize(indices, "M2")
    assert trans_layout.feature_count == base_layout.feature_count
    assert np.array_equal(trans_m2, base_m1)

    parent = FinalShotControlledFeatureStore(rows, *paths, "parent_binding_knockout")
    parent_m1, parent_layout = parent.materialize(indices, "M1")
    assert np.array_equal(parent_m1[:, parent_layout.geometry], base_m1[:, base_layout.geometry])
    for columns in parent_layout.base_columns:
        assert np.all(parent_m1[:, columns[[6, 7]]] == 0)

    identity = FinalShotControlledFeatureStore(rows, *paths, "rbp_identity_permutation")
    identity_m1, identity_layout = identity.materialize(indices, "M1")
    original_blocks = base_m1[:, base_layout.geometry.stop:].reshape(len(indices), 103, 9)
    permuted_blocks = identity_m1[:, identity_layout.geometry.stop:].reshape(len(indices), 103, 9)
    assert np.array_equal(np.sort(original_blocks, axis=1), np.sort(permuted_blocks, axis=1))
    assert not np.array_equal(original_blocks, permuted_blocks)


def test_control_code_has_no_protected_data_path() -> None:
    paths = (
        ROOT / "src" / "modeling" / "finalshot_controls.py",
        ROOT / "src" / "analysis" / "run_finalshot_direct_controls.py",
        ROOT / "src" / "analysis" / "run_finalshot_m3_controls.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    assert "data/processed/nzip" not in source
    assert "data/raw/astrocyte" not in source
    assert "astrocyte_gse330741" not in source
