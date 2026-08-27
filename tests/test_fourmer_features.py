import numpy as np

from src.modeling.fourmer_features import FOURMER_INDEX, fourmer_counts


def test_fourmer_counts_and_150nt_equivalent_scaling() -> None:
    features = fourmer_counts(["AAAAA", "ACGT"])
    assert features.shape == (2, 256)
    assert features[0, FOURMER_INDEX["AAAA"]] == 2
    assert features[1, FOURMER_INDEX["ACGT"]] == 1
    assert np.allclose(features.sum(axis=1), [2, 1])

    equivalent = fourmer_counts(["AAAAA"], equivalent_150nt=True)
    assert equivalent[0, FOURMER_INDEX["AAAA"]] == 147
    assert equivalent.sum() == 147
