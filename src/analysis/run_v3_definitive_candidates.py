"""Run the five frozen RNAddress v3 Phase 3 candidate architectures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.v3_mechanistic_features import build_mechanistic_features
from src.modeling.v3_nested import (
    NestedResult,
    directional_metrics,
    macro_metrics,
    nested_extreme,
    nested_magnitude,
    nested_ridge,
    selection_score,
)
from src.modeling.v3_stacking import add_extreme_head, rank_magnitude_stack


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
CONTEXT = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
MECHANISM_CACHE = ROOT / "data/interim/v3_nzip_mechanistic_features_with_stability.npy"
STRUCTURE_CACHE = ROOT / "data/interim/v3_nzip_structure_cache.json"
STABILITY = ROOT / "data/interim/v3_nzip_tdp_stability_prediction.npy"
INTERIM = ROOT / "data/interim/v3_candidate_nested"
OUT = ROOT / "results/v3_phase3"
SEED = 20260828


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_nested(name: str, result: NestedResult) -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    if result.inner_prediction is None:
        raise ValueError("Cannot cache nested result without inner predictions")
    np.savez(
        INTERIM / f"{name}.npz",
        prediction=result.prediction,
        inner_prediction=result.inner_prediction,
    )
    result.tuning.to_csv(INTERIM / f"{name}_tuning.csv", index=False, lineterminator="\n")


def _load_nested(name: str) -> NestedResult | None:
    array_path = INTERIM / f"{name}.npz"
    tuning_path = INTERIM / f"{name}_tuning.csv"
    if not array_path.exists() or not tuning_path.exists():
        return None
    arrays = np.load(array_path, allow_pickle=False)
    result = NestedResult(
        arrays["prediction"],
        pd.read_csv(tuning_path),
        arrays["inner_prediction"],
    )
    print(f"loaded cached nested result: {name}", flush=True)
    return result


def _get_nested(name: str, builder) -> NestedResult:
    cached = _load_nested(name)
    if cached is not None:
        return cached
    result = builder()
    _save_nested(name, result)
    return result


def _gzip_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )


def main() -> None:
    if not STABILITY.exists():
        raise FileNotFoundError("TDP stability auxiliary prediction must be built first")
    frame = pd.read_csv(SOURCE)
    context = np.load(CONTEXT, allow_pickle=False)
    stability = np.load(STABILITY, allow_pickle=False)
    mechanism = build_mechanistic_features(frame, STRUCTURE_CACHE, stability)
    np.save(MECHANISM_CACHE, mechanism.values, allow_pickle=False)
    complete = np.column_stack([context, mechanism.values]).astype(np.float32)
    if frame.shape[0] != 4_395 or context.shape != (4_395, 3_662):
        raise ValueError("Frozen N-zip/contextual shape changed")

    context_rank = _get_nested(
        "context_rank", lambda: nested_ridge(frame, context, "rank")
    )
    context_magnitude = _get_nested(
        "context_magnitude", lambda: nested_magnitude(frame, context, SEED)
    )
    c2 = rank_magnitude_stack(frame, context_rank, context_magnitude)

    mechanism_rank = _get_nested(
        "mechanism_rank", lambda: nested_ridge(frame, complete, "rank")
    )
    mechanism_magnitude = _get_nested(
        "mechanism_magnitude", lambda: nested_magnitude(frame, complete, SEED)
    )
    c3 = rank_magnitude_stack(frame, mechanism_rank, mechanism_magnitude)

    extreme_cache = INTERIM / "mechanism_extreme.npz"
    extreme_tuning_cache = INTERIM / "mechanism_extreme_tuning.csv"
    if extreme_cache.exists() and extreme_tuning_cache.exists():
        arrays = np.load(extreme_cache, allow_pickle=False)
        extreme_increase = arrays["increase"]
        extreme_decrease = arrays["decrease"]
        inner_extreme_increase = arrays["inner_increase"]
        inner_extreme_decrease = arrays["inner_decrease"]
        extreme_tuning = pd.read_csv(extreme_tuning_cache)
        print("loaded cached nested result: mechanism_extreme", flush=True)
    else:
        (
            extreme_increase,
            extreme_decrease,
            extreme_tuning,
            inner_extreme_increase,
            inner_extreme_decrease,
        ) = nested_extreme(frame, complete, return_inner=True)
        np.savez(
            extreme_cache,
            increase=extreme_increase,
            decrease=extreme_decrease,
            inner_increase=inner_extreme_increase,
            inner_decrease=inner_extreme_decrease,
        )
        extreme_tuning.to_csv(extreme_tuning_cache, index=False, lineterminator="\n")
    c4 = add_extreme_head(
        frame,
        c3,
        extreme_increase,
        extreme_decrease,
        inner_extreme_increase,
        inner_extreme_decrease,
    )

    scores = {
        "v2_6_historical": (
            frame["pred_nested_context_external_stack"].to_numpy(float),
            -frame["pred_nested_context_external_stack"].to_numpy(float),
        ),
        "contextual_magnitude": (
            context_magnitude.prediction,
            -context_magnitude.prediction,
        ),
        "rank_magnitude_stack": (c2.increase, c2.decrease),
        "mechanistic_rank_magnitude": (c3.increase, c3.decrease),
        "mechanistic_rank_magnitude_extreme": (c4.increase, c4.decrease),
    }
    prediction_output = frame[
        ["source_row", "parent_id", "delta_localization"]
    ].copy()
    metric_tables = []
    macro_rows = []
    for candidate, (increase, decrease) in scores.items():
        prediction_output[f"{candidate}_increase_score"] = increase
        prediction_output[f"{candidate}_decrease_score"] = decrease
        metrics = directional_metrics(frame, increase, decrease, model=candidate)
        metric_tables.append(metrics)
        macro = macro_metrics(metrics)
        macro["candidate"] = candidate
        macro["selection_score"] = selection_score(metrics)
        macro_rows.append(macro)
    metrics = pd.concat(metric_tables, ignore_index=True)
    macros = pd.DataFrame(macro_rows).sort_values(
        "selection_score", ascending=False, kind="stable"
    )
    _gzip_csv(prediction_output, OUT / "candidate_outer_predictions.csv.gz")
    metrics.to_csv(OUT / "candidate_parent_direction_metrics.csv", index=False, lineterminator="\n")
    macros.to_csv(OUT / "candidate_macro_metrics.csv", index=False, lineterminator="\n")

    tuning_tables = []
    for candidate, component, table in (
        ("contextual_magnitude", "magnitude", context_magnitude.tuning),
        ("rank_magnitude_stack", "rank", context_rank.tuning),
        ("rank_magnitude_stack", "magnitude", context_magnitude.tuning),
        ("rank_magnitude_stack", "stack", c2.tuning),
        ("mechanistic_rank_magnitude", "rank", mechanism_rank.tuning),
        ("mechanistic_rank_magnitude", "magnitude", mechanism_magnitude.tuning),
        ("mechanistic_rank_magnitude", "stack", c3.tuning),
        ("mechanistic_rank_magnitude_extreme", "extreme", extreme_tuning),
        ("mechanistic_rank_magnitude_extreme", "extreme_stack", c4.tuning),
    ):
        value = table.copy()
        value.insert(0, "component", component)
        value.insert(0, "candidate", candidate)
        tuning_tables.append(value)
    pd.concat(tuning_tables, ignore_index=True).to_csv(
        OUT / "candidate_inner_selections.csv", index=False, lineterminator="\n"
    )
    np.savez(
        INTERIM / "selected_candidate_components.npz",
        c2_inner_increase=c2.inner_increase,
        c2_inner_decrease=c2.inner_decrease,
        c3_inner_increase=c3.inner_increase,
        c3_inner_decrease=c3.inner_decrease,
        c4_inner_increase=c4.inner_increase,
        c4_inner_decrease=c4.inner_decrease,
        context_rank_outer=context_rank.prediction,
        context_magnitude_outer=context_magnitude.prediction,
        mechanism_rank_outer=mechanism_rank.prediction,
        mechanism_magnitude_outer=mechanism_magnitude.prediction,
        extreme_increase_outer=extreme_increase,
        extreme_decrease_outer=extreme_decrease,
    )
    manifest = {
        "phase": "v3_phase3_definitive_candidates",
        "seed": SEED,
        "rows": len(frame),
        "parents": int(frame["parent_id"].nunique()),
        "candidate_count": len(scores),
        "selected_representation": "3utrbert_3mer",
        "contextual_feature_count": context.shape[1],
        "mechanistic_feature_count_with_stability": mechanism.values.shape[1],
        "complete_feature_count": complete.shape[1],
        "source_sha256": sha256(SOURCE),
        "context_sha256": sha256(CONTEXT),
        "mechanism_sha256": sha256(MECHANISM_CACHE),
        "stability_prediction_sha256": sha256(STABILITY),
        "output_hashes": {
            name: sha256(OUT / name)
            for name in (
                "candidate_outer_predictions.csv.gz",
                "candidate_parent_direction_metrics.csv",
                "candidate_macro_metrics.csv",
                "candidate_inner_selections.csv",
            )
        },
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(macros.to_string(index=False))


if __name__ == "__main__":
    main()
