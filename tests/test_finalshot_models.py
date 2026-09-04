import numpy as np
import pandas as pd

from src.modeling.finalshot_models import (
    FeatureLayout,
    FoldScaler,
    finalshot_assay_heads,
    fit_latent_heads,
    fit_sparse_group,
)
from src.analysis.run_finalshot_direct_models import select_recipe
from src.analysis.summarize_finalshot_direct_models import choose_direct_family


def _layout() -> FeatureLayout:
    return FeatureLayout(
        geometry=slice(0, 2),
        rbp_groups=(slice(2, 5), slice(5, 8)),
        group_names=("A", "B"),
        base_columns=(np.arange(2, 5), np.arange(5, 8)),
        interaction_columns=(np.empty(0, dtype=int), np.empty(0, dtype=int)),
    )


def test_fold_scaler_matches_population_standardization():
    x = np.asarray([[1.0, 4.0, 2.0], [3.0, 4.0, 6.0]], dtype=np.float32)
    scaler = FoldScaler.fit(x)
    transformed = scaler.transform(x)
    assert np.allclose(transformed[:, [0, 2]].mean(axis=0), 0.0)
    assert np.allclose(transformed[:, [0, 2]].std(axis=0), 1.0)
    assert np.array_equal(transformed[:, 1], np.zeros(2))


def test_sparse_group_solver_is_deterministic_and_selective():
    rng = np.random.default_rng(42017)
    x = rng.normal(size=(500, 8)).astype(np.float32)
    y = 1.5 * x[:, 0] - 0.8 * x[:, 2] + rng.normal(scale=0.05, size=500)
    weights = np.linspace(0.5, 1.5, len(x))
    first = fit_sparse_group(x, y, weights, _layout(), 0.01, 0.75)
    second = fit_sparse_group(x, y, weights, _layout(), 0.01, 0.75)
    assert first.converged and second.converged
    assert np.array_equal(first.coefficient, second.coefficient)
    assert first.group_norms[0] > 0
    assert first.group_norms[1] == 0
    assert np.corrcoef(first.predict(x), y)[0, 1] > 0.99


def test_sparse_group_rejects_unfrozen_grid_value():
    x = np.eye(8, dtype=np.float32)
    with np.testing.assert_raises(ValueError):
        fit_sparse_group(x, np.arange(8.0), np.ones(8), _layout(), 0.02, 0.75)


def test_recipe_selection_applies_regret_tolerance_before_secondary_metrics():
    grid = [
        {"eligible": True, "normalized_regret": 0.100, "directional_rank_percentile": 0.51,
         "good_selection_at_3": 0.5, "penalty": 0.001, "group_fraction": 0.25},
        {"eligible": True, "normalized_regret": 0.101, "directional_rank_percentile": 0.55,
         "good_selection_at_3": 0.4, "penalty": 0.01, "group_fraction": 0.75},
        {"eligible": True, "normalized_regret": 0.103, "directional_rank_percentile": 0.99,
         "good_selection_at_3": 1.0, "penalty": 0.1, "group_fraction": 0.75},
    ]
    selected = select_recipe(grid)
    assert selected["penalty"] == 0.01


def test_direct_family_tie_prefers_simpler_family_last():
    def record(regret, rank):
        return {
            "selected_penalty": 0.01,
            "selected_group_fraction": 0.75,
            "grid": [{"penalty": 0.01, "group_fraction": 0.75,
                      "normalized_regret": regret, "directional_rank_percentile": rank,
                      "good_selection_at_3": 0.5}],
        }
    assert choose_direct_family(record(0.100, 0.55), record(0.101, 0.54)) == "M1"
    assert choose_direct_family(record(0.100, 0.55), record(0.101, 0.56)) == "M2"


def test_latent_heads_are_monotone_and_unit_scaled():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(192, 8)).astype(np.float32)
    heads = np.repeat(np.arange(3), 64)
    y = 0.4 * x[:, 0] + heads + rng.normal(scale=0.05, size=len(x))
    model = fit_latent_heads(
        x, y, np.ones(len(x)), heads, ("a", "b", "c"), _layout(),
        0.01, 0.75, "two_knot", 17, maximum_epochs=12, patience=4, batch_size=64,
    )
    phi = model.latent_score(x)
    assert abs(phi.mean()) < 1e-5
    assert abs(phi.std() - 1.0) < 1e-5
    assert np.all(model.head_slopes > 0)
    order = np.argsort(phi[heads == 0])
    calibrated = model.calibrated_prediction(x[heads == 0], np.zeros(64, dtype=int))
    assert np.all(np.diff(calibrated[order]) >= 0)
