"""Run the prespecified RNAddress v3 contextual representation benchmark."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn

from src.modeling.features import normalize_sequence
from src.modeling.utrbert_features import build_utrbert_delta_features, sha256_bytes
from src.modeling.v3_nested import (
    directional_metrics,
    macro_metrics,
    nested_extreme,
    nested_ridge,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2/nzip_development_predictions.csv.gz"
SPLICE_FEATURES = ROOT / "data/interim/splicebert_v2_2_features.npy"
SPLICE_ROWS = ROOT / "data/interim/splicebert_v2_2_source_rows.npy"
UTR_FEATURES = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
UTR_ROWS = ROOT / "data/interim/v3_3utrbert_source_rows.npy"
UTR_PAIR_HASHES = ROOT / "data/interim/v3_3utrbert_pair_sequence_hashes.npy"
UTR_ABSOLUTE = ROOT / "data/interim/v3_3utrbert_absolute_features.npy"
UTR_ABSOLUTE_HASHES = ROOT / "data/interim/v3_3utrbert_absolute_sequence_hashes.npy"
UTR_ABSOLUTE_SEQUENCES = ROOT / "data/interim/v3_3utrbert_absolute_sequences.npy"
OUT_DIR = ROOT / "results/v3_phase3"
OUT_PREDICTIONS = OUT_DIR / "representation_outer_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "representation_parent_direction_metrics.csv"
OUT_COMPARISON = OUT_DIR / "representation_comparison.csv"
OUT_TUNING = OUT_DIR / "representation_inner_selections.csv"
OUT_SELECTION = OUT_DIR / "representation_selection.json"
OUT_MANIFEST = OUT_DIR / "representation_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pair_hashes(frame: pd.DataFrame) -> np.ndarray:
    return np.asarray(
        [
            [
                sha256_bytes(normalize_sequence(row.parent_sequence)),
                sha256_bytes(normalize_sequence(row.mutant_sequence)),
            ]
            for row in frame.itertuples(index=False)
        ],
        dtype="U64",
    )


def load_splicebert(frame: pd.DataFrame) -> np.ndarray:
    features = np.load(SPLICE_FEATURES)
    rows = np.load(SPLICE_ROWS)
    if features.shape != (len(frame), 2_638):
        raise ValueError(f"Unexpected SpliceBERT feature shape: {features.shape}")
    if not np.array_equal(rows, frame["source_row"].to_numpy(np.int64)):
        raise ValueError("SpliceBERT cache rows do not match N-zip")
    return features


def load_utrbert(frame: pd.DataFrame) -> np.ndarray:
    expected_rows = frame["source_row"].to_numpy(np.int64)
    expected_hashes = _pair_hashes(frame)
    cache_paths = [
        UTR_FEATURES,
        UTR_ROWS,
        UTR_PAIR_HASHES,
        UTR_ABSOLUTE,
        UTR_ABSOLUTE_HASHES,
        UTR_ABSOLUTE_SEQUENCES,
    ]
    if all(path.exists() for path in cache_paths):
        features = np.load(UTR_FEATURES)
        rows = np.load(UTR_ROWS)
        pair_hashes = np.load(UTR_PAIR_HASHES)
        if (
            features.shape == (len(frame), 3_662)
            and np.array_equal(rows, expected_rows)
            and np.array_equal(pair_hashes, expected_hashes)
        ):
            print(f"loaded cached 3UTRBERT features {features.shape}", flush=True)
            return features
        raise ValueError("Stale 3UTRBERT cache does not match N-zip rows and sequence hashes")

    features, hashes, sequences, absolute = build_utrbert_delta_features(frame)
    if features.shape != (len(frame), 3_662):
        raise ValueError(f"Unexpected 3UTRBERT feature shape: {features.shape}")
    UTR_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    np.save(UTR_FEATURES, features, allow_pickle=False)
    np.save(UTR_ROWS, expected_rows, allow_pickle=False)
    np.save(UTR_PAIR_HASHES, expected_hashes, allow_pickle=False)
    np.save(UTR_ABSOLUTE, absolute, allow_pickle=False)
    np.save(UTR_ABSOLUTE_HASHES, hashes, allow_pickle=False)
    np.save(UTR_ABSOLUTE_SEQUENCES, sequences, allow_pickle=False)
    return features


def _macro_row(
    representation: str,
    rank_metrics: pd.DataFrame,
    magnitude_metrics: pd.DataFrame,
    extreme_metrics: pd.DataFrame,
) -> dict[str, object]:
    rank = macro_metrics(rank_metrics)
    magnitude = macro_metrics(magnitude_metrics)
    extreme = macro_metrics(extreme_metrics)
    score = (
        0.45 * rank["rank_percentile"]
        + 0.35 * (1.0 - magnitude["normalized_regret"])
        + 0.20 * extreme["oracle_top5"]
    )
    row: dict[str, object] = {
        "representation": representation,
        "representation_selection_score": score,
    }
    row.update({f"rank_{key}": value for key, value in rank.items()})
    row.update({f"magnitude_{key}": value for key, value in magnitude.items()})
    row.update({f"extreme_{key}": value for key, value in extreme.items()})
    return row


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(SOURCE)
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("N-zip Phase 3 candidate set changed")
    if frame[["source_row", "parent_id"]].duplicated().any():
        raise ValueError("N-zip source identities are not unique")

    representations = {
        "splicebert_1024nt": load_splicebert(frame),
        "3utrbert_3mer": load_utrbert(frame),
    }
    prediction_table = frame[
        ["source_row", "parent_id", "gene_name", "delta_localization"]
    ].copy()
    all_metrics = []
    all_tuning = []
    comparison = []

    for representation, features in representations.items():
        print(f"starting matched benchmark: {representation} {features.shape}", flush=True)
        rank = nested_ridge(frame, features, "rank")
        magnitude = nested_ridge(frame, features, "magnitude")
        extreme_increase, extreme_decrease, extreme_tuning = nested_extreme(frame, features)

        prediction_table[f"pred_{representation}_rank"] = rank.prediction
        prediction_table[f"pred_{representation}_magnitude"] = magnitude.prediction
        prediction_table[f"pred_{representation}_extreme_increase"] = extreme_increase
        prediction_table[f"pred_{representation}_extreme_decrease"] = extreme_decrease

        metrics_by_target = {
            "rank": directional_metrics(
                frame, rank.prediction, model=f"{representation}_rank"
            ),
            "magnitude": directional_metrics(
                frame, magnitude.prediction, model=f"{representation}_magnitude"
            ),
            "extreme": directional_metrics(
                frame,
                extreme_increase,
                extreme_decrease,
                model=f"{representation}_extreme",
            ),
        }
        for target, metrics in metrics_by_target.items():
            metrics.insert(0, "representation", representation)
            metrics.insert(1, "target", target)
            all_metrics.append(metrics)
        tuning = pd.concat([rank.tuning, magnitude.tuning, extreme_tuning], ignore_index=True)
        tuning.insert(0, "representation", representation)
        all_tuning.append(tuning)
        comparison.append(
            _macro_row(
                representation,
                metrics_by_target["rank"],
                metrics_by_target["magnitude"],
                metrics_by_target["extreme"],
            )
        )

    comparison_frame = pd.DataFrame(comparison).sort_values(
        "representation_selection_score", ascending=False
    )
    best = comparison_frame.iloc[0]
    runner_up = comparison_frame.iloc[1]
    if (
        best["representation"] != "splicebert_1024nt"
        and float(best["representation_selection_score"])
        - float(runner_up["representation_selection_score"])
        < 0.002
    ):
        selected = "splicebert_1024nt"
        reason = "score difference below 0.002 tie margin; protocol prefers established smaller SpliceBERT"
    else:
        selected = str(best["representation"])
        reason = "highest prespecified representation selection score"

    prediction_table.to_csv(
        OUT_PREDICTIONS,
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    pd.concat(all_metrics, ignore_index=True).to_csv(OUT_METRICS, index=False)
    pd.concat(all_tuning, ignore_index=True).to_csv(OUT_TUNING, index=False)
    comparison_frame.to_csv(OUT_COMPARISON, index=False)
    selection = {
        "selected_representation": selected,
        "selection_reason": reason,
        "tie_margin": 0.002,
        "candidate_count": 2,
        "hydrarna_excluded_without_performance_test": True,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    OUT_SELECTION.write_text(json.dumps(selection, indent=2) + "\n")
    output_paths = [OUT_PREDICTIONS, OUT_METRICS, OUT_TUNING, OUT_COMPARISON, OUT_SELECTION]
    manifest = {
        "phase": "v3_phase3_representation_benchmark",
        "nzip_rows": len(frame),
        "nzip_parents": int(frame["parent_id"].nunique()),
        "source_sha256": sha256(SOURCE),
        "feature_cache_hashes": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [
                SPLICE_FEATURES,
                SPLICE_ROWS,
                UTR_FEATURES,
                UTR_ROWS,
                UTR_PAIR_HASHES,
                UTR_ABSOLUTE,
                UTR_ABSOLUTE_HASHES,
                UTR_ABSOLUTE_SEQUENCES,
            ]
        },
        "output_hashes": {
            path.name: sha256(path) for path in output_paths
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "selection": selection,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(comparison_frame.to_string(index=False), flush=True)
    print(json.dumps(selection, indent=2), flush=True)


if __name__ == "__main__":
    main()
