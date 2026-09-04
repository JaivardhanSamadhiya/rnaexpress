"""Run frozen, checkpointable M3 cell, reporter, and source transfers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_finalshot_direct_models import aggregate_score
from src.analysis.run_finalshot_direct_transfers import transfer_masks
from src.analysis.run_finalshot_m3 import (
    GROUP_FRACTIONS,
    HEAD_FORMS,
    PENALTIES,
    SEEDS,
    choose_m3_recipe,
)
from src.modeling.finalshot_models import (
    FinalShotFeatureStore,
    finalshot_assay_heads,
    fit_latent_heads,
)
from src.modeling.v4_decision_models import source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
CACHE = ROOT / "data" / "interim" / "finalshot_m3_transfer_cache"
OUT = ROOT / "results" / "finalshot" / "transfers_m3"
IMPLEMENTATION = "2026-09-04-v1"
TASKS = (
    "CAD_to_N2A",
    "N2A_to_CAD",
    "Firefly_to_GFP",
    "GFP_to_Firefly",
    "leave_Mikl",
    "leave_TDP",
    "leave_Moffatt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def token(penalty: float, eta: float, head_form: str, seed: int) -> str:
    return f"l{penalty:g}_e{eta:g}_{head_form}_s{seed}"


def cache_path(task: str, inner_fold: int | None, penalty: float, eta: float,
               head_form: str, seed: int) -> Path:
    stage = "refit" if inner_fold is None else f"inner{inner_fold}"
    return CACHE / task / f"{stage}_{token(penalty, eta, head_form, seed)}.npz"


def atomic_npz(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def valid_cache(path: Path, expected: dict[str, object]) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata_json"].item()))
            prediction = archive["latent_prediction"]
        return (
            all(metadata.get(key) == value for key, value in expected.items())
            and np.isfinite(prediction).all()
        )
    except Exception:
        return False


def task_data(task: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    rows = pd.read_csv(ROWS)
    train_mask, test_mask = transfer_masks(rows, task)
    train_indices = np.flatnonzero(train_mask)
    test_indices = np.flatnonzero(test_mask)
    if not len(train_indices) or not len(test_indices):
        raise RuntimeError(f"Empty transfer partition for {task}")
    train_sets = set(rows.iloc[train_indices]["decision_set_id"].astype(str))
    test_sets = set(rows.iloc[test_indices]["decision_set_id"].astype(str))
    if train_sets & test_sets:
        raise RuntimeError(f"Transfer split divides a decision set for {task}")
    return rows, train_indices, test_indices


def expected_metadata(task: str, stage: str, penalty: float, eta: float,
                      head_form: str, seed: int, rows_hash: str,
                      inner_fold: int | None = None) -> dict[str, object]:
    metadata: dict[str, object] = {
        "implementation": IMPLEMENTATION,
        "task": task,
        "stage": stage,
        "penalty": penalty,
        "group_fraction": eta,
        "head_form": head_form,
        "seed": seed,
        "rows_sha256": rows_hash,
    }
    if inner_fold is not None:
        metadata["inner_fold"] = inner_fold
    return metadata


def fit_inner_grid(task: str) -> None:
    rows, train_indices, _ = task_data(task)
    train_rows = rows.iloc[train_indices].reset_index(drop=True)
    train_folds = train_rows["biological_fold"].to_numpy(int)
    raw_target = train_rows["localization_effect"].to_numpy(np.float32)
    heads, head_names = finalshot_assay_heads(train_rows)
    store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
    features, layout = store.materialize(train_indices, "M2")
    rows_hash = sha256(ROWS)
    unique_folds = sorted(set(train_folds))
    total = len(unique_folds) * len(PENALTIES) * len(GROUP_FRACTIONS) * len(HEAD_FORMS) * len(SEEDS)
    completed = 0
    for inner_fold in unique_folds:
        validation = train_folds == inner_fold
        training = ~validation
        fit_rows = train_rows.loc[training].reset_index(drop=True)
        validation_rows = train_rows.loc[validation].reset_index(drop=True)
        if set(fit_rows["biological_unit"]) & set(validation_rows["biological_unit"]):
            raise RuntimeError("M3 transfer inner biological-unit leakage")
        for penalty in PENALTIES:
            for eta in GROUP_FRACTIONS:
                for head_form in HEAD_FORMS:
                    for seed in SEEDS:
                        path = cache_path(task, int(inner_fold), penalty, eta, head_form, seed)
                        expected = expected_metadata(
                            task, "inner", penalty, eta, head_form, seed, rows_hash, int(inner_fold)
                        )
                        if valid_cache(path, expected):
                            completed += 1
                            continue
                        started = time.time()
                        model = fit_latent_heads(
                            features[training],
                            raw_target[training],
                            source_set_weights(fit_rows),
                            heads[training],
                            head_names,
                            layout,
                            penalty,
                            eta,
                            head_form,
                            seed,
                        )
                        metadata = {
                            **expected,
                            "train_rows": int(training.sum()),
                            "validation_rows": int(validation.sum()),
                            "unit_overlap": 0,
                            "epochs": model.epochs,
                            "stopped_early": model.stopped_early,
                            "best_objective": model.best_objective,
                            "selected_groups_at_1e-8": int((model.group_norms > 1e-8).sum()),
                            "elapsed_seconds": time.time() - started,
                            "training_outcomes_used_for_fitting": True,
                            "target_test_outcomes_used_for_fitting": False,
                            "nzip_outcomes_accessed": False,
                            "astrocyte_data_accessed": False,
                        }
                        atomic_npz(
                            path,
                            validation_indices=train_indices[validation].astype(np.int32),
                            latent_prediction=np.asarray(
                                model.latent_score(features[validation]), dtype=np.float32
                            ),
                            metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                        )
                        completed += 1
                        print(
                            f"M3 transfer={task} inner={inner_fold} "
                            f"{token(penalty, eta, head_form, seed)} epochs={model.epochs} "
                            f"seconds={metadata['elapsed_seconds']:.1f} ({completed}/{total})",
                            flush=True,
                        )


def load_recipe_predictions(rows: pd.DataFrame, task: str, train_indices: np.ndarray,
                            penalty: float, eta: float, head_form: str) -> tuple[np.ndarray, list[dict[str, object]]]:
    train_rows = rows.iloc[train_indices].reset_index(drop=True)
    folds = train_rows["biological_fold"].to_numpy(int)
    position = {int(value): index for index, value in enumerate(train_indices)}
    seed_predictions = []
    audits: list[dict[str, object]] = []
    for seed in SEEDS:
        prediction = np.full(len(train_indices), np.nan, dtype=np.float32)
        for inner_fold in sorted(set(folds)):
            path = cache_path(task, int(inner_fold), penalty, eta, head_form, seed)
            with np.load(path, allow_pickle=False) as archive:
                indices = archive["validation_indices"].astype(int)
                values = archive["latent_prediction"].astype(np.float32)
                audits.append(json.loads(str(archive["metadata_json"].item())))
            prediction[[position[int(index)] for index in indices]] = values
        if not np.isfinite(prediction).all():
            raise RuntimeError(f"Incomplete M3 transfer inner prediction for {task}/{seed}")
        seed_predictions.append(prediction)
    return np.mean(seed_predictions, axis=0), audits


def finalize(task: str) -> None:
    rows, train_indices, test_indices = task_data(task)
    train_rows = rows.iloc[train_indices].reset_index(drop=True)
    grid = []
    for penalty in PENALTIES:
        for eta in GROUP_FRACTIONS:
            for head_form in HEAD_FORMS:
                prediction, audits = load_recipe_predictions(
                    rows, task, train_indices, penalty, eta, head_form
                )
                grid.append({
                    "penalty": penalty,
                    "group_fraction": eta,
                    "head_form": head_form,
                    **aggregate_score(train_rows, prediction, f"M3_{penalty}_{eta}_{head_form}"),
                    "seed_fit_audits": audits,
                })
    selected = choose_m3_recipe(grid)
    penalty = float(selected["penalty"])
    eta = float(selected["group_fraction"])
    head_form = str(selected["head_form"])
    store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
    train_features, layout = store.materialize(train_indices, "M2")
    test_features, _ = store.materialize(test_indices, "M2")
    train_heads, head_names = finalshot_assay_heads(train_rows)
    rows_hash = sha256(ROWS)
    seed_latent = []
    seed_metadata = []
    for seed in SEEDS:
        path = cache_path(task, None, penalty, eta, head_form, seed)
        expected = expected_metadata(
            task, "transfer_refit", penalty, eta, head_form, seed, rows_hash
        )
        if not valid_cache(path, expected):
            started = time.time()
            model = fit_latent_heads(
                train_features,
                train_rows["localization_effect"].to_numpy(np.float32),
                source_set_weights(train_rows),
                train_heads,
                head_names,
                layout,
                penalty,
                eta,
                head_form,
                seed,
            )
            metadata = {
                **expected,
                "train_rows": len(train_indices),
                "test_rows": len(test_indices),
                "train_sources": sorted(train_rows["dataset"].unique()),
                "test_sources": sorted(rows.iloc[test_indices]["dataset"].unique()),
                "train_test_unit_overlap": len(
                    set(train_rows["biological_unit"])
                    & set(rows.iloc[test_indices]["biological_unit"])
                ),
                "epochs": model.epochs,
                "stopped_early": model.stopped_early,
                "best_objective": model.best_objective,
                "selected_groups_at_1e-8": int((model.group_norms > 1e-8).sum()),
                "elapsed_seconds": time.time() - started,
                "training_outcomes_used_for_fitting": True,
                "target_test_outcomes_used_for_fitting": False,
                "nzip_outcomes_accessed": False,
                "astrocyte_data_accessed": False,
            }
            atomic_npz(
                path,
                test_indices=test_indices.astype(np.int32),
                latent_prediction=np.asarray(model.latent_score(test_features), dtype=np.float32),
                coefficient=model.coefficient,
                scaler_mean=model.scaler.mean,
                scaler_scale=model.scaler.scale,
                group_norms=model.group_norms,
                head_intercepts=model.head_intercepts,
                head_slopes=model.head_slopes,
                knots=model.knots,
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
            )
        with np.load(path, allow_pickle=False) as archive:
            seed_latent.append(archive["latent_prediction"].astype(np.float32))
            seed_metadata.append(json.loads(str(archive["metadata_json"].item())))
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / f"{task}_M3.npz"
    metadata = {
        "phase": "FinalShot transfer M3",
        "task": task,
        "selected_penalty": penalty,
        "selected_group_fraction": eta,
        "selected_head_form": head_form,
        "inner_grid": grid,
        "seed_refits": seed_metadata,
        "training_outcomes_used_for_fitting": True,
        "target_test_outcomes_used_for_fitting": False,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    atomic_npz(
        destination,
        test_indices=test_indices.astype(np.int32),
        prediction=np.mean(seed_latent, axis=0).astype(np.float32),
        seed_predictions=np.stack(seed_latent),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    print(json.dumps({
        "task": task,
        "selected_penalty": penalty,
        "selected_group_fraction": eta,
        "selected_head_form": head_form,
    }, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("inner-grid", "finalize"), required=True)
    parser.add_argument("--task", choices=TASKS, required=True)
    args = parser.parse_args()
    if args.stage == "inner-grid":
        fit_inner_grid(args.task)
    else:
        finalize(args.task)


if __name__ == "__main__":
    main()
