"""Select and freeze v2.4 external localization heads without N-zip outcomes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler

from src.analysis.audit_v2_4_external_forward import (
    ARORA_ASSAYS,
    ARORA_DIR,
    ARORA_FASTA,
    MIKL,
    NZIP,
    base_gene,
    parse_fasta,
    sha256,
)
from src.modeling.splicebert_absolute import build_splicebert_absolute_features
from src.modeling.v2_features import absolute_sequence_features


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "data" / "frozen" / "v2_4_external_forward_audit.json"
INTERIM = ROOT / "data" / "interim"
OUT_DIR = ROOT / "results" / "v2_4_external"
MODEL = ROOT / "data" / "frozen" / "v2_4_external_forward_heads.npz"
MODEL_MANIFEST = ROOT / "data" / "frozen" / "v2_4_external_forward_heads.json"
ALPHAS = (1.0, 10.0, 100.0, 1000.0, 10000.0)
REPRESENTATIONS = ("mean", "cls_mean", "cls_mean_handcrafted")
MIKL_OUTCOMES = (
    "logFC(neurite/soma) - CAD",
    "logFC(neurite/soma) - Neuro-2a",
)


def fingerprint(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for row in frame[["row_id", "gene", "sequence"]].itertuples(index=False):
        digest.update(f"{row.row_id}\t{row.gene}\t{row.sequence}\n".encode())
    return digest.hexdigest()


def load_mikl() -> tuple[pd.DataFrame, list[str]]:
    parents = pd.read_csv(NZIP, usecols=["gene_name"]).drop_duplicates()
    excluded = {base_gene(value) for value in parents["gene_name"]}
    columns = [
        "gene name",
        "subset",
        "full library sequence (primers-barcode-test sequence)",
        *MIKL_OUTCOMES,
    ]
    frame = pd.read_csv(MIKL, usecols=columns).reset_index(names="source_row")
    frame = frame[
        frame["subset"].eq("wt scanning 50")
        & ~frame["gene name"].map(base_gene).isin(excluded)
    ].copy()
    frame["sequence"] = frame[
        "full library sequence (primers-barcode-test sequence)"
    ].str.slice(30, 180)
    frame = frame.dropna(subset=list(MIKL_OUTCOMES)).reset_index(drop=True)
    frame["row_id"] = frame["source_row"].map(lambda value: f"mikl:{int(value)}")
    frame["gene"] = frame["gene name"].astype(str)
    if len(frame) != 13_309 or not frame["sequence"].str.len().eq(150).all():
        raise ValueError(f"Mikl v2.4 cohort changed: {len(frame)} rows")
    return frame, list(MIKL_OUTCOMES)


def load_arora() -> tuple[pd.DataFrame, list[str]]:
    records, _ = parse_fasta(ARORA_FASTA)
    frames: list[pd.DataFrame] = []
    for filename, assay in ARORA_ASSAYS.items():
        frame = pd.read_excel(
            ARORA_DIR / filename,
            usecols=["oligoid", "genename", "neuritelog2FC"],
        ).rename(columns={"neuritelog2FC": assay})
        frames.append(frame)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=["oligoid", "genename"], validate="one_to_one")
    outcomes = list(ARORA_ASSAYS.values())
    merged[outcomes] = merged[outcomes].apply(pd.to_numeric, errors="coerce")
    merged = merged.dropna(subset=outcomes).reset_index(drop=True)
    merged["sequence"] = merged["oligoid"].map(lambda value: records[str(value)]["sequence"])
    merged["row_id"] = merged["oligoid"].map(lambda value: f"arora:{value}")
    merged["gene"] = merged["genename"].astype(str)
    if len(merged) != 7_115 or not merged["sequence"].str.len().eq(260).all():
        raise ValueError(f"Arora v2.4 cohort changed: {len(merged)} rows")
    return merged, outcomes


def percentile_targets(frame: pd.DataFrame, outcomes: list[str]) -> np.ndarray:
    targets = np.empty((len(frame), len(outcomes)), dtype=np.float64)
    for _, indices in frame.groupby("gene", sort=True).indices.items():
        indices = np.asarray(indices, dtype=int)
        for column_number, column in enumerate(outcomes):
            values = frame.iloc[indices][column].to_numpy(float)
            if len(values) == 1:
                targets[indices, column_number] = 0.0
            else:
                targets[indices, column_number] = (
                    (rankdata(values, method="average") - 1.0) / (len(values) - 1.0)
                    - 0.5
                )
    return targets


def embedding_cache(dataset: str, frame: pd.DataFrame) -> tuple[np.ndarray, str]:
    path = INTERIM / f"splicebert_v2_4_{dataset}_absolute.npy"
    manifest_path = INTERIM / f"splicebert_v2_4_{dataset}_absolute.json"
    row_hash = fingerprint(frame)
    if path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        features = np.load(path)
        if (
            manifest.get("row_fingerprint_sha256") == row_hash
            and features.shape == (len(frame), 1024)
        ):
            print(f"loaded cached {dataset} SpliceBERT features {features.shape}", flush=True)
            return features, row_hash
        raise ValueError(f"Stale {dataset} SpliceBERT cache")
    features = build_splicebert_absolute_features(
        frame["sequence"].tolist(), progress_label=f"{dataset} external sequences"
    )
    INTERIM.mkdir(parents=True, exist_ok=True)
    np.save(path, features, allow_pickle=False)
    manifest_path.write_text(
        json.dumps(
            {
                "dataset": dataset,
                "rows": len(frame),
                "row_fingerprint_sha256": row_hash,
                "feature_sha256": sha256(path),
                "shape": list(features.shape),
            },
            indent=2,
        )
        + "\n"
    )
    return features, row_hash


def representations(frame: pd.DataFrame, embedded: np.ndarray) -> dict[str, np.ndarray]:
    handcrafted = absolute_sequence_features(frame["sequence"])
    return {
        "mean": embedded[:, 512:],
        "cls_mean": embedded,
        "cls_mean_handcrafted": np.column_stack([embedded, handcrafted]).astype(np.float32),
    }


def macro_gene_spearman(
    frame: pd.DataFrame,
    targets: np.ndarray,
    predictions: np.ndarray,
    outcomes: list[str],
) -> tuple[float, dict[str, float]]:
    by_assay: dict[str, float] = {}
    for column_number, outcome in enumerate(outcomes):
        values: list[float] = []
        for _, indices in frame.groupby("gene", sort=True).indices.items():
            indices = np.asarray(indices, dtype=int)
            truth = targets[indices, column_number]
            pred = predictions[indices, column_number]
            if len(indices) < 3 or np.ptp(truth) == 0 or np.ptp(pred) == 0:
                continue
            correlation = spearmanr(truth, pred).statistic
            if np.isfinite(correlation):
                values.append(float(correlation))
        if not values:
            raise ValueError(f"No finite gene-level correlations for {outcome}")
        by_assay[outcome] = float(np.mean(values))
    return float(np.mean(list(by_assay.values()))), by_assay


def select_external_model(
    dataset: str,
    frame: pd.DataFrame,
    outcomes: list[str],
    feature_sets: dict[str, np.ndarray],
) -> tuple[pd.DataFrame, dict[str, object]]:
    targets = percentile_targets(frame, outcomes)
    groups = frame["gene"].to_numpy()
    splitter = LeaveOneGroupOut() if dataset == "arora" else GroupKFold(n_splits=5)
    split_indices = list(splitter.split(frame, groups=groups))
    result_rows: list[dict[str, object]] = []
    for representation_name in REPRESENTATIONS:
        features = feature_sets[representation_name]
        for alpha in ALPHAS:
            predictions = np.full_like(targets, np.nan)
            for fold, (train, test) in enumerate(split_indices, start=1):
                scaler = StandardScaler().fit(features[train])
                model = Ridge(
                    alpha=alpha,
                    fit_intercept=True,
                    solver="lsqr",
                    tol=1e-6,
                    max_iter=10_000,
                )
                model.fit(scaler.transform(features[train]), targets[train])
                predictions[test] = model.predict(scaler.transform(features[test]))
            if not np.isfinite(predictions).all():
                raise ValueError(f"Incomplete external CV predictions for {dataset}")
            score, assay_scores = macro_gene_spearman(frame, targets, predictions, outcomes)
            row: dict[str, object] = {
                "dataset": dataset,
                "representation": representation_name,
                "alpha": alpha,
                "dataset_macro_spearman": score,
            }
            row.update({f"spearman_{name}": value for name, value in assay_scores.items()})
            result_rows.append(row)
            print(
                f"external CV {dataset} {representation_name} alpha={alpha:g}: {score:.6f}",
                flush=True,
            )
    results = pd.DataFrame(result_rows)
    complexity = {name: index for index, name in enumerate(REPRESENTATIONS)}
    selected_row = sorted(
        result_rows,
        key=lambda row: (
            -float(row["dataset_macro_spearman"]),
            complexity[str(row["representation"])],
            -float(row["alpha"]),
        ),
    )[0]
    selected_representation = str(selected_row["representation"])
    selected_alpha = float(selected_row["alpha"])
    selected_features = feature_sets[selected_representation]
    scaler = StandardScaler().fit(selected_features)
    model = Ridge(
        alpha=selected_alpha,
        fit_intercept=True,
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    ).fit(scaler.transform(selected_features), targets)
    frozen = {
        "representation": selected_representation,
        "alpha": selected_alpha,
        "dataset_macro_spearman": float(selected_row["dataset_macro_spearman"]),
        "outcomes": outcomes,
        "mean": scaler.mean_.astype(np.float64),
        "scale": scaler.scale_.astype(np.float64),
        "coef": np.asarray(model.coef_, dtype=np.float64),
        "intercept": np.asarray(model.intercept_, dtype=np.float64),
    }
    return results, frozen


def main() -> None:
    if not AUDIT.exists():
        raise FileNotFoundError("Frozen v2.4 external audit is missing")
    mikl, mikl_outcomes = load_mikl()
    arora, arora_outcomes = load_arora()
    frames = {"mikl": mikl, "arora": arora}
    outcome_sets = {"mikl": mikl_outcomes, "arora": arora_outcomes}
    all_results: list[pd.DataFrame] = []
    frozen_models: dict[str, dict[str, object]] = {}
    row_hashes: dict[str, str] = {}
    embedding_hashes: dict[str, str] = {}
    for dataset in ("mikl", "arora"):
        frame = frames[dataset]
        embedded, row_hashes[dataset] = embedding_cache(dataset, frame)
        cache_path = INTERIM / f"splicebert_v2_4_{dataset}_absolute.npy"
        embedding_hashes[dataset] = sha256(cache_path)
        result, frozen = select_external_model(
            dataset,
            frame,
            outcome_sets[dataset],
            representations(frame, embedded),
        )
        all_results.append(result)
        frozen_models[dataset] = frozen

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = pd.concat(all_results, ignore_index=True)
    result_path = OUT_DIR / "external_grouped_cv.csv"
    results.to_csv(result_path, index=False)
    arrays: dict[str, np.ndarray] = {}
    selected: dict[str, object] = {}
    for dataset, frozen in frozen_models.items():
        for key in ("mean", "scale", "coef", "intercept"):
            arrays[f"{dataset}_{key}"] = np.asarray(frozen[key])
        selected[dataset] = {
            key: value
            for key, value in frozen.items()
            if key not in {"mean", "scale", "coef", "intercept"}
        }
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(MODEL, **arrays)
    manifest = {
        "purpose": "External-only assay heads frozen before v2.4 N-zip model definition or fit.",
        "locks": "TDP-43 locked outcomes and astrocyte outcomes were not read.",
        "protocol": "reports/v2_4_external_pretraining_protocol.md",
        "audit_sha256": sha256(AUDIT),
        "cohort_rows": {dataset: int(len(frame)) for dataset, frame in frames.items()},
        "row_fingerprint_sha256": row_hashes,
        "embedding_sha256": embedding_hashes,
        "cv_results_sha256": sha256(result_path),
        "model_npz_sha256": sha256(MODEL),
        "selected": selected,
    }
    MODEL_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
