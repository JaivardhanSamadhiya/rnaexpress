"""Two standalone source-only tracks; original controls are certified reuse."""
import os
import sys
from .common import *
from .routes import module
from src.cross_assay_20260927.models import purge


def features(track):
    assert track in TRACKS
    receipt = readj(OUT / "input_receipt.json")
    name = receipt["feature_paths"][track]
    assert sha256(ROOT / name) == receipt["files"][name]
    with np.load(ROOT / name, allow_pickle=False) as data:
        assert data.files == ["features"]
        values = np.asarray(data["features"], dtype=float)
    assert values.shape == (26258, SHAPES[track]) and np.isfinite(values).all()
    return values


def checkpoint_identity(track, frame, matrix, config, source_feature_sha, prefit_sha, core_sha):
    return {"track": track, "training_ids_sha256": rowhash(frame),
        "training_metadata_sha256": metadata_identity(frame), "training_labels_sha256": label_hash(frame.measured_delta),
        "training_feature_values_sha256": matrix_hash(matrix), "source_feature_npz_sha256": source_feature_sha,
        "source_core_sha256": core_sha, "prefit_manifest_sha256": prefit_sha, "configuration": config,
        "training_studies": sorted(frame.dataset.unique().tolist()), "training_components": sorted(frame.biological_component.unique().tolist()),
        "training_rows": len(frame), "feature_columns": matrix.shape[1], "numerical_threads": 1,
        "fitter_source_sha256": sha256(ROOT / "src/generalization_20261007/route_scaling.py"),
        "solver_source_sha256": sha256(ROOT / "src/cross_assay_20260927/models.py"),
        "original_truth_untransformed": True}


def checkpoint(track, name, frame, matrix, config, source_feature_sha, prefit_sha, core_sha):
    path = OUT / track / "fits" / (name + "_" + config["id"] + ".json")
    sidecar = path.with_suffix(".sha256")
    identity = checkpoint_identity(track, frame, matrix, config, source_feature_sha, prefit_sha, core_sha)
    if path.exists():
        assert sidecar.exists() and sidecar.read_text().strip() == sha256(path), "Checkpoint bytes changed or have no creation-time digest"
        result = readj(path)
        assert result["_identity"] == identity, "Checkpoint training labels/features/config/freeze changed"
        assert result["config"] == config and result["training_rows"] == len(frame)
        return result
    assert not sidecar.exists(), "Preserve orphan checkpoint digest"
    result = module(track).fit_model(frame, matrix, config)
    result["_identity"] = identity
    jsave(path, result)
    save(sidecar, (sha256(path) + "\n").encode())
    return result


def select_config(configs, values):
    assert len(configs) == len(values) and len(values) == 3 and np.isfinite(values).all()
    best = min(values)
    return next(config for config, value in zip(configs, values) if value <= best + 1e-12)


def run(track):
    assert track in TRACKS
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == "1"
    manifest = freeze_check(); receipt = input_check()
    assert manifest["control_fitting_policy"] == "REUSE_THREE_RBP_FIT_TWO_NEW_TRACKS"
    from .control_reuse import check as control_check
    control = control_check()
    assert control["original_labels_sha256"] == manifest["original_labels_sha256"]
    assert not (OUT / track / "run_complete.json").exists(), "Preserve completed track"
    frame = load(); matrix = features(track); mod = module(track)
    assert label_hash(frame.measured_delta) == manifest["original_labels_sha256"]
    prefit_sha = sha256(OUT / "prefit_manifest.json"); core_sha = sha256(CORE)
    source_feature_sha = receipt["files"][receipt["feature_paths"][track]]
    predictions, choices, folds, selections = [], [], [], []
    for held in STUDIES:
        test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
        source = frame.loc[train].reset_index(drop=True); source_x = matrix[train]
        values = []
        for config in mod.CONFIGS:
            source_regrets = []
            for inner in sorted(source.dataset.unique()):
                validation = source.dataset.eq(inner).to_numpy(); inner_train = purge(source, ~validation, validation)
                tr = source.loc[inner_train].reset_index(drop=True); va = source.loc[validation].reset_index(drop=True)
                assert held not in set(tr.dataset) and inner not in set(tr.dataset)
                fitted = checkpoint(track, held + "__inner__" + inner, tr, source_x[inner_train], config,
                    source_feature_sha, prefit_sha, core_sha)
                regret = inner_regret(va, mod.predict_model(fitted, source_x[validation]))
                source_regrets.append(regret)
                selections.append({"outer_held": held, "inner_held": inner, "configuration": config["id"], "regret": regret,
                    "training_rows": len(tr), "validation_rows": len(va), "training_ids_sha256": rowhash(tr),
                    "training_labels_sha256": label_hash(tr.measured_delta), "validation_ids_sha256": rowhash(va),
                    "validation_labels_sha256": label_hash(va.measured_delta)})
            assert len(source_regrets) == 3
            values.append(float(np.mean(source_regrets)))
            print(track, held, config["id"], "inner complete", flush=True)
        config = select_config(mod.CONFIGS, values)
        fitted = checkpoint(track, held + "__outer", source, source_x, config, source_feature_sha, prefit_sha, core_sha)
        target = frame.loc[test].reset_index(drop=True)
        score = mod.predict_model(fitted, matrix[test]); choices.append(decisions(target, score, track))
        predictions.extend({"track": track, "dataset": held, "intervention_id": row.intervention_id,
            "score": float(score[index]), "configuration": config["id"]} for index, row in enumerate(target.itertuples()))
        folds.append({"held": held, "selected_configuration": config,
            "all_inner_scores": dict(zip([value["id"] for value in mod.CONFIGS], values)),
            "inner_macro_regret": values[mod.CONFIGS.index(config)], "training_identity": fitted["_identity"],
            "test_ids_sha256": rowhash(target), "test_metadata_sha256": metadata_identity(target),
            "test_labels_sha256": label_hash(target.measured_delta), "test_rows": len(target)})
        print(track, held, "outer complete", flush=True)
    selected = pd.concat(choices, ignore_index=True)
    csvsave(OUT / track / "decisions.csv", selected)
    csvsave(OUT / track / "predictions.csv.gz", pd.DataFrame(predictions), True)
    csvsave(OUT / track / "inner_selection.csv", pd.DataFrame(selections))
    csvsave(OUT / track / "comparison.csv", summary(selected)); jsave(OUT / track / "folds.json", folds)
    assert len(list((OUT / track / "fits").glob("*.json"))) == 40
    jsave(OUT / track / "run_complete.json", {"status": "PASS", "track": track, "fit_files": 40,
        "prefit_manifest_sha256": prefit_sha, "prediction_rows": len(predictions), "decision_rows": len(selected),
        "standalone_fits": True, "reused_checkpoints": 0, "independent_confirmation": False, "outer_target_selection": False})


if __name__ == "__main__":
    assert len(sys.argv) == 2
    run(sys.argv[1])
