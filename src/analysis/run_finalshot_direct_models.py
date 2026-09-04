"""Run leakage-safe, resumable nested M1/M2 FinalShot evaluations.

Each invocation evaluates one model family in one outer biological fold.  It
writes atomically only after all four inner folds, recipe selection, and the
outer refit succeed.  Running the same command again validates and skips an
existing result unless ``--force`` is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.finalshot_models import FinalShotFeatureStore, fit_sparse_group
from src.modeling.v4_decision_models import decision_set_metrics, source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
MANIFEST = ROOT / "results" / "finalshot" / "rbp_feature_matrix_manifest.json"
OUT = ROOT / "results" / "finalshot" / "nested_direct"
SEED = 42_017
PENALTIES = (0.001, 0.01, 0.1)
GROUP_FRACTIONS = (0.25, 0.75)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latent_rank_target(frame: pd.DataFrame) -> np.ndarray:
    target = np.empty(len(frame), dtype=np.float32)
    for raw_indices in frame.groupby("decision_set_id", sort=True).indices.values():
        indices = np.asarray(raw_indices, dtype=int)
        effect = frame.iloc[indices]["localization_effect"].to_numpy(float)
        if len(indices) < 2 or np.ptp(effect) <= 0:
            raise RuntimeError("Frozen decision set is not rank eligible")
        target[indices] = (rankdata(effect, method="average") - 1.0) / (len(indices) - 1.0)
    return target


def aggregate_score(frame: pd.DataFrame, prediction: np.ndarray, label: str) -> dict[str, float]:
    records = []
    for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
        records.append(
            decision_set_metrics(
                frame,
                sign * prediction,
                label,
                direction,
                SEED,
                "inner_biological_fold",
            )
        )
    sets = pd.concat(records, ignore_index=True)
    unit = (
        sets.groupby(["dataset", "requested_direction", "biological_unit"], sort=True)
        .agg(
            normalized_regret=("normalized_regret", "mean"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
        )
        .reset_index()
    )
    source = unit.groupby(["dataset", "requested_direction"], sort=True).mean(numeric_only=True)
    return {
        "normalized_regret": float(source["normalized_regret"].mean()),
        "directional_rank_percentile": float(source["directional_rank_percentile"].mean()),
        "good_selection_at_3": float(source["good_selection_at_3"].mean()),
        "decision_sets": int(len(sets)),
        "biological_units": int(unit["biological_unit"].nunique()),
    }


def select_recipe(grid: list[dict[str, object]]) -> dict[str, object]:
    eligible = [row for row in grid if bool(row["eligible"])]
    if not eligible:
        raise RuntimeError("No sparse-group candidate converged in every inner fold")
    best_regret = min(float(row["normalized_regret"]) for row in eligible)
    tied = [row for row in eligible if float(row["normalized_regret"]) <= best_regret + 0.002]
    # The regret tolerance is applied before the frozen secondary metrics;
    # stronger regularization and larger group fraction are the final ties.
    return max(
        tied,
        key=lambda row: (
            float(row["directional_rank_percentile"]),
            float(row["good_selection_at_3"]),
            float(row["penalty"]),
            float(row["group_fraction"]),
        ),
    )


def output_path(family: str, outer_fold: int) -> Path:
    return OUT / f"{family}_outer_fold_{outer_fold}.npz"


def validate_existing(path: Path, family: str, outer_fold: int, rows_hash: str) -> bool:
    if not path.exists():
        return False
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
        prediction = archive["prediction"]
        test_indices = archive["test_indices"]
    valid = (
        metadata.get("family") == family
        and metadata.get("outer_fold") == outer_fold
        and metadata.get("input_hashes", {}).get("rows") == rows_hash
        and len(prediction) == len(test_indices)
        and np.isfinite(prediction).all()
    )
    if not valid:
        raise RuntimeError(f"Existing nested result failed validation: {path}")
    return True


def run(family: str, outer_fold: int, force: bool = False) -> None:
    if family not in {"M1", "M2"} or outer_fold not in range(5):
        raise ValueError("Family must be M1/M2 and outer fold must be 0..4")
    OUT.mkdir(parents=True, exist_ok=True)
    rows_hash = sha256(ROWS)
    destination = output_path(family, outer_fold)
    if not force and validate_existing(destination, family, outer_fold, rows_hash):
        print(f"validated existing {destination.relative_to(ROOT)}", flush=True)
        return

    matrix_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(RBP_MATRIX) != matrix_manifest["matrix_sha256"]:
        raise RuntimeError("Frozen RBP matrix hash changed")
    rows = pd.read_csv(ROWS)
    if len(rows) != 93_208 or rows["biological_unit"].nunique() != 213:
        raise RuntimeError("Frozen FinalShot cohort changed")
    folds = rows["biological_fold"].to_numpy(int)
    units = rows["biological_unit"].astype(str).to_numpy()
    outer_test = folds == outer_fold
    outer_indices = np.flatnonzero(~outer_test)
    test_indices = np.flatnonzero(outer_test)
    if set(units[outer_indices]) & set(units[test_indices]):
        raise RuntimeError("Outer biological-unit leakage")

    target = latent_rank_target(rows)
    store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
    started = time.time()
    outer_features, layout = store.materialize(outer_indices, family)
    inner_folds = folds[outer_indices]
    inner_rows = rows.iloc[outer_indices].reset_index(drop=True)
    inner_target = target[outer_indices]
    grid: list[dict[str, object]] = []
    all_inner_predictions: dict[tuple[float, float], np.ndarray] = {}

    for penalty in PENALTIES:
        for group_fraction in GROUP_FRACTIONS:
            prediction = np.full(len(outer_indices), np.nan, dtype=np.float32)
            fit_audit: list[dict[str, object]] = []
            for inner_fold in sorted(set(inner_folds)):
                validation = inner_folds == inner_fold
                training = ~validation
                train_frame = inner_rows.loc[training].reset_index(drop=True)
                validation_frame = inner_rows.loc[validation].reset_index(drop=True)
                overlap = set(train_frame["biological_unit"]) & set(validation_frame["biological_unit"])
                if overlap:
                    raise RuntimeError("Inner biological-unit leakage")
                model = fit_sparse_group(
                    outer_features[training],
                    inner_target[training],
                    source_set_weights(train_frame),
                    layout,
                    penalty,
                    group_fraction,
                )
                prediction[validation] = model.predict(outer_features[validation])
                fit_audit.append(
                    {
                        "inner_fold": int(inner_fold),
                        "train_rows": int(training.sum()),
                        "validation_rows": int(validation.sum()),
                        "unit_overlap": 0,
                        "converged": bool(model.converged),
                        "iterations": int(model.iterations),
                        "objective": float(model.objective),
                        "selected_groups": int((model.group_norms > 0).sum()),
                    }
                )
                print(
                    f"{family} outer={outer_fold} lambda={penalty} eta={group_fraction} "
                    f"inner={inner_fold} converged={model.converged} iterations={model.iterations}",
                    flush=True,
                )
            complete = np.isfinite(prediction).all()
            convergence = all(bool(row["converged"]) for row in fit_audit)
            summary = aggregate_score(inner_rows, prediction, f"{family}_{penalty}_{group_fraction}")
            grid.append(
                {
                    "family": family,
                    "outer_fold": outer_fold,
                    "penalty": penalty,
                    "group_fraction": group_fraction,
                    "eligible": bool(complete and convergence),
                    **summary,
                    "fits": fit_audit,
                }
            )
            all_inner_predictions[(penalty, group_fraction)] = prediction

    selected = select_recipe(grid)
    selected_key = (float(selected["penalty"]), float(selected["group_fraction"]))
    final_model = fit_sparse_group(
        outer_features,
        inner_target,
        source_set_weights(inner_rows),
        layout,
        *selected_key,
    )
    if not final_model.converged:
        raise RuntimeError("Selected outer refit did not converge")
    test_features, test_layout = store.materialize(test_indices, family)
    if (
        test_layout.feature_count != layout.feature_count
        or test_layout.geometry != layout.geometry
        or test_layout.rbp_groups != layout.rbp_groups
        or test_layout.group_names != layout.group_names
    ):
        raise RuntimeError("Train/test feature layouts differ")
    prediction = np.asarray(final_model.predict(test_features), dtype=np.float32)
    if not np.isfinite(prediction).all():
        raise RuntimeError("Outer predictions are incomplete")

    metadata = {
        "phase": "FinalShot nested direct model",
        "family": family,
        "outer_fold": outer_fold,
        "feature_count": layout.feature_count,
        "geometry_features": layout.geometry.stop,
        "rbp_groups": len(layout.rbp_groups),
        "selected_penalty": selected_key[0],
        "selected_group_fraction": selected_key[1],
        "outer_refit_converged": final_model.converged,
        "outer_refit_iterations": final_model.iterations,
        "outer_refit_objective": final_model.objective,
        "selected_groups": int((final_model.group_norms > 0).sum()),
        "elapsed_seconds": time.time() - started,
        "grid": grid,
        "input_hashes": {
            "rows": rows_hash,
            "rbp_matrix": matrix_manifest["matrix_sha256"],
            "rbp_dictionary": sha256(RBP_DICTIONARY),
            "expression": sha256(EXPRESSION),
        },
        "python": sys.version,
        "platform": platform.platform(),
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    temporary = destination.with_suffix(".tmp.npz")
    np.savez_compressed(
        temporary,
        test_indices=test_indices.astype(np.int32),
        prediction=prediction,
        selected_inner_prediction=all_inner_predictions[selected_key],
        coefficient=final_model.coefficient,
        scaler_mean=final_model.scaler.mean,
        scaler_scale=final_model.scaler.scale,
        group_norms=final_model.group_norms,
        group_names=np.asarray(final_model.group_names, dtype="U32"),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    os.replace(temporary, destination)
    print(json.dumps({key: metadata[key] for key in (
        "family", "outer_fold", "selected_penalty", "selected_group_fraction",
        "selected_groups", "elapsed_seconds"
    )}, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=("M1", "M2"))
    parser.add_argument("--outer-fold", required=True, type=int, choices=range(5))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run(args.family, args.outer_fold, args.force)


if __name__ == "__main__":
    main()
