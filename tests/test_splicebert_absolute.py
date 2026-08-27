import numpy as np
import torch

from src.modeling.splicebert_absolute import pool_absolute_hidden
from src.modeling.splicebert_features import HIDDEN_SIZE


def test_absolute_pooling_excludes_special_tokens_and_padding() -> None:
    hidden = torch.zeros((2, 6, HIDDEN_SIZE), dtype=torch.float32)
    hidden[0, 0] = 7.0
    hidden[0, 1:4] = torch.tensor([1.0, 2.0, 3.0]).reshape(3, 1)
    hidden[0, 4] = 99.0
    hidden[1, 0] = 8.0
    hidden[1, 1:5] = torch.tensor([2.0, 4.0, 6.0, 8.0]).reshape(4, 1)
    hidden[1, 5] = 99.0
    attention = torch.tensor(
        [[1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 1, 1]], dtype=torch.int64
    )

    pooled = pool_absolute_hidden(hidden, attention)

    assert pooled.shape == (2, HIDDEN_SIZE * 2)
    assert np.allclose(pooled[0, :HIDDEN_SIZE], 7.0)
    assert np.allclose(pooled[1, :HIDDEN_SIZE], 8.0)
    assert np.allclose(pooled[0, HIDDEN_SIZE:], 2.0)
    assert np.allclose(pooled[1, HIDDEN_SIZE:], 5.0)
