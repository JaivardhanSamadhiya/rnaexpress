"""Run the frozen, checkpointable M3 nested evaluation."""

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
CACHE = ROOT / "data" / "interim" / "finalshot_m3_cache"
OUT = ROOT / "results" / "finalshot" / "nested_m3"
PENALTIES = (0.001, 0.01, 0.1)
GROUP_FRACTIONS = (0.25, 0.75)
HEAD_FORMS = ("affine", "two_knot")
SEEDS = (17, 41, 89)
IMPLEMENTATION = "2026-09-03-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def token(penalty: float, eta: float, head_form: str, seed: int) -> str:
    return f"l{penalty:g}_e{eta:g}_{head_form}_s{seed}"


def inner_path(outer_fold: int, inner_fold: int, penalty: float, eta: float,
               head_form: str, seed: int) -> Path:
    return CACHE / f"outer{outer_fold}" / f"inner{inner_fold}_{token(penalty, eta, head_form, seed)}.npz"


def outer_seed_path(outer_fold: int, penalty: float, eta: float,
                    head_form: str, seed: int) -> Path:
    return CACHE / f"outer{outer_fold}" / f"refit_{token(penalty, eta, head_form, seed)}.npz"


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
        return all(metadata.get(key) == value for key, value in expected.items()) and np.isfinite(prediction).all()
    except Exception:
        return False


def fit_inner_grid(outer_fold: int) -> None:
    rows = pd.read_csv(ROWS)
    folds = rows["biological_fold"].to_numpy(int)
    outer_indices = np.flatnonzero(folds != outer_fold)
    outer_rows = rows.iloc[outer_indices].reset_index(drop=True)
    outer_folds = folds[outer_indices]
    raw_target = outer_rows["localization_effect"].to_numpy(np.float32)
    heads, head_names = finalshot_assay_heads(outer_rows)
    store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
    features, layout = store.materialize(outer_indices, "M2")
    rows_hash = sha256(ROWS)
    completed = 0
    total = len(set(outer_folds)) * len(PENALTIES) * len(GROUP_FRACTIONS) * len(HEAD_FORMS) * len(SEEDS)
    for inner_fold in sorted(set(outer_folds)):
        validation = outer_folds == inner_fold
        training = ~validation
        train_rows = outer_rows.loc[training].reset_index(drop=True)
        validation_rows = outer_rows.loc[validation].reset_index(drop=True)
        if set(train_rows["biological_unit"]) & set(validation_rows["biological_unit"]):
            raise RuntimeError("M3 inner biological-unit leakage")
        for penalty in PENALTIES:
            for eta in GROUP_FRACTIONS:
                for head_form in HEAD_FORMS:
                    for seed in SEEDS:
                        path = inner_path(outer_fold, int(inner_fold), penalty, eta, head_form, seed)
                        expected = {
                            "implementation": IMPLEMENTATION,
                            "stage": "inner",
                            "outer_fold": outer_fold,
                            "inner_fold": int(inner_fold),
                            "penalty": penalty,
                            "group_fraction": eta,
                            "head_form": head_form,
                            "seed": seed,
                            "rows_sha256": rows_hash,
                        }
                        if valid_cache(path, expected):
                            completed += 1
                            continue
                        started = time.time()
                        model = fit_latent_heads(
                            features[training], raw_target[training], source_set_weights(train_rows),
                            heads[training], head_names, layout, penalty, eta, head_form, seed,
                        )
                        latent = np.asarray(model.latent_score(features[validation]), dtype=np.float32)
                        calibrated = np.asarray(
                            model.calibrated_prediction(features[validation], heads[validation]), dtype=np.float32
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
                            "nzip_outcomes_accessed": False,
                            "astrocyte_data_accessed": False,
                        }
                        atomic_npz(
                            path,
                            validation_indices=outer_indices[validation].astype(np.int32),
                            latent_prediction=latent,
                            calibrated_prediction=calibrated,
                            group_norms=model.group_norms,
                            metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                        )
                        completed += 1
                        print(
                            f"M3 outer={outer_fold} inner={inner_fold} {token(penalty, eta, head_form, seed)} "
                            f"epochs={model.epochs} seconds={metadata['elapsed_seconds']:.1f} ({completed}/{total})",
                            flush=True,
                        )


def load_inner_recipe(rows: pd.DataFrame, outer_fold: int, penalty: float, eta: float,
                      head_form: str) -> tuple[np.ndarray, list[dict[str, object]]]:
    folds = rows["biological_fold"].to_numpy(int)
    outer_indices = np.flatnonzero(folds != outer_fold)
    position = {int(value): index for index, value in enumerate(outer_indices)}
    seed_predictions = []
    records = []
    for seed in SEEDS:
        prediction = np.full(len(outer_indices), np.nan, dtype=np.float32)
        for inner_fold in sorted(set(folds[outer_indices])):
            path = inner_path(outer_fold, int(inner_fold), penalty, eta, head_form, seed)
            with np.load(path, allow_pickle=False) as archive:
                indices = archive["validation_indices"].astype(int)
                values = archive["latent_prediction"].astype(np.float32)
                metadata = json.loads(str(archive["metadata_json"].item()))
            prediction[[position[int(index)] for index in indices]] = values
            records.append(metadata)
        if not np.isfinite(prediction).all():
            raise RuntimeError(f"Incomplete M3 inner prediction for {token(penalty, eta, head_form, seed)}")
        seed_predictions.append(prediction)
    return np.mean(seed_predictions, axis=0), records


