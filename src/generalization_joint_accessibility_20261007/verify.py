"""Independent nested score/choice/regret replay; never fit or tune."""
from .common import *
from .engine import features, checkpoint_identity, select_config
from .routes import module
from src.cross_assay_20260927.models import purge


ERROR_METRICS = ("regret", "wrong_direction", "avoidable_wrong", "no_feasible_candidate", "unavoidable_wrong", "neutral_only_alternative_wrong")


def independent_scores(model, matrix):
    """Column contribution sums, independently of the engine's BLAS scorer."""
    matrix = np.asarray(matrix, dtype=np.float64)
    beta, mean, scale = [np.asarray(model[name], dtype=np.float64) for name in ("beta", "mean", "scale")]
    assert matrix.ndim == 2 and beta.shape == mean.shape == scale.shape == (matrix.shape[1],)
    assert all(np.isfinite(value).all() for value in (matrix, beta, mean, scale)) and (scale > 0).all()
    coefficients = beta / scale
    scores = np.empty(len(matrix), dtype=np.float64)
    for first in range(0, len(matrix), 2048):
        block = matrix[first:first + 2048]
        scores[first:first + len(block)] = np.sum((block - mean) * coefficients, axis=1)
    assert np.isfinite(scores).all()
    return scores


def score_error(independent, actual):
    independent, actual = np.asarray(independent), np.asarray(actual)
    assert independent.shape == actual.shape and independent.ndim == 1 and len(independent)
    assert np.isfinite(independent).all() and np.isfinite(actual).all()
    error = float(np.max(np.abs(independent - actual)))
    assert error < 1e-9, "Shared/saved scorer does not reproduce independent model arithmetic"
    return error


def bounded_canonical_scores(model, matrix, predict):
    """Bound independent arithmetic, retain declared scorer for exact ties."""
    independent = independent_scores(model, matrix)
    canonical = np.asarray(predict(model, matrix), dtype=np.float64)
    error = score_error(independent, canonical)
    return canonical, independent, error


def pair_accuracy(truth, score):
    """Direct unordered-pair credit, ignoring truth ties; no Kendall helper."""
    numerator, denominator = 0., 0
    for first in range(len(truth) - 1):
        dy, ds = truth[first + 1:] - truth[first], score[first + 1:] - score[first]
        eligible = dy != 0
        products = np.sign(dy[eligible]) * np.sign(ds[eligible])
        numerator += float(np.sum((products + 1.) * .5)); denominator += int(eligible.sum())
    assert denominator > 0
    return numerator / denominator


def independent_decisions(frame, score, include_ranking=False):
    assert len(frame) == len(score) and np.isfinite(score).all()
    records = []; value = frame.assign(_score=np.asarray(score))
    for context, group in value.groupby("parent_context_id", sort=True):
        low, high = float(group.measured_delta.min()), float(group.measured_delta.max())
        assert high > low and group.intervention_id.is_unique
        accuracy = pair_accuracy(group.measured_delta.to_numpy(float), group._score.to_numpy(float)) if include_ranking else None
        for direction in (-1, 1):
            ordered = group.assign(_utility=direction * group._score).sort_values(["_utility", "intervention_id"], ascending=[False, True])
            chosen = ordered.iloc[0]
            best = high if direction == 1 else -low; effect = direction * float(chosen.measured_delta)
            truth = direction * group.measured_delta.to_numpy(float)
            feasible, wrong = bool((truth > 1e-12).any()), effect < -1e-12
            unavoidable = bool((truth < -1e-12).all())
            record = {"dataset": chosen.dataset, "biological_component": chosen.biological_component,
                "parent_context_id": context, "direction": direction, "selected_id": chosen.intervention_id,
                "candidates": len(group), "regret": (best - effect) / (high - low), "wrong_direction": float(wrong),
                "avoidable_wrong": float(wrong and feasible), "no_feasible_candidate": float(not feasible),
                "unavoidable_wrong": float(wrong and unavoidable),
                "neutral_only_alternative_wrong": float(wrong and not feasible and not unavoidable),
                "selected_effect": float(chosen.measured_delta), "selected_score": float(chosen._score),
                "best_recovery": float(effect == best), "top5_best_recovery": float((direction * ordered.head(5).measured_delta).max() == best)}
            if include_ranking:
                record["pairwise_accuracy"] = accuracy
            records.append(record)
    return pd.DataFrame(records)


def independent_regret(frame, score):
    d = independent_decisions(frame, score)
    return float(d.groupby(["dataset", "biological_component"]).regret.mean().groupby("dataset").mean().mean())


def assert_disjoint(training, target):
    assert not set(training.biological_component) & set(target.biological_component)
    training_alleles = set(training.parent_sequence) | set(training.mutant_sequence)
    target_alleles = set(target.parent_sequence) | set(target.mutant_sequence)
    assert not training_alleles & target_alleles


