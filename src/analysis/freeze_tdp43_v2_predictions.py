"""Freeze outcome-blind TDP-43 lock predictions after the v2.6 gate pass.

This module must not read the locked outcome artifact. It consumes only the
permitted 12-gene development table and the outcome-free four-gene lock table.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from src.modeling.v2_structure import build_structure_augmented_features

# ViennaRNA must load before scikit-learn/LightGBM on Windows because their
# bundled native runtimes otherwise collide during DLL initialization.
from scipy.stats import rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.modeling.features import normalize_sequence
from src.modeling.mikl_xgboost_heads import predict_frozen_heads
from src.modeling.splicebert_features import build_splicebert_paired_delta_features
from src.modeling.v2_features import (
    _motif_features,
    absolute_sequence_features,
    build_v2_features,
)
import lightgbm as lgb


ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "data" / "processed" / "tdp43_v2_development_pairs.csv.gz"
LOCK = ROOT / "data" / "frozen" / "tdp43_v2_locked_features.csv.gz"
LOCK_MANIFEST = ROOT / "data" / "frozen" / "tdp43_v2_lock_manifest.json"
OUTCOME = ROOT / "data" / "frozen" / "outcomes" / "tdp43_v2_locked_outcomes.csv.gz"
OUT_DIR = ROOT / "results" / "v2_tdp43_lock"
CONTEXT_CACHE = ROOT / "data" / "interim" / "tdp43_v2_splicebert_features.npy"
CONTEXT_ROWS = ROOT / "data" / "interim" / "tdp43_v2_splicebert_rows.csv.gz"
STRUCTURE_CACHE = ROOT / "data" / "interim" / "tdp43_v2_structure_cache.json"
PREDICTIONS = OUT_DIR / "tdp43_v2_frozen_predictions.csv.gz"
CUSTOM_MODEL = OUT_DIR / "tdp43_v2_custom_stack.npz"
FORWARD_MODEL = OUT_DIR / "tdp43_v2_forward_lightgbm.txt"
HEURISTIC_MODEL = OUT_DIR / "tdp43_v2_motif_accessibility_ridge.npz"
ENVIRONMENT = OUT_DIR / "environment_pip_freeze.txt"
MANIFEST = OUT_DIR / "tdp43_v2_prediction_freeze_manifest.json"
SEED = 20260826
CONTEXT_DIM = 2_638
META_DIM = 21
HEURISTIC_DIM = 22


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_key(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[
        ["gene_id", "parent_id", "mutant_id", "source_figure4e_row"]
    ].astype(str)


def grouped_percentile_targets(frame: pd.DataFrame) -> np.ndarray:
    targets = np.empty(len(frame), dtype=float)
    for _, indices in frame.groupby("gene_id", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        values = frame.iloc[indices]["delta_localization"].to_numpy(float)
        targets[indices] = (rankdata(values, method="average") - 1.0) / max(
            1.0, len(values) - 1.0
        )
    return targets


def generalized_metadata(frame: pd.DataFrame) -> np.ndarray:
    bases = "ACGT"
    output = np.zeros((len(frame), 18), dtype=np.float64)
    for row_number, row in enumerate(frame.itertuples(index=False)):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        changed = [i for i, pair in enumerate(zip(parent, mutant)) if pair[0] != pair[1]]
        if len(parent) != len(mutant) or not changed:
            raise ValueError("TDP-43 metadata requires a length-preserving intervention")
        for position in changed:
            output[row_number, bases.index(parent[position]) * 4 + bases.index(mutant[position])] += 1.0
        output[row_number, :16] /= len(changed)
        output[row_number, 16] = float(np.mean(changed)) / max(1, len(parent) - 1)
        output[row_number, 17] = len(parent) / 100.0
    return output


def mikl_deltas(frame: pd.DataFrame) -> np.ndarray:
    sequences = sorted(
        set(frame["parent_sequence"].astype(str))
        | set(frame["mutant_sequence"].astype(str))
    )
    prediction = predict_frozen_heads(sequences)
    lookup = {sequence: index for index, sequence in enumerate(sequences)}
    parent = frame["parent_sequence"].map(lookup).to_numpy(int)
    mutant = frame["mutant_sequence"].map(lookup).to_numpy(int)
    delta = prediction[mutant] - prediction[parent]
    if delta.shape != (len(frame), 2) or not np.isfinite(delta).all():
        raise ValueError("Frozen Mikl probability deltas are invalid")
    return delta


def load_context(frame: pd.DataFrame) -> np.ndarray:
    expected_rows = row_key(frame)
    if CONTEXT_CACHE.exists() and CONTEXT_ROWS.exists():
        cached_rows = pd.read_csv(CONTEXT_ROWS, dtype=str)
        features = np.load(CONTEXT_CACHE)
        if cached_rows.equals(expected_rows.reset_index(drop=True)) and features.shape == (
            len(frame),
            CONTEXT_DIM,
        ):
            print(f"loaded cached TDP-43 SpliceBERT features {features.shape}", flush=True)
            return features
        raise ValueError("Stale TDP-43 SpliceBERT cache")
    features = build_splicebert_paired_delta_features(frame)
    if features.shape != (len(frame), CONTEXT_DIM):
        raise ValueError(f"Frozen contextual feature shape changed: {features.shape}")
    CONTEXT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(CONTEXT_CACHE, features, allow_pickle=False)
    expected_rows.to_csv(CONTEXT_ROWS, index=False, compression="gzip")
    return features


def fit_ridge(features: np.ndarray, targets: np.ndarray, alpha: float):
    scaler = StandardScaler().fit(features)
    model = Ridge(
        alpha=alpha,
        fit_intercept=True,
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    ).fit(scaler.transform(features), targets)
    return scaler, model


def fit_custom(
    development: pd.DataFrame,
    locked: pd.DataFrame,
    development_context: np.ndarray,
    locked_context: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    targets = grouped_percentile_targets(development)
    genes = development["gene_id"].to_numpy(str)
    crossfit = np.full(len(development), np.nan, dtype=float)
    for fold, gene in enumerate(sorted(development["gene_id"].unique()), start=1):
        test = np.flatnonzero(genes == gene)
        train = np.flatnonzero(genes != gene)
        scaler, model = fit_ridge(
            development_context[train], targets[train], float(CONTEXT_DIM)
        )
        crossfit[test] = model.predict(scaler.transform(development_context[test]))
        print(f"cross-fitted contextual TDP-43 gene {fold}/12: {gene}", flush=True)
    if not np.isfinite(crossfit).all():
        raise ValueError("TDP-43 contextual cross-fit is incomplete")

    context_scaler, context_model = fit_ridge(
        development_context, targets, float(CONTEXT_DIM)
    )
    locked_context_score = context_model.predict(
        context_scaler.transform(locked_context)
    )
    combined = pd.concat([development, locked], ignore_index=True)
    low = np.column_stack([generalized_metadata(combined), mikl_deltas(combined)])
    if low.shape != (len(combined), 20):
        raise ValueError(f"Frozen low-dimensional shape changed: {low.shape}")
    train_features = np.column_stack([low[: len(development)], crossfit])
    locked_features = np.column_stack([low[len(development) :], locked_context_score])
    meta_scaler, meta_model = fit_ridge(train_features, targets, float(META_DIM))
    predictions = meta_model.predict(meta_scaler.transform(locked_features))
    parameters = {
        "context_mean": context_scaler.mean_,
        "context_scale": context_scaler.scale_,
        "context_coef": context_model.coef_,
        "context_intercept": np.asarray([context_model.intercept_]),
        "meta_mean": meta_scaler.mean_,
        "meta_scale": meta_scaler.scale_,
        "meta_coef": meta_model.coef_,
        "meta_intercept": np.asarray([meta_model.intercept_]),
    }
    return predictions, parameters


def fit_forward(development: pd.DataFrame, locked: pd.DataFrame):
    train_sequences = pd.concat(
        [development["mutant_sequence"], development["parent_sequence"]],
        ignore_index=True,
    )
    target = np.concatenate(
        [
            development["mutant_localization_log2_neurite_soma"].to_numpy(float),
            development["parent_localization_log2_neurite_soma"].to_numpy(float),
        ]
    )
    model = lgb.LGBMRegressor(
        objective="regression_l2",
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=30,
        reg_lambda=1.0,
        colsample_bytree=0.7,
        random_state=SEED,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(absolute_sequence_features(train_sequences), target)
    prediction = model.predict(absolute_sequence_features(locked["mutant_sequence"]))
    prediction -= model.predict(absolute_sequence_features(locked["parent_sequence"]))
    return prediction, model


def motif_accessibility_features(frame: pd.DataFrame) -> np.ndarray:
    base = build_v2_features(frame)
    augmented = build_structure_augmented_features(frame, base, STRUCTURE_CACHE, radius=10)
    motif = np.vstack(
        [
            _motif_features(normalize_sequence(row.mutant_sequence))
            - _motif_features(normalize_sequence(row.parent_sequence))
            for row in frame.itertuples(index=False)
        ]
    )
    structure = augmented.edit[:, -10:]
    output = np.column_stack([motif, structure]).astype(np.float64)
    if output.shape != (len(frame), HEURISTIC_DIM):
        raise ValueError(f"Frozen motif/accessibility shape changed: {output.shape}")
    return output


def save_npz(path: Path, parameters: dict[str, np.ndarray]) -> None:
    np.savez_compressed(path, **parameters)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = json.loads(LOCK_MANIFEST.read_text())
    if file_sha256(DEV) != frozen["artifacts"]["development"]["sha256"]:
        raise ValueError("TDP-43 development artifact hash changed")
    if file_sha256(LOCK) != frozen["artifacts"]["locked_features"]["sha256"]:
        raise ValueError("TDP-43 locked-feature artifact hash changed")
    development = pd.read_csv(DEV)
    locked = pd.read_csv(LOCK)
    if len(development) != 3_560 or development["gene_id"].nunique() != 12:
        raise ValueError("TDP-43 development boundary changed")
    if len(locked) != 1_006 or locked["gene_id"].nunique() != 4:
        raise ValueError("TDP-43 lock boundary changed")
    prohibited = {
        "parent_localization_log2_neurite_soma",
        "mutant_localization_log2_neurite_soma",
        "delta_localization",
    }
    if prohibited & set(locked.columns):
        raise ValueError("Locked feature table unexpectedly contains outcomes")

    combined = pd.concat(
        [development.drop(columns=sorted(prohibited)), locked], ignore_index=True
    )
    context = load_context(combined)
    custom_prediction, custom_parameters = fit_custom(
        development,
        locked,
        context[: len(development)],
        context[len(development) :],
    )
    forward_prediction, forward_model = fit_forward(development, locked)
    heuristic_features = motif_accessibility_features(
        pd.concat([development, locked], ignore_index=True)
    )
    heuristic_scaler, heuristic_model = fit_ridge(
        heuristic_features[: len(development)],
        grouped_percentile_targets(development),
        float(HEURISTIC_DIM),
    )
    heuristic_prediction = heuristic_model.predict(
        heuristic_scaler.transform(heuristic_features[len(development) :])
    )

    predictions = locked.copy()
    predictions["pred_nested_context_external_stack"] = custom_prediction
    predictions["pred_forward_lightgbm"] = forward_prediction
    predictions["pred_motif_accessibility_ridge"] = heuristic_prediction
    if len(predictions) != 1_006 or not np.isfinite(
        predictions.filter(like="pred_").to_numpy(float)
    ).all():
        raise ValueError("Frozen lock predictions are incomplete or non-finite")
    predictions.to_csv(PREDICTIONS, index=False, compression="gzip")
    save_npz(CUSTOM_MODEL, custom_parameters)
    forward_model.booster_.save_model(str(FORWARD_MODEL))
    save_npz(
        HEURISTIC_MODEL,
        {
            "mean": heuristic_scaler.mean_,
            "scale": heuristic_scaler.scale_,
            "coef": heuristic_model.coef_,
            "intercept": np.asarray([heuristic_model.intercept_]),
        },
    )
    ENVIRONMENT.write_text(
        subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"], text=True
        )
    )
    source_files = [
        ROOT / "src" / "analysis" / "freeze_tdp43_v2_predictions.py",
        ROOT / "src" / "modeling" / "splicebert_features.py",
        ROOT / "src" / "modeling" / "v2_features.py",
        ROOT / "src" / "modeling" / "v2_structure.py",
        ROOT / "src" / "modeling" / "mikl_xgboost_heads.py",
    ]
    artifacts = [
        PREDICTIONS,
        CUSTOM_MODEL,
        FORWARD_MODEL,
        HEURISTIC_MODEL,
        ENVIRONMENT,
        CONTEXT_CACHE,
        CONTEXT_ROWS,
        STRUCTURE_CACHE,
    ]
    manifest = {
        "freeze_date": "2026-08-27",
        "locked_outcomes_read": False,
        "locked_outcome_path_prohibited": str(OUTCOME.relative_to(ROOT)),
        "selected_custom": "nested_context_external_stack",
        "comparators": ["forward_lightgbm", "motif_accessibility_ridge"],
        "seed": SEED,
        "development_rows": len(development),
        "development_genes": int(development["gene_id"].nunique()),
        "locked_rows": len(locked),
        "locked_genes": int(locked["gene_id"].nunique()),
        "context_dim": CONTEXT_DIM,
        "meta_dim": META_DIM,
        "heuristic_dim": HEURISTIC_DIM,
        "development_sha256": file_sha256(DEV),
        "locked_features_sha256": file_sha256(LOCK),
        "locked_outcomes_expected_sha256_unread": frozen["artifacts"]["locked_outcomes"]["sha256"],
        "prefreeze_git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {
            str(path.relative_to(ROOT)): file_sha256(path) for path in source_files
        },
        "artifact_sha256": {
            str(path.relative_to(ROOT)): file_sha256(path) for path in artifacts
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
