"""Unchanged numerical narrow gate, separately labelled represented-cell scope."""
from .common import *
from .evaluate import task_summary
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap


def component_values(d, column):
    return {task: d[d.task.eq(task)].groupby("biological_component")[column].mean() for task in TASKS}


def compare(candidate, control):
    a, b = component_values(control, "regret"), component_values(candidate, "regret")
    gains = {}
    for task in TASKS:
        assert set(a[task].index) == set(b[task].index)
        gains[task] = a[task] - b[task].reindex(a[task].index)
    means = {task: float(value.mean()) for task, value in gains.items()}
    foldmap = candidate[["biological_component", "gene_fold"]].drop_duplicates().set_index("biological_component").gene_fold
    assert foldmap.index.is_unique
    fold_gains = {fold: float(np.mean([v[v.index.map(foldmap).to_numpy() == fold].mean() for v in gains.values()])) for fold in FOLDS}
    best = max(FOLDS, key=lambda fold: (fold_gains[fold], -fold))
    remaining = float(np.mean([v[v.index.map(foldmap).to_numpy() != best].mean() for v in gains.values()]))
    interval = shared_bootstrap(gains, 5000, SEED)
    wa, wb = component_values(control, "wrong_direction"), component_values(candidate, "wrong_direction")
    wrong = {task: float((wb[task] - wa[task].reindex(wb[task].index)).mean()) for task in TASKS}
    return {"mean_gain": float(np.mean(list(means.values()))), "per_known_cell_gain": means,
        "gain_ci": [float(np.quantile(interval, .025)), float(np.quantile(interval, .975))],
        "removed_best_gene_fold": best, "remaining_gain": remaining, "fold_gains": fold_gains,
        "wrong_direction_harm": wrong, "macro_wrong_direction_harm": float(np.mean(list(wrong.values())))}


def run():
    freeze_check(); receipt = readj(OUT / "verification_receipt.json")
    assert receipt["status"] == "PASS" and receipt["evaluation_manifest_sha256"] == sha256(OUT / "evaluation_manifest.json")
    for name, checksum in receipt["result_files"].items(): assert sha256(ROOT / name) == checksum
    data = {track: pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip") for track in TRACKS}
    controls = {"structure": ["raw"], "bert": ["lookup"], "combined": ["structure", "bert"]}
    results = []
    for track in TRACKS:
        summary = task_summary(data[track]).set_index("task")
        checks = {"macro_regret_at_most_0_48": float(summary.regret.mean()) <= .48,
                  "each_known_cell_below_uniform": bool((summary.regret < .5).all())}
        incremental, ablations = {}, {}
        for control in ("base", "simple"):
            value = compare(data[track], data[control]); incremental[control] = value
            checks.update({control + "_mean_gain_0_01": value["mean_gain"] >= .01,
                control + "_each_cell_gain_0_005": min(value["per_known_cell_gain"].values()) >= .005,
                control + "_bootstrap_lower_positive": value["gain_ci"][0] > 0,
                control + "_macro_wrong_harm_0_02": value["macro_wrong_direction_harm"] <= .02,
                control + "_each_cell_wrong_harm_0_05": max(value["wrong_direction_harm"].values()) <= .05,
                control + "_leave_best_fold_positive": value["remaining_gain"] > 0})
        for control in controls.get(track, []):
            value = compare(data[track], data[control]); ablations[control] = value
            checks[control + "_information_mean_0_01"] = value["mean_gain"] >= .01
            checks[control + "_information_leave_best_positive"] = value["remaining_gain"] > 0
        results.append({"track": track, "claim_eligible": track in INFORMED, "passes": track in INFORMED and all(checks.values()),
            "checks": checks, "macro_regret": float(summary.regret.mean()), "per_known_cell": summary.reset_index().to_dict("records"),
            "incremental": incremental, "information_controls": ablations})
    jsave(OUT / "gate_verdict.json", {"status": "CONDITIONAL_CELL_DEVELOPMENT_GO" if any(r["passes"] for r in results) else "NO-GO",
        "tracks": results, "scope": "Held genes conditional on represented cell, using identical frozen source models",
        "four_source_and_unseen_cell_gates_unchanged": True, "new_fits": 0, "independent_confirmation": False,
        "known_cell_prediction_alone_not_first_demonstration": True, "thresholds_changed_after_performance": False})


if __name__ == "__main__": run()
