"""Reconstruct and freeze the external Mikl 4-mer XGBoost classifiers."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBClassifier

from src.analysis.audit_v2_4_external_forward import MIKL, NZIP, base_gene, sha256
from src.modeling.fourmer_features import FOURMER_ORDER, fourmer_counts


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = ROOT / "data" / "frozen" / "v2_5_mikl_xgboost_source_manifest.json"
OUT_DIR = ROOT / "results" / "v2_5_external"
OUT_CV = OUT_DIR / "mikl_xgboost_grouped_cv.csv"
NEURITE_MODEL = ROOT / "data" / "frozen" / "v2_5_mikl_neurite_xgboost.json"
SOMA_MODEL = ROOT / "data" / "frozen" / "v2_5_mikl_soma_xgboost.json"
MODEL_MANIFEST = ROOT / "data" / "frozen" / "v2_5_mikl_xgboost_heads.json"
SEED = 20260826


def cohort_fingerprint(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for row in frame[["source_row", "gene", "sequence", "neurite", "soma"]].itertuples(
        index=False
    ):
        digest.update(
            f"{row.source_row}\t{row.gene}\t{row.sequence}\t{int(row.neurite)}\t{int(row.soma)}\n".encode()
        )
    return digest.hexdigest()


def load_cohort() -> pd.DataFrame:
    excluded = {
        base_gene(value)
        for value in pd.read_csv(NZIP, usecols=["gene_name"])["gene_name"].unique()
    }
    frame = pd.read_csv(MIKL).reset_index(names="source_row")
    frame["sequence"] = frame[
        "full library sequence (primers-barcode-test sequence)"
    ].str.slice(30, 180)
    frame = frame[
        frame["number of reads - CAD"].gt(500)
        & frame["number of reads - Neuro-2a"].gt(500)
        & ~frame["gene name"].map(base_gene).isin(excluded)
    ].sort_values("source_row", kind="stable")
    frame = frame.drop_duplicates("sequence", keep="first").copy()
    frame["gene"] = frame["gene name"].astype(str)
    frame["neurite"] = (
        frame["logFC(neurite/soma) - CAD"].gt(0)
        & frame["p-value logFC(neurite/soma) - CAD"].lt(0.05)
        & frame["logFC(neurite/soma) - Neuro-2a"].gt(0)
        & frame["p-value logFC(neurite/soma) - Neuro-2a"].lt(0.05)
    )
    frame["soma"] = (
        frame["logFC(neurite/soma) - CAD"].lt(0)
        & frame["p-value logFC(neurite/soma) - CAD"].lt(0.05)
        & frame["logFC(neurite/soma) - Neuro-2a"].lt(0)
        & frame["p-value logFC(neurite/soma) - Neuro-2a"].lt(0.05)
    )
    frame = frame.reset_index(drop=True)
    if (
        len(frame) != 35_428
        or frame["gene"].nunique() != 304
        or int(frame["neurite"].sum()) != 679
        or int(frame["soma"].sum()) != 177
        or not frame["sequence"].str.len().eq(150).all()
    ):
        raise ValueError("Frozen v2.5 Mikl cohort changed")
    return frame


def classifier(parameters: dict[str, float | int], positive_weight: float) -> XGBClassifier:
    return XGBClassifier(
        objective="binary:logistic",
        eval_metric="auc",
        tree_method="hist",
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=1.0,
        reg_lambda=1.0,
        reg_alpha=0.0,
        gamma=0.0,
        random_state=SEED,
        n_jobs=4,
        scale_pos_weight=positive_weight,
        max_depth=int(parameters["max_depth"]),
        min_child_weight=float(parameters["min_child_weight"]),
        learning_rate=float(parameters["learning_rate"]),
    )


def positive_weight(target: np.ndarray) -> float:
    positives = int(target.sum())
    negatives = len(target) - positives
    if positives == 0:
        raise ValueError("External classifier training fold has no positives")
    return negatives / positives


def main() -> None:
    if not SOURCE_MANIFEST.exists():
        raise FileNotFoundError("Frozen v2.5 source manifest is missing")
    frame = load_cohort()
    features = fourmer_counts(frame["sequence"].tolist())
    targets = {
        "neurite": frame["neurite"].to_numpy(np.int8),
        "soma": frame["soma"].to_numpy(np.int8),
    }
    groups = frame["gene"].to_numpy()
    splits = list(GroupKFold(n_splits=5).split(features, groups=groups))
    grid = [
        {
            "max_depth": depth,
            "min_child_weight": child,
            "learning_rate": rate,
        }
        for depth, child, rate in itertools.product((3, 6), (1, 10), (0.03, 0.1))
    ]
    result_rows: list[dict[str, float | int]] = []
    for parameters in grid:
        predictions = {
            label: np.full(len(frame), np.nan, dtype=float) for label in targets
        }
        for fold, (train, test) in enumerate(splits, start=1):
            for label, target in targets.items():
                model = classifier(parameters, positive_weight(target[train]))
                model.fit(features[train], target[train])
                predictions[label][test] = model.predict_proba(features[test])[:, 1]
            print(
                "completed external XGBoost "
                f"depth={parameters['max_depth']} child={parameters['min_child_weight']} "
                f"rate={parameters['learning_rate']} fold={fold}/5",
                flush=True,
            )
        if any(not np.isfinite(values).all() for values in predictions.values()):
            raise ValueError("Incomplete v2.5 external cross-validation predictions")
        neurite_auc = roc_auc_score(targets["neurite"], predictions["neurite"])
        soma_auc = roc_auc_score(targets["soma"], predictions["soma"])
        result_rows.append(
            {
                **parameters,
                "neurite_auc": float(neurite_auc),
                "soma_auc": float(soma_auc),
                "mean_auc": float((neurite_auc + soma_auc) / 2.0),
            }
        )
        print(
            f"external XGBoost result {parameters}: "
            f"neurite={neurite_auc:.6f} soma={soma_auc:.6f} "
            f"mean={(neurite_auc + soma_auc) / 2.0:.6f}",
            flush=True,
        )

    results = pd.DataFrame(result_rows)
    selected = sorted(
        result_rows,
        key=lambda row: (
            -float(row["mean_auc"]),
            int(row["max_depth"]),
            -float(row["min_child_weight"]),
            float(row["learning_rate"]),
        ),
    )[0]
    parameters = {
        key: selected[key] for key in ("max_depth", "min_child_weight", "learning_rate")
    }
    final_models: dict[str, XGBClassifier] = {}
    for label, target in targets.items():
        final_models[label] = classifier(parameters, positive_weight(target))
        final_models[label].fit(features, target)
    NEURITE_MODEL.parent.mkdir(parents=True, exist_ok=True)
    final_models["neurite"].save_model(NEURITE_MODEL)
    final_models["soma"].save_model(SOMA_MODEL)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_CV, index=False)
    manifest = {
        "purpose": "External-only Mikl 4-mer XGBoost heads frozen before v2.5 N-zip definition or fit.",
        "locks": "N-zip outcomes, TDP-43 locked outcomes and astrocyte outcomes were not read.",
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "source_row_fingerprint_sha256": cohort_fingerprint(frame),
        "rows": len(frame),
        "genes": int(frame["gene"].nunique()),
        "class_counts": {
            label: {"positive": int(target.sum()), "negative": int(len(target) - target.sum())}
            for label, target in targets.items()
        },
        "fourmer_order": list(FOURMER_ORDER),
        "selected": selected,
        "cv_results_sha256": sha256(OUT_CV),
        "neurite_model_sha256": sha256(NEURITE_MODEL),
        "soma_model_sha256": sha256(SOMA_MODEL),
        "xgboost_version": __import__("xgboost").__version__,
    }
    MODEL_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
