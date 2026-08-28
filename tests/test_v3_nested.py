import numpy as np
import pandas as pd
import torch

from src.modeling.utrbert_features import overlapping_kmers, pool_contextual_delta
from src.modeling.v3_nested import (
    extreme_labels,
    percentile_targets,
    unordered_pair_crossfits,
)


def test_utrbert_3mer_alignment_and_affected_pooling() -> None:
    assert overlapping_kmers("AATGC") == ["AAU", "AUG", "UGC"]
    parent_hidden = torch.zeros((1, 5, 768))
    mutant_hidden = parent_hidden.clone()
    mutant_hidden[:, 1:4, :] = 1.0
    pooled = pool_contextual_delta(parent_hidden, mutant_hidden, "AATGC", ["AACGC"])
    assert pooled.shape == (1, 3072)
    assert np.isfinite(pooled).all()
    assert np.allclose(pooled[0, 1536:2304], 1.0)


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
