"""Score held genes in the represented cell using unchanged old predictors."""
from .common import *
from .splits import masks
from src.generalization_crosscell_20261007.routes import module
from src.generalization_crosscell_20261007.verify import check_model
import os, sys


def features(track):
    with np.load(SOURCE_ART / (track + "_model_features.npz"), allow_pickle=False) as archive:
        assert archive.files == ["features"]
        x = archive["features"].astype(float)
    assert x.shape == (13781, WIDTHS[track]) and np.isfinite(x).all()
    return x


def select_source(configs, values):
    assert len(configs) == len(values) and np.isfinite(values).all()
    minimum = min(values)
    return next(config for config, value in zip(configs, values) if value <= minimum + 1e-12)


def source_model(track, task, fold, frame, x):
    """Validate original source-only selection and complete checkpoint inputs."""
    source_task = TASKS[task][1]
    roster = readj(SOURCE_OUT / track / "folds.json")
    assert len(roster) == 6 and {(r["task"], r["fold"]) for r in roster} == {(t, f) for _, t in TASKS.values() for f in FOLDS}
    info = next(r for r in roster if r["task"] == source_task and r["fold"] == fold)
    mod = module(track)
    rows = pd.read_csv(SOURCE_OUT / track / "source_selection.csv", float_precision="round_trip")
    values = []
    for config in mod.CONFIGS:
        row = rows[rows.task.eq(source_task) & rows.outer_fold.eq(fold) & rows.configuration.eq(config["id"])]
        assert len(row) == 1
        value = float(row.iloc[0].combined_source_oof_macro_regret)
        assert abs(value - info["all_source_oof_scores"][config["id"]]) < 1e-12
        values.append(value)
    config = select_source(mod.CONFIGS, values)
    assert config == info["selected_configuration"]
    train, test, opposite = masks(frame, task, fold)
    source = frame.loc[train].reset_index(drop=True)
    assert rowhash(source) == info["training_ids_sha256"]
    assert rowhash(frame.loc[opposite]) == info["test_ids_sha256"]
    path = SOURCE_OUT / track / "fits" / (source_task + "__fold" + str(fold) + "__outer_" + config["id"] + ".json")
    model = readj(path)
    # The original checkpoint binds IDs/parsed labels/configuration and the
    # original prefit. Matrices are bound by that prefit and our evaluation
    # manifest, rather than inventing absent creation-time checkpoint fields.
    check_model(model, source, config, track)
    return model, config, test, path


def task_summary(d):
    cols = ["regret", "wrong_direction", "avoidable_wrong", "pairwise_accuracy"]
    return d.groupby(["model", "task", "biological_component"])[cols].mean().groupby(["model", "task"]).mean().reset_index()


def run(root_start=False):
    assert root_start, "Root explicitly starts new evaluation after committing its freeze"
    freeze_check()
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"): assert os.environ.get(name) == "1"
    assert not (OUT / "evaluation_complete.json").exists()
    frame = load(True)
    for track in TRACKS:
        assert not (OUT / track / "complete.json").exists()
        x, predictions, all_decisions, rosters = features(track), [], [], []
        for task in TASKS:
            for fold in FOLDS:
                model, config, test, path = source_model(track, task, fold, frame, x)
                target = frame.loc[test].reset_index(drop=True)
                score = module(track).predict_model(model, x[test])
                d = decisions(target, score, track); d["task"] = task; d["gene_fold"] = fold
                all_decisions.append(d)
                predictions.extend({"track": track, "task": task, "gene_fold": fold,
                    "intervention_id": row.intervention_id, "score": float(score[i]), "configuration": config["id"]}
                    for i, row in enumerate(target.itertuples()))
                rosters.append({"task": task, "source_task": TASKS[task][1], "fold": fold,
                    "configuration": config, "source_checkpoint": path.relative_to(ROOT).as_posix(),
                    "source_checkpoint_sha256": sha256(path), "target_ids_sha256": rowhash(target), "target_rows": len(target)})
        assert len(predictions) == 13781 and len({r["intervention_id"] for r in predictions}) == 13781
        d = pd.concat(all_decisions, ignore_index=True)
        csvsave(OUT / track / "predictions.csv.gz", pd.DataFrame(predictions), True)
        csvsave(OUT / track / "decisions.csv", d)
        csvsave(OUT / track / "comparison.csv", task_summary(d))
        jsave(OUT / track / "roster.json", rosters)
        jsave(OUT / track / "complete.json", {"status": "PASS", "rows": 13781, "new_fits": 0,
            "evaluation_manifest_sha256": sha256(OUT / "evaluation_manifest.json")})
        print("Known-cell", track, "six fixed predictor evaluations complete; zero fits", flush=True)
        del x
    jsave(OUT / "evaluation_complete.json", {"status": "PASS", "tracks": TRACKS, "new_fits": 0,
        "reused_outer_predictors": 42, "evaluation_manifest_sha256": sha256(OUT / "evaluation_manifest.json"),
        "scope": "Gene generalization conditional on represented cell; same-data development"})


if __name__ == "__main__": run("--root-start" in sys.argv[1:])
