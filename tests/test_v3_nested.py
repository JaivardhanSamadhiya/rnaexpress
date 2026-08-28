import numpy as np
import pandas as pd
import torch

from src.modeling.utrbert_features import (
    overlapping_kmers,
    pool_contextual_delta,
    pool_paired_contextual_delta,
)
from src.modeling.v3_mechanistic_features import build_mechanistic_features
from src.modeling.v3_nested import (
    NestedResult,
    extreme_labels,
    percentile_targets,
    unordered_pair_crossfits,
)
from src.modeling.v3_stacking import rank_magnitude_stack


def test_utrbert_3mer_alignment_and_affected_pooling() -> None:
    assert overlapping_kmers("AATGC") == ["AAU", "AUG", "UGC"]
    parent_hidden = torch.zeros((1, 5, 768))
    mutant_hidden = parent_hidden.clone()
    mutant_hidden[:, 1:4, :] = 1.0
    pooled = pool_contextual_delta(parent_hidden, mutant_hidden, "AATGC", ["AACGC"])
    assert pooled.shape == (1, 3072)
    assert np.isfinite(pooled).all()
    assert np.allclose(pooled[0, 1536:2304], 1.0)


def test_paired_utrbert_pool_matches_single_parent_pool() -> None:
    parent = torch.zeros((2, 7, 768))
    mutant = parent.clone()
    mutant[0, 1:4] = 1.0
    mutant[1, 3:6] = 2.0
    parents = ["AACGTAA", "TTACGCA"]
    mutants = ["AATGTAA", "TTAGGCA"]
    paired = pool_paired_contextual_delta(parent, mutant, parents, mutants)
    expected = np.vstack(
        [
            pool_contextual_delta(parent[i : i + 1], mutant[i : i + 1], parents[i], [mutants[i]])[0]
            for i in range(2)
        ]
    )
    assert np.array_equal(paired, expected)


def test_training_targets_never_require_held_parent_outcomes() -> None:
    frame = pd.DataFrame(
        {
            "parent_id": ["a"] * 10 + ["b"] * 10,
            "delta_localization": np.arange(20, dtype=float),
        }
    )
    train = np.arange(10)
    labels_before = extreme_labels(frame, train, "increase")
    ranks_before = percentile_targets(frame, train)[train]
    frame.loc[10:, "delta_localization"] = -9999
    assert np.array_equal(labels_before, extreme_labels(frame, train, "increase"))
    assert np.array_equal(ranks_before, percentile_targets(frame, train)[train])
    assert labels_before.sum() == 1


def test_symmetric_pair_crossfits_equal_ordered_inner_predictions() -> None:
    parents = np.repeat(np.array(["a", "b", "c", "d"]), 3)
    row_value = np.arange(len(parents), dtype=float)

    def predictor(train: np.ndarray, test: np.ndarray) -> np.ndarray:
        return row_value[test] + row_value[train].mean()

    cached = unordered_pair_crossfits(parents, predictor, n_jobs=2)
    for outer_parent in sorted(np.unique(parents)):
        for inner_parent in sorted(np.unique(parents)):
            if outer_parent == inner_parent:
                continue
            inner_test = np.flatnonzero(parents == inner_parent)
            inner_train = np.flatnonzero(
                (parents != outer_parent) & (parents != inner_parent)
            )
            expected = predictor(inner_train, inner_test)
            pair = tuple(sorted((outer_parent, inner_parent)))
            assert np.array_equal(cached[pair][inner_test], expected)


def test_parent_state_interaction_changes_same_edit_action(tmp_path) -> None:
    parent_a = "A" * 12 + "C" * 12 + "A" * 12
    parent_b = "G" * 12 + "C" * 12 + "U" * 12
    position = 18
    mutant_a = parent_a[:position] + "G" + parent_a[position + 1 :]
    mutant_b = parent_b[:position] + "G" + parent_b[position + 1 :]
    frame = pd.DataFrame(
        {
            "parent_sequence": [parent_a, parent_b],
            "mutant_sequence": [mutant_a, mutant_b],
        }
    )
    result = build_mechanistic_features(frame, tmp_path / "structure.json")
    feature = result.names.index("interaction_substitution_C>G_x_parent_gc")
    predictions = result.values[:, feature]
    assert predictions[0] != predictions[1]


def test_stack_weight_never_uses_outer_parent_outcomes() -> None:
    parents = np.repeat(np.array(["a", "b", "c"]), 6)
    frame = pd.DataFrame(
        {
            "parent_id": parents,
            "source_row": np.arange(len(parents)),
            "delta_localization": np.linspace(-2.0, 2.0, len(parents)),
        }
    )
    outer = np.linspace(-1.0, 1.0, len(frame))
    rank_inner = np.full((3, len(frame)), np.nan)
    magnitude_inner = np.full((3, len(frame)), np.nan)
    for fold, parent in enumerate(["a", "b", "c"]):
        train = parents != parent
        rank_inner[fold, train] = outer[train]
        magnitude_inner[fold, train] = outer[train] ** 3
    rank = NestedResult(outer, pd.DataFrame(), rank_inner)
    magnitude = NestedResult(outer**3, pd.DataFrame(), magnitude_inner)
    before = rank_magnitude_stack(frame, rank, magnitude)
    changed = frame.copy()
    changed.loc[changed["parent_id"] == "a", "delta_localization"] = 99_999.0
    after = rank_magnitude_stack(changed, rank, magnitude)
    held = parents == "a"
    assert np.array_equal(before.increase[held], after.increase[held])
    assert before.tuning.iloc[0]["magnitude_weight"] == after.tuning.iloc[0]["magnitude_weight"]
