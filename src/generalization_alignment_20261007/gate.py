"""Unchanged strict gate plus fixed matched alignment/information contrasts."""
from .common import *
from src.generalization_next_20261007.bootstrap import shared_bootstrap

INFORMED_COMPARATORS = {"structure":["raw"], "bert":["base", "lookup"], "combined":["structure", "bert"]}


def incremental_checks(gains):
    gains = np.asarray(gains, dtype=float)
    assert gains.shape == (4,) and np.isfinite(gains).all()
    return {"macro_incremental_gain_at_least_0_01":float(gains.mean()) >= .01,
            "incremental_leave_best_assay_out_positive":float(np.delete(gains, np.argmax(gains)).mean()) > 0}


def comparison(root, track):
    complete = readj(root / track / "run_complete.json")
    assert complete["status"] == "PASS" and complete["fit_files"] == 40 and complete["prediction_rows"] == 26258
    value = pd.read_csv(root / track / "comparison.csv").set_index("dataset")
    assert len(value) == 4 and set(value.index) == set(STUDIES)
    return value


def contrast(candidate, control, label):
    gains = np.array([float(control.loc[study].regret) - float(candidate.loc[study].regret) for study in STUDIES])
    checks = incremental_checks(gains)
    return {"comparator":label, "mean_gain":float(gains.mean()), "per_assay_gain":dict(zip(STUDIES, gains)),
            "checks":checks, "passes":all(checks.values())}


