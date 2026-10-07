"""Invented-data invariants; no project feature/model/outcome reads or fits."""
import unittest
from unittest.mock import patch
from .common import np, pd, SRC, OUT, META, sha256, jsave, TASKS, FOLDS
from .splits import masks, exact_menu_pairs
from .evaluate import select_source, source_model
from .gate import compare
from .contrast import paired_contrast
from .canonical_paired_contrast import shared_matrix, common_choices
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
from src.generalization_crosscell_20261007.routes import CONFIGS
from src.generalization_rbp_20261007.canonical_inner_replay import canonical_scores, decision_table, decisions_equal


def toy():
    rows = []
    parents, variants = ["AAAAC", "CCCCA", "GGGGA"], ["AAAAT", "CCCCT", "GGGGT"]
    for cell in ("CAD", "Neuro-2a"):
        for fold in FOLDS:
            for allele in (0, 1):
                rows.append({"intervention_id": cell + str(fold) + str(allele), "dataset": "mikl_gse173098",
                    "cell_type": cell, "endpoint_class": "projection", "held_parent_fold": fold,
                    "biological_component": "gene" + str(fold), "gene_transcript": "G" + str(fold),
                    "parent_context_id": cell + "_parent" + str(fold), "parent_sequence": parents[fold],
                    "mutant_sequence": variants[fold] + str(allele), "measured_delta": float(allele)})
    return pd.DataFrame(rows)


