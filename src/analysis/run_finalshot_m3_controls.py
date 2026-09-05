"""Run frozen, checkpointed M3 mechanism-breaking controls."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_finalshot_direct_models import aggregate_score, sha256
from src.analysis.run_finalshot_m3 import (
    GROUP_FRACTIONS,
    HEAD_FORMS,
    PENALTIES,
    SEEDS,
    atomic_npz,
    choose_m3_recipe,
    token,
    valid_cache,
)
from src.modeling.finalshot_controls import CONTROL_NAMES, FinalShotControlledFeatureStore
from src.modeling.finalshot_models import finalshot_assay_heads, fit_latent_heads
from src.modeling.v4_decision_models import source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
CACHE = ROOT / "data" / "interim" / "finalshot_m3_control_cache"
OUT = ROOT / "results" / "finalshot" / "nested_controls_m3"
IMPLEMENTATION = "2026-09-05-v1"


def cache_path(control: str, outer_fold: int, inner_fold: int | None, penalty: float,
               eta: float, head_form: str, seed: int) -> Path:
    stage = "refit" if inner_fold is None else f"inner{inner_fold}"
    return CACHE / control / f"outer{outer_fold}" / f"{stage}_{token(penalty, eta, head_form, seed)}.npz"


def output_path(control: str, outer_fold: int) -> Path:
    return OUT / control / f"M3_outer_fold_{outer_fold}.npz"


def expected(control: str, stage: str, outer_fold: int, penalty: float, eta: float,
             head_form: str, seed: int, rows_hash: str,
             inner_fold: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "implementation": IMPLEMENTATION,
        "control": control,
        "stage": stage,
        "outer_fold": outer_fold,
        "penalty": penalty,
        "group_fraction": eta,
        "head_form": head_form,
        "seed": seed,
        "rows_sha256": rows_hash,
    }
    if inner_fold is not None:
        result["inner_fold"] = inner_fold
    return result


def control_data(control: str) -> tuple[pd.DataFrame, FinalShotControlledFeatureStore, np.ndarray]:
    rows = pd.read_csv(ROWS)
    store = FinalShotControlledFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION, control)
    eligible_indices = np.flatnonzero(store.eligible_mask)
    return rows, store, eligible_indices


def fit_inner_grid(control: str, outer_fold: int) -> None:
    rows, store, eligible_indices = control_data(control)
    control_rows = rows.iloc[eligible_indices].reset_index(drop=True)
    folds = control_rows["biological_fold"].to_numpy(int)
    outer_positions = np.flatnonzero(folds != outer_fold)
    outer_indices = eligible_indices[outer_positions]
    outer_rows = control_rows.iloc[outer_positions].reset_index(drop=True)
    outer_folds = folds[outer_positions]
    raw_target = outer_rows["localization_effect"].to_numpy(np.float32)
    heads, head_names = finalshot_assay_heads(outer_rows)
    features, layout = store.materialize(outer_indices, "M2")
    rows_hash = sha256(ROWS)
    completed = 0
    total = len(set(outer_folds)) * len(PENALTIES) * len(GROUP_FRACTIONS) * len(HEAD_FORMS) * len(SEEDS)
    for inner_fold in sorted(set(outer_folds)):
        validation = outer_folds == inner_fold
        training = ~validation
        fit_rows = outer_rows.loc[training].reset_index(drop=True)
        validation_rows = outer_rows.loc[validation].reset_index(drop=True)
        if set(fit_rows["biological_unit"]) & set(validation_rows["biological_unit"]):
            raise RuntimeError("M3 control inner biological-unit leakage")
        for penalty in PENALTIES:
            for eta in GROUP_FRACTIONS:
                for head_form in HEAD_FORMS:
                    for seed in SEEDS:
                        path = cache_path(control, outer_fold, int(inner_fold), penalty, eta, head_form, seed)
                        metadata_expected = expected(
                            control, "inner", outer_fold, penalty, eta, head_form, seed,
                            rows_hash, int(inner_fold),
                        )
                        if valid_cache(path, metadata_expected):
                            completed += 1
                            continue
                        started = time.time()
                        model = fit_latent_heads(
                            features[training], raw_target[training], source_set_weights(fit_rows),
                            heads[training], head_names, layout, penalty, eta, head_form, seed,
                        )
                        metadata = {
                            **metadata_expected,
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
                            latent_prediction=np.asarray(model.latent_score(features[validation]), dtype=np.float32),
                            metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                        )
                        completed += 1
                        print(
                            f"M3 control={control} outer={outer_fold} inner={inner_fold} "
                            f"{token(penalty, eta, head_form, seed)} ({completed}/{total})",
                            flush=True,
                        )


def load_recipe(control: str, rows: pd.DataFrame, eligible_indices: np.ndarray,
                outer_fold: int, penalty: float, eta: float,
                head_form: str) -> tuple[np.ndarray, list[dict[str, object]]]:
    control_rows = rows.iloc[eligible_indices].reset_index(drop=True)
    folds = control_rows["biological_fold"].to_numpy(int)
    outer_positions = np.flatnonzero(folds != outer_fold)
    outer_indices = eligible_indices[outer_positions]
    position = {int(value): index for index, value in enumerate(outer_indices)}
    seed_predictions = []
    audits = []
    for seed in SEEDS:
        prediction = np.full(len(outer_indices), np.nan, dtype=np.float32)
        for inner_fold in sorted(set(folds[outer_positions])):
            path = cache_path(control, outer_fold, int(inner_fold), penalty, eta, head_form, seed)
            with np.load(path, allow_pickle=False) as archive:
                indices = archive["validation_indices"].astype(int)
                values = archive["latent_prediction"].astype(np.float32)
                audits.append(json.loads(str(archive["metadata_json"].item())))
            prediction[[position[int(index)] for index in indices]] = values
        if not np.isfinite(prediction).all():
            raise RuntimeError("Incomplete M3 control inner predictions")
        seed_predictions.append(prediction)
    return np.mean(seed_predictions, axis=0), audits


def finalize(control: str, outer_fold: int) -> None:
    rows, store, eligible_indices = control_data(control)
    control_rows = rows.iloc[eligible_indices].reset_index(drop=True)
    folds = control_rows["biological_fold"].to_numpy(int)
    outer_positions = np.flatnonzero(folds != outer_fold)
    test_positions = np.flatnonzero(folds == outer_fold)
    outer_indices = eligible_indices[outer_positions]
    test_indices = eligible_indices[test_positions]
    outer_rows = control_rows.iloc[outer_positions].reset_index(drop=True)
    grid = []
    for penalty in PENALTIES:
        for eta in GROUP_FRACTIONS:
            for head_form in HEAD_FORMS:
                prediction, audits = load_recipe(
                    control, rows, eligible_indices, outer_fold, penalty, eta, head_form
                )
                grid.append({
                    "penalty": penalty,
                    "group_fraction": eta,
                    "head_form": head_form,
                    **aggregate_score(outer_rows, prediction, f"{control}_M3_{penalty}_{eta}_{head_form}"),
                    "seed_fit_audits": audits,
                })
    selected = choose_m3_recipe(grid)
    penalty = float(selected["penalty"])
    eta = float(selected["group_fraction"])
    head_form = str(selected["head_form"])
    train_features, layout = store.materialize(outer_indices, "M2")
    test_features, test_layout = store.materialize(test_indices, "M2")
    if layout.feature_count != test_layout.feature_count or layout.rbp_groups != test_layout.rbp_groups:
        raise RuntimeError("M3 control train/test feature layouts differ")
    train_heads, head_names = finalshot_assay_heads(outer_rows)
    test_rows = control_rows.iloc[test_positions].reset_index(drop=True)
    test_heads, _ = finalshot_assay_heads(test_rows)
    rows_hash = sha256(ROWS)
    seed_latent = []
    seed_calibrated = []
    seed_metadata = []
    for seed in SEEDS:
        path = cache_path(control, outer_fold, None, penalty, eta, head_form, seed)
        metadata_expected = expected(
            control, "outer_refit", outer_fold, penalty, eta, head_form, seed, rows_hash
        )
        if not valid_cache(path, metadata_expected):
            started = time.time()
            model = fit_latent_heads(
                train_features,
                outer_rows["localization_effect"].to_numpy(np.float32),
                source_set_weights(outer_rows),
                train_heads,
                head_names,
                layout,
                penalty,
                eta,
                head_form,
                seed,
            )
            metadata = {
                **metadata_expected,
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
    destination = output_path(control, outer_fold)
    metadata = {
        "phase": "FinalShot M3 mechanism-breaking control",
        "control": control,
        "outer_fold": outer_fold,
        "eligible_rows": int(len(eligible_indices)),
        "excluded_rows": int(len(rows) - len(eligible_indices)),
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
        "control": control,
        "outer_fold": outer_fold,
        "selected_penalty": penalty,
        "selected_group_fraction": eta,
        "selected_head_form": head_form,
    }), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", choices=CONTROL_NAMES, required=True)
    parser.add_argument("--stage", choices=("inner-grid", "finalize"), required=True)
    parser.add_argument("--outer-fold", type=int, choices=range(5), required=True)
    args = parser.parse_args()
    if args.stage == "inner-grid":
        fit_inner_grid(args.control, args.outer_fold)
    else:
        finalize(args.control, args.outer_fold)


if __name__ == "__main__":
    main()