def choose_m3_recipe(grid: list[dict[str, object]]) -> dict[str, object]:
    best_regret = min(float(row["normalized_regret"]) for row in grid)
    tied = [row for row in grid if float(row["normalized_regret"]) <= best_regret + 0.002]
    return max(
        tied,
        key=lambda row: (
            float(row["directional_rank_percentile"]),
            float(row["good_selection_at_3"]),
            1 if row["head_form"] == "affine" else 0,
            float(row["penalty"]),
            float(row["group_fraction"]),
        ),
    )


def finalize_outer(outer_fold: int) -> None:
    rows = pd.read_csv(ROWS)
    folds = rows["biological_fold"].to_numpy(int)
    outer_indices = np.flatnonzero(folds != outer_fold)
    test_indices = np.flatnonzero(folds == outer_fold)
    outer_rows = rows.iloc[outer_indices].reset_index(drop=True)
    grid = []
    for penalty in PENALTIES:
        for eta in GROUP_FRACTIONS:
            for head_form in HEAD_FORMS:
                prediction, audits = load_inner_recipe(rows, outer_fold, penalty, eta, head_form)
                score = aggregate_score(outer_rows, prediction, f"M3_{penalty}_{eta}_{head_form}")
                grid.append({
                    "penalty": penalty,
                    "group_fraction": eta,
                    "head_form": head_form,
                    **score,
                    "seed_fit_audits": audits,
                })
    selected = choose_m3_recipe(grid)
    penalty = float(selected["penalty"])
    eta = float(selected["group_fraction"])
    head_form = str(selected["head_form"])
    store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
    train_features, layout = store.materialize(outer_indices, "M2")
    test_features, _ = store.materialize(test_indices, "M2")
    train_heads, head_names = finalshot_assay_heads(outer_rows)
    test_heads, _ = finalshot_assay_heads(rows.iloc[test_indices].reset_index(drop=True))
    seed_latent = []
    seed_calibrated = []
    seed_metadata = []
    for seed in SEEDS:
        path = outer_seed_path(outer_fold, penalty, eta, head_form, seed)
        expected = {
            "implementation": IMPLEMENTATION,
            "stage": "outer_refit",
            "outer_fold": outer_fold,
            "penalty": penalty,
            "group_fraction": eta,
            "head_form": head_form,
            "seed": seed,
            "rows_sha256": sha256(ROWS),
        }
        if not valid_cache(path, expected):
            started = time.time()
            model = fit_latent_heads(
                train_features,
                outer_rows["localization_effect"].to_numpy(np.float32),
                source_set_weights(outer_rows), train_heads, head_names, layout,
                penalty, eta, head_form, seed,
            )
            metadata = {
                **expected,
                "train_rows": len(outer_indices),
                "test_rows": len(test_indices),
                "unit_overlap": 0,
                "epochs": model.epochs,
                "stopped_early": model.stopped_early,
                "best_objective": model.best_objective,
                "selected_groups_at_1e-8": int((model.group_norms > 1e-8).sum()),
                "elapsed_seconds": time.time() - started,
                "nzip_outcomes_accessed": False,
                "astrocyte_data_accessed": False,
            }
            atomic_npz(
                path,
                test_indices=test_indices.astype(np.int32),
                latent_prediction=np.asarray(model.latent_score(test_features), dtype=np.float32),
                calibrated_prediction=np.asarray(
                    model.calibrated_prediction(test_features, test_heads), dtype=np.float32
                ),
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
            seed_calibrated.append(archive["calibrated_prediction"].astype(np.float32))
            seed_metadata.append(json.loads(str(archive["metadata_json"].item())))
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / f"M3_outer_fold_{outer_fold}.npz"
    metadata = {
        "phase": "FinalShot nested M3",
        "outer_fold": outer_fold,
        "selected_penalty": penalty,
        "selected_group_fraction": eta,
        "selected_head_form": head_form,
        "inner_grid": grid,
        "seed_refits": seed_metadata,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    atomic_npz(
        destination,
        test_indices=test_indices.astype(np.int32),
        prediction=np.mean(seed_latent, axis=0).astype(np.float32),
        seed_predictions=np.stack(seed_latent),
        calibrated_prediction=np.mean(seed_calibrated, axis=0).astype(np.float32),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    print(json.dumps({
        "outer_fold": outer_fold,
        "selected_penalty": penalty,
        "selected_group_fraction": eta,
        "selected_head_form": head_form,
    }, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("inner-grid", "finalize"), required=True)
    parser.add_argument("--outer-fold", type=int, choices=range(5), required=True)
    args = parser.parse_args()
    if args.stage == "inner-grid":
        fit_inner_grid(args.outer_fold)
    else:
        finalize_outer(args.outer_fold)


if __name__ == "__main__":
    main()
