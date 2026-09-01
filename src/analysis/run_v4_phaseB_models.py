"""Train and evaluate the frozen RNAddress v4 Phase B model family."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_decision_models import (
    add_model_keys,
    decision_set_metrics,
    fit_dfl,
    fit_pairwise,
    fit_predict_then_rank,
    geometry_features,
    normalized_utility,
    source_set_weights,
)
from src.modeling.v4_embeddings import (
    MODEL_SPECS,
    PROJECTION_SEED,
    PROJECTION_SIZE,
    embed_pairs_resumable,
    pair_row_hash,
    sha256,
)


OUT = ROOT / "results" / "v4_phaseB"
INTERIM = ROOT / "data" / "interim"
CANDIDATES = OUT / "phaseB_candidates.csv.gz"
ROWS = OUT / "model_candidate_rows.csv.gz"
INTERVENTIONS = OUT / "model_interventions.csv.gz"
REPRESENTATION_SUMMARY = OUT / "representation_benchmark_summary.json"
SEEDS = (17, 41, 89)
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}


def prepare() -> None:
    rows = pd.read_csv(CANDIDATES)
    rows = rows[rows["selection_eligible"]].copy()
    rows = add_model_keys(rows)
    rows = rows.sort_values(["dataset", "decision_set_id", "candidate_id"]).reset_index(drop=True)
    pair_keys = ["dataset", "parent_id", "mutant_id"]
    interventions = (
        rows.sort_values(pair_keys)
        .drop_duplicates(pair_keys)
        [[*pair_keys, "parent_sequence", "mutant_sequence"]]
        .reset_index(drop=True)
    )
    interventions["feature_row"] = np.arange(len(interventions), dtype=int)
    rows = rows.merge(interventions[[*pair_keys, "feature_row"]], on=pair_keys, validate="many_to_one")
    rows.to_csv(ROWS, index=False, compression=GZIP_OPTIONS)
    interventions.to_csv(INTERVENTIONS, index=False, compression=GZIP_OPTIONS)
    summary = {
        "candidate_rows": len(rows),
        "decision_sets": int(rows["decision_set_id"].nunique()),
        "biological_units": int(rows["biological_unit"].nunique()),
        "unique_intervention_pairs": len(interventions),
        "folds": {
            f"{dataset}:fold_{fold}": int(count)
            for (dataset, fold), count in rows.groupby(
                ["dataset", "biological_fold"]
            )["biological_unit"].nunique().items()
        },
    }
    (OUT / "model_cohort.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


def selected_representation() -> str:
    summary = json.loads(REPRESENTATION_SUMMARY.read_text(encoding="utf-8"))
    return str(summary["selected_representation"])


def full_embedding_paths(model_name: str) -> tuple[Path, Path]:
    return (
        INTERIM / f"v4_phaseB_{model_name}_full_features.npy",
        INTERIM / f"v4_phaseB_{model_name}_full_features.json",
    )


def embed() -> None:
    if not INTERVENTIONS.exists():
        prepare()
    model_name = selected_representation()
    feature_path, metadata_path = full_embedding_paths(model_name)
    frame = pd.read_csv(INTERVENTIONS)
    if not feature_path.exists() and not metadata_path.exists():
        benchmark_rows_path = OUT / "representation_benchmark_interventions.csv.gz"
        benchmark_features_path = INTERIM / f"v4_phaseB_{model_name}_benchmark_features.npy"
        if benchmark_rows_path.exists() and benchmark_features_path.exists():
            shape = (len(frame), PROJECTION_SIZE * 3)
            output = np.lib.format.open_memmap(
                feature_path, mode="w+", dtype=np.float32, shape=shape
            )
            output[:] = np.nan
            benchmark_rows = pd.read_csv(benchmark_rows_path)
            benchmark_features = np.load(benchmark_features_path, mmap_mode="r")
            pair_keys = ["dataset", "parent_id", "mutant_id"]
            mapping = frame[pair_keys].merge(
                benchmark_rows[pair_keys + ["feature_row"]],
                on=pair_keys,
                how="left",
                validate="one_to_one",
            )
            copied = mapping["feature_row"].notna().to_numpy()
            output[copied] = benchmark_features[
                mapping.loc[copied, "feature_row"].to_numpy(int)
            ]
            output.flush()
            metadata_path.write_text(
                json.dumps(
                    {
                        "model": MODEL_SPECS[model_name],
                        "row_hash": pair_row_hash(frame),
                        "shape": list(shape),
                        "projection_size_per_block": PROJECTION_SIZE,
                        "projection_seed": PROJECTION_SEED,
                        "completed_rows": int(copied.sum()),
                        "seeded_from_benchmark_cache": int(copied.sum()),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"seeded {int(copied.sum())} full-cache rows from benchmark", flush=True)
    embed_pairs_resumable(frame, model_name, feature_path, metadata_path, batch_size=64)
    print(f"{model_name} full feature cache sha256={sha256(feature_path)}")


def feature_blocks(rows: pd.DataFrame) -> dict[str, np.ndarray]:
    model_name = selected_representation()
    feature_path, _ = full_embedding_paths(model_name)
    embedded = np.load(feature_path, mmap_mode="r")
    mapped = np.asarray(embedded[rows["feature_row"].to_numpy(int)])
    parent = mapped[:, :128]
    mutant = mapped[:, 128:256]
    context = mapped[:, 256:384]
    absolute_delta = mutant - parent
    geometry_all = geometry_features(rows, categories=True)
    geometry_numeric = geometry_features(rows, categories=False)
    return {
        "parent_only": parent.astype(np.float32),
        "mutant_only": mutant.astype(np.float32),
        "delta_only": np.column_stack([context, absolute_delta]).astype(np.float32),
        "parent_plus_delta": np.column_stack([parent, context, geometry_all]).astype(np.float32),
        "absolute_forward_delta": np.column_stack([absolute_delta, geometry_all]).astype(np.float32),
        "edit_only": geometry_numeric.astype(np.float32),
        "metadata_only": geometry_all.astype(np.float32),
    }


def _outer_scores(
    rows: pd.DataFrame,
    features: np.ndarray,
    kind: str,
    sign: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    global_scores = np.full(len(rows), np.nan)
    hierarchical_scores = np.full(len(rows), np.nan)
    for fold in range(5):
        train = rows["biological_fold"].ne(fold).to_numpy()
        test = ~train
        train_rows = rows.loc[train].reset_index(drop=True)
        if kind == "ptr":
            model = fit_predict_then_rank(features[train], train_rows, sign)
        elif kind == "pairwise":
            model = fit_pairwise(features[train], train_rows, sign, seed)
        elif kind == "dfl":
            model = fit_dfl(features[train], train_rows, sign, seed)
        else:
            raise ValueError(kind)
        global_scores[test] = model.predict(
            features[test], rows.loc[test, "assay_context"], use_residual=False
        )
        hierarchical_scores[test] = model.predict(
            features[test], rows.loc[test, "assay_context"], use_residual=True
        )
    if not np.isfinite(global_scores).all() or not np.isfinite(hierarchical_scores).all():
        raise ValueError(f"Incomplete {kind} outer predictions")
    return global_scores, hierarchical_scores


def _ridge_ablation_scores(
    rows: pd.DataFrame,
    features: np.ndarray,
    sign: int,
) -> np.ndarray:
    scores = np.full(len(rows), np.nan)
    for fold in range(5):
        train = rows["biological_fold"].ne(fold).to_numpy()
        test = ~train
        train_rows = rows.loc[train].reset_index(drop=True)
        scaler = StandardScaler().fit(features[train])
        x_train = scaler.transform(features[train])
        model = Ridge(alpha=100.0)
        model.fit(
            x_train,
            normalized_utility(train_rows, sign),
            sample_weight=source_set_weights(train_rows),
        )
        scores[test] = model.predict(scaler.transform(features[test]))
    return scores


def _nearest_neighbor_scores(
    rows: pd.DataFrame,
    features: np.ndarray,
    sign: int,
) -> np.ndarray:
    scores = np.full(len(rows), np.nan)
    reduced = features[:, : min(features.shape[1], 64)]
    for fold in range(5):
        train = rows["biological_fold"].ne(fold).to_numpy()
        test = ~train
        train_rows = rows.loc[train].reset_index(drop=True)
        train_indices = np.flatnonzero(train)
        if len(train_indices) > 20_000:
            ordering = np.argsort(
                [hashlib.sha256(str(value).encode()).hexdigest() for value in rows.loc[train, "candidate_id"]]
            )[:20_000]
            train_indices = train_indices[ordering]
            train_rows = rows.iloc[train_indices].reset_index(drop=True)
        scaler = StandardScaler().fit(reduced[train_indices])
        model = KNeighborsRegressor(n_neighbors=25, weights="distance", metric="cosine", n_jobs=-1)
        model.fit(
            scaler.transform(reduced[train_indices]), normalized_utility(train_rows, sign)
        )
        scores[test] = model.predict(scaler.transform(reduced[test]))
    return scores


def _absolute_forward_scores(
    rows: pd.DataFrame,
    parent_features: np.ndarray,
    mutant_features: np.ndarray,
    sign: int,
) -> np.ndarray:
    """Fit a shared absolute-state head and difference mutant minus parent.

    Each training parent is the zero point for its measured intervention effect;
    mutant states receive the within-set normalized directional utility.  This is
    the only identifiable absolute-forward comparator when sources publish
    intervention effects but not a common absolute localization scale.
    """
    scores = np.full(len(rows), np.nan)
    for fold in range(5):
        train = rows["biological_fold"].ne(fold).to_numpy()
        test = ~train
        train_rows = rows.loc[train].reset_index(drop=True)
        state_train = np.row_stack([parent_features[train], mutant_features[train]])
        target = np.concatenate(
            [np.zeros(train.sum(), dtype=float), normalized_utility(train_rows, sign)]
        )
        row_weights = source_set_weights(train_rows)
        weights = np.concatenate([row_weights, row_weights])
        scaler = StandardScaler().fit(state_train)
        model = Ridge(alpha=100.0)
        model.fit(scaler.transform(state_train), target, sample_weight=weights)
        mutant_score = model.predict(scaler.transform(mutant_features[test]))
        parent_score = model.predict(scaler.transform(parent_features[test]))
        scores[test] = mutant_score - parent_score
    return scores


def _append_metrics(
    records: list[pd.DataFrame],
    rows: pd.DataFrame,
    score: np.ndarray,
    name: str,
    sign: int,
    seed: int,
    evaluation: str,
) -> None:
    direction = "increase" if sign == 1 else "decrease"
    records.append(decision_set_metrics(rows, score, name, direction, seed, evaluation))


def _random_metrics(template: pd.DataFrame) -> pd.DataFrame:
    random = template.copy()
    random["model"] = "random_exact"
    random["seed"] = 17
    random["evaluation"] = "exact_expectation"
    random["directional_rank_percentile"] = 0.5
    random["normalized_regret"] = random["random_expected_regret"]
    random["selected_normalized_utility"] = 1.0 - random["random_expected_regret"]
    random["selected_experimental_utility"] = np.nan
    random["good_selection_at_1"] = random["random_good_selection_at_1"]
    random["good_selection_at_3"] = random["random_good_selection_at_3"]
    random["good_selection_at_5"] = random["random_good_selection_at_5"]
    random["oracle_recovered"] = 1.0 / random["candidate_count"]
    random["spearman"] = 0.0
    return random


def evaluate() -> None:
    rows = pd.read_csv(ROWS)
    blocks = feature_blocks(rows)
    primary = blocks["parent_plus_delta"]
    metrics: list[pd.DataFrame] = []
    score_arrays: dict[str, np.ndarray] = {}
    for sign in (1, -1):
        ptr_global, ptr_hierarchical = _outer_scores(rows, primary, "ptr", sign, 17)
        direction = "increase" if sign == 1 else "decrease"
        score_arrays[f"ptr_global_{direction}"] = ptr_global.astype(np.float32)
        score_arrays[f"ptr_hierarchical_{direction}"] = ptr_hierarchical.astype(np.float32)
        _append_metrics(metrics, rows, ptr_global, "predict_then_rank_global", sign, 17, "outer_grouped")
        _append_metrics(
            metrics, rows, ptr_hierarchical, "predict_then_rank_hierarchical", sign, 17, "outer_grouped"
        )
        for seed in SEEDS:
            for kind in ("pairwise", "dfl"):
                global_score, hierarchical_score = _outer_scores(rows, primary, kind, sign, seed)
                score_arrays[f"{kind}_global_{direction}_seed{seed}"] = global_score.astype(np.float32)
                score_arrays[f"{kind}_hierarchical_{direction}_seed{seed}"] = hierarchical_score.astype(
                    np.float32
                )
                _append_metrics(
                    metrics,
                    rows,
                    global_score,
                    f"{kind}_global",
                    sign,
                    seed,
                    "outer_grouped",
                )
                _append_metrics(
                    metrics,
                    rows,
                    hierarchical_score,
                    f"{kind}_hierarchical",
                    sign,
                    seed,
                    "outer_grouped",
                )
        for name, features in blocks.items():
            score = _ridge_ablation_scores(rows, features, sign)
            _append_metrics(metrics, rows, score, f"ridge_{name}", sign, 17, "ablation")
        size_score = rows["edit_cost"].to_numpy(float)
        _append_metrics(metrics, rows, size_score, "edit_size_heuristic", sign, 17, "baseline")
        nearest = _nearest_neighbor_scores(rows, blocks["delta_only"], sign)
        _append_metrics(metrics, rows, nearest, "nearest_neighbor", sign, 17, "baseline")
        absolute_forward = _absolute_forward_scores(
            rows, blocks["parent_only"], blocks["mutant_only"], sign
        )
        _append_metrics(
            metrics,
            rows,
            absolute_forward,
            "absolute_forward_difference",
            sign,
            17,
            "baseline",
        )

    set_metrics = pd.concat(metrics, ignore_index=True)
    set_metrics = pd.concat([set_metrics, _random_metrics(set_metrics[set_metrics["model"].eq("predict_then_rank_global")])])
    set_metrics.to_csv(OUT / "model_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    unit_metrics = (
        set_metrics.groupby(
            ["model", "seed", "dataset", "requested_direction", "evaluation", "biological_unit"]
        )
        .agg(
            decision_sets=("decision_set_id", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            selected_experimental_utility=("selected_experimental_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            oracle_recovered=("oracle_recovered", "mean"),
            spearman=("spearman", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )
    unit_metrics.to_csv(OUT / "model_biological_unit_metrics.csv", index=False)
    aggregate = (
        unit_metrics.groupby(["model", "seed", "dataset", "requested_direction", "evaluation"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            selected_experimental_utility=("selected_experimental_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            oracle_recovered=("oracle_recovered", "mean"),
            spearman=("spearman", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
        )
        .reset_index()
    )
    aggregate.to_csv(OUT / "model_aggregate_metrics.csv", index=False)
    np.savez_compressed(OUT / "outer_candidate_scores.npz", **score_arrays)
    select_models = aggregate[
        aggregate["model"].isin(
            ["predict_then_rank_hierarchical", "pairwise_hierarchical", "dfl_hierarchical"]
        )
    ]
    means = select_models.groupby("model").agg(
        rank=("directional_rank_percentile", "mean"),
        regret=("normalized_regret", "mean"),
        good3=("good_selection_at_3", "mean"),
    )
    ptr = means.loc["predict_then_rank_hierarchical"]
    dfl_source = select_models.groupby(["model", "dataset"]).agg(
        regret=("normalized_regret", "mean"), good3=("good_selection_at_3", "mean")
    )
    dfl_gains = []
    for dataset in sorted(rows["dataset"].unique()):
        baseline = dfl_source.loc[("predict_then_rank_hierarchical", dataset)]
        candidate = dfl_source.loc[("dfl_hierarchical", dataset)]
        dfl_gains.append(
            {
                "dataset": dataset,
                "regret_gain": float(baseline["regret"] - candidate["regret"]),
                "good3_gain": float(candidate["good3"] - baseline["good3"]),
            }
        )
    passing_sources = sum(
        item["regret_gain"] >= 0.01 and item["good3_gain"] >= 0.01 for item in dfl_gains
    )
    no_large_degradation = all(item["regret_gain"] >= -0.03 for item in dfl_gains)
    dfl_pass = passing_sources >= 2 and no_large_degradation
    if dfl_pass:
        selected = "dfl"
    elif means.loc["pairwise_hierarchical", "regret"] < ptr["regret"] and means.loc[
        "pairwise_hierarchical", "rank"
    ] > ptr["rank"]:
        selected = "pairwise"
    else:
        selected = "ptr"
    summary = {
        "phase": "v4_phaseB_definitive_models",
        "git_commit_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selected_representation": selected_representation(),
        "selected_model_kind": selected,
        "model_means": means.reset_index().to_dict("records"),
        "dfl_gate": {
            "per_source_gains": dfl_gains,
            "passing_sources": passing_sources,
            "no_source_regret_degradation_below_minus_0_03": no_large_degradation,
            "passed": dfl_pass,
        },
        "seeds": list(SEEDS),
        "scope_guards": {"nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "score_archive_sha256": sha256(OUT / "outer_candidate_scores.npz"),
    }
    (OUT / "model_selection.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "embed", "evaluate", "all"], nargs="?", default="all")
    args = parser.parse_args()
    if args.stage in {"prepare", "all"}:
        prepare()
    if args.stage in {"embed", "all"}:
        embed()
    if args.stage in {"evaluate", "all"}:
        evaluate()


if __name__ == "__main__":
    main()
