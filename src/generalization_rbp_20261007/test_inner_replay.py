"""Synthetic falsification tests; no project frames, features, or fits loaded."""
import copy
import unittest
from .inner_replay import (
    np, pd, ids_hash, reconstructed_purge, replay_scores, extreme_regret,
    selected_index, check_checkpoint,
)


class InnerReplayTests(unittest.TestCase):
    def test_affine_and_explicit_score_replay_with_nontrivial_scaling(self):
        matrix = np.array([[3., 5., 7.], [-4., 1., 2.], [5., -3., 8.], [11., 2., 9.]], np.float32)
        model = {"mean": [1., -2., 4.], "scale": [2., 5., .25],
                 "beta": [.5, -.75, 0.], "active": [True, True, False]}
        expected = np.array([sum((float(row[j]) - model["mean"][j]) / model["scale"][j] * model["beta"][j]
                                 for j in range(3)) for row in matrix])
        def reference(m, x):
            return ((x - np.array(m["mean"])) / np.array(m["scale"])) @ np.array(m["beta"])
        score, err, affine_err = replay_scores(model, matrix, [3, 0, 2, 1], reference, batch_rows=2)
        np.testing.assert_allclose(score, expected[[3, 0, 2, 1]], atol=1e-14, rtol=0)
        self.assertLessEqual(max(err, affine_err), 1e-14)
        with self.assertRaises(AssertionError):
            replay_scores(model, matrix, [0, 1], lambda m, x: reference(m, x) + .001)

    def test_extreme_choice_directions_lexical_ties_and_component_weights(self):
        # Component one has two wrong contexts (regret1 each); component two
        # has one right context (regret0). Equal component result is .5,
        # not the context/candidate pooled answer2/3 or4/5.
        rows = []
        for context, component, y, s in [
            ("p1", "c1", [-2., 2.], [2., -2.]),
            ("p2", "c1", [-1., 0., 1.], [1., 0., -1.]),
            ("p3", "c2", [-3., 3.], [-3., 3.]),
        ]:
            rows.extend({"dataset": "study", "biological_component": component,
                         "parent_context_id": context, "intervention_id": context + str(i),
                         "measured_delta": value, "score": score}
                        for i, (value, score) in enumerate(zip(y, s)))
        frame = pd.DataFrame(rows)
        regret, per_study, choices, digest = extreme_regret(frame, frame.score)
        self.assertEqual(regret, .5)
        self.assertEqual(per_study, {"study": .5})
        self.assertEqual(choices, 6)
        shuffled = frame.sample(frac=1, random_state=4).reset_index(drop=True)
        self.assertEqual(extreme_regret(shuffled, shuffled.score), (regret, per_study, choices, digest))
        tied = pd.DataFrame({"dataset": ["s"] * 3, "biological_component": ["c"] * 3,
            "parent_context_id": ["p"] * 3, "intervention_id": ["z", "a", "b"],
            "measured_delta": [-4., 1., 2.]})
        # Both directions choose lexical'a' at score0; .5 average regret.
        self.assertEqual(extreme_regret(tied, np.zeros(3))[0], .5)

    def test_global_component_purge_and_original_allele_second_guard(self):
        frame = pd.DataFrame({"biological_component": ["shared", "shared", "other"],
                              "parent_sequence": ["AAAA", "AAAA", "GGGG"],
                              "mutant_sequence": ["CAAA", "GAAA", "TGGG"]})
        mask = reconstructed_purge(frame, [False, True, True], [True, False, False])
        np.testing.assert_array_equal(mask, [False, False, True])
        malformed = frame.copy(); malformed.loc[1, "biological_component"] = "unlinked"
        with self.assertRaises(AssertionError):
            reconstructed_purge(malformed, [False, True, True], [True, False, False])

    def test_nested_selection_fixed_order_and_checkpoint_corruption(self):
        self.assertEqual(selected_index([.4, .4 - 5e-13, .5]), 0)
        self.assertEqual(selected_index([.4, .4 - 2e-12, .5]), 1)
        training = pd.DataFrame({"intervention_id": ["z", "a"], "dataset": ["s1", "s2"],
                                 "biological_component": ["c1", "c2"]})
        config = {"id": "fixed", "penalty": .05, "scaling": "pair"}
        model = {"_config": config, "config": config, "_training_ids_sha256": ids_hash(training),
            "_training_studies": ["s1", "s2"], "training_studies": ["s1", "s2"],
            "_training_components": ["c1", "c2"], "training_components": ["c1", "c2"], "training_rows": 2}
        check_checkpoint(model, training, config, ["held"])
        for key, value in [("_training_ids_sha256", ids_hash(training.iloc[::-1])),
                           ("_config", {"id": "other"}), ("training_rows", 3)]:
            corrupt = copy.deepcopy(model); corrupt[key] = value
            with self.assertRaises(AssertionError):
                check_checkpoint(corrupt, training, config, ["held"])
        with self.assertRaises(AssertionError):
            check_checkpoint(model, training, config, ["s1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
