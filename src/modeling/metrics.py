"""Parent-level inverse-design metrics and exact random expectations."""

from __future__ import annotations

from math import comb

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr


DIRECTIONS = {"increase": 1.0, "decrease": -1.0}


def rank_percentile(measured_utility: np.ndarray, selected_index: int) -> float:
    n = len(measured_utility)
    if n <= 1:
        return 1.0
    ranks = rankdata(-measured_utility, method="average")
    return float(1.0 - (ranks[selected_index] - 1.0) / (n - 1.0))


def exact_random_success(n: int, m: int, k: int) -> float:
    k = min(k, n)
    if m <= 0:
        return 0.0
    if n - m < k:
        return 1.0
    return float(1.0 - comb(n - m, k) / comb(n, k))


def expected_random_best(values: np.ndarray, k: int) -> float:
    """Expected maximum in a uniformly sampled size-k subset, without replacement."""
    ordered = np.sort(np.asarray(values, float))
    n = len(ordered)
    k = min(k, n)
    denominator = comb(n, k)
    expectation = 0.0
    # If ordered[i] is the subset maximum, choose the other k-1 from i lower items.
    for i in range(k - 1, n):
        expectation += ordered[i] * comb(i, k - 1) / denominator
    return float(expectation)


def evaluate_parent(
    frame: pd.DataFrame,
    prediction_column: str,
    threshold: float,
    model_name: str,
) -> list[dict[str, object]]:
    measured = frame["delta_localization"].to_numpy(float)
    predicted = frame[prediction_column].to_numpy(float)
    n = len(frame)
    rows: list[dict[str, object]] = []
    rho = float(spearmanr(predicted, measured).statistic)
    if not np.isfinite(rho):
        rho = 0.0
    for direction, sign in DIRECTIONS.items():
        measured_utility = sign * measured
        predicted_utility = sign * predicted
        order = np.argsort(-predicted_utility, kind="stable")
        best = float(np.max(measured_utility))
        worst = float(np.min(measured_utility))
        effect_range = best - worst
        selected = int(order[0])
        measured_selected = float(measured_utility[selected])
        regret = best - measured_selected
        result: dict[str, object] = {
            "model": model_name,
            "parent_id": str(frame["parent_id"].iloc[0]),
            "direction": direction,
            "n_candidates": n,
            "selected_source_row": int(frame["source_row"].iloc[selected]),
            "selected_edit": (
                f"{frame['reference_nt'].iloc[selected]}"
                f"{int(frame['edit_position_1based'].iloc[selected])}"
                f"{frame['alternate_nt'].iloc[selected]}"
            ),
            "measured_effect": float(measured[selected]),
            "measured_utility": measured_selected,
            "best_measured_utility": best,
            "regret": float(regret),
            "normalized_regret": float(regret / effect_range) if effect_range > 0 else 0.0,
            "rank_percentile": rank_percentile(measured_utility, selected),
            "spearman": rho,
            "random_expected_effect": float(sign * np.mean(measured)),
            "random_expected_regret_at_1": float(best - np.mean(measured_utility)),
            "random_expected_rank_percentile": 0.5,
        }
        successful = measured_utility > threshold
        m = int(successful.sum())
        for k in [1, 3, 5]:
            top = order[: min(k, n)]
            result[f"success_at_{k}"] = float(successful[top].any())
            result[f"precision_at_{k}"] = float(successful[top].mean())
            result[f"random_success_at_{k}"] = exact_random_success(n, m, k)
            result[f"random_precision_at_{k}"] = float(m / n)
            result[f"random_expected_regret_at_{k}"] = float(
                best - expected_random_best(measured_utility, k)
            )
        rows.append(result)
    return rows


def evaluate_predictions(
    predictions: pd.DataFrame,
    prediction_columns: dict[str, str],
    threshold: float,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for parent_id, frame in predictions.groupby("parent_id", sort=True):
        del parent_id
        for model_name, column in prediction_columns.items():
            records.extend(evaluate_parent(frame, column, threshold, model_name))
    return pd.DataFrame.from_records(records)


def parent_macro(metric_rows: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        c
        for c in metric_rows.columns
        if c
        not in {
            "model",
            "parent_id",
            "direction",
            "selected_edit",
            "selected_source_row",
        }
        and pd.api.types.is_numeric_dtype(metric_rows[c])
    ]
    by_parent = metric_rows.groupby(["model", "parent_id"], as_index=False)[numeric].mean()
    return by_parent.groupby("model", as_index=False)[numeric].mean()


def bootstrap_parent_differences(
    metric_rows: pd.DataFrame,
    selected_model: str,
    baseline_model: str,
    metrics: list[str],
    seed: int = 20260826,
    draws: int = 10000,
) -> list[dict[str, object]]:
    averaged = metric_rows.groupby(["model", "parent_id"], as_index=False)[metrics].mean()
    selected = averaged[averaged["model"] == selected_model].set_index("parent_id")
    baseline = averaged[averaged["model"] == baseline_model].set_index("parent_id")
    ids = sorted(set(selected.index) & set(baseline.index))
    rng = np.random.default_rng(seed)
    output: list[dict[str, object]] = []
    for metric in metrics:
        differences = (selected.loc[ids, metric] - baseline.loc[ids, metric]).to_numpy(float)
        samples = rng.choice(differences, size=(draws, len(ids)), replace=True).mean(axis=1)
        output.append(
            {
                "selected_model": selected_model,
                "baseline_model": baseline_model,
                "metric": metric,
                "parents": len(ids),
                "mean_difference": float(np.mean(differences)),
                "ci95_low": float(np.quantile(samples, 0.025)),
                "ci95_high": float(np.quantile(samples, 0.975)),
            }
        )
    return output
