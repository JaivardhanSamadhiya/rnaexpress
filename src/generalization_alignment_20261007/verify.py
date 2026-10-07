"""Replay every nested checkpoint on original truth; no fitting/selection."""
from .common import *
from .engine import features, validate_checkpoint, selected_config
from .routes import configurations, predict_model
from src.cross_assay_20260927.models import purge


def independent_decisions(frame, score):
    assert len(frame) == len(score) and np.isfinite(score).all()
    records = []
    value = frame.assign(_score=np.asarray(score))
    for context, group in value.groupby("parent_context_id", sort=True):
        low, high = float(group.measured_delta.min()), float(group.measured_delta.max())
        assert high > low
        for direction in (-1, 1):
            chosen = group.assign(_utility=direction * group._score).sort_values(
                ["_utility", "intervention_id"], ascending=[False, True]).iloc[0]
            best = high if direction == 1 else -low
            effect = direction * float(chosen.measured_delta)
            records.append({"dataset":chosen.dataset, "biological_component":chosen.biological_component,
                            "parent_context_id":context, "direction":direction, "selected_id":chosen.intervention_id,
                            "regret":(best - effect) / (high - low), "wrong_direction":float(effect < -1e-12),
                            "avoidable_wrong":float(effect < -1e-12 and best > 1e-12)})
    return pd.DataFrame(records)


def independent_regret(frame, score):
    d = independent_decisions(frame, score)
    return float(d.groupby(["dataset", "biological_component"]).regret.mean().groupby("dataset").mean().mean())


def run():
    freeze_check()
    from src.generalization_next_20261007.common import freeze_check as next_freeze
    next_freeze()
    frame = load(); inner_count, outer_count, decisions_count, errors = 0, 0, 0, []
    srle_identities = []
    for track in TRACKS:
        x, configs = features(track), configurations(track)
        pred = pd.read_csv(OUT / track / "predictions.csv.gz", float_precision="round_trip")
        saved_d = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip")
        inner_rows = pd.read_csv(OUT / track / "inner_selection.csv", float_precision="round_trip")
        folds = readj(OUT / track / "folds.json")
        assert len(pred) == 26258 and pred.intervention_id.is_unique and set(pred.intervention_id) == set(frame.intervention_id)
        assert len(folds) == 4 and {row["held"] for row in folds} == set(STUDIES)
        for fold in folds:
            held = fold["held"]; test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
            source, target = frame.loc[train].reset_index(drop=True), frame.loc[test].reset_index(drop=True)
            source_x = x[train]
            assert rowhash(source) == fold["training_ids_sha256"] and rowhash(target) == fold["test_ids_sha256"]
            assert not set(source.biological_component) & set(target.biological_component)
            values = []
            for config in configs:
                regrets = []
                for inner in sorted(source.dataset.unique()):
                    validation = source.dataset.eq(inner).to_numpy(); permitted = purge(source, ~validation, validation)
                    tr, va = source.loc[permitted].reset_index(drop=True), source.loc[validation].reset_index(drop=True)
                    model = readj(OUT / track / "fits" / (held + "__inner__" + inner + "_" + config["id"] + ".json"))
                    validate_checkpoint(model, tr, config, track)
                    assert not {held, inner} & set(model["_training_studies"])
                    regret = independent_regret(va, predict_model(model, source_x[validation], va)); regrets.append(regret)
                    row = inner_rows[inner_rows.outer_held.eq(held) & inner_rows.inner_held.eq(inner) & inner_rows.configuration.eq(config["id"])]
                    assert len(row) == 1 and abs(float(row.iloc[0].regret) - regret) < 1e-12
                    assert row.iloc[0].training_ids_sha256 == model["_training_ids_sha256"]
                    assert row.iloc[0].training_original_label_sha256 == model["_training_original_label_sha256"]
                    assert row.iloc[0].training_aligned_label_sha256 == model["_training_aligned_label_sha256"]
                    inner_count += 1
                values.append(float(np.mean(regrets)))
                assert abs(values[-1] - fold["all_inner_scores"][config["id"]]) < 1e-12
            selected = selected_config(configs, values)
            assert selected == fold["selected_configuration"]
            model = readj(OUT / track / "fits" / (held + "__outer_" + selected["id"] + ".json"))
            validate_checkpoint(model, source, selected, track)
            assert held not in model["_training_studies"]
            score = predict_model(model, x[test], target)
            saved = pred[pred.dataset.eq(held)].set_index("intervention_id").loc[target.intervention_id]
            assert set(saved.configuration) == {selected["id"]}
            error = float(np.max(np.abs(saved.score.to_numpy() - score))); errors.append(error)
            assert error < 1e-9
            expected = independent_decisions(target, score).set_index(["parent_context_id", "direction"])
            recorded = saved_d[saved_d.dataset.eq(held)].set_index(["parent_context_id", "direction"])
            assert set(recorded.index) == set(expected.index)
            recorded = recorded.loc[expected.index]
            assert np.array_equal(expected.selected_id, recorded.selected_id)
            for metric in ("regret", "wrong_direction", "avoidable_wrong"):
                np.testing.assert_allclose(expected[metric], recorded[metric], atol=1e-12, rtol=0)
            decisions_count += len(recorded); outer_count += 1
            if held == "srle":
                control_fold = next(row for row in readj(NEXT_OUT / track / "folds.json") if row["held"] == held)
                assert selected == control_fold["selected_configuration"]
                control = readj(NEXT_OUT / track / "fits" / (held + "__outer_" + selected["id"] + ".json"))
                assert control["_training_ids_sha256"] == rowhash(source)
                for key in ("beta", "mean", "scale", "active", "pair_rms"):
                    np.testing.assert_array_equal(control[key], model[key])
                from src.generalization_20261007.route_scaling import predict_model as unflipped_predict
                np.testing.assert_array_equal(score, -unflipped_predict(control, x[test]))
                srle_identities.append(track)
        np.testing.assert_allclose(saved_d.wrong_direction, saved_d.avoidable_wrong + saved_d.unavoidable_wrong + saved_d.neutral_only_alternative_wrong, atol=1e-12, rtol=0)
        assert len(list((OUT / track / "fits").glob("*.json"))) == 40
        stored = pd.read_csv(OUT / track / "comparison.csv").sort_values("dataset").reset_index(drop=True)
        replay = summary(saved_d).sort_values("dataset").reset_index(drop=True)
        pd.testing.assert_frame_equal(stored, replay, check_exact=False, atol=1e-12, rtol=0)
        print("Alignment independent inner+outer replay", track, "PASS", flush=True)
    assert inner_count == 216 and outer_count == 24
    jsave(OUT / "verification_receipt.json", {"status":"PASS", "checkpoints":inner_count + outer_count,
        "inner_original_truth_regrets_replayed":inner_count, "outer_targets_replayed":outer_count,
        "candidate_scores_replayed":26258 * 6, "selected_decisions_checked":decisions_count,
        "maximum_outer_score_error":max(errors), "original_allele_and_label_hashes_checked":True,
        "aligned_label_hashes_checked":True, "source_only_configurations_reselected_from_replay":True,
        "held_SRLE_exact_unflipped_model_inversion_tracks":srle_identities,
        "verification_source_sha256":sha256(Path(__file__)), "models_fit":0, "independent_confirmation":False})


if __name__ == "__main__":
    run()
