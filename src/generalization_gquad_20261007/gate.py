"""Unchanged strict four-assay gate and fixed information controls."""
from .common import *
from src.generalization_next_20261007.bootstrap import shared_bootstrap

from .spec import INCREMENTAL, ELIGIBLE
NEW_ENCODER_TRACKS = ELIGIBLE


def incremental_checks(gains):
    gains = np.asarray(gains, dtype=float)
    assert gains.shape == (4,) and np.isfinite(gains).all()
    return {"macro_incremental_gain_at_least_0_01": float(gains.mean()) >= .01,
        "incremental_leave_best_assay_out_positive": float(np.delete(gains, np.argmax(gains)).mean()) > 0}


def strict_checks(regrets, gains, gains_h0, wrong_harm, wrong_harm_h0, bootstrap):
    arrays = [np.asarray(value, dtype=float) for value in (regrets, gains, gains_h0, wrong_harm, wrong_harm_h0)]
    assert all(value.shape == (4,) and np.isfinite(value).all() for value in arrays)
    regrets, gains, gains_h0, wrong_harm, wrong_harm_h0 = arrays
    bootstrap = np.asarray(bootstrap, dtype=float)
    assert bootstrap.shape == (5000,) and np.isfinite(bootstrap).all()
    positive = np.maximum(gains, 0)
    share = float(positive.max() / positive.sum()) if positive.sum() > 0 else 1.
    checks = {"macro_regret_at_most_0_468": float(regrets.mean()) <= .468,
        "macro_gain_vs_simple_at_least_0_02": float(gains.mean()) >= .02,
        "three_assays_gain_vs_simple_at_least_0_02": int((gains >= .02).sum()) >= 3,
        "three_assays_gain_vs_H0_at_least_0_01": int((gains_h0 >= .01).sum()) >= 3,
        "Mikl_SRLE_harm_at_most_0_01_vs_both": bool((gains[[1, 3]] >= -.01).all() and (gains_h0[[1, 3]] >= -.01).all()),
        "any_assay_harm_vs_simple_at_most_0_05": bool((gains >= -.05).all()),
        "macro_avoidable_harm_at_most_0_02_vs_both": max(float(wrong_harm.mean()), float(wrong_harm_h0.mean())) <= .02,
        "each_avoidable_harm_at_most_0_05_vs_both": max(float(wrong_harm.max()), float(wrong_harm_h0.max())) <= .05,
        "leave_best_assay_out_positive": float(np.delete(gains, np.argmax(gains)).mean()) > 0,
        "max_positive_gain_share_at_most_0_60": share <= .6,
        "descriptive_bootstrap_lower_at_least_minus_0_01": float(np.quantile(bootstrap, .025)) >= -.01}
    return checks, share


