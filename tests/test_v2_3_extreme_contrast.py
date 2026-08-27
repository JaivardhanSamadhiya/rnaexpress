import numpy as np
import pandas as pd

from src.analysis.run_v2_3_extreme_contrast import extreme_training_targets


def test_extreme_targets_are_balanced_per_parent_and_ties_use_source_row() -> None:
    frame = pd.DataFrame(
        {
            "parent_id": ["a"] * 8,
            "source_row": [8, 7, 6, 5, 4, 3, 2, 1],
            "delta_localization": [0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 5.0],
        }
    )
    selected, targets = extreme_training_targets(frame, np.arange(8))
    assert selected.tolist() == [1, 0, 7, 6]
    assert targets.tolist() == [-1.0, -1.0, 1.0, 1.0]
