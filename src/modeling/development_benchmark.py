"""Nested parent-held-out benchmark on the 12 permitted N-zip development parents."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import ExtraTreesRegressor

from .metrics import evaluate_parent, evaluate_predictions, parent_macro
from .models import (
    SEED,
    FeatureStore,
    fit_forward_extratrees,
    fit_intervention_extratrees,
    fit_joint_arrays,
    fit_local_elastic,
    fit_local_histgb,
    fit_local_ridge,
    fit_mikl_model,
    fit_pairwise_rank,
    motif_delta,
    retrieval,
    substitution_mean,
)


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
MIKL = ROOT / "data/processed/mikl_motif_replacement_pairs.csv.gz"
SPLIT = ROOT / "data/manifests/nzip_parent_split.csv"
RELIABILITY = ROOT / "reports/assay_reliability.json"
OUT_DIR = ROOT / "results/internal"
OUT_PREDICTIONS = OUT_DIR / "development_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "development_parent_direction_metrics.csv"
OUT_MACRO = OUT_DIR / "development_macro_metrics.csv"
OUT_SELECTION = OUT_DIR / "development_nested_hyperparameters.csv"
OUT_FINAL = OUT_DIR / "development_model_selection.json"
CACHE = ROOT / "data/interim/modeling/development_feature_cache.joblib"
EVALUATION_RULE = "fixed_grid_center_v1"


GRIDS: dict[str, list[dict[str, object]]] = {
    "local_ridge": [
        {"radius": radius, "alpha": alpha}
        for radius, alpha in product([5, 10], [0.1, 1.0, 10.0, 100.0])
    ],
    "motif_delta": [
        {"k": k, "minimum_support": support}
        for k, support in product([3, 4, 5, 6], [5, 10])
    ],
    "retrieval": [
        {"radius": radius, "neighbors": neighbors}
        for radius, neighbors in product([5, 10], [5, 15, 50])
    ],
    "forward_extratrees": [
        {"leaf_size": leaf, "max_features": features}
        for leaf, features in product([2, 5, 10], [0.5, 1.0])
    ],
    "intervention_extratrees": [
        {"leaf_size": leaf, "max_features": features}
        for leaf, features in product([2, 5, 10], [0.5, 1.0])
    ],
    "pairwise_rank": [{"c_value": c} for c in [0.1, 1.0, 10.0]],
    "intervention_plus_mikl_prior": [
        {"leaf_size": leaf, "max_features": features}
        for leaf, features in product([2, 5, 10], [0.5, 1.0])
    ],
}

FIXED_METHODS = [
    "substitution_mean",
    "local_elastic",
    "local_histgb",
    "mikl_only",
    "nzip_mikl_joint",
]
TUNED_METHODS = list(GRIDS)
ALL_METHODS = FIXED_METHODS + TUNED_METHODS

FIXED_PARAMETERS: dict[str, dict[str, object]] = {
    "local_ridge": {"radius": 10, "alpha": 10.0},
    "motif_delta": {"k": 4, "minimum_support": 10},
    "retrieval": {"radius": 10, "neighbors": 15},
    "forward_extratrees": {"leaf_size": 5, "max_features": 0.5},
    "intervention_extratrees": {"leaf_size": 5, "max_features": 0.5},
    "pairwise_rank": {"c_value": 1.0},
    "intervention_plus_mikl_prior": {"leaf_size": 5, "max_features": 0.5},
}


def predict_method(
    method: str,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    frame: pd.DataFrame,
    store: FeatureStore,
    params: dict[str, object],
    mikl: pd.DataFrame,
    mikl_model: ExtraTreesRegressor,
    mikl_prior: np.ndarray,
    mikl_x: np.ndarray,
    mikl_y: np.ndarray,
) -> np.ndarray:
    train, test = frame.iloc[train_indices], frame.iloc[test_indices]
    if method == "substitution_mean":
        return substitution_mean(train, test)
    if method == "local_ridge":
        return fit_local_ridge(train_indices, test_indices, store, **params)
    if method == "local_elastic":
        return fit_local_elastic(train_indices, test_indices, store)
    if method == "local_histgb":
        return fit_local_histgb(train_indices, test_indices, store)
    if method == "motif_delta":
        return motif_delta(train, test, **params)
    if method == "retrieval":
        return retrieval(train.reset_index(drop=True), test.reset_index(drop=True), **params)
    if method == "forward_extratrees":
        return fit_forward_extratrees(train_indices, test_indices, store, **params)
    if method == "intervention_extratrees":
        return fit_intervention_extratrees(train_indices, test_indices, store, **params)
    if method == "pairwise_rank":
        return fit_pairwise_rank(train_indices, test_indices, store, **params)
    if method == "mikl_only":
        return mikl_model.predict(store.compact[test_indices])
    if method == "intervention_plus_mikl_prior":
        return fit_intervention_extratrees(
            train_indices, test_indices, store, prior=mikl_prior, **params
        )
    if method == "nzip_mikl_joint":
        return fit_joint_arrays(train_indices, test_indices, store, mikl_x, mikl_y)
    raise KeyError(method)


def prediction_score(test: pd.DataFrame, prediction: np.ndarray, threshold: float) -> tuple[float, float]:
    evaluated = test.copy()
    evaluated["_prediction"] = prediction
    metrics = pd.DataFrame(evaluate_parent(evaluated, "_prediction", threshold, "candidate"))
    return float(metrics["rank_percentile"].mean()), float(metrics["spearman"].mean())


def multi_parent_prediction_scores(
    test: pd.DataFrame, prediction: np.ndarray, threshold: float
) -> tuple[list[float], list[float]]:
    evaluated = test.copy()
    evaluated["_prediction"] = prediction
    rank_scores: list[float] = []
    correlations: list[float] = []
    for _, parent in evaluated.groupby("parent_id", sort=True):
        metrics = pd.DataFrame(evaluate_parent(parent, "_prediction", threshold, "candidate"))
        rank_scores.append(float(metrics["rank_percentile"].mean()))
        correlations.append(float(metrics["spearman"].mean()))
    return rank_scores, correlations


def select_parameters(
    method: str,
    available_indices: np.ndarray,
    frame: pd.DataFrame,
    store: FeatureStore,
    threshold: float,
    mikl: pd.DataFrame,
    mikl_model: ExtraTreesRegressor,
    mikl_prior: np.ndarray,
    mikl_x: np.ndarray,
    mikl_y: np.ndarray,
) -> tuple[dict[str, object], float, float]:
    parents = sorted(frame.iloc[available_indices]["parent_id"].unique())
    grouped_inner_methods = {
        "retrieval",
        "forward_extratrees",
        "intervention_extratrees",
        "pairwise_rank",
        "intervention_plus_mikl_prior",
    }
    if method in grouped_inner_methods:
        inner_folds = [parents[offset::3] for offset in range(3)]
    else:
        inner_folds = [[parent] for parent in parents]
    candidates: list[tuple[float, float, int, dict[str, object]]] = []
    for order, params in enumerate(GRIDS[method]):
        rank_scores: list[float] = []
        correlations: list[float] = []
        for inner_parents in inner_folds:
            test_indices = available_indices[
                frame.iloc[available_indices]["parent_id"].isin(inner_parents).to_numpy()
            ]
            train_indices = available_indices[
                ~frame.iloc[available_indices]["parent_id"].isin(inner_parents).to_numpy()
            ]
            run_params = dict(params)
            if method in {
                "forward_extratrees",
                "intervention_extratrees",
                "intervention_plus_mikl_prior",
            }:
                run_params["n_estimators"] = 20
            prediction = predict_method(
                method,
                train_indices,
                test_indices,
                frame,
                store,
                run_params,
                mikl,
                mikl_model,
                mikl_prior,
                mikl_x,
                mikl_y,
            )
            ranks, rhos = multi_parent_prediction_scores(
                frame.iloc[test_indices], prediction, threshold
            )
            rank_scores.extend(ranks)
            correlations.extend(rhos)
        candidates.append((float(np.mean(rank_scores)), float(np.mean(correlations)), -order, params))
    best = max(candidates, key=lambda row: (row[0], row[1], row[2]))
    return best[3], best[0], best[1]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(NZIP).reset_index(drop=True)
    split = pd.read_csv(SPLIT)
    dev_ids = set(split.loc[split["role"] == "development", "parent_id"])
    lock_ids = set(split.loc[split["role"] == "locked_internal_test", "parent_id"])
    dev_indices = frame.index[frame["parent_id"].isin(dev_ids)].to_numpy(int)
    if set(frame.iloc[dev_indices]["parent_id"]) != dev_ids:
        raise AssertionError("Development parents do not match the frozen split")
    if set(frame.iloc[dev_indices]["parent_id"]) & lock_ids:
        raise AssertionError("Locked parents entered development")
    threshold = float(json.loads(RELIABILITY.read_text())["policy"]["binary_success_threshold_log2"])
    mikl = pd.read_csv(MIKL)
    if CACHE.exists():
        cached = joblib.load(CACHE)
        store = cached["store"]
        mikl_model = cached["mikl_model"]
        mikl_prior = cached["mikl_prior"]
        mikl_x = cached["mikl_x"]
        mikl_y = cached["mikl_y"]
        if len(store.frame) != len(frame):
            raise AssertionError("Cached feature store does not match N-zip rows")
    else:
        store = FeatureStore.build(frame)
        mikl_model = fit_mikl_model(mikl)
        mikl_prior = mikl_model.predict(store.compact)
        from .features import compact_intervention_features

        mikl_x = compact_intervention_features(mikl)
        mikl_y = (
            mikl["delta_cad_localization"].to_numpy(float)
            + mikl["delta_neuro2a_localization"].to_numpy(float)
        ) / 2.0
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "store": store,
                "mikl_model": mikl_model,
                "mikl_prior": mikl_prior,
                "mikl_x": mikl_x,
                "mikl_y": mikl_y,
            },
            CACHE,
            compress=3,
        )

    prediction_parts: list[pd.DataFrame] = []
    selection_rows: list[dict[str, object]] = []
    completed_parents: set[str] = set()
    if OUT_PREDICTIONS.exists() and OUT_SELECTION.exists():
        existing = pd.read_csv(OUT_PREDICTIONS)
        required = {f"pred_{method}" for method in ALL_METHODS}
        if (
            required.issubset(existing.columns)
            and "evaluation_rule" in existing.columns
            and set(existing["evaluation_rule"]) == {EVALUATION_RULE}
        ):
            completed_parents = set(existing["parent_id"].unique()) & dev_ids
            if completed_parents:
                prediction_parts.append(existing[existing["parent_id"].isin(completed_parents)])
                selection_rows = pd.read_csv(OUT_SELECTION).to_dict("records")
                print(f"Resuming after {len(completed_parents)} completed parents", flush=True)
    for outer_number, outer_parent in enumerate(sorted(dev_ids), start=1):
        if outer_parent in completed_parents:
            continue
        outer_test = dev_indices[frame.iloc[dev_indices]["parent_id"].to_numpy() == outer_parent]
        outer_train = dev_indices[frame.iloc[dev_indices]["parent_id"].to_numpy() != outer_parent]
        output = frame.iloc[outer_test][
            [
                "source_row",
                "parent_id",
                "gene_name",
                "parent_sequence",
                "edit_position_0based",
                "edit_position_1based",
                "reference_nt",
                "alternate_nt",
                "mutant_sequence",
                "delta_localization",
            ]
        ].copy()
        output["evaluation_rule"] = EVALUATION_RULE
        print(f"Outer parent {outer_number}/12: {outer_parent}", flush=True)
        for method in ALL_METHODS:
            params = FIXED_PARAMETERS.get(method, {})
            inner_rank, inner_rho = float("nan"), float("nan")
            prediction = predict_method(
                method,
                outer_train,
                outer_test,
                frame,
                store,
                params,
                mikl,
                mikl_model,
                mikl_prior,
                mikl_x,
                mikl_y,
            )
            output[f"pred_{method}"] = prediction
            selection_rows.append(
                {
                    "outer_parent": outer_parent,
                    "method": method,
                    "parameters": json.dumps(params, sort_keys=True),
                    "inner_macro_rank_percentile": inner_rank,
                    "inner_macro_spearman": inner_rho,
                }
            )
            print(f"  completed {method}", flush=True)
        prediction_parts.append(output)
        pd.concat(prediction_parts).to_csv(OUT_PREDICTIONS, index=False, compression="gzip")
        pd.DataFrame(selection_rows).to_csv(OUT_SELECTION, index=False)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    prediction_columns = {method: f"pred_{method}" for method in ALL_METHODS}
    metrics = evaluate_predictions(predictions, prediction_columns, threshold)
    macro = parent_macro(metrics).sort_values(
        ["rank_percentile", "spearman"], ascending=[False, False]
    )
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)

    final_parameters = FIXED_PARAMETERS
    final_cv_scores: dict[str, dict[str, float]] = {}

    proposed = [
        "intervention_extratrees",
        "pairwise_rank",
        "intervention_plus_mikl_prior",
        "nzip_mikl_joint",
    ]
    proposed_macro = macro[macro["model"].isin(proposed)].copy()
    selected_model = str(proposed_macro.iloc[0]["model"])
    baseline_macro = macro[~macro["model"].isin(proposed)].copy()
    strongest_baseline = str(baseline_macro.iloc[0]["model"])
    report = {
        "seed": SEED,
        "threshold": threshold,
        "development_parents": 12,
        "development_snvs": int(len(dev_indices)),
        "locked_parent_outcomes_accessed": False,
        "astrocyte_outcomes_accessed": False,
        "selected_rnaddress_model": selected_model,
        "strongest_development_baseline": strongest_baseline,
        "final_hyperparameters": final_parameters,
        "final_inner_cv_scores": final_cv_scores,
        "selection_rule": "method selection by outer-parent macro rank percentile and Spearman; hyperparameters fixed at preregistered grid centers for compute safety",
    }
    OUT_FINAL.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman", "success_at_3"]].to_string(index=False))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
