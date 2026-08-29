"""Parent-level statistical summaries for RNAddress v3 Phase 3."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .v3_nested import macro_metrics


BOOTSTRAP_SEED = 20260828
BOOTSTRAP_RESAMPLES = 10_000
MEANINGFUL_EFFECT = 0.6758642587586807


def parent_composite(metrics: pd.DataFrame) -> pd.DataFrame:
    table = metrics.copy()
    table["composite"] = 0.5 * table["rank_percentile"] + 0.5 * (
        1.0 - table["normalized_regret"]
    )
    return (
        table.groupby("parent_id", sort=True, as_index=False)["composite"]
        .mean()
        .sort_values("parent_id")
        .reset_index(drop=True)
    )


def paired_parent_robustness(
    candidate: pd.DataFrame,
    baseline: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    left = parent_composite(candidate).rename(columns={"composite": "candidate_composite"})
    right = parent_composite(baseline).rename(columns={"composite": "baseline_composite"})
    paired = left.merge(right, on="parent_id", validate="one_to_one")
    paired["gain"] = paired["candidate_composite"] - paired["baseline_composite"]
    ordered = paired.sort_values("gain", ascending=False, kind="stable")
    summary = {
        "mean_parent_gain": float(paired["gain"].mean()),
        "median_parent_gain": float(paired["gain"].median()),
        "improved_parent_count": int((paired["gain"] > 0).sum()),
        "parent_count": len(paired),
        "leave_best_one_mean_gain": float(ordered.iloc[1:]["gain"].mean()),
        "leave_best_two_mean_gain": float(ordered.iloc[2:]["gain"].mean()),
    }
    return paired, summary


def exact_random_expectations(frame: pd.DataFrame) -> dict[str, float]:
    rows = []
    for _, indices in frame.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        measured = frame.iloc[indices]["delta_localization"].to_numpy(float)
        for sign in (1.0, -1.0):
            utility = sign * measured
            best = float(utility.max())
            worst = float(utility.min())
            span = best - worst
            regret = (best - utility) / span if span else np.zeros(len(utility))
            near = utility >= worst + 0.90 * span
            rows.append(
                {
                    "rank_percentile": 0.5,
                    "normalized_regret": float(regret.mean()),
                    "selected_utility": float(utility.mean()),
                    "oracle_top1": min(1, len(utility)) / len(utility),
                    "oracle_top3": min(3, len(utility)) / len(utility),
                    "oracle_top5": min(5, len(utility)) / len(utility),
                    "oracle_top10": min(10, len(utility)) / len(utility),
                    "near_oracle": float(near.mean()),
                    "meaningful_effect_rate": float((utility >= MEANINGFUL_EFFECT).mean()),
                }
            )
    return {key: float(pd.DataFrame(rows)[key].mean()) for key in rows[0]}


def bootstrap_macro_intervals(
    metrics: pd.DataFrame,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    parents = np.asarray(sorted(metrics["parent_id"].unique()))
    if len(parents) != 15:
        raise ValueError("Parent bootstrap expects all 15 N-zip parents")
    rng = np.random.default_rng(seed)
    columns = (
        "rank_percentile",
        "normalized_regret",
        "selected_utility",
        "oracle_top1",
        "oracle_top3",
        "oracle_top5",
        "oracle_top10",
        "near_oracle",
        "mean_oracle_rank",
        "spearman_utility",
    )
    values = np.empty((resamples, len(columns)), dtype=float)
    by_parent = {parent: metrics[metrics["parent_id"] == parent] for parent in parents}
    for sample in range(resamples):
        selected = rng.choice(parents, size=len(parents), replace=True)
        table = pd.concat([by_parent[parent] for parent in selected], ignore_index=True)
        macro = macro_metrics(table)
        values[sample] = [macro[column] for column in columns]
    records = []
    observed = macro_metrics(metrics)
    for index, column in enumerate(columns):
        records.append(
            {
                "metric": column,
                "estimate": observed[column],
                "ci95_low": float(np.quantile(values[:, index], 0.025)),
                "ci95_high": float(np.quantile(values[:, index], 0.975)),
                "bootstrap_resamples": resamples,
                "seed": seed,
            }
        )
    return pd.DataFrame(records)
