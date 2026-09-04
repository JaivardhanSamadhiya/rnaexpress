"""Evaluate frozen distributed-unit, matched-mechanism, and edit-edit gates."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_decision_models import decision_set_metrics
from src.modeling.v4_phaseB2_context import edit_band, operation_signature


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
PREDICTIONS = ROOT / "results" / "finalshot" / "m0_m3_predictions.csv.gz"
OUT = ROOT / "results" / "finalshot"
FULL = "M1_M2_M3_nested_selected"
BASE = "M0_geometry"
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def add_metrics(frame: pd.DataFrame, score: np.ndarray, model: str, evaluation: str) -> pd.DataFrame:
    return pd.concat([
        decision_set_metrics(frame, score, model, "increase", SEED, evaluation),
        decision_set_metrics(frame, -score, model, "decrease", SEED, evaluation),
    ], ignore_index=True)


def unit_source(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fields = ["directional_rank_percentile", "normalized_regret", "good_selection_at_3", "good_selection_at_5"]
    unit = metrics.groupby(
        ["model", "dataset", "requested_direction", "biological_unit"], sort=True
    ).agg(decision_sets=("decision_set_id", "size"), **{field: (field, "mean") for field in fields}).reset_index()
    source = unit.groupby(["model", "dataset", "requested_direction"], sort=True).agg(
        biological_units=("biological_unit", "size"), decision_sets=("decision_sets", "sum"),
        **{field: (field, "mean") for field in fields},
    ).reset_index()
    return unit, source


def paired_context(unit: pd.DataFrame) -> pd.DataFrame:
    full = unit[unit["model"].eq(FULL)]
    base = unit[unit["model"].eq(BASE)]
    paired = full.merge(base, on=["dataset", "requested_direction", "biological_unit"],
                        suffixes=("_full", "_m0"), validate="one_to_one")
    paired["rank_context_value"] = paired["directional_rank_percentile_full"] - paired["directional_rank_percentile_m0"]
    paired["regret_context_value"] = paired["normalized_regret_m0"] - paired["normalized_regret_full"]
    paired["good3_context_value"] = paired["good_selection_at_3_full"] - paired["good_selection_at_3_m0"]
    paired["good5_context_value"] = paired["good_selection_at_5_full"] - paired["good_selection_at_5_m0"]
    return paired


def distributed_gate(unit_context: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    by_unit = unit_context.groupby(["dataset", "biological_unit"], sort=True).agg(
        directions=("requested_direction", "nunique"),
        rank_context_value=("rank_context_value", "mean"),
        regret_context_value=("regret_context_value", "mean"),
    ).reset_index()
    rng = np.random.default_rng(SEED)
    sources = sorted(by_unit["dataset"].unique())
    bootstrap = np.empty(10_000, dtype=float)
    for draw in range(len(bootstrap)):
        values = []
        for source in sources:
            source_values = by_unit.loc[by_unit["dataset"].eq(source), "regret_context_value"].to_numpy()
            values.append(float(rng.choice(source_values, size=len(source_values), replace=True).mean()))
        bootstrap[draw] = np.mean(values)
    source_means = by_unit.groupby("dataset")["regret_context_value"].mean()
    source_counts = by_unit["dataset"].value_counts()
    # Leave the single best unit out, retaining equal source weighting.
    best_index = int(by_unit["regret_context_value"].idxmax())
    leave_best = by_unit.drop(index=best_index).groupby("dataset")["regret_context_value"].mean().mean()
    result = {
        "biological_units": int(len(by_unit)),
        "all_units_have_both_directions": bool(by_unit["directions"].eq(2).all()),
        "positive_median_unit_regret_context_value": float(by_unit["regret_context_value"].median()),
        "unit_improvement_fraction": float(by_unit["regret_context_value"].gt(0).mean()),
        "equal_source_mean_regret_context_value": float(source_means.mean()),
        "leave_best_one_out_equal_source_mean": float(leave_best),
        "bootstrap_95_interval": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
        "source_unit_counts": {key: int(value) for key, value in source_counts.items()},
    }
    result["gate_B"] = bool(
        result["positive_median_unit_regret_context_value"] > 0
        and result["unit_improvement_fraction"] >= 0.55
        and result["leave_best_one_out_equal_source_mean"] > 0
        and result["bootstrap_95_interval"][0] >= -0.005
    )
    return by_unit, result


def metadata_keys(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["match_edit_band"] = edit_band(work["edit_cost"]).to_numpy()
    work["match_operation_signature"] = operation_signature(work).to_numpy()
    work["match_motif"] = work["motif_family"].fillna("none").astype(str)
    keys = ["cell_type", "match_motif", "intervention_class", "match_operation_signature", "match_edit_band"]
    work["cross_stratum"] = work[keys].astype(str).agg("||".join, axis=1)
    return work


def mikl_matched(rows: pd.DataFrame, prediction: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    mask = rows["dataset"].eq("mikl_gse173098").to_numpy()
    mikl = metadata_keys(rows.loc[mask].reset_index(drop=True))
    scores = prediction.loc[mask, [BASE, FULL]].reset_index(drop=True)
    eligible_strata = []
    audit = []
    for name, indices in mikl.groupby("cross_stratum", sort=True).indices.items():
        idx = np.asarray(indices, dtype=int)
        units = mikl.iloc[idx]["biological_unit"].nunique()
        eligible = len(idx) >= 20 and units >= 5
        audit.append({"cross_stratum": name, "rows": len(idx), "genes": units, "eligible": eligible})
        if eligible:
            eligible_strata.append(name)
    candidate = mikl[mikl["cross_stratum"].isin(eligible_strata)].copy()
    candidate["original_position"] = candidate.index
    within_keys = ["decision_set_id", "cross_stratum"]
    sizes = candidate.groupby(within_keys)["candidate_id"].transform("size")
    candidate = candidate.loc[sizes.ge(4)].copy().reset_index(drop=True)
    candidate["original_decision_set_id"] = candidate["decision_set_id"]
    candidate["decision_set_id"] = candidate[["decision_set_id", "cross_stratum"]].astype(str).agg("||".join, axis=1)
    selected_scores = scores.iloc[candidate["original_position"].to_numpy(int)].reset_index(drop=True)
    metric_frames = []
    for model in (BASE, FULL):
        observed = add_metrics(candidate, selected_scores[model].to_numpy(float), model, "mikl_matched_held_gene")
        motif_lookup = candidate[["decision_set_id", "match_motif"]].drop_duplicates("decision_set_id")
        observed = observed.merge(motif_lookup, on="decision_set_id", validate="many_to_one")
        metric_frames.append(observed)
    metrics = pd.concat(metric_frames, ignore_index=True)
    unit = metrics.groupby(["model", "requested_direction", "biological_unit", "match_motif"], sort=True).agg(
        rank=("directional_rank_percentile", "mean"), regret=("normalized_regret", "mean"),
        sets=("decision_set_id", "size"),
    ).reset_index()
    motif = unit.groupby(["model", "requested_direction", "match_motif"], sort=True).agg(
        genes=("biological_unit", "nunique"), sets=("sets", "sum"), rank=("rank", "mean"), regret=("regret", "mean")
    ).reset_index()
    full = motif[motif["model"].eq(FULL)]
    base = motif[motif["model"].eq(BASE)]
    paired = full.merge(base, on=["requested_direction", "match_motif"], suffixes=("_full", "_m0"))
    paired["rank_context_value"] = paired["rank_full"] - paired["rank_m0"]
    paired["regret_context_value"] = paired["regret_m0"] - paired["regret_full"]
    result = {
        "eligible_cross_strata": len(eligible_strata),
        "matched_rows": len(candidate),
        "matched_decision_subsets": int(candidate["decision_set_id"].nunique()),
        "matched_genes": int(candidate["biological_unit"].nunique()),
        "motif_direction_tasks": len(paired),
        "motif_macro_rank_context_value": float(paired["rank_context_value"].mean()),
        "motif_macro_regret_context_value": float(paired["regret_context_value"].mean()),
        "positive_rank_motif_tasks": int(paired["rank_context_value"].gt(0).sum()),
        "positive_regret_motif_tasks": int(paired["regret_context_value"].gt(0).sum()),
    }
    result["gate_C"] = bool(
        result["motif_macro_rank_context_value"] >= 0.010
        and result["motif_macro_regret_context_value"] >= 0.005
    )
    return pd.DataFrame(audit), paired, result


def band_analysis(rows: pd.DataFrame, prediction: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    bands = edit_band(rows["edit_cost"]).to_numpy()
    definitions = {
        "exact_1": bands == "1", "2-5": bands == "2-5", "6-10": bands == "6-10",
        "2-10": np.isin(bands, ["2-5", "6-10"]), "11-25": bands == "11-25",
        "26-50": bands == "26-50", ">50": bands == ">50",
    }
    records = []
    for band, mask in definitions.items():
        frame = rows.loc[mask].reset_index(drop=True)
        scores = prediction.loc[mask].reset_index(drop=True)
        model_metrics = []
        for model in (BASE, FULL):
            model_metrics.append(add_metrics(frame, scores[model].to_numpy(float), model, f"edit_band_{band}"))
        metrics = pd.concat(model_metrics, ignore_index=True)
        unit, source = unit_source(metrics)
        full = source[source["model"].eq(FULL)]
        base = source[source["model"].eq(BASE)]
        paired = full.merge(base, on=["dataset", "requested_direction"], suffixes=("_full", "_m0"))
        records.append({
            "edit_band": band,
            "candidate_rows": len(frame),
            "decision_sets": int(metrics[metrics["model"].eq(FULL)]["decision_set_id"].nunique()),
            "biological_units": int(unit[unit["model"].eq(FULL)]["biological_unit"].nunique()),
            "source_direction_tasks": len(paired),
            "rank_context_value": float((paired["directional_rank_percentile_full"] - paired["directional_rank_percentile_m0"]).mean()),
            "regret_context_value": float((paired["normalized_regret_m0"] - paired["normalized_regret_full"]).mean()),
        })
    table = pd.DataFrame(records)
    indexed = table.set_index("edit_band")
    combined = indexed.loc["2-10"]
    result = {
        "combined_2_10_rank_context_value": float(combined["rank_context_value"]),
        "combined_2_10_regret_context_value": float(combined["regret_context_value"]),
        "two_to_five_regret_context_value": float(indexed.loc["2-5", "regret_context_value"]),
        "six_to_ten_regret_context_value": float(indexed.loc["6-10", "regret_context_value"]),
    }
    companion_ok = (
        result["combined_2_10_regret_context_value"] >= -0.002
        if result["combined_2_10_rank_context_value"] >= 0.020
        else result["combined_2_10_rank_context_value"] >= -0.002
    )
    result["gate_F"] = bool(
        (result["combined_2_10_rank_context_value"] >= 0.020
         or result["combined_2_10_regret_context_value"] >= 0.010)
        and companion_ok
        and result["two_to_five_regret_context_value"] >= -0.005
        and result["six_to_ten_regret_context_value"] >= -0.005
    )
    return table, result


def main() -> None:
    rows = pd.read_csv(ROWS)
    prediction = pd.read_csv(PREDICTIONS)
    identity = ["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold", "feature_row"]
    if not rows[identity].astype(str).equals(prediction[identity].astype(str)):
        raise RuntimeError("Prediction alignment changed")
    metrics = pd.concat([
        add_metrics(rows, prediction[BASE].to_numpy(float), BASE, "outer_biological_fold"),
        add_metrics(rows, prediction[FULL].to_numpy(float), FULL, "outer_biological_fold"),
    ], ignore_index=True)
    unit, _ = unit_source(metrics)
    unit_context = paired_context(unit)
    by_unit, gate_b = distributed_gate(unit_context)
    match_audit, match_table, gate_c = mikl_matched(rows, prediction)
    band_table, gate_f = band_analysis(rows, prediction)
    unit_context.to_csv(OUT / "grouped_unit_context_values.csv", index=False)
    by_unit.to_csv(OUT / "grouped_unit_direction_average.csv", index=False)
    match_audit.to_csv(OUT / "mikl_matching_audit.csv", index=False)
    match_table.to_csv(OUT / "mikl_matched_motif_metrics.csv", index=False)
    band_table.to_csv(OUT / "small_edit_metrics.csv", index=False)
    result = {
        "model": FULL,
        "gate_B_distributed_units": gate_b,
        "gate_C_mikl_matched": gate_c,
        "gate_F_small_edit": gate_f,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    (OUT / "grouped_gate_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
