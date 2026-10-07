"""Independent saved-score/choice/regret and exact row/fold replay, no fitting."""
from .common import *
from .engine import features, module
from .projection import load_projections, project_pool_summaries
from .production import requests, positions_key, validate_cached, structure_probability
from .scoring import summaries
from src.cross_assay_20260927.models import purge


def verify_feature_identity():
    original, encoded = inventories()
    roster, positions = requests(encoded)
    stored_rows = pd.read_csv(ART / "model_row_index.csv.gz", low_memory=False)
    pd.testing.assert_frame_equal(stored_rows, original)
    base, raw, access = [features(track) for track in TRACKS]
    with np.load(NEXT_ART / "base_features.npz", allow_pickle=False) as archive:
        np.testing.assert_array_equal(base, archive["features"])
    np.testing.assert_array_equal(raw[:, :246], base)
    np.testing.assert_array_equal(access[:, :502], raw)
    del base, access, raw
    for mode, track, start in (("raw", "raw", 246), ("access", "access", 502)):
        matrix = features(track)
        cache = {sequence: validate_cached(sequence, masks, mode)[:2] for sequence, masks in roster.items()}
        for index, (parent, mutant, mask) in enumerate(zip(encoded.parent_sequence, encoded.mutant_sequence, positions)):
            parent_global, parent_local = cache[parent]
            mutant_global, mutant_local = cache[mutant]
            key = positions_key(mask)
            expected = np.r_[mutant_global - parent_global, mutant_local[key] - parent_local[key]].astype(np.float32)
            np.testing.assert_array_equal(matrix[index, start:start + 256], expected)
        del cache, matrix
    # Independent scoring API, which enumerates pools separately from the cache
    # producer's pooled_blocks, checks one deterministic candidate per assay.
    matrices = load_projections()
    checked = []
    for study in STUDIES:
        index = encoded[encoded.dataset.eq(study)].sort_values("intervention_id").index[0]
        row, mask = encoded.loc[index], positions[index]
        for mode in ("raw", "access"):
            p_probability = m_probability = None
            if mode == "access":
                p_probability = structure_probability(row.parent_sequence)[0]
                m_probability = structure_probability(row.mutant_sequence)[0]
            parent = project_pool_summaries(summaries(row.parent_sequence, mask, p_probability), matrices)
            mutant = project_pool_summaries(summaries(row.mutant_sequence, mask, m_probability), matrices)
            p_global, p_local, _, _ = validate_cached(row.parent_sequence, roster[row.parent_sequence], mode)
            m_global, m_local, _, _ = validate_cached(row.mutant_sequence, roster[row.mutant_sequence], mode)
            key = positions_key(mask)
            actual = np.r_[m_global - p_global, m_local[key] - p_local[key]]
            np.testing.assert_allclose(mutant - parent, actual, atol=1e-10, rtol=1e-12)
        checked.append(str(row.intervention_id))
    return checked


