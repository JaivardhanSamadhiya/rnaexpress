"""Additive canonical-shape nested replay; never fit or change models.

Run only after the target namespace's complete frozen fits exist. Independent
column sums bound the original full-validation predictor; canonical scores
retain the declared exact lexical tie semantics. Existing replay files remain
untouched, and this helper writes a distinct receipt.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import os

from .inner_replay import (
    np, pd, checked_model, ids_hash, reconstructed_purge, selected_index,
    check_checkpoint,
)

NAMESPACES = {
    "next": "generalization_next_20261007",
    "rbp": "generalization_rbp_20261007",
    "alignment": "generalization_alignment_20261007",
}
SCORE_ATOL, REGRET_ATOL, BATCH_ROWS = 1e-9, 1e-12, 1024


def canonical_scores(model, matrix, row_indices, predictor, signs=None,
                     batch_rows=BATCH_ROWS):
    """Call predictor once with the original complete validation shape.

    Only independent arithmetic is blocked. Repeated small predictor calls can
    change floating-point reduction order and must not redefine exact ties.
    """
    assert batch_rows > 0
    mean, scale, beta = checked_model(model, matrix.shape[1])
    row_indices = np.asarray(row_indices, dtype=int)
    assert row_indices.ndim == 1 and len(row_indices)
    full = np.asarray(matrix[row_indices], dtype=np.float64)
    assert full.ndim == 2 and np.isfinite(full).all()
    sign = np.ones(len(full)) if signs is None else np.asarray(signs, dtype=float)
    assert sign.shape == (len(full),) and np.isin(sign, [-1., 1.]).all()
    # The frozen engine uses an advanced-indexed float64 validation matrix.
    canonical = np.asarray(predictor(model, full), dtype=np.float64)
    assert canonical.shape == (len(full),) and np.isfinite(canonical).all()
    coefficients = beta / scale
    error = 0.
    for first in range(0, len(full), batch_rows):
        last = min(first + batch_rows, len(full))
        manual = np.sum((full[first:last] - mean) * coefficients, axis=1)
        manual *= sign[first:last]
        assert np.isfinite(manual).all()
        error = max(error, float(np.max(np.abs(manual - canonical[first:last]))))
    assert error <= SCORE_ATOL, "Independent formula differs from canonical full-shape scorer"
    return canonical, error


def decision_table(frame, score):
    """Independent lexical max/min choices and original-truth arithmetic."""
    frame = frame.reset_index(drop=True)
    score = np.asarray(score, dtype=float)
    assert score.shape == (len(frame),) and np.isfinite(score).all()
    records = []
    for context, group in frame.assign(_score=score).groupby("parent_context_id", sort=True):
        assert group.intervention_id.is_unique
        assert group.dataset.nunique() == group.biological_component.nunique() == 1
        group = group.sort_values("intervention_id", kind="stable")
        truth, utility = group.measured_delta.to_numpy(float), group._score.to_numpy(float)
        low, high = float(truth.min()), float(truth.max())
        assert np.isfinite(truth).all() and high > low and len(group) >= 2
        for direction in (-1, 1):
            index = int(np.argmax(direction * utility))
            chosen = group.iloc[index]
            oriented = direction * truth
            effect, best = float(oriented[index]), float(oriented.max())
            wrong = effect < -1e-12
            feasible, unavoidable = bool((oriented > 1e-12).any()), bool((oriented < -1e-12).all())
            records.append({"dataset": str(chosen.dataset), "biological_component": str(chosen.biological_component),
                "parent_context_id": str(context), "direction": direction, "selected_id": str(chosen.intervention_id),
                "regret": (best - effect) / (high - low), "wrong_direction": float(wrong),
                "avoidable_wrong": float(wrong and feasible), "no_feasible_candidate": float(not feasible),
                "unavoidable_wrong": float(wrong and unavoidable),
                "neutral_only_alternative_wrong": float(wrong and not feasible and not unavoidable)})
    assert records
    return pd.DataFrame(records)


def regret_from_decisions(decisions):
    return float(decisions.groupby(["dataset", "biological_component"]).regret.mean().groupby("dataset").mean().mean())


def choice_digest(decisions):
    ordered = decisions.sort_values(["dataset", "parent_context_id", "direction"])
    values = ordered[["dataset", "biological_component", "parent_context_id", "direction", "selected_id", "regret"]].values.tolist()
    return hashlib.sha256(json.dumps(values, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def decisions_equal(actual, expected):
    keys = ["parent_context_id", "direction"]
    assert not expected.duplicated(keys).any()
    actual, expected = [value.set_index(keys) for value in (actual, expected)]
    assert actual.index.is_unique and set(actual.index) == set(expected.index)
    expected = expected.loc[actual.index]
    for field in ("dataset", "biological_component", "selected_id"):
        assert np.array_equal(actual[field], expected[field]), field
    for field in ("regret", "wrong_direction", "avoidable_wrong", "no_feasible_candidate", "unavoidable_wrong", "neutral_only_alternative_wrong"):
        np.testing.assert_allclose(actual[field], expected[field], rtol=0, atol=REGRET_ATOL)


def run(mode):
    assert mode in NAMESPACES
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
        assert os.environ.get(variable) == "1", "Canonical replay requires original one-thread scoring"
    ns = NAMESPACES[mode]
    common = importlib.import_module("src." + ns + ".common")
    routes = importlib.import_module("src." + ns + ".routes")
    manifest = common.freeze_check()
    if mode == "alignment":
        importlib.import_module("src.generalization_next_20261007.common").freeze_check()
    loaded = common.load()
    frame = (loaded[0] if isinstance(loaded, tuple) else loaded).reset_index(drop=True)
    del loaded
    assert len(frame) == 26258 and frame.intervention_id.is_unique
    from src.cross_assay_20260927.models import purge as frozen_purge
    alignment_checkpoint = None
    if mode == "alignment":
        alignment_checkpoint = importlib.import_module("src." + ns + ".engine").validate_checkpoint
    records, selections, outer_records, files = [], [], [], {}
    maximum_error = 0.
    prefit_sha = common.sha256(common.OUT / "prefit_manifest.json")
    for track in common.TRACKS:
        complete_path = common.OUT / track / "run_complete.json"
        complete = common.readj(complete_path)
        assert complete["status"] == "PASS" and complete["track"] == track
        assert complete["fit_files"] == 40 and complete["prediction_rows"] == 26258
        assert complete["prefit_manifest_sha256"] == prefit_sha
        path = (common.NEXT_ART if mode == "alignment" else common.ART) / (track + "_model_features.npz")
        relative = path.relative_to(common.ROOT).as_posix()
        assert common.sha256(path) == manifest["files"][relative]
        with np.load(path, allow_pickle=False) as archive:
            assert archive.files == ["features"]
            matrix = archive["features"].astype(float)
        assert len(matrix) == len(frame) and np.isfinite(matrix).all()
        mod = routes if mode == "alignment" else routes.module(track)
        configs = routes.configurations(track) if mode == "alignment" else mod.CONFIGS
        stored_path = common.OUT / track / "inner_selection.csv"
        stored = pd.read_csv(stored_path, float_precision="round_trip")
        assert len(stored) == 36 and not stored.duplicated(["outer_held", "inner_held", "configuration"]).any()
        pred_path = common.OUT / track / "predictions.csv.gz"
        pred = pd.read_csv(pred_path, float_precision="round_trip")
        assert len(pred) == len(frame) and pred.intervention_id.is_unique
        assert set(pred.intervention_id) == set(frame.intervention_id) and set(pred.track) == {track}
        decisions_path = common.OUT / track / "decisions.csv"
        saved_decisions = pd.read_csv(decisions_path, float_precision="round_trip")
        folds_path = common.OUT / track / "folds.json"
        folds = common.readj(folds_path)
        assert len(folds) == 4 and {fold["held"] for fold in folds} == set(common.STUDIES)
        for held in common.STUDIES:
            test = frame.dataset.eq(held).to_numpy()
            allowed = reconstructed_purge(frame, ~test, test)
            np.testing.assert_array_equal(allowed, frozen_purge(frame, ~test, test))
            source_indices = np.flatnonzero(allowed)
            source, target = [frame.loc[mask].reset_index(drop=True) for mask in (allowed, test)]
            assert len(set(source.dataset)) == 3 and held not in set(source.dataset)
            values = []
            for config in configs:
                regrets = []
                for inner in sorted(source.dataset.unique()):
                    validation = source.dataset.eq(inner).to_numpy()
                    permitted = reconstructed_purge(source, ~validation, validation)
                    np.testing.assert_array_equal(permitted, frozen_purge(source, ~validation, validation))
                    training, va = [source.loc[mask].reset_index(drop=True) for mask in (permitted, validation)]
                    fit_path = common.OUT / track / "fits" / (held + "__inner__" + inner + "_" + config["id"] + ".json")
                    model = common.readj(fit_path)
                    if mode == "alignment":
                        alignment_checkpoint(model, training, config, track)
                        signs = routes.endpoint_sign(va)
                        predictor = lambda m, x: routes.predict_model(m, x, va)
                    else:
                        check_checkpoint(model, training, config, (held, inner))
                        signs, predictor = None, mod.predict_model
                    assert not {held, inner} & set(model["_training_studies"])
                    score, error = canonical_scores(model, matrix, source_indices[validation], predictor, signs)
                    maximum_error = max(maximum_error, error)
                    decisions = decision_table(va, score)
                    regret = regret_from_decisions(decisions); regrets.append(regret)
                    row = stored[stored.outer_held.eq(held) & stored.inner_held.eq(inner) & stored.configuration.eq(config["id"])]
                    assert len(row) == 1
                    record = row.iloc[0]
                    assert abs(regret - float(record.regret)) <= REGRET_ATOL
                    assert record.training_ids_sha256 == ids_hash(training)
                    assert int(record.training_rows) == len(training) and int(record.validation_rows) == len(va)
                    if mode == "alignment":
                        assert record.training_original_label_sha256 == model["_training_original_label_sha256"]
                        assert record.training_aligned_label_sha256 == model["_training_aligned_label_sha256"]
                    records.append({"track": track, "outer_held": held, "inner_held": inner, "configuration": config["id"],
                        "training_ids_sha256": ids_hash(training), "validation_ids_sha256": ids_hash(va),
                        "regret": regret, "decisions": len(decisions), "choice_sha256": choice_digest(decisions),
                        "independent_arithmetic_max_error": error, "checkpoint_sha256": common.sha256(fit_path)})
                    files[fit_path.relative_to(common.ROOT).as_posix()] = common.sha256(fit_path)
                assert len(regrets) == 3
                values.append(float(np.mean(regrets)))
            selected = configs[selected_index(values)]
            fold = next(fold for fold in folds if fold["held"] == held)
            assert fold["selected_configuration"] == selected
            assert set(fold["all_inner_scores"]) == {config["id"] for config in configs}
            for config, value in zip(configs, values):
                assert abs(value - fold["all_inner_scores"][config["id"]]) <= REGRET_ATOL
            if mode != "alignment":
                assert abs(values[configs.index(selected)] - fold["inner_macro_regret"]) <= REGRET_ATOL
                assert fold["training_studies"] == sorted(source.dataset.unique())
            assert fold["training_ids_sha256"] == ids_hash(source) and fold["test_ids_sha256"] == ids_hash(target)
            assert fold["training_components"] == sorted(source.biological_component.unique())
            assert int(fold["test_rows"]) == len(target)
            outer_path = common.OUT / track / "fits" / (held + "__outer_" + selected["id"] + ".json")
            model = common.readj(outer_path)
            if mode == "alignment":
                alignment_checkpoint(model, source, selected, track)
                signs = routes.endpoint_sign(target)
                predictor = lambda m, x: routes.predict_model(m, x, target)
            else:
                check_checkpoint(model, source, selected, (held,))
                signs, predictor = None, mod.predict_model
            assert held not in set(model["_training_studies"])
            score, error = canonical_scores(model, matrix, np.flatnonzero(test), predictor, signs)
            maximum_error = max(maximum_error, error)
            saved = pred[pred.dataset.eq(held)].set_index("intervention_id").loc[target.intervention_id]
            assert set(saved.configuration) == {selected["id"]}
            saved_error = float(np.max(np.abs(score - saved.score.to_numpy(float))))
            assert saved_error <= SCORE_ATOL
            decisions = decision_table(target, score)
            decisions_equal(decisions, saved_decisions[saved_decisions.dataset.eq(held)])
            outer_records.append({"track": track, "held": held, "independent_arithmetic_max_error": error,
                "saved_score_max_error": saved_error, "choices": len(decisions), "choice_sha256": choice_digest(decisions)})
            files[outer_path.relative_to(common.ROOT).as_posix()] = common.sha256(outer_path)
            selections.append({"track": track, "held": held, "selected_configuration": selected,
                "recomputed_inner_means": dict(zip([config["id"] for config in configs], values))})
            print(mode, track, held, "canonical-shape inner+outer replay PASS", flush=True)
        assert len(list((common.OUT / track / "fits").glob("*.json"))) == 40
        for value in (path, stored_path, pred_path, decisions_path, folds_path, complete_path):
            files[value.relative_to(common.ROOT).as_posix()] = common.sha256(value)
        del matrix
    assert len(records) == len(common.TRACKS) * 36 and len(outer_records) == len(common.TRACKS) * 4
    helper = Path(__file__).resolve()
    legacy_helper = Path(importlib.import_module("src.generalization_rbp_20261007.inner_replay").__file__).resolve()
    common.jsave(common.OUT / "canonical_inner_replay.json", {"status": "PASS", "namespace": ns,
        "role": "ADDITIVE_FULL_VALIDATION_CANONICAL_SCORE_REPLAY", "inner_checkpoints_checked": len(records),
        "outer_checkpoints_checked": len(outer_records), "nested_choices_checked": len(selections),
        "canonical_predictor_calls": "One original full-validation/target matrix per checkpoint; independent arithmetic only is blocked",
        "maximum_independent_arithmetic_error": maximum_error, "score_tolerance": SCORE_ATOL,
        "regret_tolerance": REGRET_ATOL, "lexical_ties_use": "canonical original scorer, no epsilon score ties",
        "numerical_threads": 1, "batch_rows_independent_only": BATCH_ROWS, "prefit_manifest_sha256": prefit_sha,
        "replay_source_sha256": common.sha256(helper), "legacy_helpers_sha256": common.sha256(legacy_helper),
        "replay_source_pinned_in_target_prefit_manifest": manifest["files"].get(helper.relative_to(common.ROOT).as_posix()) == common.sha256(helper),
        "parsed_model_input_provenance_scope": "Original target freeze and saved checkpoint identity; no retroactive creation-time certificate added",
        "files": files, "inner": records, "outer": outer_records, "selections": selections,
        "models_fit": 0, "protected_outcomes_opened": False, "independent_confirmation": False})
    print(mode, "PASS", len(records), "inner", len(outer_records), "outer checkpoints", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=sorted(NAMESPACES))
    run(parser.parse_args().mode)