class KnownCellTests(unittest.TestCase):
    def test_exact_original_masks_cover_same_cell_full_menus(self):
        frame = toy()
        for task, (cell, _) in TASKS.items():
            seen = []
            for fold in FOLDS:
                train, held, opposite = masks(frame, task, fold)
                self.assertEqual(set(frame.loc[train, "cell_type"]), {cell})
                self.assertEqual(set(frame.loc[held, "cell_type"]), {cell})
                self.assertEqual(set(frame.loc[opposite, "cell_type"]), {"Neuro-2a" if cell == "CAD" else "CAD"})
                self.assertEqual(int(held.sum()), 2)
                seen.extend(frame.loc[held, "intervention_id"])
            self.assertEqual(len(seen), len(set(seen)))
            self.assertEqual(set(seen), set(frame[frame.cell_type.eq(cell)].intervention_id))

    def test_same_cell_only_allele_overlap_rejected_without_silent_refit(self):
        frame = toy()
        frame.loc[frame.intervention_id.eq("CAD00"), "mutant_sequence"] = "CCCCA"
        # Opposite-cell target does not contain this allele, so its old source
        # mask remains valid; the distinct same-cell guard must reject reuse.
        from src.generalization_crosscell_20261007.splits import outer_masks
        train, _ = outer_masks(frame, "CAD_to_N2A", 0)
        self.assertTrue(train.any())
        with self.assertRaisesRegex(AssertionError, "Same-cell allele overlap"):
            masks(frame, "CAD_known", 0)

    def test_exact_menus_require_full_equality_and_record_lexical_order(self):
        frame = toy(); pairs, excluded = exact_menu_pairs(frame)
        self.assertEqual(len(pairs), 3); self.assertFalse(excluded)
        frame.loc[frame.intervention_id.eq("Neuro-2a01"), "mutant_sequence"] = "OTHER"
        pairs, excluded = exact_menu_pairs(frame)
        self.assertEqual(len(pairs), 2); self.assertEqual(sum(x["rows"] for x in excluded), 4)
        frame = toy()
        frame.loc[frame.cell_type.eq("Neuro-2a") & frame.held_parent_fold.eq(0), "intervention_id"] = ["z", "a"]
        pairs, _ = exact_menu_pairs(frame)
        self.assertFalse(next(r for r in pairs if r["gene_fold"] == 0)["lexical_allele_order_matches"])
        frame.loc[frame.intervention_id.eq("a"), "mutant_sequence"] = "AAAAT0"
        with self.assertRaisesRegex(AssertionError, "Duplicate alleles"):
            exact_menu_pairs(frame)

    def test_selected_config_uses_original_source_oof_order_and_four_arg_api(self):
        from . import evaluate
        frame = toy(); train, _, opposite = masks(frame, "CAD_known", 0)
        from .common import rowhash
        roster = [{"task": source, "fold": fold} for _, source in TASKS.values() for fold in FOLDS]
        chosen = next(r for r in roster if r == {"task": "CAD_to_N2A", "fold": 0})
        chosen.update({"all_source_oof_scores": dict(zip([c["id"] for c in CONFIGS], [.4, .4 - 5e-13, .6])),
            "selected_configuration": CONFIGS[0], "training_ids_sha256": rowhash(frame.loc[train]),
            "test_ids_sha256": rowhash(frame.loc[opposite])})
        rows = pd.DataFrame([{"task": "CAD_to_N2A", "outer_fold": 0, "configuration": c["id"],
            "combined_source_oof_macro_regret": value} for c, value in zip(CONFIGS, [.4, .4 - 5e-13, .6])])
        for altered in (frame, frame.assign(measured_delta=-100 * frame.measured_delta)):
            with patch.object(evaluate, "readj", side_effect=[roster, {"fake": True}]), \
                 patch.object(evaluate.pd, "read_csv", return_value=rows), patch.object(evaluate, "check_model") as checker:
                _, config, _, _ = source_model("base", "CAD_known", 0, altered, np.zeros((len(frame), 246)))
                self.assertEqual(config, CONFIGS[0]); self.assertEqual(len(checker.call_args.args), 4)
        self.assertEqual(select_source(CONFIGS, [.6, .5, .4]), CONFIGS[2])

    def test_metadata_loader_explicitly_excludes_effect_columns(self):
        from . import common
        rows = []
        for index in range(26258):
            component = index % 187
            cell = "CAD" if index < 6889 else "Neuro-2a"
            rows.append({"intervention_id": "fake" + str(index), "dataset": "mikl_gse173098" if index < 13781 else "other",
                "cell_type": cell, "endpoint_class": "projection", "held_parent_fold": component % 3,
                "biological_component": "g" + str(component), "gene_transcript": "G" + str(component),
                "parent_context_id": cell + "g" + str(component), "parent_sequence": "AAA", "mutant_sequence": "AAT"})
        invented = pd.DataFrame(rows)
        with patch.object(common.pd, "read_csv", return_value=invented) as reader:
            result = common.load(False)
            self.assertEqual(len(result), 13781)
            self.assertEqual(reader.call_count, 1)
            self.assertEqual(reader.call_args.kwargs["usecols"], META)
            self.assertNotIn("measured_delta", result)

    def test_shared_component_draw_and_unequal_fold_weighting(self):
        a = pd.Series([1., -1.], index=["g1", "g2"])
        np.testing.assert_allclose(shared_bootstrap({"CAD_known": a, "N2A_known": -a}, 64, 4), 0., atol=1e-15, rtol=0)
        rows = []
        for task in TASKS:
            for component, fold, gain in [("a", 0, .1), ("b", 1, .02), ("c", 2, .04), ("d", 2, .04)]:
                rows.append({"task": task, "biological_component": component, "gene_fold": fold,
                    "regret": .5 - gain, "wrong_direction": .1})
        candidate = pd.DataFrame(rows); value = compare(candidate, candidate.assign(regret=.5))
        self.assertEqual(value["removed_best_gene_fold"], 0)
        self.assertAlmostEqual(value["remaining_gain"], .10 / 3)
        self.assertAlmostEqual(value["mean_gain"], .05)

    def test_canonical_full_shape_ties_and_decision_identity(self):
        from src.generalization_20261007.route_scaling import predict_model
        frame = toy().iloc[:2].reset_index(drop=True)
        matrix = np.array([[1e16, 1., -1e16], [1e16, 0., -1e16]])
        model = {"mean": [0., 0., 0.], "scale": [1., 1., 1.], "beta": [1e-12] * 3, "active": [True] * 3}
        calls = []
        def scorer(m, x):
            calls.append(x.shape); return predict_model(m, x)
        score, error = canonical_scores(model, matrix, [0, 1], scorer, batch_rows=1)
        self.assertEqual(calls, [(2, 3)]); self.assertLessEqual(error, 1e-9)
        expected = decision_table(frame, score)
        if score[0] == score[1]: self.assertEqual(set(expected.selected_id), {"CAD00"})
        with self.assertRaises(AssertionError): decisions_equal(expected, expected.assign(biological_component="wrong"))
        with self.assertRaises(AssertionError): decisions_equal(expected, pd.concat([expected, expected.iloc[:1]]))

    def test_matched_state_contrast_uses_same_source_task_full_menus(self):
        pairs = pd.DataFrame(exact_menu_pairs(toy())[0]); rows = []
        for fold in FOLDS:
            for direction in (-1, 1):
                rows.append({"task": "CAD_known", "parent_context_id": "CAD_parent" + str(fold),
                    "biological_component": "gene" + str(fold), "gene_fold": fold, "candidates": 2,
                    "direction": direction, "regret": .1})
        known = pd.DataFrame(rows)
        crossed = known.assign(task="CAD_to_N2A", parent_context_id=known.parent_context_id.str.replace("CAD_", "Neuro-2a_"), regret=.3)
        value = paired_contrast(pairs, known, crossed, "CAD_known")
        self.assertEqual(len(value), 6); np.testing.assert_allclose(value.known_advantage, .2)
        with self.assertRaises(AssertionError): paired_contrast(pairs, known, crossed.assign(candidates=1), "CAD_known")

    def test_common_pair_matrix_requires_exact_feature_bytes(self):
        frame = toy(); pairs = pd.DataFrame(exact_menu_pairs(frame)[0])
        matrix = np.tile(np.arange(18, dtype=float).reshape(6, 3), (2, 1))
        rows, shared = shared_matrix(frame, matrix, pairs, 0)
        self.assertEqual(len(rows), 2); np.testing.assert_array_equal(shared, matrix[:2])
        changed = matrix.copy(); changed[6, 1] = np.nextafter(changed[6, 1], np.inf)
        with self.assertRaisesRegex(AssertionError, "feature-byte inequality"):
            shared_matrix(frame, changed, pairs, 0)
        changed = matrix.copy(); changed[6, 0] = -0.
        with self.assertRaisesRegex(AssertionError, "feature-byte inequality"):
            shared_matrix(frame, changed, pairs, 0)

    def test_common_sequence_tie_policy_selects_same_allele_in_both_truths(self):
        frame = toy()
        frame.loc[frame.cell_type.eq("Neuro-2a") & frame.held_parent_fold.eq(0), "intervention_id"] = ["z", "a"]
        frame.loc[frame.cell_type.eq("Neuro-2a") & frame.held_parent_fold.eq(0), "measured_delta"] = [1., 0.]
        pairs = pd.DataFrame(exact_menu_pairs(frame)[0])
        matrix = np.tile(np.arange(18, dtype=float).reshape(6, 3), (2, 1))
        rows, shared = shared_matrix(frame, matrix, pairs, 0)
        selected = common_choices(rows, np.zeros(2), "CAD_known")
        self.assertEqual(set(selected.selected_mutant_sequence), {"AAAAT0"})
        self.assertEqual(set(selected.N2A_selected_id), {"z"})
        self.assertAlmostEqual(selected.known_regret.mean(), .5)
        self.assertAlmostEqual(selected.crossed_regret.mean(), .5)
        selected = common_choices(rows, np.array([0., 1.]), "CAD_known")
        np.testing.assert_allclose(selected.known_advantage, 1.)
        calls = []
        def scorer(model, x):
            calls.append(x.shape); return x @ np.asarray(model["beta"])
        model = {"mean": [0.] * 3, "scale": [1.] * 3, "beta": [1.] * 3, "active": [True] * 3}
        canonical_scores(model, shared, np.arange(len(shared)), scorer, batch_rows=1)
        self.assertEqual(calls, [(2, 3)])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(KnownCellTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    jsave(OUT / "tests_receipt_reviewed_final.json", {"status": "PASS", "tests": result.testsRun,
        "source_hashes": {p.name: sha256(p) for p in sorted(SRC.glob("*.py"))},
        "scope": "Invented masks/alleles/menu equality, original OOF choice, metadata-only columns, canonical ties, component weighting and descriptive pairing",
        "project_outcomes_read": False, "project_models_read": False, "project_features_read": False,
        "estimator_fits": 0, "numpy_version": np.__version__, "pandas_version": pd.__version__})
