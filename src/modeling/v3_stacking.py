"""Strict outer-fold-safe RNAddress v3 score stacking."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .v3_nested import NestedResult, directional_metrics, selection_score


MAGNITUDE_WEIGHTS = (0.25, 0.50, 0.75)
EXTREME_WEIGHTS = (0.10, 0.20)


@dataclass
class DirectionalStackResult:
    increase: np.ndarray
    decrease: np.ndarray
    tuning: pd.DataFrame
    inner_increase: np.ndarray
    inner_decrease: np.ndarray


def _moments(values: np.ndarray) -> tuple[float, float]:
    mean = float(np.mean(values))
    scale = float(np.std(values))
    return mean, scale if scale > 0 else 1.0


def rank_magnitude_stack(
    frame: pd.DataFrame,
    rank: NestedResult,
    magnitude: NestedResult,
) -> DirectionalStackResult:
    if rank.inner_prediction is None or magnitude.inner_prediction is None:
        raise ValueError("Rank/magnitude stacking requires outer-training cross-fits")
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    increase = np.full(len(frame), np.nan)
    decrease = np.full(len(frame), np.nan)
    inner_increase = np.full((len(parent_ids), len(frame)), np.nan)
    inner_decrease = np.full((len(parent_ids), len(frame)), np.nan)
    tuning = []
    for outer_fold, outer_parent in enumerate(parent_ids):
        train = np.flatnonzero(parents != outer_parent)
        test = np.flatnonzero(parents == outer_parent)
        rank_train = rank.inner_prediction[outer_fold, train]
        magnitude_train = magnitude.inner_prediction[outer_fold, train]
        if not np.isfinite(rank_train).all() or not np.isfinite(magnitude_train).all():
            raise ValueError("Base cross-fits are incomplete")
        rank_mean, rank_scale = _moments(rank_train)
        magnitude_mean, magnitude_scale = _moments(magnitude_train)
        rank_train_z = (rank_train - rank_mean) / rank_scale
        magnitude_train_z = (magnitude_train - magnitude_mean) / magnitude_scale
        choices = []
        for weight_magnitude in MAGNITUDE_WEIGHTS:
            weight_rank = 1.0 - weight_magnitude
            score = weight_rank * rank_train_z + weight_magnitude * magnitude_train_z
            metrics = directional_metrics(
                frame.iloc[train].reset_index(drop=True), score, -score, model="inner_stack"
            )
            choices.append((selection_score(metrics), weight_magnitude))
        best_score, best_weight_magnitude = max(
            choices, key=lambda item: (item[0], -item[1])
        )
        best_weight_rank = 1.0 - best_weight_magnitude
        selected_inner = (
            best_weight_rank * rank_train_z + best_weight_magnitude * magnitude_train_z
        )
        inner_increase[outer_fold, train] = selected_inner
        inner_decrease[outer_fold, train] = -selected_inner
        rank_test_z = (rank.prediction[test] - rank_mean) / rank_scale
        magnitude_test_z = (magnitude.prediction[test] - magnitude_mean) / magnitude_scale
        selected_test = (
            best_weight_rank * rank_test_z + best_weight_magnitude * magnitude_test_z
        )
        increase[test] = selected_test
        decrease[test] = -selected_test
        tuning.append(
            {
                "outer_parent": outer_parent,
                "magnitude_weight": best_weight_magnitude,
                "rank_weight": best_weight_rank,
                "inner_selection_score": best_score,
                "rank_crossfit_mean": rank_mean,
                "rank_crossfit_scale": rank_scale,
                "magnitude_crossfit_mean": magnitude_mean,
                "magnitude_crossfit_scale": magnitude_scale,
            }
        )
    if not np.isfinite(increase).all() or not np.isfinite(decrease).all():
        raise ValueError("Rank/magnitude stack predictions are incomplete")
    return DirectionalStackResult(
        increase,
        decrease,
        pd.DataFrame(tuning),
        inner_increase,
        inner_decrease,
    )


def add_extreme_head(
    frame: pd.DataFrame,
    base: DirectionalStackResult,
    extreme_increase: np.ndarray,
    extreme_decrease: np.ndarray,
    inner_extreme_increase: np.ndarray,
    inner_extreme_decrease: np.ndarray,
) -> DirectionalStackResult:
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    increase = np.full(len(frame), np.nan)
    decrease = np.full(len(frame), np.nan)
    inner_increase = np.full((len(parent_ids), len(frame)), np.nan)
    inner_decrease = np.full((len(parent_ids), len(frame)), np.nan)
    tuning = []
    outer_extreme = {"increase": extreme_increase, "decrease": extreme_decrease}
    inner_extreme = {
        "increase": inner_extreme_increase,
        "decrease": inner_extreme_decrease,
    }
    base_outer = {"increase": base.increase, "decrease": base.decrease}
    base_inner = {"increase": base.inner_increase, "decrease": base.inner_decrease}
    outputs = {"increase": increase, "decrease": decrease}
    inner_outputs = {"increase": inner_increase, "decrease": inner_decrease}
    for outer_fold, outer_parent in enumerate(parent_ids):
        train = np.flatnonzero(parents != outer_parent)
        test = np.flatnonzero(parents == outer_parent)
        direction_values = {}
        moments = {}
        for direction in ("increase", "decrease"):
            values = inner_extreme[direction][outer_fold, train]
            if not np.isfinite(values).all():
                raise ValueError("Extreme cross-fits are incomplete")
            mean, scale = _moments(values)
            moments[direction] = (mean, scale)
            direction_values[direction] = (values - mean) / scale
        choices = []
        for weight in EXTREME_WEIGHTS:
            trial_increase = (
                (1.0 - weight) * base.inner_increase[outer_fold, train]
                + weight * direction_values["increase"]
            )
            trial_decrease = (
                (1.0 - weight) * base.inner_decrease[outer_fold, train]
                + weight * direction_values["decrease"]
            )
            metrics = directional_metrics(
                frame.iloc[train].reset_index(drop=True),
                trial_increase,
                trial_decrease,
                model="inner_extreme_stack",
            )
            choices.append((selection_score(metrics), weight))
        best_score, best_weight = max(choices, key=lambda item: (item[0], -item[1]))
        for direction in ("increase", "decrease"):
            mean, scale = moments[direction]
            selected_inner = (
                (1.0 - best_weight) * base_inner[direction][outer_fold, train]
                + best_weight * direction_values[direction]
            )
            selected_outer = (
                (1.0 - best_weight) * base_outer[direction][test]
                + best_weight * (outer_extreme[direction][test] - mean) / scale
            )
            inner_outputs[direction][outer_fold, train] = selected_inner
            outputs[direction][test] = selected_outer
        tuning.append(
            {
                "outer_parent": outer_parent,
                "extreme_weight": best_weight,
                "base_weight": 1.0 - best_weight,
                "inner_selection_score": best_score,
                "increase_extreme_crossfit_mean": moments["increase"][0],
                "increase_extreme_crossfit_scale": moments["increase"][1],
                "decrease_extreme_crossfit_mean": moments["decrease"][0],
                "decrease_extreme_crossfit_scale": moments["decrease"][1],
            }
        )
    if not np.isfinite(increase).all() or not np.isfinite(decrease).all():
        raise ValueError("Extreme stack predictions are incomplete")
    return DirectionalStackResult(
        increase,
        decrease,
        pd.DataFrame(tuning),
        inner_increase,
        inner_decrease,
    )
