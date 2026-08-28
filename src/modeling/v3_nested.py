"""Leakage-safe nested utilities for RNAddress v3 development."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import os
from typing import Callable

from joblib import Parallel, delayed
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


ALPHA_FACTORS = (0.1, 1.0, 10.0)
LOGISTIC_C = (0.1, 1.0, 10.0)
DIRECTIONS = {"increase": 1.0, "decrease": -1.0}


def percentile_targets(frame: pd.DataFrame, indices: np.ndarray | None = None) -> np.ndarray:
    if indices is None:
        indices = np.arange(len(frame), dtype=int)
    result = np.full(len(frame), np.nan, dtype=float)
    subset = frame.iloc[indices]
    for _, local_indices in subset.groupby("parent_id", sort=True).indices.items():
        selected = indices[np.asarray(local_indices, dtype=int)]
        values = frame.iloc[selected]["delta_localization"].to_numpy(float)
        result[selected] = (rankdata(values, method="average") - 1.0) / max(1, len(values) - 1)
    return result


def extreme_labels(frame: pd.DataFrame, train: np.ndarray, direction: str) -> np.ndarray:
    sign = DIRECTIONS[direction]
    labels = np.zeros(len(train), dtype=int)
    subset = frame.iloc[train]
    for _, local_indices in subset.groupby("parent_id", sort=True).indices.items():
        local_indices = np.asarray(local_indices, dtype=int)
        utility = sign * subset.iloc[local_indices]["delta_localization"].to_numpy(float)
        threshold = float(np.quantile(utility, 0.90, method="linear"))
        labels[local_indices] = utility >= threshold
    return labels


def directional_metrics(
    frame: pd.DataFrame,
    increase_score: np.ndarray,
    decrease_score: np.ndarray | None = None,
    model: str = "model",
) -> pd.DataFrame:
    if decrease_score is None:
        decrease_score = -np.asarray(increase_score, float)
    score_by_direction = {
        "increase": np.asarray(increase_score, float),
        "decrease": np.asarray(decrease_score, float),
    }
    records: list[dict[str, object]] = []
    for parent_id, indices in frame.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        measured = frame.iloc[indices]["delta_localization"].to_numpy(float)
        for direction, sign in DIRECTIONS.items():
            utility = sign * measured
            predicted = score_by_direction[direction][indices]
            order = np.argsort(-predicted, kind="stable")
            selected = int(order[0])
            oracle = int(np.argmax(utility))
            oracle_rank = int(np.flatnonzero(order == oracle)[0]) + 1
            best = float(np.max(utility))
            worst = float(np.min(utility))
            effect_range = best - worst
            selected_utility = float(utility[selected])
            ranks = rankdata(utility, method="average")
            rank_percentile = float((ranks[selected] - 1.0) / max(1, len(utility) - 1))
            if np.ptp(predicted) == 0 or np.ptp(utility) == 0:
                rho = 0.0
            else:
                rho = float(spearmanr(predicted, utility).statistic)
                if not np.isfinite(rho):
                    rho = 0.0
            records.append(
                {
                    "model": model,
                    "parent_id": str(parent_id),
                    "direction": direction,
                    "n_candidates": len(indices),
                    "selected_source_row": int(frame.iloc[indices[selected]]["source_row"]),
                    "selected_measured_effect": float(measured[selected]),
                    "selected_utility": selected_utility,
                    "oracle_utility": best,
                    "raw_regret": best - selected_utility,
                    "normalized_regret": (best - selected_utility) / effect_range if effect_range else 0.0,
                    "rank_percentile": rank_percentile,
                    "spearman_utility": rho,
                    "oracle_rank": oracle_rank,
                    "oracle_top1": oracle_rank <= 1,
                    "oracle_top3": oracle_rank <= 3,
                    "oracle_top5": oracle_rank <= 5,
                    "oracle_top10": oracle_rank <= 10,
                    "near_oracle": selected_utility >= worst + 0.90 * effect_range,
                }
            )
    return pd.DataFrame.from_records(records)


def macro_metrics(metrics: pd.DataFrame) -> dict[str, float]:
    return {
        "rank_percentile": float(metrics["rank_percentile"].mean()),
        "normalized_regret": float(metrics["normalized_regret"].mean()),
        "selected_utility": float(metrics["selected_utility"].mean()),
        "oracle_top1": float(metrics["oracle_top1"].mean()),
        "oracle_top3": float(metrics["oracle_top3"].mean()),
        "oracle_top5": float(metrics["oracle_top5"].mean()),
        "oracle_top10": float(metrics["oracle_top10"].mean()),
        "near_oracle": float(metrics["near_oracle"].mean()),
        "mean_oracle_rank": float(metrics["oracle_rank"].mean()),
        "spearman_utility": float(metrics["spearman_utility"].mean()),
    }


def selection_score(metrics: pd.DataFrame) -> float:
    macro = macro_metrics(metrics)
    return float(
        0.45 * macro["rank_percentile"]
        + 0.35 * (1.0 - macro["normalized_regret"])
        + 0.20 * macro["oracle_top5"]
    )


def _ridge_predict(
    features: np.ndarray,
    target: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    alpha_factor: float,
) -> np.ndarray:
    scaler = StandardScaler().fit(features[train])
    model = Ridge(
        alpha=float(alpha_factor * features.shape[1]),
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    )
    model.fit(scaler.transform(features[train]), target[train])
    return model.predict(scaler.transform(features[test]))


@dataclass
class NestedResult:
    prediction: np.ndarray
    tuning: pd.DataFrame


def _pair_prediction_job(
    pair: tuple[object, object],
    parents: np.ndarray,
    n_rows: int,
    predictor: Callable[[np.ndarray, np.ndarray], np.ndarray],
) -> tuple[tuple[object, object], np.ndarray]:
    left, right = pair
    test = np.flatnonzero((parents == left) | (parents == right))
    train = np.flatnonzero((parents != left) & (parents != right))
    values = np.full(n_rows, np.nan, dtype=float)
    values[test] = predictor(train, test)
    return pair, values


def unordered_pair_crossfits(
    parents: np.ndarray,
    predictor: Callable[[np.ndarray, np.ndarray], np.ndarray],
    *,
    n_jobs: int | None = None,
) -> dict[tuple[object, object], np.ndarray]:
    """Fit each two-parent exclusion once and reuse it in both nesting orders.

    For outer parent A / inner parent B and outer B / inner A, the training rows,
    fitted preprocessing and fitted model are identical. Predicting both excluded
    groups together therefore removes an exact duplicate fit without changing any
    training partition or validation prediction.
    """
    parent_ids = tuple(sorted(pd.unique(parents)))
    pairs = tuple(combinations(parent_ids, 2))
    if n_jobs is None:
        requested = int(os.environ.get("RNADDRESS_N_JOBS", "4"))
        n_jobs = max(1, min(requested, len(pairs)))
    with threadpool_limits(limits=1):
        records = Parallel(n_jobs=n_jobs, prefer="threads")(
            delayed(_pair_prediction_job)(pair, parents, len(parents), predictor)
            for pair in pairs
        )
    return dict(records)


def nested_ridge(
    frame: pd.DataFrame,
    features: np.ndarray,
    target_name: str,
) -> NestedResult:
    if target_name == "rank":
        target = percentile_targets(frame)
    elif target_name == "magnitude":
        target = frame["delta_localization"].to_numpy(float)
    else:
        raise ValueError(f"Unknown Ridge target: {target_name}")
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    prediction = np.full(len(frame), np.nan, dtype=float)
    tuning_records = []
    pair_predictions = {}
    for factor in ALPHA_FACTORS:
        print(f"precomputing symmetric Ridge {target_name} inner fits: alpha={factor}", flush=True)
        pair_predictions[factor] = unordered_pair_crossfits(
            parents,
            lambda train, test, factor=factor: _ridge_predict(
                features, target, train, test, factor
            ),
        )
    for outer_fold, outer_parent in enumerate(parent_ids, start=1):
        outer_test = np.flatnonzero(parents == outer_parent)
        outer_train = np.flatnonzero(parents != outer_parent)
        scores = []
        for factor in ALPHA_FACTORS:
            crossfit = np.full(len(frame), np.nan, dtype=float)
            for inner_parent in parent_ids:
                if inner_parent == outer_parent:
                    continue
                inner_test = np.flatnonzero((parents == inner_parent) & (parents != outer_parent))
                pair = tuple(sorted((outer_parent, inner_parent)))
                crossfit[inner_test] = pair_predictions[factor][pair][inner_test]
            inner_frame = frame.iloc[outer_train].reset_index(drop=True)
            inner_prediction = crossfit[outer_train]
            metrics = directional_metrics(inner_frame, inner_prediction, model="inner")
            scores.append((selection_score(metrics), factor))
        best_score, best_factor = max(scores, key=lambda item: (item[0], item[1]))
        prediction[outer_test] = _ridge_predict(
            features, target, outer_train, outer_test, best_factor
        )
        tuning_records.append(
            {
                "target": target_name,
                "outer_parent": outer_parent,
                "alpha_factor": best_factor,
                "inner_selection_score": best_score,
            }
        )
        print(
            f"nested Ridge {target_name} fold {outer_fold}/15: {outer_parent} alpha={best_factor}",
            flush=True,
        )
    if not np.isfinite(prediction).all():
        raise ValueError("Nested Ridge predictions are incomplete")
    return NestedResult(prediction, pd.DataFrame(tuning_records))


def _logistic_predict(
    frame: pd.DataFrame,
    features: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    direction: str,
    c_value: float,
) -> np.ndarray:
    labels = extreme_labels(frame, train, direction)
    scaler = StandardScaler().fit(features[train])
    model = LogisticRegression(
        C=c_value,
        class_weight="balanced",
        penalty="l2",
        solver="newton-cg",
        max_iter=500,
        tol=1e-4,
        random_state=20260828,
    )
    model.fit(scaler.transform(features[train]), labels)
    return model.predict_proba(scaler.transform(features[test]))[:, 1]


def nested_extreme(frame: pd.DataFrame, features: np.ndarray) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    predictions = {direction: np.full(len(frame), np.nan) for direction in DIRECTIONS}
    tuning_records = []
    pair_predictions = {}
    for direction in DIRECTIONS:
        for c_value in LOGISTIC_C:
            print(
                f"precomputing symmetric extreme inner fits: direction={direction} C={c_value}",
                flush=True,
            )
            pair_predictions[(direction, c_value)] = unordered_pair_crossfits(
                parents,
                lambda train, test, direction=direction, c_value=c_value: _logistic_predict(
                    frame, features, train, test, direction, c_value
                ),
            )
    for outer_fold, outer_parent in enumerate(parent_ids, start=1):
        outer_test = np.flatnonzero(parents == outer_parent)
        outer_train = np.flatnonzero(parents != outer_parent)
        for direction in DIRECTIONS:
            scores = []
            for c_value in LOGISTIC_C:
                crossfit = np.full(len(frame), np.nan)
                for inner_parent in parent_ids:
                    if inner_parent == outer_parent:
                        continue
                    inner_test = np.flatnonzero((parents == inner_parent) & (parents != outer_parent))
                    pair = tuple(sorted((outer_parent, inner_parent)))
                    crossfit[inner_test] = pair_predictions[(direction, c_value)][pair][inner_test]
                inner_frame = frame.iloc[outer_train].reset_index(drop=True)
                inner_scores = crossfit[outer_train]
                if direction == "increase":
                    metrics = directional_metrics(
                        inner_frame, inner_scores, np.zeros(len(inner_scores)), model="inner"
                    )
                    metrics = metrics[metrics["direction"] == "increase"]
                else:
                    metrics = directional_metrics(
                        inner_frame, np.zeros(len(inner_scores)), inner_scores, model="inner"
                    )
                    metrics = metrics[metrics["direction"] == "decrease"]
                scores.append((selection_score(metrics), c_value))
            best_score, best_c = max(scores, key=lambda item: (item[0], -item[1]))
            predictions[direction][outer_test] = _logistic_predict(
                frame, features, outer_train, outer_test, direction, best_c
            )
            tuning_records.append(
                {
                    "target": f"extreme_{direction}",
                    "outer_parent": outer_parent,
                    "logistic_c": best_c,
                    "inner_selection_score": best_score,
                }
            )
        print(f"nested extreme fold {outer_fold}/15: {outer_parent}", flush=True)
    if not all(np.isfinite(values).all() for values in predictions.values()):
        raise ValueError("Nested extreme predictions are incomplete")
    return predictions["increase"], predictions["decrease"], pd.DataFrame(tuning_records)
