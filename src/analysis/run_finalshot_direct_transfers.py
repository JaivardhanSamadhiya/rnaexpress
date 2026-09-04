"""Run frozen M0/R1/M1/M2 cell, reporter, and source transfers."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_finalshot_direct_models import (
    GROUP_FRACTIONS,
    PENALTIES,
    aggregate_score,
    latent_rank_target,
    select_recipe,
)
from src.modeling.finalshot_models import FinalShotFeatureStore
from src.modeling.finalshot_models import fit_sparse_group
from src.modeling.v4_decision_models import geometry_features, source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"
EXPRESSION = ROOT / "results" / "finalshot" / "rbp_expression_proxy.csv"
UTR_MATRIX = ROOT / "data" / "interim" / "v4_phaseB_3utrbert_full_features.npy"
OUT = ROOT / "results" / "finalshot" / "transfers_direct"


def transfer_masks(rows: pd.DataFrame, task: str) -> tuple[np.ndarray, np.ndarray]:
    dataset = rows["dataset"].astype(str)
    cell = rows["cell_type"].astype(str)
    reporter = rows["reporter"].astype(str)
    if task == "CAD_to_N2A":
        scope = dataset.eq("mikl_gse173098")
        return (scope & cell.eq("CAD")).to_numpy(), (scope & cell.eq("Neuro-2a")).to_numpy()
    if task == "N2A_to_CAD":
        scope = dataset.eq("mikl_gse173098")
        return (scope & cell.eq("Neuro-2a")).to_numpy(), (scope & cell.eq("CAD")).to_numpy()
    if task == "Firefly_to_GFP":
        scope = dataset.eq("moffatt_gse334718")
        return (scope & reporter.eq("Firefly")).to_numpy(), (scope & reporter.eq("GFP")).to_numpy()
    if task == "GFP_to_Firefly":
        scope = dataset.eq("moffatt_gse334718")
        return (scope & reporter.eq("GFP")).to_numpy(), (scope & reporter.eq("Firefly")).to_numpy()
    held = {
        "leave_Mikl": "mikl_gse173098",
        "leave_TDP": "tdp43_gse288185",
        "leave_Moffatt": "moffatt_gse334718",
    }.get(task)
    if held is None:
        raise ValueError(f"Unknown transfer task: {task}")
    return dataset.ne(held).to_numpy(), dataset.eq(held).to_numpy()


def ridge_features(rows: pd.DataFrame, indices: np.ndarray, family: str, utr: np.ndarray) -> np.ndarray:
    geometry = geometry_features(rows.iloc[indices].reset_index(drop=True), categories=True)
    if family == "M0":
        return geometry
    feature_rows = rows.iloc[indices]["feature_row"].to_numpy(int)
    return np.column_stack([geometry, utr[feature_rows, :128], utr[feature_rows, 256:384]]).astype(np.float32)


def fit_ridge(train_x: np.ndarray, train_y: np.ndarray, train_rows: pd.DataFrame,
              test_x: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    scaler = StandardScaler().fit(train_x)
    model = Ridge(alpha=100.0, solver="lsqr", tol=1e-6)
    model.fit(scaler.transform(train_x), train_y, sample_weight=source_set_weights(train_rows))
    return np.asarray(model.predict(scaler.transform(test_x)), dtype=np.float32), {
        "alpha": 100.0, "solver": "lsqr", "iterations": int(np.asarray(model.n_iter_).reshape(-1)[0])
    }


def run(task: str, family: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / f"{task}_{family}.npz"
    if destination.exists():
        with np.load(destination, allow_pickle=False) as archive:
            test_indices = archive["test_indices"].astype(np.int32)
            prediction = archive["prediction"].astype(np.float32)
            metadata = json.loads(str(archive["metadata_json"].item()))
            if np.isfinite(prediction).all():
                if "target_test_outcomes_used_for_fitting" not in metadata:
                    metadata.pop("target_outcomes_used_for_fitting", None)
                    metadata["training_outcomes_used_for_fitting"] = True
                    metadata["target_test_outcomes_used_for_fitting"] = False
                    temporary = destination.with_suffix(".tmp.npz")
                    np.savez_compressed(
                        temporary,
                        test_indices=test_indices,
                        prediction=prediction,
                        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                    )
                    os.replace(temporary, destination)
                print(f"validated existing {destination.relative_to(ROOT)}", flush=True)
                return
    rows = pd.read_csv(ROWS)
    train_mask, test_mask = transfer_masks(rows, task)
    train_indices = np.flatnonzero(train_mask)
    test_indices = np.flatnonzero(test_mask)
    train_rows = rows.iloc[train_indices].reset_index(drop=True)
    test_rows = rows.iloc[test_indices].reset_index(drop=True)
    if not len(train_rows) or not len(test_rows):
        raise RuntimeError("Empty transfer partition")
    if set(train_rows["decision_set_id"]) & set(test_rows["decision_set_id"]):
        raise RuntimeError("Transfer split divides a decision set")
    target = latent_rank_target(train_rows)
    started = time.time()
    metadata: dict[str, object] = {
        "task": task, "family": family, "train_rows": len(train_rows), "test_rows": len(test_rows),
        "train_sources": sorted(train_rows["dataset"].unique()),
        "test_sources": sorted(test_rows["dataset"].unique()),
        "training_outcomes_used_for_fitting": True,
        "target_test_outcomes_used_for_fitting": False,
        "nzip_outcomes_accessed": False, "astrocyte_data_accessed": False,
    }
    if family in {"M0", "R1"}:
        utr = np.load(UTR_MATRIX, mmap_mode="r")
        train_x = ridge_features(rows, train_indices, family, utr)
        test_x = ridge_features(rows, test_indices, family, utr)
        prediction, recipe = fit_ridge(train_x, target, train_rows, test_x)
        metadata["recipe"] = recipe
    else:
        store = FinalShotFeatureStore(rows, RBP_MATRIX, RBP_DICTIONARY, EXPRESSION)
        train_x, layout = store.materialize(train_indices, family)
        test_x, test_layout = store.materialize(test_indices, family)
        if layout.feature_count != test_layout.feature_count or layout.rbp_groups != test_layout.rbp_groups:
            raise RuntimeError("Transfer feature layouts differ")
        fold_values = train_rows["biological_fold"].to_numpy(int)
        grid = []
        predictions = {}
        for penalty in PENALTIES:
            for eta in GROUP_FRACTIONS:
                inner_prediction = np.full(len(train_rows), np.nan, dtype=np.float32)
                audits = []
                for fold in sorted(set(fold_values)):
                    validation = fold_values == fold
                    training = ~validation
                    inner_rows = train_rows.loc[training].reset_index(drop=True)
                    model = fit_sparse_group(
                        train_x[training], target[training], source_set_weights(inner_rows),
                        layout, penalty, eta,
                    )
                    inner_prediction[validation] = model.predict(train_x[validation])
                    audits.append({"fold": int(fold), "converged": model.converged,
                                   "iterations": model.iterations, "selected_groups": int((model.group_norms > 0).sum())})
                score = aggregate_score(train_rows, inner_prediction, f"{family}_{penalty}_{eta}")
                grid.append({"family": family, "penalty": penalty, "group_fraction": eta,
                             "eligible": all(item["converged"] for item in audits), **score, "fits": audits})
                predictions[(penalty, eta)] = inner_prediction
        selected = select_recipe(grid)
        recipe = (float(selected["penalty"]), float(selected["group_fraction"]))
        model = fit_sparse_group(train_x, target, source_set_weights(train_rows), layout, *recipe)
        if not model.converged:
            raise RuntimeError("Selected transfer refit did not converge")
        prediction = np.asarray(model.predict(test_x), dtype=np.float32)
        metadata.update({
            "selected_penalty": recipe[0], "selected_group_fraction": recipe[1],
            "selected_groups": int((model.group_norms > 0).sum()), "grid": grid,
            "outer_refit_iterations": model.iterations,
        })
    metadata["elapsed_seconds"] = time.time() - started
    temporary = destination.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, test_indices=test_indices.astype(np.int32), prediction=prediction,
                        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)))
    os.replace(temporary, destination)
    print(json.dumps(metadata, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, choices=(
        "CAD_to_N2A", "N2A_to_CAD", "Firefly_to_GFP", "GFP_to_Firefly",
        "leave_Mikl", "leave_TDP", "leave_Moffatt",
    ))
    parser.add_argument("--family", required=True, choices=("M0", "R1", "M1", "M2"))
    args = parser.parse_args()
    run(args.task, args.family)


if __name__ == "__main__":
    main()
