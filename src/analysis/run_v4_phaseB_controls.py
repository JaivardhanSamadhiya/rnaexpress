"""Run preregistered RNAddress v4 leakage and shortcut controls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_v4_phaseB_models import ROWS, feature_blocks
from src.modeling.v4_decision_models import (
    decision_set_metrics,
    fit_dfl,
    fit_pairwise,
    fit_predict_then_rank,
)


OUT = ROOT / "results" / "v4_phaseB"
SEEDS = (17, 41, 89)
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}


def permute_outcomes_within_source(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    result = frame.copy()
    rng = np.random.default_rng(seed)
    original = frame["localization_effect"].to_numpy(float)
    permuted = original.copy()
    for _, indices in frame.groupby("dataset", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        permuted[indices] = original[rng.permutation(indices)]
    result["localization_effect"] = permuted
    if np.array_equal(original, permuted):
        raise ValueError("Outcome permutation did not alter labels")
    return result


def permute_parent_context_features(
    frame: pd.DataFrame, features: np.ndarray, seed: int
) -> np.ndarray:
    result = features.copy()
    rng = np.random.default_rng(seed)
    changed = 0
    for _, indices in frame.groupby("dataset", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        order = rng.permutation(indices)
        result[indices, :256] = features[order, :256]
        changed += int(np.any(result[indices, :256] != features[indices, :256], axis=1).sum())
    if changed == 0:
        raise ValueError("Parent/context permutation did not alter features")
    return result


def permute_scores_within_decision_set(
    frame: pd.DataFrame, scores: np.ndarray, seed: int
) -> np.ndarray:
    result = scores.copy()
    rng = np.random.default_rng(seed)
    changed = 0
    for _, indices in frame.groupby("decision_set_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        shuffled = rng.permutation(scores[indices])
        result[indices] = shuffled
        changed += int(np.sum(shuffled != scores[indices]))
    if changed == 0:
        raise ValueError("Intervention permutation did not alter scores")
    return result


def _fit(kind: str, features: np.ndarray, rows: pd.DataFrame, sign: int, seed: int):
    if kind == "ptr":
        return fit_predict_then_rank(features, rows, sign)
    if kind == "pairwise":
        return fit_pairwise(features, rows, sign, seed)
    if kind == "dfl":
        return fit_dfl(features, rows, sign, seed)
    raise ValueError(kind)


def _permuted_outer_scores(
    rows: pd.DataFrame,
    features: np.ndarray,
    kind: str,
    sign: int,
    seed: int,
    outcome_permutation: bool,
) -> np.ndarray:
    scores = np.full(len(rows), np.nan)
    for fold in range(5):
        train = rows["biological_fold"].ne(fold).to_numpy()
        test = ~train
        train_rows = rows.loc[train].reset_index(drop=True)
        if outcome_permutation:
            train_rows = permute_outcomes_within_source(train_rows, seed + fold * 1009)
        model = _fit(kind, features[train], train_rows, sign, seed)
        scores[test] = model.predict(
            features[test], rows.loc[test, "assay_context"], use_residual=True
        )
    if not np.isfinite(scores).all():
        raise ValueError("Control generated incomplete scores")
    return scores


def _exact_random(template: pd.DataFrame, seed: int, control: str) -> pd.DataFrame:
    result = template.copy()
    result["control"] = control
    result["seed"] = seed
    result["directional_rank_percentile"] = 0.5
    result["normalized_regret"] = result["random_expected_regret"]
    result["selected_normalized_utility"] = 1.0 - result["random_expected_regret"]
    result["selected_experimental_utility"] = np.nan
    for k in (1, 3, 5):
        result[f"good_selection_at_{k}"] = result[f"random_good_selection_at_{k}"]
    result["oracle_recovered"] = 1.0 / result["candidate_count"]
    result["spearman"] = 0.0
    return result


def _aggregate(metrics: pd.DataFrame) -> pd.DataFrame:
    unit = (
        metrics.groupby(
            ["control", "seed", "dataset", "requested_direction", "biological_unit"]
        )
        .agg(
            decision_sets=("decision_set_id", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )
    return (
        unit.groupby(["control", "seed", "dataset", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )


def main() -> None:
    rows = pd.read_csv(ROWS)
    primary = feature_blocks(rows)["parent_plus_delta"]
    selection = json.loads((OUT / "model_selection.json").read_text(encoding="utf-8"))
    kind = str(selection["selected_model_kind"])
    archive = np.load(OUT / "outer_candidate_scores.npz")
    records: list[pd.DataFrame] = []
    for sign, direction in ((1, "increase"), (-1, "decrease")):
        key = (
            f"ptr_hierarchical_{direction}"
            if kind == "ptr"
            else f"{kind}_hierarchical_{direction}_seed17"
        )
        real_scores = np.asarray(archive[key], dtype=float)
        template = decision_set_metrics(
            rows, real_scores, "control", direction, 17, "controls"
        )
        for seed in SEEDS:
            intervention_scores = permute_scores_within_decision_set(rows, real_scores, seed)
            metric = decision_set_metrics(
                rows, intervention_scores, "control", direction, seed, "controls"
            )
            metric["control"] = "intervention_permutation_within_set"
            records.append(metric)

            outcome_scores = _permuted_outer_scores(
                rows, primary, kind, sign, seed, outcome_permutation=True
            )
            metric = decision_set_metrics(
                rows, outcome_scores, "control", direction, seed, "controls"
            )
            metric["control"] = "outcome_permutation_within_source"
            records.append(metric)

            parent_features = permute_parent_context_features(rows, primary, seed)
            parent_scores = _permuted_outer_scores(
                rows, parent_features, kind, sign, seed, outcome_permutation=False
            )
            metric = decision_set_metrics(
                rows, parent_scores, "control", direction, seed, "controls"
            )
            metric["control"] = "parent_context_permutation"
            records.append(metric)

            records.append(_exact_random(template, seed, "source_only_exact_expectation"))
        print(f"completed controls for {direction}", flush=True)

    metrics = pd.concat(records, ignore_index=True)
    metrics.to_csv(OUT / "control_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    aggregate = _aggregate(metrics)
    aggregate.to_csv(OUT / "control_aggregate_metrics.csv", index=False)
    summary = (
        aggregate.groupby("control")
        .agg(
            rank=("directional_rank_percentile", "mean"),
            regret=("normalized_regret", "mean"),
            random_regret=("random_expected_regret", "mean"),
            rank_distance_from_chance=("directional_rank_percentile", lambda value: float(abs(value.mean() - 0.5))),
        )
        .reset_index()
    )
    summary["regret_distance_from_random"] = (
        summary["regret"] - summary["random_regret"]
    ).abs()
    summary["within_frozen_0_02_tolerance"] = (
        summary["rank_distance_from_chance"].le(0.02)
        & summary["regret_distance_from_random"].le(0.02)
    )
    summary.to_csv(OUT / "control_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
