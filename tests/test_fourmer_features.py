import numpy as np

from src.modeling.fourmer_features import FOURMER_INDEX, fourmer_counts
from src.modeling.mikl_xgboost_heads import predict_frozen_heads


def test_fourmer_counts_and_150nt_equivalent_scaling() -> None:
    features = fourmer_counts(["AAAAA", "ACGT"])
    assert features.shape == (2, 256)
    assert features[0, FOURMER_INDEX["AAAA"]] == 2
    assert features[1, FOURMER_INDEX["ACGT"]] == 1
    assert np.allclose(features.sum(axis=1), [2, 1])

    equivalent = fourmer_counts(["AAAAA"], equivalent_150nt=True)
    assert equivalent[0, FOURMER_INDEX["AAAA"]] == 147
    assert equivalent.sum() == 147


def test_frozen_mikl_heads_return_two_finite_probabilities() -> None:
    prediction = predict_frozen_heads(["ACGT" * 25, "TGCA" * 25])

    assert prediction.shape == (2, 2)
    assert np.isfinite(prediction).all()
    assert ((prediction >= 0) & (prediction <= 1)).all()