def run():
    freeze_check()
    frame = load()
    independent_feature_ids = verify_feature_identity()
    errors, decision_count, model_count, inner_fit_count = [], 0, 0, 0
    for track in TRACKS:
        x, mod = features(track), module(track)
        pred = pd.read_csv(OUT / track / "predictions.csv.gz", float_precision="round_trip")
        decision = pd.read_csv(OUT / track / "decisions.csv", float_precision="round_trip")
        inner = pd.read_csv(OUT / track / "inner_selection.csv", float_precision="round_trip")
        assert len(pred) == len(frame) and not pred.intervention_id.duplicated().any()
        assert set(pred.intervention_id) == set(frame.intervention_id)
        for fold in readj(OUT / track / "folds.json"):
            held = fold["held"]
            test = frame.dataset.eq(held).to_numpy(); train = purge(frame, ~test, test)
            source = frame.loc[train].reset_index(drop=True)
            target = frame.loc[test].reset_index(drop=True)
            expected = rowhash(source)
            assert expected == fold["training_ids_sha256"]
            assert rowhash(target) == fold["test_ids_sha256"]
            assert not set(fold["training_components"]) & set(target.biological_component)
            for config in mod.CONFIGS:
                for inner_held in sorted(source.dataset.unique()):
                    validation = source.dataset.eq(inner_held).to_numpy()
                    inner_train = purge(source, ~validation, validation)
                    training = source.loc[inner_train].reset_index(drop=True)
                    saved = readj(OUT / track / "fits" / (held + "__inner__" + inner_held + "_" + config["id"] + ".json"))
                    assert saved["_training_ids_sha256"] == rowhash(training)
                    assert held not in saved["_training_studies"] and inner_held not in saved["_training_studies"]
                    assert not set(training.biological_component) & set(source.loc[validation].biological_component)
                    selected_row = inner[(inner.outer_held == held) & (inner.inner_held == inner_held) &
                                         (inner.configuration == config["id"])]
                    assert len(selected_row) == 1 and selected_row.iloc[0].training_ids_sha256 == rowhash(training)
                    inner_fit_count += 1
            values = inner[inner.outer_held.eq(held)].groupby("configuration").regret.mean()
            minimum = float(values.min())
            selected = next(config for config in mod.CONFIGS if float(values[config["id"]]) <= minimum + 1e-12)
            assert selected == fold["selected_configuration"]
            model = readj(OUT / track / "fits" / (held + "__outer_" + selected["id"] + ".json"))
            assert model["_training_ids_sha256"] == expected and held not in model["_training_studies"]
            actual = mod.predict_model(model, x[test])
            saved = pred[pred.dataset.eq(held)].set_index("intervention_id").loc[target.intervention_id]
            error = float(np.max(np.abs(actual - saved.score.to_numpy())))
            assert error < 1e-9; errors.append(error)
            joined = saved.reset_index().merge(target[["intervention_id", "parent_context_id", "biological_component", "measured_delta"]],
                                               on="intervention_id", validate="one_to_one")
            for direction in (-1, 1):
                chosen = joined.assign(utility=direction * joined.score).sort_values(
                    ["parent_context_id", "utility", "intervention_id"], ascending=[True, False, True]
                ).drop_duplicates("parent_context_id").set_index("parent_context_id")
                recorded = decision[decision.dataset.eq(held) & decision.direction.eq(direction)].set_index("parent_context_id").loc[chosen.index]
                assert np.array_equal(recorded.selected_id.to_numpy(), chosen.intervention_id.to_numpy())
                bounds = joined.groupby("parent_context_id").measured_delta.agg(["min", "max"]).loc[chosen.index]
                best = bounds["max"].to_numpy() if direction == 1 else -bounds["min"].to_numpy()
                effect = direction * chosen.measured_delta.to_numpy()
                regret = (best - effect) / (bounds["max"] - bounds["min"]).to_numpy()
                np.testing.assert_allclose(regret, recorded.regret, atol=1e-12, rtol=0)
                np.testing.assert_array_equal((effect < -1e-12).astype(float), recorded.wrong_direction)
                np.testing.assert_array_equal(((effect < -1e-12) & (best > 1e-12)).astype(float), recorded.avoidable_wrong)
                decision_count += len(recorded)
        np.testing.assert_allclose(decision.wrong_direction,
            decision.avoidable_wrong + decision.unavoidable_wrong + decision.neutral_only_alternative_wrong,
            atol=1e-12, rtol=0)
        model_count += len(list((OUT / track / "fits").glob("*.json")))
        print("Verified RBP", track, flush=True)
    assert model_count == 120 and inner_fit_count == 108
    jsave(OUT / "verification_receipt.json", {
        "status": "PASS", "models": model_count, "inner_training_folds_checked": inner_fit_count,
        "candidate_scores_replayed": len(frame) * len(TRACKS), "maximum_score_error": max(errors),
        "selected_decisions_independently_checked": decision_count,
        "all_feature_rows_reconstructed_from_caches": True,
        "independent_uncompressed_pool_feature_checks": independent_feature_ids,
        "source_only_selection_checked": True, "original_allele_row_identity_checked": True,
        "protected_outcomes_opened": False, "verification_code_sha256": sha256(Path(__file__)),
    })
    print("RBP independent verification PASS", flush=True)


if __name__ == "__main__":
    run()
