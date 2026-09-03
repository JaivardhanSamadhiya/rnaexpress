"""Run the frozen matched-head FinalShot representation comparison.

This is the first FinalShot script authorized to read certified localization
outcomes.  It is restricted to v4 model rows and never references N-zip or
Astrocyte paths.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_decision_models import decision_set_metrics, geometry_features, source_set_weights


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
RBP_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
RBP_MANIFEST = ROOT / "results" / "finalshot" / "rbp_feature_matrix_manifest.json"
UTR_MATRIX = ROOT / "data" / "interim" / "v4_phaseB_3utrbert_full_features.npy"
UTR_METADATA = ROOT / "data" / "interim" / "v4_phaseB_3utrbert_full_features.json"
OUT = ROOT / "results" / "finalshot"
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latent_rank_target(frame: pd.DataFrame) -> np.ndarray:
    target = np.empty(len(frame), dtype=np.float64)
    for indices in frame.groupby("decision_set_id", sort=True).indices.values():
        idx = np.asarray(indices, dtype=int)
        values = frame.iloc[idx]["localization_effect"].to_numpy(float)
        if len(idx) < 2 or np.ptp(values) <= 0:
            raise RuntimeError("Frozen decision set is not rank eligible")
        target[idx] = (rankdata(values, method="average") - 1.0) / (len(idx) - 1.0)
    return target


def fit_predict(features: np.ndarray, frame: pd.DataFrame, target: np.ndarray) -> tuple[np.ndarray, list[dict[str, object]]]:
    predictions = np.full(len(frame), np.nan, dtype=np.float64)
    audits: list[dict[str, object]] = []
    folds = frame["biological_fold"].to_numpy(int)
    units = frame["biological_unit"].astype(str).to_numpy()
    for fold in range(5):
        test = folds == fold
        train = ~test
        overlap = set(units[train]) & set(units[test])
        if overlap:
            raise RuntimeError(f"Biological-unit leakage in fold {fold}")
        scaler = StandardScaler().fit(features[train])
        x_train = scaler.transform(features[train])
        model = Ridge(alpha=100.0, solver="lsqr", tol=1e-6)
        model.fit(x_train, target[train], sample_weight=source_set_weights(frame.loc[train]))
        predictions[test] = model.predict(scaler.transform(features[test]))
        audits.append({
            "fold": fold,
            "train_rows": int(train.sum()),
            "test_rows": int(test.sum()),
            "train_units": int(pd.Series(units[train]).nunique()),
            "test_units": int(pd.Series(units[test]).nunique()),
            "unit_overlap": 0,
            "solver": "lsqr",
            "iterations": int(np.asarray(model.n_iter_).reshape(-1)[0]),
        })
    if not np.isfinite(predictions).all():
        raise RuntimeError("Representation predictions are incomplete")
    return predictions, audits


def aggregate(set_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_columns = [
        "directional_rank_percentile", "normalized_regret", "selected_normalized_utility",
        "selected_experimental_utility", "good_selection_at_1", "good_selection_at_3",
        "good_selection_at_5", "oracle_recovered", "spearman",
    ]
    unit = (
        set_metrics.groupby(["model", "dataset", "requested_direction", "biological_unit"])
        .agg(decision_sets=("decision_set_id", "size"), **{column: (column, "mean") for column in metric_columns})
        .reset_index()
    )
    source = (
        unit.groupby(["model", "dataset", "requested_direction"])
        .agg(biological_units=("biological_unit", "size"), decision_sets=("decision_sets", "sum"),
             **{column: (column, "mean") for column in metric_columns})
        .reset_index()
    )
    return unit, source


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(ROWS)
    expected_sources = {"mikl_gse173098", "tdp43_gse288185", "moffatt_gse334718"}
    if len(rows) != 93_208 or rows["decision_set_id"].nunique() != 445 or set(rows["dataset"]) != expected_sources:
        raise RuntimeError("Frozen v4 model cohort changed")
    if rows["biological_unit"].nunique() != 213:
        raise RuntimeError("Frozen biological-unit cohort changed")
    target = latent_rank_target(rows)
    geometry = geometry_features(rows, categories=True)
    feature_rows = rows["feature_row"].to_numpy(int)

    rbp_metadata = json.loads(RBP_MANIFEST.read_text(encoding="utf-8"))
    if sha256(RBP_MATRIX) != rbp_metadata["matrix_sha256"]:
        raise RuntimeError("Assembled RBP feature matrix hash changed")
    utr_metadata = json.loads(UTR_METADATA.read_text(encoding="utf-8"))
    if sha256(UTR_MATRIX) != utr_metadata["feature_sha256"]:
        raise RuntimeError("Frozen 3UTRBERT feature matrix hash changed")

    utr = np.load(UTR_MATRIX, mmap_mode="r")
    rbp = np.load(RBP_MATRIX, mmap_mode="r")
    feature_sets = {
        "R0_geometry": geometry,
        "R1_3utrbert": np.column_stack([geometry, utr[feature_rows, :128], utr[feature_rows, 256:384]]).astype(np.float32),
        "R2_rbpnet_output": np.column_stack([geometry, rbp[feature_rows]]).astype(np.float32),
    }
    predictions: dict[str, np.ndarray] = {}
    audit_rows: list[dict[str, object]] = []
    for name, features in feature_sets.items():
        score, audits = fit_predict(features, rows, target)
        predictions[name] = score
        audit_rows.extend({"representation": name, "feature_count": features.shape[1], **audit} for audit in audits)
        print(f"completed {name} ({features.shape[1]} features)", flush=True)
        if name != "R0_geometry":
            del features

    set_records: list[pd.DataFrame] = []
    for name, score in predictions.items():
        for direction, sign in (("increase", 1), ("decrease", -1)):
            set_records.append(decision_set_metrics(rows, sign * score, name, direction, SEED, "held_biological_fold"))
    set_metrics = pd.concat(set_records, ignore_index=True)
    unit_metrics, source_metrics = aggregate(set_metrics)

    context_rows: list[dict[str, object]] = []
    base = source_metrics[source_metrics["model"] == "R0_geometry"]
    for name in ("R1_3utrbert", "R2_rbpnet_output"):
        full = source_metrics[source_metrics["model"] == name]
        paired = full.merge(base, on=["dataset", "requested_direction"], suffixes=("_full", "_geometry"), validate="one_to_one")
        for row in paired.itertuples(index=False):
            context_rows.append({
                "representation": name,
                "dataset": row.dataset,
                "requested_direction": row.requested_direction,
                "rank_context_value": row.directional_rank_percentile_full - row.directional_rank_percentile_geometry,
                "regret_context_value": row.normalized_regret_geometry - row.normalized_regret_full,
                "good3_context_value": row.good_selection_at_3_full - row.good_selection_at_3_geometry,
                "good5_context_value": row.good_selection_at_5_full - row.good_selection_at_5_geometry,
            })
    context = pd.DataFrame(context_rows)
    summary = []
    for name, group in context.groupby("representation", sort=True):
        summary.append({
            "representation": name,
            "equal_source_direction_rank_context_value": float(group["rank_context_value"].mean()),
            "equal_source_direction_regret_context_value": float(group["regret_context_value"].mean()),
            "positive_rank_tasks": int(group["rank_context_value"].gt(0).sum()),
            "positive_regret_tasks": int(group["regret_context_value"].gt(0).sum()),
            "source_direction_tasks": len(group),
        })

    prediction_frame = rows[["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold", "feature_row"]].copy()
    for name, values in predictions.items():
        prediction_frame[name] = values
    prediction_frame.to_csv(OUT / "representation_predictions.csv.gz", index=False, compression=GZIP)
    set_metrics.to_csv(OUT / "representation_set_metrics.csv.gz", index=False, compression=GZIP)
    unit_metrics.to_csv(OUT / "representation_unit_metrics.csv", index=False)
    source_metrics.to_csv(OUT / "representation_source_metrics.csv", index=False)
    context.to_csv(OUT / "representation_context_values.csv", index=False)
    pd.DataFrame(audit_rows).to_csv(OUT / "representation_fold_audit.csv", index=False)
    result = {
        "phase": "FinalShot frozen matched-head representation benchmark",
        "protocol_commit": "30c89a3",
        "rows": len(rows),
        "decision_sets": int(rows["decision_set_id"].nunique()),
        "biological_units": int(rows["biological_unit"].nunique()),
        "target": "within-training-decision-set empirical effect midrank",
        "head": "training-fold StandardScaler + weighted Ridge(alpha=100, solver=lsqr, tol=1e-6)",
        "summary": summary,
        "input_hashes": {
            ROWS.relative_to(ROOT).as_posix(): sha256(ROWS),
            RBP_MATRIX.relative_to(ROOT).as_posix(): sha256(RBP_MATRIX),
            UTR_MATRIX.relative_to(ROOT).as_posix(): sha256(UTR_MATRIX),
        },
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    (OUT / "representation_benchmark.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
