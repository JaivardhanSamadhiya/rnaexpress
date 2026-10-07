"""Independent canonical arithmetic and decisions, without refitting."""
from .common import *
from .evaluate import features, source_model, task_summary
from .splits import masks
from src.generalization_crosscell_20261007.routes import module
from src.generalization_rbp_20261007.canonical_inner_replay import canonical_scores, decision_table, decisions_equal
import os


def run():
    freeze_check()
    assert all(os.environ.get(v) == "1" for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"))
    assert readj(OUT / "evaluation_complete.json")["status"] == "PASS"
    frame = load(True); max_error, models, choices, crossed_models = 0., 0, 0, 0
    for track in TRACKS:
        x = features(track)
        p = pd.read_csv(OUT / track / "predictions.csv.gz", float_precision="round_trip")
        d = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip")
        old_p = pd.read_csv(SOURCE_OUT / track / "predictions.csv.gz", float_precision="round_trip")
        old_d = pd.read_csv(SOURCE_OUT / track / "decisions.csv", float_precision="round_trip")
        assert len(p) == len(frame) and p.intervention_id.is_unique and set(p.intervention_id) == set(frame.intervention_id)
        assert set(p.track) == set(d.model) == {track}
        assert len(old_p) == len(frame) and old_p.intervention_id.is_unique and set(old_p.intervention_id) == set(frame.intervention_id)
        assert set(old_p.track) == set(old_d.model) == {track}
        assert not old_d.duplicated(["task", "gene_fold", "parent_context_id", "direction"]).any()
        assert not d.duplicated(["task", "gene_fold", "parent_context_id", "direction"]).any()
        roster = readj(OUT / track / "roster.json")
        assert len(roster) == 6 and {(r["task"], r["fold"]) for r in roster} == {(t, f) for t in TASKS for f in FOLDS}
        for task in TASKS:
            for fold in FOLDS:
                model, config, test, path = source_model(track, task, fold, frame, x)
                target = frame.loc[test].reset_index(drop=True)
                score, arithmetic_error = canonical_scores(model, x, np.flatnonzero(test), module(track).predict_model)
                saved = p[p.task.eq(task) & p.gene_fold.eq(fold)].set_index("intervention_id").loc[target.intervention_id]
                assert set(saved.configuration) == {config["id"]}
                error = float(np.max(np.abs(score - saved.score.to_numpy(float)))); assert error <= 1e-9
                max_error = max(max_error, error, arithmetic_error)
                expected = decision_table(target, score)
                decisions_equal(expected, d[d.task.eq(task) & d.gene_fold.eq(fold)])
                # The old source replay has no final result SHA map. Verify
                # current crossed arrays using this exact same checkpoint.
                _, _, opposite = masks(frame, task, fold)
                old_target = frame.loc[opposite].reset_index(drop=True)
                old_score, old_error = canonical_scores(model, x, np.flatnonzero(opposite), module(track).predict_model)
                archived = old_p[old_p.task.eq(TASKS[task][1]) & old_p.gene_fold.eq(fold)].set_index("intervention_id").loc[old_target.intervention_id]
                assert set(archived.configuration) == {config["id"]}
                archived_error = float(np.max(np.abs(old_score - archived.score.to_numpy(float)))); assert archived_error <= 1e-9
                max_error = max(max_error, old_error, archived_error)
                old_expected = decision_table(old_target, old_score)
                decisions_equal(old_expected, old_d[old_d.task.eq(TASKS[task][1]) & old_d.gene_fold.eq(fold)])
                crossed_models += 1
                entry = next(r for r in roster if r["task"] == task and r["fold"] == fold)
                assert entry["configuration"] == config and entry["source_checkpoint_sha256"] == sha256(path)
                assert entry["source_task"] == TASKS[task][1]
                assert entry["source_checkpoint"] == path.relative_to(ROOT).as_posix()
                assert entry["target_ids_sha256"] == rowhash(target) and entry["target_rows"] == len(target)
                models += 1; choices += len(expected)
        current = task_summary(d).sort_values("task").reset_index(drop=True)
        archived = pd.read_csv(OUT / track / "comparison.csv", float_precision="round_trip").sort_values("task").reset_index(drop=True)
        pd.testing.assert_frame_equal(current, archived, check_exact=False, atol=1e-12, rtol=0)
        del x
    assert models == crossed_models == 42
    jsave(OUT / "verification_receipt.json", {"status": "PASS", "predictors_checked": models,
        "decisions_checked": choices, "maximum_score_error": max_error, "new_fits": 0,
        "source_configuration_unchanged": True, "same_cell_exact_allele_purge_checked": True,
        "canonical_full_target_ties_preserved": True, "evaluation_manifest_sha256": sha256(OUT / "evaluation_manifest.json"),
        "crossed_state_predictors_rechecked": crossed_models, "same_checkpoint_both_states_verified": True,
        "result_files": {p.relative_to(ROOT).as_posix(): sha256(p) for track in TRACKS for p in (OUT / track).rglob("*") if p.is_file()},
        "independent_confirmation": False})


if __name__ == "__main__": run()
