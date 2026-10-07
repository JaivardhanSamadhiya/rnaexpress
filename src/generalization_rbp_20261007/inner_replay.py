"""Additive, fit-free independent replay of every nested validation checkpoint.

No frozen production module is changed. Only exposed, admitted source labels
are loaded. This diagnostic never calls a fit routine or selects a new model.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json

import numpy as np
import pandas as pd


NAMESPACES = {"rbp": "generalization_rbp_20261007",
              "next": "generalization_next_20261007"}
SCORE_ATOL = 1e-9
REGRET_ATOL = 1e-12
SELECTION_ATOL = 1e-12
BATCH_ROWS = 1024


def ids_hash(frame):
    return hashlib.sha256("|".join(frame.intervention_id).encode()).hexdigest()


def reconstructed_purge(frame, requested_training, held):
    """Independently reproduce the component exclusion, then check alleles."""
    requested_training, held = [np.asarray(mask, bool) for mask in (requested_training, held)]
    assert requested_training.shape == held.shape == (len(frame),)
    assert not (requested_training & held).any()
    held_frame = frame.loc[held]
    held_components = set(held_frame.biological_component)
    keep = np.array([bool(wanted and component not in held_components)
                     for wanted, component in zip(requested_training, frame.biological_component)])
    held_alleles = set(held_frame.parent_sequence) | set(held_frame.mutant_sequence)
    training_alleles = set(frame.loc[keep, "parent_sequence"]) | set(frame.loc[keep, "mutant_sequence"])
    assert not training_alleles.intersection(held_alleles), "Original allele leakage / incomplete component closure"
    return keep


def checked_model(model, dimensions):
    mean, scale, beta = [np.asarray(model[key], np.float64) for key in ("mean", "scale", "beta")]
    assert mean.shape == scale.shape == beta.shape == (dimensions,)
    assert np.isfinite(mean).all() and np.isfinite(scale).all() and np.isfinite(beta).all()
    assert (scale > 0).all()
    active = np.asarray(model["active"], bool)
    assert active.shape == beta.shape and (beta[~active] == 0).all()
    return mean, scale, beta


def replay_scores(model, matrix, row_indices, predictor, batch_rows=BATCH_ROWS):
    """Use explicit arithmetic; also cross-check an affine reparameterization."""
    mean, scale, beta = checked_model(model, matrix.shape[1])
    row_indices = np.asarray(row_indices, int)
    score = np.empty(len(row_indices), np.float64)
    coefficients = beta / scale
    intercept = -float(mean @ coefficients)
    reference_error, affine_error = 0., 0.
    for start in range(0, len(row_indices), batch_rows):
        stop = min(start + batch_rows, len(row_indices))
        block = np.asarray(matrix[row_indices[start:stop]], np.float64)
        assert np.isfinite(block).all()
        z = (block - mean[None, :]) / scale[None, :]
        # Sum rather than shared predict_model's dot product independently
        # checks the operation; the published dot form is retained for exact
        # tie semantics and compared against both independent expressions.
        summed = np.sum(z * beta[None, :], axis=1)
        dot = z @ beta
        reference = np.asarray(predictor(model, block), float)
        affine = block @ coefficients + intercept
        reference_error = max(reference_error, float(np.max(np.abs(summed - reference), initial=0.)),
                              float(np.max(np.abs(dot - reference), initial=0.)))
        affine_error = max(affine_error, float(np.max(np.abs(affine - reference), initial=0.)))
        assert reference_error <= SCORE_ATOL and affine_error <= SCORE_ATOL, "Checkpoint score mismatch"
        score[start:stop] = dot
    return score, reference_error, affine_error


def extreme_regret(frame, score):
    """Lexical ties, both directions, equal contexts/components/studies.

    Does not call the frozen decisions(), summary(), or inner_regret().
    The returned choice digest certifies the complete reconstructed decisions.
    """
    frame = frame.reset_index(drop=True)
    score = np.asarray(score, float)
    assert len(frame) == len(score) and np.isfinite(score).all()
    context_values, choices = {}, []
    for context, group in frame.groupby("parent_context_id", sort=True):
        assert group.dataset.nunique() == group.biological_component.nunique() == 1
        group = group.sort_values("intervention_id", kind="stable")
        y = group.measured_delta.to_numpy(float)
        s = score[group.index.to_numpy()]
        span = float(y.max() - y.min())
        assert len(group) >= 2 and span > 0 and np.isfinite(y).all()
        values = []
        for direction in (-1, 1):
            oriented_y, oriented_score = direction * y, direction * s
            selected = int(np.argmax(oriented_score))
            regret = float((oriented_y.max() - oriented_y[selected]) / span)
            assert 0 <= regret <= 1
            values.append(regret)
            choices.append([str(context), direction, str(group.intervention_id.iloc[selected]), regret])
        key = (str(group.dataset.iloc[0]), str(group.biological_component.iloc[0]))
        context_values.setdefault(key, []).append(float(np.mean(values)))
    assert context_values
    studies = {}
    for (study, component), values in sorted(context_values.items()):
        studies.setdefault(study, []).append(float(np.mean(values)))
    per_study = {study: float(np.mean(values)) for study, values in sorted(studies.items())}
    digest = hashlib.sha256(json.dumps(choices, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return float(np.mean(list(per_study.values()))), per_study, len(choices), digest


def selected_index(values):
    values = np.asarray(values, float)
    assert values.ndim == 1 and len(values) and np.isfinite(values).all()
    return next(i for i, value in enumerate(values) if value <= values.min() + SELECTION_ATOL)


def check_checkpoint(model, training, config, excluded_studies):
    assert model["_config"] == model["config"] == config, "Configuration mismatch"
    assert model["_training_ids_sha256"] == ids_hash(training), "Training ID order mismatch"
    studies = sorted(training.dataset.unique().tolist())
    components = sorted(training.biological_component.unique().tolist())
    assert model["_training_studies"] == model["training_studies"] == studies
    assert model["_training_components"] == model["training_components"] == components
    assert not set(excluded_studies).intersection(studies)
    assert model["training_rows"] == len(training)


def run(namespace_key):
    assert namespace_key in NAMESPACES
    namespace = NAMESPACES[namespace_key]
    common = importlib.import_module("src." + namespace + ".common")
    routes = importlib.import_module("src." + namespace + ".routes")
    manifest = common.freeze_check()
    loaded = common.load()
    frame = (loaded[0] if isinstance(loaded, tuple) else loaded).reset_index(drop=True)
    assert len(frame) == 26258 and not frame.intervention_id.duplicated().any()
    if isinstance(loaded, tuple):
        del loaded
    from src.cross_assay_20260927.models import purge as published_purge
    records, selections, files = [], [], {}
    expected = len(common.TRACKS) * 4 * 3 * 3
    for track in common.TRACKS:
        complete_path = common.OUT / track / "run_complete.json"
        complete = common.readj(complete_path)
        assert complete["status"] == "PASS" and complete["prefit_manifest_sha256"] == common.sha256(common.OUT / "prefit_manifest.json")
        path = common.ART / (track + "_model_features.npz")
        with np.load(path, allow_pickle=False) as archive:
            matrix = archive["features"]
        assert len(matrix) == len(frame) and np.isfinite(matrix).all()
        files[path.relative_to(common.ROOT).as_posix()] = common.sha256(path)
        mod = routes.module(track)
        csvpath = common.OUT / track / "inner_selection.csv"
        stored = pd.read_csv(csvpath)
        assert len(stored) == 36 and not stored.duplicated(["outer_held", "inner_held", "configuration"]).any()
        folds_path = common.OUT / track / "folds.json"
        folds = common.readj(folds_path)
        assert len(folds) == 4 and {fold["held"] for fold in folds} == set(common.STUDIES)
        for held in common.STUDIES:
            outer_test = frame.dataset.eq(held).to_numpy()
            source_mask = reconstructed_purge(frame, ~outer_test, outer_test)
            np.testing.assert_array_equal(source_mask, published_purge(frame, ~outer_test, outer_test))
            source_indices = np.flatnonzero(source_mask)
            source = frame.loc[source_mask].reset_index(drop=True)
            inner_studies = sorted(source.dataset.unique())
            assert len(inner_studies) == 3 and held not in inner_studies
            values = []
            for config in mod.CONFIGS:
                regrets = []
                for inner in inner_studies:
                    validation = source.dataset.eq(inner).to_numpy()
                    inner_train = reconstructed_purge(source, ~validation, validation)
                    np.testing.assert_array_equal(inner_train, published_purge(source, ~validation, validation))
                    training, target = [source.loc[mask].reset_index(drop=True) for mask in (inner_train, validation)]
                    fit_path = common.OUT / track / "fits" / (held + "__inner__" + inner + "_" + config["id"] + ".json")
                    model = common.readj(fit_path)
                    check_checkpoint(model, training, config, (held, inner))
                    scores, reference_error, affine_error = replay_scores(model, matrix, source_indices[validation], mod.predict_model)
                    regret, per_study, choices, digest = extreme_regret(target, scores)
                    assert set(per_study) == {inner}
                    row = stored[(stored.outer_held == held) & (stored.inner_held == inner) & (stored.configuration == config["id"])]
                    assert len(row) == 1
                    row = row.iloc[0]
                    assert row.training_rows == len(training) and row.validation_rows == len(target)
                    assert row.training_ids_sha256 == ids_hash(training)
                    error = abs(regret - float(row.regret))
                    assert error <= REGRET_ATOL, "Replayed inner choice/regret differs: " + str(fit_path)
                    regrets.append(regret)
                    records.append({"track": track, "outer_held": held, "inner_held": inner,
                        "configuration": config["id"], "training_rows": len(training), "validation_rows": len(target),
                        "training_ids_sha256": ids_hash(training), "validation_ids_sha256": ids_hash(target),
                        "regret": regret, "stored_regret_absolute_error": error, "choices": choices,
                        "choice_sha256": digest, "score_reference_max_absolute_error": reference_error,
                        "score_affine_max_absolute_error": affine_error, "checkpoint_sha256": common.sha256(fit_path)})
                    files[fit_path.relative_to(common.ROOT).as_posix()] = common.sha256(fit_path)
                values.append(float(np.mean(regrets)))
            index = selected_index(values)
            config = mod.CONFIGS[index]
            fold = next(fold for fold in folds if fold["held"] == held)
            assert fold["selected_configuration"] == config
            assert abs(fold["inner_macro_regret"] - values[index]) <= REGRET_ATOL
            assert set(fold["all_inner_scores"]) == {c["id"] for c in mod.CONFIGS}
            for c, value in zip(mod.CONFIGS, values):
                assert abs(fold["all_inner_scores"][c["id"]] - value) <= REGRET_ATOL
            assert fold["training_ids_sha256"] == ids_hash(source)
            assert fold["training_studies"] == sorted(source.dataset.unique())
            assert fold["training_components"] == sorted(source.biological_component.unique())
            assert fold["test_rows"] == int(outer_test.sum())
            assert fold["test_ids_sha256"] == ids_hash(frame.loc[outer_test])
            outer_fit = common.OUT / track / "fits" / (held + "__outer_" + config["id"] + ".json")
            check_checkpoint(common.readj(outer_fit), source, config, (held,))
            files[outer_fit.relative_to(common.ROOT).as_posix()] = common.sha256(outer_fit)
            selections.append({"track": track, "outer_held": held, "selected_configuration": config,
                               "recomputed_inner_means": dict(zip([c["id"] for c in mod.CONFIGS], values))})
            print(namespace_key, track, held, "inner prediction/regret/selection replay PASS", flush=True)
        for p in (csvpath, folds_path, complete_path):
            files[p.relative_to(common.ROOT).as_posix()] = common.sha256(p)
        del matrix
    assert len(records) == expected and len(selections) == len(common.TRACKS) * 4
    source_path = Path(__file__).resolve()
    source_relative = source_path.relative_to(common.ROOT).as_posix()
    receipt = {"status": "PASS", "role": "ADDITIVE_INDEPENDENT_INNER_CHECKPOINT_REPLAY",
        "namespace": namespace, "checkpoints_checked": len(records), "nested_choices_checked": len(selections),
        "no_new_fits": True, "protected_outcomes_opened": False, "independent_confirmation": False,
        "batch_rows": BATCH_ROWS, "score_tolerance": SCORE_ATOL, "regret_tolerance": REGRET_ATOL,
        "selection_tolerance": SELECTION_ATOL, "prefit_manifest_sha256": common.sha256(common.OUT / "prefit_manifest.json"),
        "replay_source_sha256": common.sha256(source_path),
        "replay_source_pinned_in_target_prefit_manifest": manifest["files"].get(source_relative) == common.sha256(source_path),
        "files": files, "checkpoints": records, "selections": selections}
    common.jsave(common.OUT / "independent_inner_replay.json", receipt)
    print(namespace_key, "PASS", len(records), "checkpoints", len(selections), "nested selections", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", choices=sorted(NAMESPACES))
    run(parser.parse_args().namespace)
