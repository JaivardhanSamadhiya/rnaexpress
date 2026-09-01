"""Run the frozen RNAddress v4 Phase B representation benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_embeddings import MODEL_SPECS, embed_pairs_resumable, sha256


OUT = ROOT / "results" / "v4_phaseB"
INTERIM = ROOT / "data" / "interim"
CANDIDATES = OUT / "phaseB_candidates.csv.gz"
BENCHMARK_ROWS = OUT / "representation_benchmark_rows.csv.gz"
INTERVENTIONS = OUT / "representation_benchmark_interventions.csv.gz"
CAP_PER_SET = 64
RIDGE_ALPHA = 100.0
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}
MODELS = ("3utrbert", "splicebert")
EDIT_BANDS = ("exact_1", "small_2_5", "short_6_10", "medium_11_25", "regional_26_50", "large_gt50")
INTERVENTION_CLASSES = (
    "motif_random_replacement",
    "tdp43_motif_complement_replacement",
    "sufficiency_background_replacement",
    "necessity_deletion_with_inactive_padding",
    "random_substitution",
    "regional_shuffle",
    "shape_structure_perturbation",
)
EDIT_TIERS = ("exact_snv", "small_local_edit", "motif_scale_edit", "regional_edit", "large_element_edit")


def stable_order(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def edit_band(value: int) -> str:
    if value == 1:
        return "exact_1"
    if value <= 5:
        return "small_2_5"
    if value <= 10:
        return "short_6_10"
    if value <= 25:
        return "medium_11_25"
    if value <= 50:
        return "regional_26_50"
    return "large_gt50"


def round_robin_indices(frame: pd.DataFrame, cap: int) -> list[int]:
    queues: dict[str, list[int]] = {}
    for band in EDIT_BANDS:
        rows = frame[frame["benchmark_edit_band"].eq(band)].copy()
        rows["_order"] = rows["candidate_id"].map(stable_order)
        queues[band] = rows.sort_values("_order").index.tolist()
    selected: list[int] = []
    while len(selected) < min(cap, len(frame)):
        advanced = False
        for band in EDIT_BANDS:
            if queues[band] and len(selected) < cap:
                selected.append(queues[band].pop(0))
                advanced = True
        if not advanced:
            break
    return selected


def prepare() -> None:
    candidates = pd.read_csv(CANDIDATES)
    candidates = candidates[candidates["selection_eligible"]].copy()
    candidates["benchmark_edit_band"] = candidates["edit_distance"].astype(int).map(edit_band)
    selected_indices: list[int] = []
    for _, frame in candidates.groupby("decision_set_id", sort=True):
        selected_indices.extend(round_robin_indices(frame, CAP_PER_SET))
    rows = candidates.loc[selected_indices].copy()
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
    rows.to_csv(BENCHMARK_ROWS, index=False, compression=GZIP_OPTIONS)
    interventions.to_csv(INTERVENTIONS, index=False, compression=GZIP_OPTIONS)
    summary = {
        "candidate_cap_per_decision_set": CAP_PER_SET,
        "eligible_decision_sets": int(rows["decision_set_id"].nunique()),
        "benchmark_candidate_rows": len(rows),
        "unique_intervention_pairs": len(interventions),
        "by_source": rows.groupby("dataset").agg(
            decision_sets=("decision_set_id", "nunique"), candidate_rows=("candidate_id", "size")
        ).to_dict("index"),
        "edit_bands": rows["benchmark_edit_band"].value_counts().sort_index().to_dict(),
        "outcome_blind_selection": True,
    }
    (OUT / "representation_benchmark_cohort.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def embedding_paths(model_name: str) -> tuple[Path, Path]:
    return (
        INTERIM / f"v4_phaseB_{model_name}_benchmark_features.npy",
        INTERIM / f"v4_phaseB_{model_name}_benchmark_features.json",
    )


def embed(model_name: str) -> None:
    if not INTERVENTIONS.exists():
        prepare()
    frame = pd.read_csv(INTERVENTIONS)
    feature_path, metadata_path = embedding_paths(model_name)
    embed_pairs_resumable(frame, model_name, feature_path, metadata_path, batch_size=64)
    print(f"{model_name} feature cache sha256={sha256(feature_path)}")


def geometry(frame: pd.DataFrame) -> np.ndarray:
    length = frame["parent_sequence"].str.len().astype(float)
    numeric = np.column_stack(
        [
            np.log1p(frame["edit_distance"].astype(float)),
            frame["edit_fraction"].astype(float),
            np.log1p(frame["edit_cost"].astype(float)),
            np.log1p(frame["substitution_count"].astype(float)),
            np.log1p(frame["insertion_length"].astype(float)),
            np.log1p(frame["deletion_length"].astype(float)),
            np.log1p(frame["replacement_length"].astype(float)),
            np.log1p(frame["changed_block_count"].astype(float)),
            frame["mean_edit_position_1based"].astype(float) / length,
            frame["first_edit_position_1based"].astype(float) / length,
            frame["last_edit_position_1based"].astype(float) / length,
            frame["edit_span_length"].astype(float) / length,
        ]
    ).astype(np.float32)
    composition = []
    for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"]):
        scale = float(len(parent))
        composition.append(
            [(mutant.count(base) - parent.count(base)) / scale for base in "ACGT"]
        )
    categories = []
    for value in INTERVENTION_CLASSES:
        categories.append(frame["intervention_class"].eq(value).astype(float).to_numpy())
    for value in EDIT_TIERS:
        categories.append(frame["edit_tier"].eq(value).astype(float).to_numpy())
    return np.column_stack([numeric, np.asarray(composition, dtype=np.float32), *categories]).astype(
        np.float32
    )


def biological_unit(frame: pd.DataFrame) -> pd.Series:
    values = []
    for row in frame.to_dict("records"):
        if row["dataset"] == "mikl_gse173098":
            values.append(f"mikl_gene:{str(row['gene_name']).lower()}")
        elif row["dataset"] == "tdp43_gse288185":
            values.append(f"tdp_gene:{row['gene_id']}")
        else:
            parent_sequence_hash = hashlib.sha256(
                str(row["parent_sequence"]).encode("ascii")
            ).hexdigest()
            values.append(f"moffatt_parent_sequence:{parent_sequence_hash}")
    return pd.Series(values, index=frame.index, dtype=str)


def normalized_utility(frame: pd.DataFrame, sign: int) -> np.ndarray:
    signed = frame["localization_effect"].to_numpy(dtype=float) * sign
    series = pd.Series(signed, index=frame.index)
    minimum = series.groupby(frame["decision_set_id"]).transform("min").to_numpy()
    maximum = series.groupby(frame["decision_set_id"]).transform("max").to_numpy()
    scale = maximum - minimum
    if not np.all(scale > 0):
        raise ValueError("Representation benchmark contains a zero-range decision set")
    return (signed - minimum) / scale


def source_set_weights(frame: pd.DataFrame) -> np.ndarray:
    set_sizes = frame.groupby("decision_set_id")["candidate_id"].transform("size").to_numpy(float)
    unit_sets = frame.groupby("biological_unit")["decision_set_id"].transform("nunique").to_numpy(float)
    source_units = frame.groupby("dataset")["biological_unit"].transform("nunique").to_numpy(float)
    weights = 1.0 / (set_sizes * unit_sets * source_units)
    return weights / weights.mean()


def fold_definitions(frame: pd.DataFrame) -> list[tuple[str, set[str]]]:
    definitions: list[tuple[str, set[str]]] = []
    for dataset, source in frame.groupby("dataset"):
        units = sorted(source["biological_unit"].unique())
        for fold in range(5):
            held = {
                unit
                for unit in units
                if int(hashlib.sha256(unit.encode()).hexdigest()[:8], 16) % 5 == fold
            }
            definitions.append((dataset, held))
    return definitions


def set_metrics(frame: pd.DataFrame, score_column: str) -> list[dict[str, object]]:
    records = []
    for (model, dataset, decision_set_id, direction), group in frame.groupby(
        ["model", "dataset", "decision_set_id", "requested_direction"], sort=True
    ):
        sign = 1 if direction == "increase" else -1
        utility = group["localization_effect"].to_numpy(float) * sign
        scores = group[score_column].to_numpy(float)
        order = np.lexsort((group["candidate_id"].to_numpy(str), -scores))
        best = float(utility.max())
        worst = float(utility.min())
        scale = best - worst
        if scale <= 0:
            continue
        normalized_regrets = (best - utility) / scale
        selected = int(order[0])
        true_rank = rankdata(-utility, method="average")[selected]
        rank_percentile = 1.0 - (true_rank - 1.0) / (len(group) - 1.0)
        good = normalized_regrets <= 0.10
        random_regret = float(normalized_regrets.mean())
        good_count = int(good.sum())
        random_good = {}
        for k in (1, 3, 5):
            k_eff = min(k, len(group))
            random_good[k] = 1.0 - (
                math.comb(len(group) - good_count, k_eff) / math.comb(len(group), k_eff)
                if len(group) - good_count >= k_eff
                else 0.0
            )
        records.append(
            {
                "model": model,
                "dataset": dataset,
                "decision_set_id": decision_set_id,
                "biological_unit": group["biological_unit"].iloc[0],
                "requested_direction": direction,
                "candidate_count": len(group),
                "directional_rank_percentile": float(rank_percentile),
                "normalized_regret": float(normalized_regrets[selected]),
                "selected_normalized_utility": float(1.0 - normalized_regrets[selected]),
                "selected_experimental_utility": float(utility[selected]),
                "good_selection_at_1": float(good[order[:1]].any()),
                "good_selection_at_3": float(good[order[: min(3, len(group))]].any()),
                "good_selection_at_5": float(good[order[: min(5, len(group))]].any()),
                "random_expected_regret": random_regret,
                "random_good_selection_at_1": random_good[1],
                "random_good_selection_at_3": random_good[3],
                "random_good_selection_at_5": random_good[5],
                "spearman": float(spearmanr(scores, utility).statistic)
                if np.unique(scores).size > 1 and np.unique(utility).size > 1
                else np.nan,
            }
        )
    return records


def evaluate() -> None:
    rows = pd.read_csv(BENCHMARK_ROWS)
    rows["biological_unit"] = biological_unit(rows)
    geometry_features = geometry(rows)
    predictions = []
    for model_name in MODELS:
        feature_path, metadata_path = embedding_paths(model_name)
        if not feature_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Missing frozen {model_name} embedding cache")
        intervention_features = np.load(feature_path, mmap_mode="r")
        mapped = np.asarray(intervention_features[rows["feature_row"].to_numpy(int)])
        parent = mapped[:, :128]
        context = mapped[:, 256:384]
        features = np.column_stack([parent, context, geometry_features]).astype(np.float32)
        scores = {1: np.full(len(rows), np.nan), -1: np.full(len(rows), np.nan)}
        for target_dataset, held_units in fold_definitions(rows):
            test = rows["dataset"].eq(target_dataset) & rows["biological_unit"].isin(held_units)
            train = ~test
            if not test.any() or not train.any():
                raise ValueError("Invalid representation benchmark biological fold")
            scaler = StandardScaler().fit(features[train])
            x_train = scaler.transform(features[train])
            x_test = scaler.transform(features[test])
            weights = source_set_weights(rows.loc[train])
            for sign in (1, -1):
                target = normalized_utility(rows.loc[train], sign)
                model = Ridge(alpha=RIDGE_ALPHA)
                model.fit(x_train, target, sample_weight=weights)
                if np.isfinite(scores[sign][test]).any():
                    raise ValueError("A representation row received multiple outer predictions")
                scores[sign][test] = model.predict(x_test)
        for sign, direction in ((1, "increase"), (-1, "decrease")):
            if not np.isfinite(scores[sign]).all():
                raise ValueError(f"Incomplete {model_name} {direction} predictions")
            predictions.append(
                pd.DataFrame(
                    {
                        "model": model_name,
                        "candidate_id": rows["candidate_id"],
                        "decision_set_id": rows["decision_set_id"],
                        "dataset": rows["dataset"],
                        "biological_unit": rows["biological_unit"],
                        "requested_direction": direction,
                        "localization_effect": rows["localization_effect"],
                        "score": scores[sign],
                    }
                )
            )
    prediction_frame = pd.concat(predictions, ignore_index=True)
    prediction_frame.to_csv(
        OUT / "representation_benchmark_predictions.csv.gz", index=False, compression=GZIP_OPTIONS
    )
    metric_rows = pd.DataFrame(set_metrics(prediction_frame, "score"))
    metric_rows.to_csv(OUT / "representation_benchmark_set_metrics.csv", index=False)
    unit_metrics = (
        metric_rows.groupby(["model", "dataset", "requested_direction", "biological_unit"])
        .agg(
            decision_sets=("decision_set_id", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            spearman=("spearman", "mean"),
        )
        .reset_index()
    )
    aggregate = (
        unit_metrics.groupby(["model", "dataset", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            spearman=("spearman", "mean"),
        )
        .reset_index()
    )
    aggregate.to_csv(OUT / "representation_benchmark_metrics.csv", index=False)
    selection = aggregate.groupby("model").agg(
        directional_rank_percentile=("directional_rank_percentile", "mean"),
        selected_normalized_utility=("selected_normalized_utility", "mean"),
    )
    selection["selection_score"] = selection.mean(axis=1)
    winner = str(selection["selection_score"].idxmax())
    if selection["selection_score"].max() - selection["selection_score"].min() < 0.01:
        winner = "splicebert"
    summary = {
        "phase": "v4_phaseB_representation_benchmark",
        "git_commit_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "models": MODEL_SPECS,
        "rinalmo": {
            "evaluated": False,
            "reason_frozen_before_results": "650M model, no local pinned checkpoint, and no CUDA/GPU on this host",
        },
        "ridge_alpha": RIDGE_ALPHA,
        "selection": selection.reset_index().to_dict("records"),
        "tie_margin": 0.01,
        "selected_representation": winner,
        "scope_guards": {"nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "embedding_caches": {
            name: {
                "path": embedding_paths(name)[0].relative_to(ROOT).as_posix(),
                "sha256": sha256(embedding_paths(name)[0]),
                "metadata_sha256": sha256(embedding_paths(name)[1]),
            }
            for name in MODELS
        },
    }
    (OUT / "representation_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "embed", "evaluate", "all"], nargs="?", default="all")
    parser.add_argument("--model", choices=MODELS)
    args = parser.parse_args()
    if args.stage in {"prepare", "all"}:
        prepare()
    if args.stage == "embed":
        if not args.model:
            parser.error("--model is required for the embed stage")
        embed(args.model)
    elif args.stage == "all":
        for model_name in MODELS:
            embed(model_name)
        evaluate()
    elif args.stage == "evaluate":
        evaluate()


if __name__ == "__main__":
    main()