def run():
    freeze_check()
    from src.generalization_next_20261007.common import freeze_check as next_freeze
    next_freeze()
    assert readj(OUT / "verification_receipt.json")["status"] == "PASS"
    assert readj(NEXT_OUT / "verification_receipt.json")["status"] == "PASS"
    old = pd.read_csv(ROOT / "artifacts/cross_assay_20260927/model_comparison.csv")
    old = old[old.stage.eq("held_assay")].set_index(["model", "dataset"])
    names = ["uniform", "metadata", "composition"]
    selected = {study:min(names, key=lambda name:(float(old.loc[name, study].regret),
                float(old.loc[name, study].avoidable_wrong), name)) for study in STUDIES}
    prior = pd.read_csv(ROOT / "results/cross_assay_20260927/decision_metrics.csv")
    prior = prior[prior.stage.eq("held_assay")]
    aligned = {track:comparison(OUT, track) for track in TRACKS}
    unflipped = {track:comparison(NEXT_OUT, track) for track in TRACKS}
    controls, results, all_decisions = {}, [], []
    for track in TRACKS:
        assert readj(OUT / track / "run_complete.json")["prefit_manifest_sha256"] == sha256(OUT / "prefit_manifest.json")
        assert readj(NEXT_OUT / track / "run_complete.json")["prefit_manifest_sha256"] == sha256(NEXT_OUT / "prefit_manifest.json")
        for filename in ("run_complete.json", "comparison.csv", "decisions.csv", "predictions.csv.gz", "folds.json", "inner_selection.csv"):
            path = NEXT_OUT / track / filename
            controls[path.relative_to(ROOT).as_posix()] = sha256(path)
        comp = aligned[track]
        d = pd.read_csv(OUT / track / "decisions.csv"); all_decisions.append(d)
        g = np.array([float(old.loc[selected[s], s].regret) - float(comp.loc[s].regret) for s in STUDIES])
        gh = np.array([float(old.loc["interaction_3", s].regret) - float(comp.loc[s].regret) for s in STUDIES])
        wrong = np.array([float(comp.loc[s].avoidable_wrong) - float(old.loc[selected[s], s].avoidable_wrong) for s in STUDIES])
        wrong_h = np.array([float(comp.loc[s].avoidable_wrong) - float(old.loc["interaction_3", s].avoidable_wrong) for s in STUDIES])
        positive = np.maximum(g, 0); share = float(positive.max() / positive.sum()) if positive.sum() else 1.
        component_gains = {}
        for s in STUDIES:
            a = prior[prior.dataset.eq(s) & prior.model.eq(selected[s])].groupby("biological_component").regret.mean()
            b = d[d.dataset.eq(s)].groupby("biological_component").regret.mean()
            assert set(a.index) == set(b.index)
            component_gains[s] = a - b.reindex(a.index)
        boot = shared_bootstrap(component_gains, 5000, SEED)
        checks = {
            "macro_regret_at_most_0_468":float(comp.regret.mean()) <= .468,
            "macro_gain_vs_simple_at_least_0_02":float(g.mean()) >= .02,
            "three_assays_gain_vs_simple_at_least_0_02":int((g >= .02).sum()) >= 3,
            "three_assays_gain_vs_H0_at_least_0_01":int((gh >= .01).sum()) >= 3,
            "Mikl_SRLE_harm_at_most_0_01_vs_both":all(float(comp.loc[s].regret) <= min(float(old.loc[selected[s], s].regret), float(old.loc["interaction_3", s].regret)) + .01 for s in ["mikl_gse173098", "srle"]),
            "any_assay_harm_vs_simple_at_most_0_05":bool((g >= -.05).all()),
            "macro_avoidable_harm_at_most_0_02_vs_both":max(float(wrong.mean()), float(wrong_h.mean())) <= .02,
            "each_avoidable_harm_at_most_0_05_vs_both":max(float(wrong.max()), float(wrong_h.max())) <= .05,
            "leave_best_assay_out_positive":float(np.delete(g, np.argmax(g)).mean()) > 0,
            "max_positive_gain_share_at_most_0_60":share <= .6,
            "descriptive_bootstrap_lower_at_least_minus_0_01":float(np.quantile(boot, .025)) >= -.01}
        orientation = contrast(comp, unflipped[track], "unflipped_next_" + track)
        information = [contrast(comp, aligned[control], "aligned_" + control)
                       for control in INFORMED_COMPARATORS.get(track, [])]
        historical_pass = all(checks.values())
        alignment_pass = historical_pass and orientation["passes"]
        informed = track in INFORMED_COMPARATORS
        results.append({"track":track, "passes":bool(alignment_pass and informed and all(row["passes"] for row in information)),
            "historical_gate_passes":historical_pass, "alignment_hypothesis_passes":alignment_pass,
            "informed_route":informed, "checks":checks, "matched_alignment_comparison":orientation,
            "aligned_information_comparisons":information, "macro_regret":float(comp.regret.mean()),
            "macro_gain_vs_simple":float(g.mean()), "macro_gain_vs_H0":float(gh.mean()),
            "gain_ci":[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
            "per_assay":[{"dataset":s, "regret":float(comp.loc[s].regret), "gain_vs_simple":float(g[i]),
                          "gain_vs_H0":float(gh[i]), "avoidable_wrong":float(comp.loc[s].avoidable_wrong)} for i, s in enumerate(STUDIES)]})
    jsave(OUT / "gate_verdict.json", {"status":"DEVELOPMENT_GO" if any(row["passes"] for row in results) else "NO-GO",
        "tracks":results, "observed_data_followup":True, "prior_polarity_NO_GO_retained":True,
        "criteria_changed_after_alignment_results":False, "independent_confirmation":False,
        "matched_unflipped_output_hashes":controls,
        "scope":"Repeatedly exposed development filter. Base/raw/lookup are controls; endpoint is confounded with assay, with one nuclear source. No novel universal mechanism or calibrated absolute benefit claim."})
    csvsave(ART / "model_comparison.csv", pd.concat([pd.read_csv(OUT / track / "comparison.csv") for track in TRACKS], ignore_index=True))
    csvsave(ART / "decision_metrics.csv.gz", pd.concat(all_decisions, ignore_index=True), True)
    print(readj(OUT / "gate_verdict.json")["status"], flush=True)


if __name__ == "__main__":
    run()
