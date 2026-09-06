"""Assemble frozen FinalShot mechanism controls and evaluate Gate G."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.summarize_finalshot_direct_models import aggregate, inner_summary
from src.analysis.summarize_finalshot_m3 import choose_final_family, selected_m3_grid
from src.modeling.v4_decision_models import decision_set_metrics


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
PRIMARY = ROOT / "results" / "finalshot" / "m0_m3_predictions.csv.gz"
DIRECT = ROOT / "results" / "finalshot" / "nested_controls_direct"
M3 = ROOT / "results" / "finalshot" / "nested_controls_m3"
OUT = ROOT / "results" / "finalshot"
CONTROLS = ("rbp_identity_permutation", "delta_rbp_shuffle")
SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def load_archive(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    with np.load(path, allow_pickle=False) as archive:
        indices = archive["test_indices"].astype(int)
        prediction = archive["prediction"].astype(np.float32)
        metadata = json.loads(str(archive["metadata_json"].item()))
    if len(indices) != len(prediction) or not np.isfinite(prediction).all():
        raise RuntimeError(f"Invalid control archive: {path}")
    return indices, prediction, metadata


def assemble_control(control: str, rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    family_predictions = {name: np.full(len(rows), np.nan, dtype=np.float32) for name in ("M1", "M2", "M3")}
    eligible = np.zeros(len(rows), dtype=bool)
    selected_families = []
    for fold in range(5):
        direct = {
            family: load_archive(DIRECT / control / f"{family}_outer_fold_{fold}.npz")
            for family in ("M1", "M2")
        }
        m3 = load_archive(M3 / control / f"M3_outer_fold_{fold}.npz")
        reference = direct["M1"][0]
        if not np.array_equal(reference, direct["M2"][0]) or not np.array_equal(reference, m3[0]):
            raise RuntimeError(f"Control outer indices differ for {control}/fold {fold}")
        if not np.all(rows.iloc[reference]["biological_fold"].to_numpy(int) == fold):
            raise RuntimeError(f"Control outer-fold mismatch for {control}/fold {fold}")
        candidates = {
            "M1": inner_summary(direct["M1"][2]),
            "M2": inner_summary(direct["M2"][2]),
            "M3": selected_m3_grid(m3[2]),
        }
        selected = choose_final_family(candidates)
        selected_families.append(selected)
        eligible[reference] = True
        family_predictions["M1"][reference] = direct["M1"][1]
        family_predictions["M2"][reference] = direct["M2"][1]
        family_predictions["M3"][reference] = m3[1]
    selected_prediction = np.full(len(rows), np.nan, dtype=np.float32)
    for fold, family in enumerate(selected_families):
        mask = eligible & rows["biological_fold"].eq(fold).to_numpy()
        selected_prediction[mask] = family_predictions[family][mask]
    if not np.isfinite(selected_prediction[eligible]).all():
        raise RuntimeError(f"Incomplete selected control prediction: {control}")
    return eligible, selected_prediction, selected_families


def context_summary(frame: pd.DataFrame, baseline: np.ndarray, prediction: np.ndarray,
                    label: str, control: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sets = []
    for model, score in (("M0_geometry", baseline), (label, prediction)):
        for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
            metric = decision_set_metrics(frame, sign * score, model, direction, SEED, control)
            metric["control"] = control
            sets.append(metric)
    set_metrics = pd.concat(sets, ignore_index=True)
    _, source = aggregate(set_metrics)
    m0 = source[source["model"].eq("M0_geometry")]
    full = source[source["model"].eq(label)]
    paired = full.merge(m0, on=["dataset", "requested_direction"], suffixes=("_full", "_m0"))
    context = pd.DataFrame({
        "control": control,
        "model": label,
        "dataset": paired["dataset"],
        "requested_direction": paired["requested_direction"],
        "rank_context_value": paired["directional_rank_percentile_full"] - paired["directional_rank_percentile_m0"],
        "regret_context_value": paired["normalized_regret_m0"] - paired["normalized_regret_full"],
    })
    return set_metrics, context


def main() -> None:
    rows = pd.read_csv(ROWS)
    primary = pd.read_csv(PRIMARY)
    identity = ["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold", "feature_row"]
    if not rows[identity].astype(str).equals(primary[identity].astype(str)):
        raise RuntimeError("Primary predictions do not align with frozen rows")
    all_sets = []
    all_context = []
    control_results = []
    for control in CONTROLS:
        eligible, control_prediction, selected_families = assemble_control(control, rows)
        frame = rows.loc[eligible].reset_index(drop=True)
        baseline = primary.loc[eligible, "M0_geometry"].to_numpy(float)
        observed = primary.loc[eligible, "M1_M2_M3_nested_selected"].to_numpy(float)
        sets, observed_context = context_summary(
            frame, baseline, observed, "observed_nested", control
        )
        control_sets, broken_context = context_summary(
            frame, baseline, control_prediction[eligible], "broken_nested", control
        )
        all_sets.extend([sets, control_sets[control_sets["model"].eq("broken_nested")]])
        all_context.extend([observed_context, broken_context])
        observed_rank = float(observed_context["rank_context_value"].mean())
        observed_regret = float(observed_context["regret_context_value"].mean())
        broken_rank = float(broken_context["rank_context_value"].mean())
        broken_regret = float(broken_context["regret_context_value"].mean())
        rank_retained = broken_rank / observed_rank
        regret_retained = broken_regret / observed_regret
        result = {
            "control": control,
            "eligible_rows": int(eligible.sum()),
            "excluded_rows": int((~eligible).sum()),
            "outer_fold_selected_family": selected_families,
            "observed_rank_context_value": observed_rank,
            "observed_regret_context_value": observed_regret,
            "control_rank_context_value": broken_rank,
            "control_regret_context_value": broken_regret,
            "rank_retained_fraction": rank_retained,
            "regret_retained_fraction": regret_retained,
            "rank_eliminated_fraction": 1.0 - rank_retained,
            "regret_eliminated_fraction": 1.0 - regret_retained,
            "mean_retained_fraction": float(np.mean([rank_retained, regret_retained])),
            "eliminates_at_least_half_one_metric": bool(
                rank_retained <= 0.5 or regret_retained <= 0.5
            ),
            "mean_retained_at_most_half": bool(np.mean([rank_retained, regret_retained]) <= 0.5),
            "control_meets_gate_A": bool(broken_rank >= 0.020 and broken_regret >= 0.010),
        }
        result["individual_pass"] = bool(
            result["eliminates_at_least_half_one_metric"]
            and result["mean_retained_at_most_half"]
            and not result["control_meets_gate_A"]
        )
        control_results.append(result)
    summary = {
        "phase": "FinalShot Gate G mechanism-breaking controls",
        "controls": control_results,
        "gate_G_pass": all(item["individual_pass"] for item in control_results),
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    pd.concat(all_sets, ignore_index=True).to_csv(
        OUT / "mechanism_control_set_metrics.csv.gz", index=False, compression=GZIP
    )
    pd.concat(all_context, ignore_index=True).to_csv(
        OUT / "mechanism_control_context_values.csv", index=False
    )
    (OUT / "gate_g_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
