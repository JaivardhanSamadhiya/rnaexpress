"""Assemble completed M1/M2 outer-fold jobs and report direct-model evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_decision_models import decision_set_metrics


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
REPRESENTATION_PREDICTIONS = ROOT / "results" / "finalshot" / "representation_predictions.csv.gz"
NESTED = ROOT / "results" / "finalshot" / "nested_direct"
OUT = ROOT / "results" / "finalshot"
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}
METRICS = (
    "directional_rank_percentile",
    "normalized_regret",
    "selected_normalized_utility",
    "selected_experimental_utility",
    "good_selection_at_1",
    "good_selection_at_3",
    "good_selection_at_5",
    "oracle_recovered",
    "spearman",
)


def load_family(family: str, rows: pd.DataFrame) -> tuple[np.ndarray, list[dict[str, object]]]:
    prediction = np.full(len(rows), np.nan, dtype=np.float32)
    metadata = []
    for fold in range(5):
        path = NESTED / f"{family}_outer_fold_{fold}.npz"
        if not path.exists():
            raise FileNotFoundError(f"Missing nested result: {path}")
        with np.load(path, allow_pickle=False) as archive:
            indices = archive["test_indices"].astype(int)
            values = archive["prediction"].astype(np.float32)
            record = json.loads(str(archive["metadata_json"].item()))
        if record["family"] != family or record["outer_fold"] != fold:
            raise RuntimeError(f"Nested metadata mismatch: {path}")
        if not np.all(rows.iloc[indices]["biological_fold"].to_numpy(int) == fold):
            raise RuntimeError(f"Outer-fold indices mismatch: {path}")
        if np.isfinite(prediction[indices]).any():
            raise RuntimeError(f"Duplicate outer predictions: {path}")
        prediction[indices] = values
        metadata.append(record)
    if not np.isfinite(prediction).all():
        raise RuntimeError(f"Incomplete nested predictions for {family}")
    return prediction, metadata


def aggregate(set_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    unit = (
        set_metrics.groupby(["model", "dataset", "requested_direction", "biological_unit"], sort=True)
        .agg(decision_sets=("decision_set_id", "size"), **{key: (key, "mean") for key in METRICS})
        .reset_index()
    )
    source = (
        unit.groupby(["model", "dataset", "requested_direction"], sort=True)
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            **{key: (key, "mean") for key in METRICS},
        )
        .reset_index()
    )
    return unit, source


def inner_summary(record: dict[str, object]) -> dict[str, float]:
    for candidate in record["grid"]:
        if (
            float(candidate["penalty"]) == float(record["selected_penalty"])
            and float(candidate["group_fraction"]) == float(record["selected_group_fraction"])
        ):
            return candidate
    raise RuntimeError("Selected recipe is absent from inner grid")


def choose_direct_family(m1: dict[str, object], m2: dict[str, object]) -> str:
    candidates = [("M1", inner_summary(m1)), ("M2", inner_summary(m2))]
    best_regret = min(float(record["normalized_regret"]) for _, record in candidates)
    tied = [(name, record) for name, record in candidates
            if float(record["normalized_regret"]) <= best_regret + 0.002]
    return max(
        tied,
        key=lambda item: (
            float(item[1]["directional_rank_percentile"]),
            float(item[1]["good_selection_at_3"]),
            1 if item[0] == "M1" else 0,
        ),
    )[0]


def main() -> None:
    rows = pd.read_csv(ROWS)
    representation = pd.read_csv(REPRESENTATION_PREDICTIONS)
    identity = ["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold", "feature_row"]
    if not rows[identity].astype(str).equals(representation[identity].astype(str)):
        raise RuntimeError("Representation predictions do not align with frozen rows")
    predictions = {"M0_geometry": representation["R0_geometry"].to_numpy(float)}
    metadata: dict[str, list[dict[str, object]]] = {}
    for family in ("M1", "M2"):
        predictions[family], metadata[family] = load_family(family, rows)
    selected_family = [choose_direct_family(metadata["M1"][fold], metadata["M2"][fold]) for fold in range(5)]
    selected = np.full(len(rows), np.nan, dtype=np.float32)
    for fold, family in enumerate(selected_family):
        mask = rows["biological_fold"].eq(fold).to_numpy()
        selected[mask] = predictions[family][mask]
    predictions["M1_M2_nested_selected"] = selected

    set_records = []
    for model, score in predictions.items():
        for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
            set_records.append(
                decision_set_metrics(rows, sign * score, model, direction, SEED, "outer_biological_fold")
            )
    set_metrics = pd.concat(set_records, ignore_index=True)
    unit_metrics, source_metrics = aggregate(set_metrics)

    baseline = source_metrics[source_metrics["model"].eq("M0_geometry")]
    context_records = []
    for model in ("M1", "M2", "M1_M2_nested_selected"):
        full = source_metrics[source_metrics["model"].eq(model)]
        paired = full.merge(baseline, on=["dataset", "requested_direction"], suffixes=("_full", "_m0"))
        for row in paired.itertuples(index=False):
            context_records.append(
                {
                    "model": model,
                    "dataset": row.dataset,
                    "requested_direction": row.requested_direction,
                    "rank_context_value": row.directional_rank_percentile_full - row.directional_rank_percentile_m0,
                    "regret_context_value": row.normalized_regret_m0 - row.normalized_regret_full,
                    "good3_context_value": row.good_selection_at_3_full - row.good_selection_at_3_m0,
                    "good5_context_value": row.good_selection_at_5_full - row.good_selection_at_5_m0,
                }
            )
    context = pd.DataFrame(context_records)
    summary = []
    for model, group in context.groupby("model", sort=True):
        summary.append(
            {
                "model": model,
                "equal_source_direction_rank_context_value": float(group["rank_context_value"].mean()),
                "equal_source_direction_regret_context_value": float(group["regret_context_value"].mean()),
                "positive_rank_tasks": int(group["rank_context_value"].gt(0).sum()),
                "positive_regret_tasks": int(group["regret_context_value"].gt(0).sum()),
                "gate_A": bool(
                    group["rank_context_value"].mean() >= 0.020
                    and group["regret_context_value"].mean() >= 0.010
                ),
            }
        )

    prediction_frame = rows[identity].copy()
    for model, score in predictions.items():
        prediction_frame[model] = score
    prediction_frame.to_csv(OUT / "direct_model_predictions.csv.gz", index=False, compression=GZIP)
    set_metrics.to_csv(OUT / "direct_model_set_metrics.csv.gz", index=False, compression=GZIP)
    unit_metrics.to_csv(OUT / "direct_model_unit_metrics.csv", index=False)
    source_metrics.to_csv(OUT / "direct_model_source_metrics.csv", index=False)
    context.to_csv(OUT / "direct_model_context_values.csv", index=False)
    result = {
        "phase": "FinalShot M0-M2 nested direct evaluation",
        "outer_fold_selected_family": selected_family,
        "summary": summary,
        "fit_recipes": {
            family: [
                {
                    "outer_fold": record["outer_fold"],
                    "penalty": record["selected_penalty"],
                    "group_fraction": record["selected_group_fraction"],
                    "selected_groups": record["selected_groups"],
                    "converged": record["outer_refit_converged"],
                }
                for record in records
            ]
            for family, records in metadata.items()
        },
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    (OUT / "direct_model_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
