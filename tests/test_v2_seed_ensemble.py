import numpy as np

from src.analysis.run_v2_1_seed_ensemble import percentile_scores


def test_percentile_scores_span_unit_interval() -> None:
    scores = percentile_scores(np.asarray([4.0, 1.0, 3.0, 2.0]))
    assert np.allclose(scores, [1.0, 0.0, 2.0 / 3.0, 1.0 / 3.0])


def test_percentile_scores_average_ties() -> None:
    scores = percentile_scores(np.asarray([1.0, 2.0, 2.0]))
    assert np.allclose(scores, [0.0, 0.75, 0.75])
