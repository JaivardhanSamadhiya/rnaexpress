"""Scoped synthetic metadata/roster/checkpoint/decision checks; no fitting."""
import unittest
from unittest.mock import patch
from .common import np, pd, SRC, OUT, jsave, sha256
from . import routes, engine
from .gate import incremental_checks
from .verify import independent_decisions, independent_regret
from src.cross_assay_20260927.models import pair_indices, purge
from src.generalization_20261007.route_scaling import pair_rms


def toy():
    rows = []
    for endpoint, study, sign in (("projection", "toy_P", 1.), ("nuclear_cytoplasmic", "toy_N", -1.)):
        for index in range(4):
            rows.append({"intervention_id":study + str(index), "dataset":study, "biological_component":study,
                "parent_context_id":study + "_parent", "endpoint_class":endpoint,
                "parent_sequence":study + "_reference", "mutant_sequence":study + "_variant" + str(index),
                "measured_delta":sign * index, "metadata_sentinel":"unchanged"})
    return pd.DataFrame(rows)


class AlignmentTests(unittest.TestCase):
    def test_fixed_metadata_orientation_rejects_unknown_or_mixed(self):
        frame = toy(); expected = np.array([1.] * 4 + [-1.] * 4)
        np.testing.assert_array_equal(routes.endpoint_sign(frame), expected)
        changed = frame.copy(); changed["dataset"] = "same"; changed["measured_delta"] = np.nan
        np.testing.assert_array_equal(routes.endpoint_sign(changed), expected)
        changed.loc[0, "endpoint_class"] = "unknown"
        with self.assertRaises(ValueError): routes.endpoint_sign(changed)
        with self.assertRaises(ValueError): routes.endpoint_sign(frame.drop(columns="endpoint_class"))
        frame["parent_context_id"] = "mixed"
        with self.assertRaises(AssertionError): routes.endpoint_sign(frame)

    def test_all_feature_columns_pass_through_without_metadata_mutation(self):
        frame = toy(); before = frame.copy(deep=True)
        for track, dimension in routes.SHAPES.items():
            matrix = np.arange(len(frame) * dimension, dtype=float).reshape(len(frame), dimension)
            before_x = matrix.copy(); captured = {}
            config = routes.configurations(track)[1]
            def no_fit(training, x, cfg):
                captured["truth"] = training.measured_delta.to_numpy(float).copy()
                np.testing.assert_array_equal(x, matrix)
                self.assertEqual(cfg, config)
                return {"beta":[0.] * dimension, "config":cfg}
            with patch.object(routes, "pair_fit", side_effect=no_fit):
                model = routes.fit_model(frame, matrix, config, track)
            np.testing.assert_array_equal(captured["truth"], frame.measured_delta * routes.endpoint_sign(frame))
            pd.testing.assert_frame_equal(frame, before); np.testing.assert_array_equal(matrix, before_x)
            self.assertEqual(model["fitted_columns"], dimension)
            self.assertFalse(model["sign_is_learned_feature"])

    def test_signed_inference_keeps_original_truth(self):
        frame = toy(); dimension = routes.SHAPES["base"]
        matrix = np.zeros((len(frame), dimension)); matrix[:, 0] = np.tile(np.arange(4), 2)
        model = {"alignment_track":"base", "endpoint_signs":dict(routes.ENDPOINT_SIGNS),
                 "beta":[1.] + [0.] * (dimension - 1), "mean":[0.] * dimension, "scale":[1.] * dimension}
        actual = routes.predict_model(model, matrix, frame)
        np.testing.assert_array_equal(actual, [0., 1., 2., 3., -0., -1., -2., -3.])
        self.assertEqual(independent_regret(frame, actual), 0.)

    def test_roster_weights_ties_and_pair_scaling_unchanged(self):
        frame = toy(); aligned = frame.copy(); aligned["measured_delta"] *= routes.endpoint_sign(frame)
        old, new = pair_indices(frame), pair_indices(aligned)
        for index in (0, 1, 3, 4): np.testing.assert_array_equal(old[index], new[index])
        np.testing.assert_array_equal(new[2], old[2] * routes.endpoint_sign(frame)[old[0]])
        matrix = np.arange(len(frame) * 3, dtype=float).reshape(len(frame), 3)
        np.testing.assert_array_equal(pair_rms(matrix, old[0], old[1], old[3]), pair_rms(matrix, new[0], new[1], new[3]))

    def test_original_component_and_allele_purge(self):
        frame = pd.DataFrame({"biological_component":["shared", "shared", "other"],
                             "parent_sequence":["AAAA", "AAAA", "CCCC"], "mutant_sequence":["AAAT", "AATA", "CCCG"]})
        np.testing.assert_array_equal(purge(frame, np.array([False, True, True]), np.array([True, False, False])), [False, False, True])

    def test_selection_tolerance_and_lexical_choices(self):
        configs = routes.configurations("base")
        self.assertEqual(engine.selected_config(configs, [.4 + 5e-13, .4, .6]), configs[0])
        frame = toy().iloc[:4].reset_index(drop=True)
        actual = independent_decisions(frame, np.array([1., 1., 0., 0.])).set_index("direction")
        self.assertEqual(actual.loc[1].selected_id, "toy_P0")
        self.assertEqual(actual.loc[-1].selected_id, "toy_P2")
        self.assertEqual(actual.loc[1].regret, 1.)
        self.assertAlmostEqual(actual.loc[-1].regret, 2 / 3)

    def test_resume_rejects_changed_labels_config_or_prefit_identity(self):
        identity = {"_training_ids_sha256":"IDs", "_training_identity_sha256":"rows",
                    "_training_original_label_sha256":"original", "_training_aligned_label_sha256":"aligned",
                    "_configuration":routes.configurations("base")[0], "_prefit_manifest_sha256":"freeze"}
        model = {**identity, "alignment_track":"base", "config":identity["_configuration"],
                 "training_original_label_sha256":"original", "training_aligned_label_sha256":"aligned",
                 "beta":[0.] * routes.SHAPES["base"]}
        with patch.object(engine, "checkpoint_identity", return_value=identity):
            engine.validate_checkpoint(model, None, identity["_configuration"], "base")
            for key in ("_training_original_label_sha256", "_training_aligned_label_sha256", "_configuration", "_prefit_manifest_sha256"):
                with self.assertRaises(AssertionError):
                    engine.validate_checkpoint({**model, key:"changed"}, None, identity["_configuration"], "base")

    def test_increment_requires_mean_and_non_single_assay_gain(self):
        self.assertTrue(all(incremental_checks([.06, .01, .01, -.005]).values()))
        self.assertFalse(all(incremental_checks([.08, 0., 0., 0.]).values()))
        self.assertFalse(all(incremental_checks([.002] * 4).values()))


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AlignmentTests))
    assert result.wasSuccessful()
    jsave(OUT / "tests_receipt_final.json", {"status":"PASS", "tests":result.testsRun,
        "source_hashes":{path.name:sha256(path) for path in sorted(SRC.glob("*.py"))},
        "scope":"Synthetic metadata, all-column pass-through with mocked fitter, pair roster/scaling, purge, cached identity and original-truth choice checks",
        "biological_rows_loaded":False, "models_fit":0, "protected_outcomes_opened":False})


if __name__ == "__main__":
    run()
