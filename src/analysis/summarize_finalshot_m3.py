"""Assemble the five frozen M3 outer folds and compare M0-M3."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.summarize_finalshot_direct_models import aggregate, inner_summary, load_family
from src.modeling.v4_decision_models import decision_set_metrics


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
DIRECT = ROOT / "results" / "finalshot" / "direct_model_predictions.csv.gz"
M3_DIR = ROOT / "results" / "finalshot" / "nested_m3"
OUT = ROOT / "results" / "finalshot"
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def selected_m3_grid(metadata: dict[str, object]) -> dict[str, object]:
    for row in metadata["inner_grid"]:
        if (
            float(row["penalty"]) == float(metadata["selected_penalty"])
            and float(row["group_fraction"]) == float(metadata["selected_group_fraction"])
            and str(row["head_form"]) == str(metadata["selected_head_form"])
        ):
            return row
    raise RuntimeError("Selected M3 recipe is absent from its inner grid")


def choose_final_family(records: dict[str, dict[str, object]]) -> str:
    best_regret = min(float(row["normalized_regret"]) for row in records.values())
    tied = [(name, row) for name, row in records.items()
            if float(row["normalized_regret"]) <= best_regret + 0.002]
    simplicity = {"M1": 3, "M2": 2, "M3": 1}
    return max(
        tied,
        key=lambda item: (
            float(item[1]["directional_rank_percentile"]),
            float(item[1]["good_selection_at_3"]),
            simplicity[item[0]],
            float(item[1]["penalty"]),
            float(item[1]["group_fraction"]),
            1 if item[1].get("head_form", "affine") == "affine" else 0,
        ),
    )[0]


def main() -> None:
    rows = pd.read_csv(ROWS)
    direct = pd.read_csv(DIRECT)
    identity = ["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold", "feature_row"]
    if not rows[identity].astype(str).equals(direct[identity].astype(str)):
        raise RuntimeError("Direct predictions do not align with frozen rows")
    m1_prediction, m1_meta = load_family("M1", rows)
    m2_prediction, m2_meta = load_family("M2", rows)
    m3_prediction = np.full(len(rows), np.nan, dtype=np.float32)
    seed_predictions = np.full((3, len(rows)), np.nan, dtype=np.float32)
    m3_meta = []
    for fold in range(5):
        path = M3_DIR / f"M3_outer_fold_{fold}.npz"
        with np.load(path, allow_pickle=False) as archive:
            indices = archive["test_indices"].astype(int)
            m3_prediction[indices] = archive["prediction"]
            seed_predictions[:, indices] = archive["seed_predictions"]
            metadata = json.loads(str(archive["metadata_json"].item()))
        if metadata["outer_fold"] != fold or not np.all(rows.iloc[indices]["biological_fold"].to_numpy() == fold):
            raise RuntimeError(f"M3 outer-fold mismatch in {path}")
        m3_meta.append(metadata)
    if not np.isfinite(m3_prediction).all() or not np.isfinite(seed_predictions).all():
        raise RuntimeError("M3 held-fold prediction assembly is incomplete")

    family_prediction = {"M1": m1_prediction, "M2": m2_prediction, "M3": m3_prediction}
    selected_families = []
    selected_prediction = np.full(len(rows), np.nan, dtype=np.float32)
    for fold in range(5):
        candidates = {
            "M1": inner_summary(m1_meta[fold]),
            "M2": inner_summary(m2_meta[fold]),
            "M3": selected_m3_grid(m3_meta[fold]),
        }
        family = choose_final_family(candidates)
        selected_families.append(family)
        mask = rows["biological_fold"].eq(fold).to_numpy()
        selected_prediction[mask] = family_prediction[family][mask]

    predictions = {
        "M0_geometry": direct["M0_geometry"].to_numpy(float),
        "M1": m1_prediction,
        "M2": m2_prediction,
        "M3": m3_prediction,
        "M1_M2_M3_nested_selected": selected_prediction,
        "M3_seed17": seed_predictions[0],
        "M3_seed41": seed_predictions[1],
        "M3_seed89": seed_predictions[2],
    }
    sets = []
    for model, prediction in predictions.items():
        for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
            sets.append(decision_set_metrics(rows, sign * prediction, model, direction, SEED, "outer_biological_fold"))
    set_metrics = pd.concat(sets, ignore_index=True)
    unit_metrics, source_metrics = aggregate(set_metrics)
    baseline = source_metrics[source_metrics["model"].eq("M0_geometry")]
    context_records = []
    for model in predictions:
        if model == "M0_geometry":
            continue
        full = source_metrics[source_metrics["model"].eq(model)]
        paired = full.merge(baseline, on=["dataset", "requested_direction"], suffixes=("_full", "_m0"))
        for row in paired.itertuples(index=False):
            context_records.append({
                "model": model,
                "dataset": row.dataset,
                "requested_direction": row.requested_direction,
                "rank_context_value": row.directional_rank_percentile_full - row.directional_rank_percentile_m0,
                "regret_context_value": row.normalized_regret_m0 - row.normalized_regret_full,
                "good3_context_value": row.good_selection_at_3_full - row.good_selection_at_3_m0,
                "good5_context_value": row.good_selection_at_5_full - row.good_selection_at_5_m0,
            })
    context = pd.DataFrame(context_records)
    summaries = []
    for model, group in context.groupby("model", sort=True):
        summaries.append({
            "model": model,
            "rank_context_value": float(group["rank_context_value"].mean()),
            "regret_context_value": float(group["regret_context_value"].mean()),
            "positive_rank_tasks": int(group["rank_context_value"].gt(0).sum()),
            "positive_regret_tasks": int(group["regret_context_value"].gt(0).sum()),
            "gate_A": bool(group["rank_context_value"].mean() >= 0.020 and group["regret_context_value"].mean() >= 0.010),
        })
    seed_summary = [row for row in summaries if row["model"].startswith("M3_seed")]
    seed_stability = {
        "rank_context_value_std": float(np.std([row["rank_context_value"] for row in seed_summary], ddof=0)),
        "regret_context_value_std": float(np.std([row["regret_context_value"] for row in seed_summary], ddof=0)),
        "all_seed_gate_A_agree": len({row["gate_A"] for row in seed_summary}) == 1,
    }

    prediction_frame = rows[identity].copy()
    for model, prediction in predictions.items():
        prediction_frame[model] = prediction
    prediction_frame.to_csv(OUT / "m0_m3_predictions.csv.gz", index=False, compression=GZIP)
    set_metrics.to_csv(OUT / "m0_m3_set_metrics.csv.gz", index=False, compression=GZIP)
    unit_metrics.to_csv(OUT / "m0_m3_unit_metrics.csv", index=False)
    source_metrics.to_csv(OUT / "m0_m3_source_metrics.csv", index=False)
    context.to_csv(OUT / "m0_m3_context_values.csv", index=False)
    result = {
        "phase": "FinalShot M0-M3 nested biological-fold evaluation",
        "outer_fold_selected_family": selected_families,
        "m3_recipes": [{
            "outer_fold": item["outer_fold"],
            "penalty": item["selected_penalty"],
            "group_fraction": item["selected_group_fraction"],
            "head_form": item["selected_head_form"],
        } for item in m3_meta],
        "summary": summaries,
        "seed_stability": seed_stability,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    (OUT / "m0_m3_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
