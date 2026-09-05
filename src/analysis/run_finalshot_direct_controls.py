"""Run checkpointed nested M1/M2 FinalShot mechanism-breaking controls."""

from __future__ import annotations

import argparse
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

from src.analysis.run_finalshot_direct_models import (
    GROUP_FRACTIONS,
    PENALTIES,
    aggregate_score,
    latent_rank_target,
    select_recipe,
    sha256,
)
from src.modeling.finalshot_controls import CONTROL_NAMES, FinalShotControlledFeatureStore
from src.modeling.finalshot_models import fit_sparse_group
from src.modeling.v4_decision_models import source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
MANIFEST = ROOT / "results" / "finalshot" / "rbp_feature_matrix_manifest.json"
OUT = ROOT / "results" / "finalshot" / "nested_controls_direct"


def output_path(control: str, family: str, outer_fold: int) -> Path:
    return OUT / control / f"{family}_outer_fold_{outer_fold}.npz"


def run(control: str, family: str, outer_fold: int) -> None:
    if control not in CONTROL_NAMES or family not in {"M1", "M2"} or outer_fold not in range(5):
        raise ValueError("Invalid frozen direct-control request")
    if control in {"cell_context_permutation", "trans_interaction_knockout"} and family != "M2":
        raise ValueError(f"{control} is defined only for M2")
    destination = output_path(control, family, outer_fold)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows_hash = sha256(ROWS)
    if destination.exists():
        with np.load(destination, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata_json"].item()))
            prediction = archive["prediction"]
        if (
            metadata.get("control") == control
            and metadata.get("family") == family
            and metadata.get("outer_fold") == outer_fold
            and metadata.get("rows_sha256") == rows_hash
            and np.isfinite(prediction).all()
        ):
            print(f"validated existing {destination.relative_to(ROOT)}", flush=True)
            return
        raise RuntimeError(f"Existing control archive failed validation: {destination}")

    matrix_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(RBP_MATRIX) != matrix_manifest["matrix_sha256"]:
        raise RuntimeError("Frozen RBP matrix hash changed")
    rows = pd.read_csv(ROWS)
    store = FinalShotControlledFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION, control)
    eligible_indices = np.flatnonzero(store.eligible_mask)
    control_rows = rows.iloc[eligible_indices].reset_index(drop=True)
    folds = control_rows["biological_fold"].to_numpy(int)
    units = control_rows["biological_unit"].astype(str).to_numpy()
    outer_test = folds == outer_fold
    train_positions = np.flatnonzero(~outer_test)
    test_positions = np.flatnonzero(outer_test)
    train_indices = eligible_indices[train_positions]
    test_indices = eligible_indices[test_positions]
    if set(units[train_positions]) & set(units[test_positions]):
        raise RuntimeError("Control outer biological-unit leakage")
    target = latent_rank_target(control_rows)
    train_target = target[train_positions]
    train_rows = control_rows.iloc[train_positions].reset_index(drop=True)
    train_folds = folds[train_positions]
    started = time.time()
    train_features, layout = store.materialize(train_indices, family)
    grid = []
    for penalty in PENALTIES:
        for eta in GROUP_FRACTIONS:
            prediction = np.full(len(train_rows), np.nan, dtype=np.float32)
            audits = []
            for inner_fold in sorted(set(train_folds)):
                validation = train_folds == inner_fold
                training = ~validation
                fit_rows = train_rows.loc[training].reset_index(drop=True)
                validation_rows = train_rows.loc[validation].reset_index(drop=True)
                if set(fit_rows["biological_unit"]) & set(validation_rows["biological_unit"]):
                    raise RuntimeError("Control inner biological-unit leakage")
                model = fit_sparse_group(
                    train_features[training],
                    train_target[training],
                    source_set_weights(fit_rows),
                    layout,
                    penalty,
                    eta,
                )
                prediction[validation] = model.predict(train_features[validation])
                audits.append({
                    "inner_fold": int(inner_fold),
                    "converged": bool(model.converged),
                    "iterations": int(model.iterations),
                    "selected_groups": int((model.group_norms > 0).sum()),
                })
                print(
                    f"control={control} family={family} outer={outer_fold} inner={inner_fold} "
                    f"lambda={penalty} eta={eta} converged={model.converged}",
                    flush=True,
                )
            grid.append({
                "family": family,
                "penalty": penalty,
                "group_fraction": eta,
                "eligible": bool(np.isfinite(prediction).all() and all(item["converged"] for item in audits)),
                **aggregate_score(train_rows, prediction, f"{control}_{family}_{penalty}_{eta}"),
                "fits": audits,
            })
    selected = select_recipe(grid)
    recipe = (float(selected["penalty"]), float(selected["group_fraction"]))
    model = fit_sparse_group(
        train_features, train_target, source_set_weights(train_rows), layout, *recipe
    )
    if not model.converged:
        raise RuntimeError("Selected control refit did not converge")
    test_features, test_layout = store.materialize(test_indices, family)
    if (
        layout.feature_count != test_layout.feature_count
        or layout.geometry != test_layout.geometry
        or layout.rbp_groups != test_layout.rbp_groups
        or layout.group_names != test_layout.group_names
    ):
        raise RuntimeError("Controlled train/test layouts differ")
    prediction = np.asarray(model.predict(test_features), dtype=np.float32)
    metadata = {
        "phase": "FinalShot direct mechanism-breaking control",
        "control": control,
        "family": family,
        "outer_fold": outer_fold,
        "eligible_rows": int(len(eligible_indices)),
        "excluded_rows": int(len(rows) - len(eligible_indices)),
        "train_rows": int(len(train_indices)),
        "test_rows": int(len(test_indices)),
        "feature_count": layout.feature_count,
        "selected_penalty": recipe[0],
        "selected_group_fraction": recipe[1],
        "selected_groups": int((model.group_norms > 0).sum()),
        "outer_refit_iterations": model.iterations,
        "grid": grid,
        "rows_sha256": rows_hash,
        "rbp_matrix_sha256": matrix_manifest["matrix_sha256"],
        "elapsed_seconds": time.time() - started,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    temporary = destination.with_suffix(".tmp.npz")
    np.savez_compressed(
        temporary,
        test_indices=test_indices.astype(np.int32),
        prediction=prediction,
        coefficient=model.coefficient,
        group_norms=model.group_norms,
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    os.replace(temporary, destination)
    print(json.dumps({
        "control": control,
        "family": family,
        "outer_fold": outer_fold,
        "selected_penalty": recipe[0],
        "selected_group_fraction": recipe[1],
    }), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", choices=CONTROL_NAMES, required=True)
    parser.add_argument("--family", choices=("M1", "M2"), required=True)
    parser.add_argument("--outer-fold", type=int, choices=range(5), required=True)
    args = parser.parse_args()
    run(args.control, args.family, args.outer_fold)


if __name__ == "__main__":
    main()
