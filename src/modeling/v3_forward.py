"""Strict grouped absolute-sequence forward comparators for RNAddress v3."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .v3_nested import ALPHA_FACTORS, directional_metrics, selection_score, unordered_pair_crossfits


@dataclass
class ForwardResult:
    prediction: np.ndarray
    tuning: pd.DataFrame


def _forward_predict(
    mutant_features: np.ndarray,
    parent_features: np.ndarray,
    absolute_target: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    alpha_factor: float,
) -> np.ndarray:
    scaler = StandardScaler().fit(mutant_features[train])
    model = Ridge(
        alpha=float(alpha_factor * mutant_features.shape[1]),
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    )
    model.fit(scaler.transform(mutant_features[train]), absolute_target[train])
    mutant = model.predict(scaler.transform(mutant_features[test]))
    parent = model.predict(scaler.transform(parent_features[test]))
    return mutant - parent


def nested_forward_ridge(
    frame: pd.DataFrame,
    mutant_features: np.ndarray,
    parent_features: np.ndarray,
) -> ForwardResult:
    if mutant_features.shape != parent_features.shape or len(frame) != len(mutant_features):
        raise ValueError("Forward absolute feature shapes differ")
    target = frame["mutant_localization_log2_neurite_soma"].to_numpy(float)
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    pair_predictions = {}
    for factor in ALPHA_FACTORS:
        print(f"precomputing absolute forward inner fits: alpha={factor}", flush=True)
        pair_predictions[factor] = unordered_pair_crossfits(
            parents,
            lambda train, test, factor=factor: _forward_predict(
                mutant_features,
                parent_features,
                target,
                train,
                test,
                factor,
            ),
        )
    prediction = np.full(len(frame), np.nan)
    tuning = []
    for outer_fold, outer_parent in enumerate(parent_ids, start=1):
        outer_test = np.flatnonzero(parents == outer_parent)
        outer_train = np.flatnonzero(parents != outer_parent)
        choices = []
        for factor in ALPHA_FACTORS:
            crossfit = np.full(len(frame), np.nan)
            for inner_parent in parent_ids:
                if inner_parent == outer_parent:
                    continue
                inner_test = np.flatnonzero(parents == inner_parent)
                pair = tuple(sorted((outer_parent, inner_parent)))
                crossfit[inner_test] = pair_predictions[factor][pair][inner_test]
            metrics = directional_metrics(
                frame.iloc[outer_train].reset_index(drop=True),
                crossfit[outer_train],
                model="inner_forward",
            )
            choices.append((selection_score(metrics), factor))
        best_score, best_factor = max(choices, key=lambda item: (item[0], item[1]))
        prediction[outer_test] = _forward_predict(
            mutant_features,
            parent_features,
            target,
            outer_train,
            outer_test,
            best_factor,
        )
        tuning.append(
            {
                "outer_parent": outer_parent,
                "alpha_factor": best_factor,
                "inner_selection_score": best_score,
            }
        )
        print(
            f"nested absolute forward fold {outer_fold}/15: {outer_parent} alpha={best_factor}",
            flush=True,
        )
    if not np.isfinite(prediction).all():
        raise ValueError("Forward predictions are incomplete")
    return ForwardResult(prediction, pd.DataFrame(tuning))