def checked_model(path, identity, config):
    path = Path(path)
    assert path.with_suffix(".sha256").read_text().strip() == sha256(path)
    model = readj(path)
    assert model["_identity"] == identity and model["config"] == config
    assert model["training_rows"] == identity["training_rows"]
    assert len(model["beta"]) == len(model["mean"]) == len(model["scale"]) == identity["feature_columns"]
    return model


def decisions_roster_check(saved, frame, track):
    assert set(saved.model) == {track} and set(saved.dataset) == set(STUDIES)
    fields = ["dataset", "parent_context_id", "direction"]
    assert not saved.duplicated(fields).any()
    expected = {(study, context, direction) for study, context in frame[["dataset", "parent_context_id"]].drop_duplicates().itertuples(index=False, name=None) for direction in (-1, 1)}
    actual = set(saved[fields].itertuples(index=False, name=None))
    assert actual == expected and len(saved) == len(expected), "Missing/extra/relabeled saved decisions"


def run():
    manifest = freeze_check(); receipt = input_check(); frame = load()
    from .control_reuse import check as control_check
    control = control_check()
    assert control["original_labels_sha256"] == label_hash(frame.measured_delta)
    prefit_sha = sha256(OUT / "prefit_manifest.json"); core_sha = sha256(CORE)
    assert label_hash(frame.measured_delta) == manifest["original_labels_sha256"]
    inner_count, outer_count, decision_count = 0, 0, 0
    inner_errors, outer_errors, saved_errors, independent_saved_errors = [], [], [], []
    inner_candidate_count = 0
    verified_files = {}
    for track in TRACKS:
        x = features(track); mod = module(track); configs = mod.CONFIGS
        complete = readj(OUT / track / "run_complete.json")
        assert complete["status"] == "PASS" and complete["track"] == track and complete["fit_files"] == 40
        assert complete["prediction_rows"] == 26258 and complete["prefit_manifest_sha256"] == prefit_sha
        assert complete["standalone_fits"] and complete["reused_checkpoints"] == 0
        pred = pd.read_csv(OUT / track / "predictions.csv.gz", float_precision="round_trip")
        saved_d = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip")
        decisions_roster_check(saved_d, frame, track)
        inner_rows = pd.read_csv(OUT / track / "inner_selection.csv", float_precision="round_trip")
        folds = readj(OUT / track / "folds.json")
        assert len(pred) == 26258 and pred.intervention_id.is_unique and set(pred.intervention_id) == set(frame.intervention_id)
        assert set(pred.track) == {track} and len(inner_rows) == 36
        assert len(folds) == 4 and {fold["held"] for fold in folds} == set(STUDIES)
        source_feature_sha = receipt["files"][receipt["feature_paths"][track]]
        for fold in folds:
            held = fold["held"]; test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
            source = frame.loc[train].reset_index(drop=True); source_x = x[train]; target = frame.loc[test].reset_index(drop=True)
            assert held not in set(source.dataset); assert_disjoint(source, target)
            assert fold["test_ids_sha256"] == rowhash(target) and fold["test_metadata_sha256"] == metadata_identity(target)
            assert fold["test_labels_sha256"] == label_hash(target.measured_delta) and fold["test_rows"] == len(target)
            values = []
            for config in configs:
                regrets = []
                for inner in sorted(source.dataset.unique()):
                    validation = source.dataset.eq(inner).to_numpy(); permitted = purge(source, ~validation, validation)
                    tr = source.loc[permitted].reset_index(drop=True); va = source.loc[validation].reset_index(drop=True)
                    assert not {held, inner} & set(tr.dataset); assert_disjoint(tr, va); assert_disjoint(tr, target)
                    identity = checkpoint_identity(track, tr, source_x[permitted], config, source_feature_sha, prefit_sha, core_sha)
                    model = checked_model(OUT / track / "fits" / (held + "__inner__" + inner + "_" + config["id"] + ".json"), identity, config)
                    score, independent, arithmetic_error = bounded_canonical_scores(model, source_x[validation], mod.predict_model)
                    inner_errors.append(arithmetic_error)
                    inner_candidate_count += len(va)
                    regret = independent_regret(va, score); regrets.append(regret)
                    row = inner_rows[inner_rows.outer_held.eq(held) & inner_rows.inner_held.eq(inner) & inner_rows.configuration.eq(config["id"])]
                    assert len(row) == 1; recorded = row.iloc[0]
                    assert abs(float(recorded.regret) - regret) < 1e-12
                    assert recorded.training_ids_sha256 == rowhash(tr) and recorded.validation_ids_sha256 == rowhash(va)
                    assert recorded.training_labels_sha256 == label_hash(tr.measured_delta)
                    assert recorded.validation_labels_sha256 == label_hash(va.measured_delta)
                    assert int(recorded.training_rows) == len(tr) and int(recorded.validation_rows) == len(va)
                    inner_count += 1
                assert len(regrets) == 3; values.append(float(np.mean(regrets)))
                assert abs(values[-1] - float(fold["all_inner_scores"][config["id"]])) < 1e-12
            selected = select_config(configs, values)
            assert selected == fold["selected_configuration"]
            assert abs(float(fold["inner_macro_regret"]) - values[configs.index(selected)]) < 1e-12
            identity = checkpoint_identity(track, source, source_x, selected, source_feature_sha, prefit_sha, core_sha)
            assert identity == fold["training_identity"]
            model = checked_model(OUT / track / "fits" / (held + "__outer_" + selected["id"] + ".json"), identity, selected)
            score, independent, arithmetic_error = bounded_canonical_scores(model, x[test], mod.predict_model)
            outer_errors.append(arithmetic_error)
            saved = pred[pred.dataset.eq(held)].set_index("intervention_id").loc[target.intervention_id]
            assert set(saved.configuration) == {selected["id"]}
            saved_errors.append(score_error(score, saved.score.to_numpy()))
            independent_saved_errors.append(score_error(independent, saved.score.to_numpy()))
            expected = independent_decisions(target, score, include_ranking=True).set_index(["parent_context_id", "direction"])
            recorded = saved_d[saved_d.dataset.eq(held)].set_index(["parent_context_id", "direction"])
            assert recorded.index.is_unique and set(recorded.index) == set(expected.index); recorded = recorded.loc[expected.index]
            assert np.array_equal(expected.selected_id, recorded.selected_id)
            assert np.array_equal(expected.dataset, recorded.dataset)
            assert np.array_equal(expected.biological_component, recorded.biological_component)
            for metric in ERROR_METRICS + ("candidates", "selected_effect", "best_recovery", "top5_best_recovery", "pairwise_accuracy"):
                np.testing.assert_allclose(expected[metric], recorded[metric], atol=1e-12, rtol=0)
            np.testing.assert_allclose(expected.selected_score, recorded.selected_score, atol=1e-9, rtol=0)
            decision_count += len(recorded); outer_count += 1
        np.testing.assert_allclose(saved_d.wrong_direction, saved_d.avoidable_wrong + saved_d.unavoidable_wrong + saved_d.neutral_only_alternative_wrong, atol=1e-12, rtol=0)
        assert len(list((OUT / track / "fits").glob("*.json"))) == 40
        stored = pd.read_csv(OUT / track / "comparison.csv", float_precision="round_trip").sort_values("dataset").reset_index(drop=True)
        replay = summary(saved_d).sort_values("dataset").reset_index(drop=True)
        pd.testing.assert_frame_equal(stored, replay, check_exact=False, atol=1e-12, rtol=0)
        assert complete["decision_rows"] == len(saved_d)
        for path in (OUT / track).rglob("*"):
            if path.is_file():
                verified_files[path.relative_to(ROOT).as_posix()] = sha256(path)
        print("Joint accessibility independent inner+outer replay", track, "PASS", flush=True)
    assert inner_count == 72 and outer_count == 8
    jsave(OUT / "verification_receipt.json", {"status": "PASS", "prefit_manifest_sha256": prefit_sha,
        "checkpoints": inner_count + outer_count, "inner_original_truth_regrets_replayed": inner_count,
        "outer_targets_replayed": outer_count, "candidate_scores_replayed": 26258 * len(TRACKS),
        "inner_candidate_scores_independently_recomputed": inner_candidate_count,
        "inner_prediction_scope": "No inner candidate arrays were saved; independent coefficient sums are bounded against canonical engine scorer; independently reconstructed original-truth regret uses canonical values to preserve exact ties and checks saved inner selections",
        "selected_decisions_checked": decision_count, "maximum_inner_score_error": max(inner_errors),
        "maximum_outer_arithmetic_score_error": max(outer_errors), "maximum_outer_score_error": max(saved_errors),
        "maximum_outer_independent_vs_saved_score_error": max(independent_saved_errors),
        "score_reconstruction": "Blocked column contribution sums from beta/mean/scale, independent of engine BLAS predictor",
        "exact_tie_choice_arithmetic": "Canonical engine scorer after independent formula bound, fixed before fits; alternative floating summation order does not redefine exact ties",
        "independent_error_classification_checked": list(ERROR_METRICS), "direct_pair_credit_and_recovery_checked": True,
        "checkpoint_creation_hashes_checked": True, "original_allele_label_feature_hashes_checked": True,
        "all_source_only_configurations_reselected_from_replay": True, "files": verified_files,
        "verification_source_sha256": sha256(Path(__file__)), "models_fit": 0, "independent_confirmation": False})


if __name__ == "__main__":
    run()
