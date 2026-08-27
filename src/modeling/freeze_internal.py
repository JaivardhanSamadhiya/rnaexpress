"""Freeze all predictions for the three locked N-zip parents without labels."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from .development_benchmark import ALL_METHODS, FIXED_PARAMETERS, predict_method
from .features import compact_intervention_features
from .models import FeatureStore, fit_mikl_model, train_pairwise_model


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
MIKL = ROOT / "data/processed/mikl_motif_replacement_pairs.csv.gz"
SPLIT = ROOT / "data/manifests/nzip_parent_split.csv"
DEV_PREDICTIONS = ROOT / "results/internal/development_predictions.csv.gz"
OUT_DIR = ROOT / "results/internal"
OUT_PREDICTIONS = OUT_DIR / "frozen_locked_predictions.csv.gz"
OUT_MODEL = OUT_DIR / "final_pairwise_rank_model.joblib"
OUT_MANIFEST = OUT_DIR / "internal_freeze_manifest.json"
OUT_REPORT = ROOT / "reports/internal_freeze.md"
OUTCOME_COLUMNS = [
    "parent_localization_log2_neurite_soma",
    "mutant_localization_log2_neurite_soma",
    "delta_localization",
]
FEATURE_COLUMNS = [
    "dataset",
    "source_row",
    "parent_id",
    "gene_id",
    "gene_name",
    "source_tile_id",
    "parent_sequence",
    "edit_position_0based",
    "edit_position_1based",
    "reference_nt",
    "alternate_nt",
    "mutant_sequence",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def development_labels(dev_ids: set[str]) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    columns = ["source_row", "parent_id", *OUTCOME_COLUMNS]
    for chunk in pd.read_csv(NZIP, usecols=columns, chunksize=500):
        permitted = chunk[chunk["parent_id"].isin(dev_ids)].copy()
        if not permitted.empty:
            parts.append(permitted)
    labels = pd.concat(parts, ignore_index=True)
    if set(labels["parent_id"]) != dev_ids:
        raise AssertionError("Development labels do not match frozen parent split")
    return labels


def deterministic_random_score(frame: pd.DataFrame) -> np.ndarray:
    values = []
    for row in frame.itertuples(index=False):
        key = (
            f"20260826|{row.parent_id}|{row.edit_position_0based}|"
            f"{row.reference_nt}|{row.alternate_nt}"
        )
        values.append(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16) / 2**64)
    return np.asarray(values)


def main() -> None:
    split = pd.read_csv(SPLIT)
    dev_ids = set(split.loc[split["role"] == "development", "parent_id"])
    lock_ids = set(split.loc[split["role"] == "locked_internal_test", "parent_id"])

    # Read candidate identity for every row without any outcome columns. Outcome
    # columns are separately streamed and retained only for permitted dev parents.
    candidates = pd.read_csv(NZIP, usecols=FEATURE_COLUMNS)
    labels = development_labels(dev_ids)
    frame = candidates.merge(labels, on=["source_row", "parent_id"], how="left", validate="one_to_one")
    dev_indices = frame.index[frame["parent_id"].isin(dev_ids)].to_numpy(int)
    lock_indices = frame.index[frame["parent_id"].isin(lock_ids)].to_numpy(int)
    if len(dev_indices) != 3540 or len(lock_indices) != 855:
        raise AssertionError("Frozen N-zip row counts changed")
    if frame.iloc[lock_indices][OUTCOME_COLUMNS].notna().any().any():
        raise AssertionError("Locked outcomes entered the freeze frame")

    store = FeatureStore.build(frame)
    mikl = pd.read_csv(MIKL)
    mikl_model = fit_mikl_model(mikl)
    mikl_prior = mikl_model.predict(store.compact)
    mikl_x = compact_intervention_features(mikl)
    mikl_y = (
        mikl["delta_cad_localization"].to_numpy(float)
        + mikl["delta_neuro2a_localization"].to_numpy(float)
    ) / 2.0

    output = frame.iloc[lock_indices][FEATURE_COLUMNS].copy()
    pairwise_model = train_pairwise_model(dev_indices, store, c_value=1.0)
    pairwise_margin = pairwise_model.decision_function(store.intervention10[lock_indices])

    cross_fitted = pd.read_csv(DEV_PREDICTIONS, usecols=["pred_pairwise_rank", "delta_localization"])
    calibrator = IsotonicRegression(out_of_bounds="clip", increasing=True)
    calibrator.fit(
        cross_fitted["pred_pairwise_rank"].to_numpy(float),
        cross_fitted["delta_localization"].to_numpy(float),
    )
    development_calibrated = calibrator.predict(
        cross_fitted["pred_pairwise_rank"].to_numpy(float)
    )
    residual_rmse = float(
        np.sqrt(
            np.mean(
                (
                    development_calibrated
                    - cross_fitted["delta_localization"].to_numpy(float)
                )
                ** 2
            )
        )
    )

    for method in ALL_METHODS:
        params = FIXED_PARAMETERS.get(method, {})
        if method == "pairwise_rank":
            prediction = calibrator.predict(pairwise_margin)
            output["pairwise_margin"] = pairwise_margin
        else:
            prediction = predict_method(
                method,
                dev_indices,
                lock_indices,
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
        output[f"rank_increase_{method}"] = (
            output.groupby("parent_id")[f"pred_{method}"].rank(
                method="first", ascending=False
            )
        ).astype(int)
        output[f"rank_decrease_{method}"] = (
            output.groupby("parent_id")[f"pred_{method}"].rank(
                method="first", ascending=True
            )
        ).astype(int)
    output["pred_random"] = deterministic_random_score(output)
    output["prediction_uncertainty_log2"] = residual_rmse
    output["target_score_increase"] = output["pred_pairwise_rank"]
    output["target_score_decrease"] = -output["pred_pairwise_rank"]
    if any(column in output for column in OUTCOME_COLUMNS):
        raise AssertionError("An outcome column entered frozen predictions")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output.sort_values(
        ["parent_id", "edit_position_0based", "alternate_nt"]
    ).to_csv(OUT_PREDICTIONS, index=False, compression="gzip")
    model_artifact = {
        "model_name": "pairwise_rank",
        "seed": 20260826,
        "features": "intervention10",
        "pairwise_model": pairwise_model,
        "isotonic_calibrator": calibrator,
        "development_calibration_rmse": residual_rmse,
        "training_parent_ids": sorted(dev_ids),
        "locked_parent_ids": sorted(lock_ids),
    }
    joblib.dump(model_artifact, OUT_MODEL, compress=3)

    code_commit = subprocess.check_output(
        ["git", "-c", "safe.directory=D:/rnaexpress", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    code_files = [
        ROOT / "src/modeling/features.py",
        ROOT / "src/modeling/models.py",
        ROOT / "src/modeling/metrics.py",
        ROOT / "src/modeling/freeze_internal.py",
    ]
    manifest = {
        "frozen_role": "locked internal N-zip evaluation",
        "code_commit": code_commit,
        "selected_model": "pairwise_rank",
        "training_parents": 12,
        "training_snvs": 3540,
        "locked_parents": 3,
        "locked_candidates": 855,
        "locked_outcomes_accessed": False,
        "astrocyte_outcomes_accessed": False,
        "seed": 20260826,
        "hyperparameters": FIXED_PARAMETERS,
        "binary_threshold_log2": 0.6758642587586807,
        "model_sha256": sha256(OUT_MODEL),
        "predictions_sha256": sha256(OUT_PREDICTIONS),
        "code_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in code_files},
        "calibration": {
            "method": "isotonic on 12-parent cross-fitted development predictions",
            "rmse_log2": residual_rmse,
            "ranking_unchanged_by_monotonic_calibration": True,
        },
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    OUT_REPORT.write_text(
        "# Locked internal freeze\n\n"
        f"Code commit: `{code_commit}`.\n\n"
        "The selected method is pairwise ranking over explicit parent/edit features. "
        "It was trained on 3,540 SNVs from 12 development parents using C=1 and "
        "300 deterministic training pairs per parent. Raw margins are monotonically "
        "calibrated to localization-effect units using only cross-fitted development "
        f"predictions (RMSE {residual_rmse:.3f} log2).\n\n"
        "All twelve baselines/ablations were fit on the same development parents. "
        "The frozen file contains 855 candidates from Cdc42_2, Cflar_1 and Ndufa2 "
        "with increase/decrease ranks and no measured outcomes.\n\n"
        f"Model SHA256: `{manifest['model_sha256']}`.\n\n"
        f"Prediction SHA256: `{manifest['predictions_sha256']}`.\n\n"
        "Locked N-zip outcomes and all astrocyte outcomes were not accessed by this pipeline.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
