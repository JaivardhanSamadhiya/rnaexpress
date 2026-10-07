"""Fixed-sign nested source-only ranking; immutable checkpoint identities."""
from .common import *
from .routes import configurations, endpoint_sign, fit_model, predict_model
from src.cross_assay_20260927.models import purge
import os, sys


def features(track):
    assert track in TRACKS
    with np.load(NEXT_ART / (track + "_model_features.npz"), allow_pickle=False) as archive:
        matrix = archive["features"].astype(float)
    assert matrix.shape == (26258, SHAPES[track]) and np.isfinite(matrix).all()
    return matrix


def checkpoint_identity(frame, config, track):
    return {"_training_ids_sha256":rowhash(frame), "_training_identity_sha256":identity_hash(frame),
            "_training_original_label_sha256":label_hash(frame.measured_delta),
            "_training_aligned_label_sha256":label_hash(frame.measured_delta.to_numpy(float) * endpoint_sign(frame)),
            "_training_studies":sorted(frame.dataset.unique()),
            "_training_components":sorted(frame.biological_component.unique()),
            "_configuration":config, "_track":track,
            "_prefit_manifest_sha256":sha256(OUT / "prefit_manifest.json")}


def validate_checkpoint(result, frame, config, track):
    for key, value in checkpoint_identity(frame, config, track).items():
        assert result[key] == value, key
    assert result["alignment_track"] == track and result["config"] == config
    assert result["training_original_label_sha256"] == result["_training_original_label_sha256"]
    assert result["training_aligned_label_sha256"] == result["_training_aligned_label_sha256"]
    assert len(result["beta"]) == SHAPES[track]


def checkpoint(track, name, frame, matrix, config):
    path = OUT / track / "fits" / (name + "_" + config["id"] + ".json")
    if path.exists():
        result = readj(path); validate_checkpoint(result, frame, config, track)
        return result
    result = fit_model(frame, matrix, config, track)
    result.update(checkpoint_identity(frame, config, track))
    validate_checkpoint(result, frame, config, track)
    jsave(path, result)
    return result


def selected_config(configs, values):
    minimum = min(values)
    return next(config for config, value in zip(configs, values) if value <= minimum + 1e-12)


def run(track):
    freeze_check()
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == "1"
    assert track in TRACKS and not (OUT / track / "run_complete.json").exists()
    frame, matrix, configs = load(), features(track), configurations(track)
    predictions, choices, folds, selections = [], [], [], []
    for held in STUDIES:
        test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
        source, source_x = frame.loc[train].reset_index(drop=True), matrix[train]
        values = []
        for config in configs:
            regrets = []
            for inner in sorted(source.dataset.unique()):
                validation = source.dataset.eq(inner).to_numpy()
                permitted = purge(source, ~validation, validation)
                tr, va = source.loc[permitted].reset_index(drop=True), source.loc[validation].reset_index(drop=True)
                assert not {held, inner} & set(tr.dataset)
                fitted = checkpoint(track, held + "__inner__" + inner, tr, source_x[permitted], config)
                regret = inner_regret(va, predict_model(fitted, source_x[validation], va)); regrets.append(regret)
                selections.append({"outer_held":held, "inner_held":inner, "configuration":config["id"],
                    "regret":regret, "training_rows":len(tr), "validation_rows":len(va),
                    "training_ids_sha256":rowhash(tr), "training_original_label_sha256":label_hash(tr.measured_delta),
                    "training_aligned_label_sha256":label_hash(tr.measured_delta.to_numpy(float) * endpoint_sign(tr))})
            values.append(float(np.mean(regrets)))
            print("alignment", track, held, config["id"], "inner complete", flush=True)
        config = selected_config(configs, values)
        fitted = checkpoint(track, held + "__outer", source, source_x, config)
        target = frame.loc[test].reset_index(drop=True)
        score = predict_model(fitted, matrix[test], target)
        choices.append(decisions(target, score, track))
        predictions.extend({"track":track, "dataset":held, "intervention_id":row.intervention_id,
                            "score":float(score[index]), "configuration":config["id"]}
                           for index, row in enumerate(target.itertuples()))
        folds.append({"held":held, "selected_configuration":config,
                      "all_inner_scores":dict(zip([c["id"] for c in configs], values)),
                      "training_ids_sha256":rowhash(source), "test_ids_sha256":rowhash(target),
                      "training_components":sorted(source.biological_component.unique()), "test_rows":len(target)})
        print("alignment", track, held, "outer complete", flush=True)
    selected = pd.concat(choices, ignore_index=True)
    csvsave(OUT / track / "decisions.csv", selected)
    csvsave(OUT / track / "predictions.csv.gz", pd.DataFrame(predictions), True)
    csvsave(OUT / track / "inner_selection.csv", pd.DataFrame(selections))
    csvsave(OUT / track / "comparison.csv", summary(selected))
    jsave(OUT / track / "folds.json", folds)
    count = len(list((OUT / track / "fits").glob("*.json")))
    assert count == 40 and len(predictions) == 26258
    jsave(OUT / track / "run_complete.json", {"status":"PASS", "track":track, "fit_files":count,
        "prediction_rows":len(predictions), "decision_rows":len(selected),
        "prefit_manifest_sha256":sha256(OUT / "prefit_manifest.json"), "observed_data_followup":True,
        "outer_target_selection":False, "sign_selected_from_outcomes":False, "independent_confirmation":False})


if __name__ == "__main__":
    run(sys.argv[1])
