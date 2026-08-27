import numpy as np
import pandas as pd
import torch

from src.analysis.run_v2_2_splicebert import percentile_targets
from src.modeling.splicebert_features import HIDDEN_SIZE, pool_contextual_delta


def test_percentile_targets_are_parent_normalized() -> None:
    frame = pd.DataFrame(
        {
            "parent_id": ["a", "a", "a", "b", "b"],
            "delta_localization": [3.0, 1.0, 2.0, -1.0, 1.0],
        }
    )
    assert np.allclose(percentile_targets(frame), [1.0, 0.0, 0.5, 0.0, 1.0])


def test_contextual_delta_pooling_uses_aligned_edit_and_window() -> None:
    parent = "AAAA"
    mutants = ["ACAA"]
    parent_hidden = torch.zeros((1, 6, HIDDEN_SIZE))
    mutant_hidden = torch.zeros((1, 6, HIDDEN_SIZE))
    mutant_hidden[:, 0, :] = 1.0
    mutant_hidden[:, 2, :] = 2.0
    pooled = pool_contextual_delta(
        parent_hidden, mutant_hidden, parent, mutants, radius=0
    )
    assert pooled.shape == (1, HIDDEN_SIZE * 4)
    assert np.allclose(pooled[0, :HIDDEN_SIZE], 1.0)
    assert np.allclose(pooled[0, HIDDEN_SIZE : HIDDEN_SIZE * 2], 0.5)
    assert np.allclose(pooled[0, HIDDEN_SIZE * 2 :], 2.0)