def run():
    freeze_check(); input_check()
    verification = readj(OUT / "verification_receipt.json")
    assert verification["status"] == "PASS" and verification["prefit_manifest_sha256"] == sha256(OUT / "prefit_manifest.json")
    assert verification["inner_original_truth_regrets_replayed"] == 180 and verification["outer_targets_replayed"] == 20
    assert verification["maximum_inner_score_error"] < 1e-9 and verification["maximum_outer_arithmetic_score_error"] < 1e-9
    assert verification["maximum_outer_score_error"] < 1e-9 and verification["direct_pair_credit_and_recovery_checked"]
    assert verification["maximum_outer_independent_vs_saved_score_error"] < 1e-9
    for name, expected in verification["files"].items():
        assert sha256(ROOT / name) == expected, name
    old = pd.read_csv(ROOT / "artifacts/cross_assay_20260927/model_comparison.csv")
    old = old[old.stage.eq("held_assay")].set_index(["model", "dataset"])
    simple_models = {study: min(["uniform", "metadata", "composition"], key=lambda model: (float(old.loc[model, study].regret), float(old.loc[model, study].avoidable_wrong), model)) for study in STUDIES}
    simple = {study: min(float(old.loc[model, study].regret) for model in ["uniform", "metadata", "composition"]) for study in STUDIES}
    h0 = {study: float(old.loc["interaction_3", study].regret) for study in STUDIES}
    prior = pd.read_csv(ROOT / "results/cross_assay_20260927/decision_metrics.csv")
    prior = prior[prior.stage.eq("held_assay")]
    comparisons = {track: pd.read_csv(OUT / track / "comparison.csv", float_precision="round_trip").set_index("dataset") for track in TRACKS}
    results, all_decisions = [], []
    for track in TRACKS:
        complete = readj(OUT / track / "run_complete.json")
        assert complete["status"] == "PASS" and complete["fit_files"] == 40 and complete["prediction_rows"] == 26258
        assert complete["prefit_manifest_sha256"] == sha256(OUT / "prefit_manifest.json")
        comp = comparisons[track]; assert set(comp.index) == set(STUDIES) and comp.index.is_unique
        d = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip"); all_decisions.append(d)
        regrets = np.asarray([float(comp.loc[study].regret) for study in STUDIES])
        gains = np.asarray([simple[study] - float(comp.loc[study].regret) for study in STUDIES])
        gains_h0 = np.asarray([h0[study] - float(comp.loc[study].regret) for study in STUDIES])
        wrong = np.asarray([float(comp.loc[study].avoidable_wrong) - float(old.loc[simple_models[study], study].avoidable_wrong) for study in STUDIES])
        wrong_h0 = np.asarray([float(comp.loc[study].avoidable_wrong) - float(old.loc["interaction_3", study].avoidable_wrong) for study in STUDIES])
        by_study = {}
        for study in STUDIES:
            a = prior[prior.dataset.eq(study) & prior.model.eq(simple_models[study])].groupby("biological_component").regret.mean()
            b = d[d.dataset.eq(study)].groupby("biological_component").regret.mean()
            assert set(a.index) == set(b.index)
            by_study[study] = a - b.reindex(a.index)
        bootstrap = shared_bootstrap(by_study, draws=5000, seed=SEED)
        checks, share = strict_checks(regrets, gains, gains_h0, wrong, wrong_h0, bootstrap)
        incremental = []
        for comparator in INCREMENTAL.get(track, []):
            control = comparisons[comparator]
            gain = np.asarray([float(control.loc[study].regret) - float(comp.loc[study].regret) for study in STUDIES])
            additional = incremental_checks(gain)
            incremental.append({"comparator": comparator, "mean_gain": float(gain.mean()), "per_assay_gain": dict(zip(STUDIES, gain.tolist())),
                "checks": additional, "passes": all(additional.values())})
        strict_pass = all(checks.values()); informed_pass = strict_pass and track in INCREMENTAL and all(row["passes"] for row in incremental)
        results.append({"track": track, "historical_gate_passes": strict_pass, "informed_route_passes": informed_pass,
            "GQ_folding_potential_route": track in NEW_ENCODER_TRACKS, "passes": informed_pass and track in NEW_ENCODER_TRACKS,
            "checks": checks, "incremental_comparisons": incremental, "macro_regret": float(regrets.mean()),
            "macro_gain_vs_simple": float(gains.mean()), "macro_gain_vs_H0": float(gains_h0.mean()), "max_positive_gain_share": share,
            "gain_ci": [float(np.quantile(bootstrap, .025)), float(np.quantile(bootstrap, .975))],
            "per_assay": [{"dataset": study, "regret": float(regrets[index]), "gain_vs_simple": float(gains[index]),
                "gain_vs_H0": float(gains_h0[index]), "avoidable_wrong": float(comp.loc[study].avoidable_wrong)} for index, study in enumerate(STUDIES)]})
    csvsave(ART / "model_comparison.csv", pd.concat([pd.read_csv(OUT / track / "comparison.csv", float_precision="round_trip") for track in TRACKS], ignore_index=True))
    csvsave(ART / "decision_metrics.csv.gz", pd.concat(all_decisions, ignore_index=True), True)
    jsave(OUT / "gate_verdict.json", {"status": "DEVELOPMENT_GO" if any(result["passes"] for result in results) else "NO-GO",
        "tracks": results, "prefit_manifest_sha256": sha256(OUT / "prefit_manifest.json"),
        "verification_receipt_sha256": sha256(OUT / "verification_receipt.json"),
        "criteria_changed_after_results": False, "independent_confirmation": False, "observed_data_followup": True,
        "GQ_folding_potential_claim_requires": NEW_ENCODER_TRACKS, "shared_structure_result_is_new_independent_evidence": False,
        "approximate_global_GQ_metric_not_in_cell_occupancy": True, "SRLE46nt_junction_only": True,
        "no_local_GQ_occupancy_feature": True, "subsequent_endpoint_aligned_development": True,
        "controls": "All five independently refit under same source-only grid; no old checkpoint reuse or claim of new control evidence",
        "calibration": "Relative candidate utility only; GQ input is modeled folding potential, not calibrated localization probability, in-cell occupancy, biological mechanism or independent confirmation"})
    print(readj(OUT / "gate_verdict.json")["status"], flush=True)


if __name__ == "__main__":
    run()
