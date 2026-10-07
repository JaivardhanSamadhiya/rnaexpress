"""Fixed descriptive exact-menu contrast; no selection, refitting or gate rescue."""
from .common import *
from .gate import component_values
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap


def paired_contrast(pairs, known, crossed, task):
    cell, source_task = TASKS[task]
    own, other = ("CAD_context", "N2A_context") if cell == "CAD" else ("N2A_context", "CAD_context")
    assert not known.duplicated(["task", "parent_context_id", "direction"]).any()
    assert not crossed.duplicated(["task", "parent_context_id", "direction"]).any()
    left = known[known.task.eq(task)].set_index(["parent_context_id", "direction"])
    right = crossed[crossed.task.eq(source_task)].set_index(["parent_context_id", "direction"])
    rows = []
    for row in pairs.itertuples():
        for direction in (-1, 1):
            a, b = left.loc[(getattr(row, own), direction)], right.loc[(getattr(row, other), direction)]
            assert a.biological_component == b.biological_component == row.biological_component
            assert int(a.gene_fold) == int(b.gene_fold) == int(row.gene_fold)
            assert int(a.candidates) == int(b.candidates) == int(row.candidates)
            rows.append({"task": task, "biological_component": row.biological_component,
                "gene_fold": int(row.gene_fold), "known_context": getattr(row, own),
                "crossed_context": getattr(row, other), "direction": direction,
                "known_regret": float(a.regret), "crossed_regret": float(b.regret),
                "known_advantage": float(b.regret - a.regret),
                "lexical_allele_order_matches": bool(row.lexical_allele_order_matches)})
    return pd.DataFrame(rows)


def run():
    freeze_check()
    receipt = readj(OUT / "verification_receipt.json"); assert receipt["status"] == "PASS"
    assert receipt["same_checkpoint_both_states_verified"] and receipt["crossed_state_predictors_rechecked"] == 42
    assert receipt["evaluation_manifest_sha256"] == sha256(OUT / "evaluation_manifest.json")
    for name, checksum in receipt["result_files"].items(): assert sha256(ROOT / name) == checksum
    pairs = pd.read_csv(OUT / "exact_menu_pairs.csv")
    assert len(pairs) and pairs.biological_component.nunique() == 187
    summaries = []
    for track in TRACKS:
        known = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip")
        crossed = pd.read_csv(SOURCE_OUT / track / "decisions.csv", float_precision="round_trip")
        roster = readj(OUT / track / "roster.json")
        source_roster = readj(SOURCE_OUT / track / "folds.json")
        for entry in roster:
            original = next(r for r in source_roster if r["task"] == entry["source_task"] and r["fold"] == entry["fold"])
            assert original["selected_configuration"] == entry["configuration"]
            assert sha256(ROOT / entry["source_checkpoint"]) == entry["source_checkpoint_sha256"]
        paired = pd.concat([paired_contrast(pairs, known, crossed, task) for task in TASKS], ignore_index=True)
        strata = {"all_exact_menus": paired,
            "lexical_order_equal": paired[paired.lexical_allele_order_matches],
            "lexical_order_different": paired[~paired.lexical_allele_order_matches]}
        for name, subset in strata.items():
            gains = component_values(subset, "known_advantage")
            assert all(len(v) for v in gains.values())
            if name == "all_exact_menus": assert all(len(v) == 187 for v in gains.values())
            interval = shared_bootstrap(gains, 5000, SEED)
            summaries.append({"track": track, "stratum": name,
                "mean_known_advantage": float(np.mean([v.mean() for v in gains.values()])),
                "per_known_cell": {task: float(v.mean()) for task, v in gains.items()},
                "descriptive_ci": [float(np.quantile(interval, .025)), float(np.quantile(interval, .975))],
                "paired_menus": int(subset[subset.task.eq("CAD_known")].known_context.nunique()),
                "components": subset.biological_component.nunique(),
                "lexical_order_mismatched_menus": int((~pairs.lexical_allele_order_matches).sum())})
        csvsave(OUT / track / "state_contrast.csv", paired)
    jsave(OUT / "state_contrast.json", {"status": "DESCRIPTIVE", "tracks": summaries,
        "objective": "crossed-state regret minus same-state regret, identical frozen source predictor",
        "scope": "Exact full menus only, equal directions/menus within gene, then genes/cells",
        "new_fits": 0, "selects_nothing": True, "changes_no_gate": True,
        "causal_cell_state_claim": False, "biological_confirmation": False})


if __name__ == "__main__": run()
