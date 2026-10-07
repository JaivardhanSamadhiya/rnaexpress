"""Controlled ranking-scale and regularization comparison on frozen features.

No command-line fitting is performed by importing this module. The shared
experiment runner selects a configuration using training-assay holdouts only.
"""
from src.cross_assay_20260927.common import np
from src.cross_assay_20260927.models import (
    optimize, pair_indices, row_weights, scaler,
)


CONFIGS = [
    {"id": "candidate_005", "scaling": "candidate", "penalty": .005},
    {"id": "candidate_05", "scaling": "candidate", "penalty": .05},
    {"id": "candidate_5", "scaling": "candidate", "penalty": .5},
    {"id": "pair_005", "scaling": "pair", "penalty": .005},
    {"id": "pair_05", "scaling": "pair", "penalty": .05},
    {"id": "pair_5", "scaling": "pair", "penalty": .5},
]


def build_features(frame, base246):
    """Return the unchanged historical interaction_3 matrix."""
    matrix = np.asarray(base246, dtype=float)
    assert matrix.ndim == 2 and matrix.shape == (len(frame), 246)
    assert np.isfinite(matrix).all()
    return matrix


def pair_rms(matrix, left, right, weights):
    """Training-only RMS of signed pair differences, without centering them."""
    weights = np.asarray(weights, dtype=float)
    assert len(weights) and np.isfinite(weights).all() and (weights > 0).all()
    differences = matrix[left] - matrix[right]
    return np.sqrt(np.sum(weights[:, None] * differences**2, axis=0) / weights.sum())


def fit_model(frame, x, config):
    """Fit one prespecified convex ranker using this training frame only."""
    # Other frozen feature routes reuse the same fitter and default to pair RMS.
    # The shared runner, rather than this generic fitter, enforces their grids.
    config = {**config, "scaling": config.get("scaling", "pair")}
    assert config["scaling"] in ("candidate", "pair")
    assert np.isfinite(config["penalty"]) and config["penalty"] > 0
    frame = frame.reset_index(drop=True)
    matrix = np.asarray(x, dtype=float)
    assert matrix.ndim == 2 and len(matrix) == len(frame)
    assert np.isfinite(matrix).all()
    left, right, labels, weights, studies = pair_indices(frame)
    assert len(labels), "Training pool has no non-tied sampled preferences"
    mean, candidate_scale = scaler(matrix, row_weights(frame))
    ranking_rms = pair_rms(matrix, left, right, weights)
    # Train-unsupported columns are explicitly frozen at zero. Parent-constant
    # columns can vary between contexts while carrying no pair-ranking signal.
    active = ranking_rms >= 1e-8
    scale = candidate_scale.copy() if config["scaling"] == "candidate" else ranking_rms.copy()
    scale[scale < 1e-8] = 1.
    differences = (matrix[left] - matrix[right]) / scale
    beta = np.zeros(matrix.shape[1])
    if active.any():
        fitted, residual, objective = optimize(
            differences[:, active], labels, weights, penalty=config["penalty"],
        )
        assert not residual
        beta[active] = fitted
    else:
        objective = float(np.log(2.))
    return {
        "config": dict(config), "mean": mean.tolist(), "scale": scale.tolist(),
        "beta": beta.tolist(), "active": active.tolist(),
        "candidate_scale": candidate_scale.tolist(), "pair_rms": ranking_rms.tolist(),
        "training_rows": len(frame), "training_pairs": len(labels),
        "training_studies": sorted(frame.dataset.unique().tolist()),
        "training_components": sorted(frame.biological_component.unique().tolist()),
        "objective": objective,
        "pair_sampling": "unchanged historical outcome-blind cap256 per context",
        "direction_head": "not fitted; score is relative candidate utility",
    }


def predict_model(model, x):
    matrix = np.asarray(x, dtype=float)
    beta = np.asarray(model["beta"], dtype=float)
    assert matrix.ndim == 2 and matrix.shape[1] == len(beta)
    assert np.isfinite(matrix).all()
    return ((matrix - np.asarray(model["mean"])) / np.asarray(model["scale"])) @ beta
