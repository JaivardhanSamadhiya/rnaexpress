"""Synthetic replay falsification only: no project labels, inference or fits."""
import unittest
from .canonical_inner_replay import (
    np, pd, canonical_scores, decision_table, regret_from_decisions,
    decisions_equal, choice_digest, selected_index, reconstructed_purge,
)


def toy_frame():
    return pd.DataFrame({"dataset": ["s"] * 3, "biological_component": ["g"] * 3,
        "parent_context_id": ["p"] * 3, "intervention_id": ["z", "a", "b"],
        "measured_delta": [-2., 1., 2.]})


class CanonicalReplayTests(unittest.TestCase):
    def test_predictor_full_shape_once_not_independent_block_shape(self):
        matrix = np.zeros((5, 2))
        model = {"mean": [0., 0.], "scale": [1., 1.], "beta": [0., 0.], "active": [False, False]}
        calls = []
        def predictor(m, x):
            calls.append(x.shape)
            # A tolerated row-count-dependent perturbation would split ties.
            return np.zeros(len(x)) if len(x) == 3 else np.arange(len(x)) * 1e-12
        score, error = canonical_scores(model, matrix, [4, 1, 3], predictor, batch_rows=2)
        self.assertEqual(calls, [(3, 2)])
        np.testing.assert_array_equal(score, [0., 0., 0.])
        self.assertEqual(error, 0.)
        decisions = decision_table(toy_frame(), score)
        self.assertEqual(list(decisions.selected_id), ["a", "a"])
        self.assertEqual(regret_from_decisions(decisions), .5)

    def test_manual_allowed_difference_does_not_redefine_canonical_ties(self):
        matrix = np.asarray([[1e16, 1., -1e16], [1e16, 0., -1e16], [1e16, 0., -1e16]])
        model = {"mean": [0.] * 3, "scale": [1.] * 3, "beta": [1e-12] * 3, "active": [True] * 3}
        # Fixed artificial canonical scores isolate summation-order semantics.
        score, error = canonical_scores(model, matrix, [0, 1, 2], lambda m, x: np.zeros(len(x)), batch_rows=2)
        self.assertGreater(error, 0.)
        self.assertLess(error, 1e-9)
        self.assertEqual(list(decision_table(toy_frame(), score).selected_id), ["a", "a"])
        with self.assertRaises(AssertionError):
            canonical_scores(model, matrix, [0, 1, 2], lambda m, x: np.full(len(x), 1e-3))

    def test_metadata_polarity_replays_original_score_after_independent_bound(self):
        matrix = np.asarray([[3., 5.], [-4., 1.], [5., -3.], [11., 2.]], np.float32)
        model = {"mean": [1., -2.], "scale": [2., 5.], "beta": [.5, -.75], "active": [True, True]}
        signs = np.asarray([-1., 1., -1.])
        def predictor(m, x):
            return (((x - np.asarray(m["mean"])) / np.asarray(m["scale"])) @ np.asarray(m["beta"])) * signs
        expected = predictor(model, matrix[[3, 0, 2]].astype(float))
        score, error = canonical_scores(model, matrix, [3, 0, 2], predictor, signs, batch_rows=2)
        np.testing.assert_array_equal(score, expected)
        self.assertLess(error, 1e-12)
        with self.assertRaises(AssertionError):
            canonical_scores(model, matrix, [3, 0, 2], predictor, [0., 1., 1.])

    def test_equal_component_weights_and_input_row_permutation(self):
        rows = []
        for context, gene, effects, scores in [
            ("p1", "g1", [-2., 2.], [2., -2.]),
            ("p2", "g1", [-1., 0., 1.], [1., 0., -1.]),
            ("p3", "g2", [-3., 3.], [-3., 3.]),
        ]:
            rows += [{"dataset": "s", "biological_component": gene, "parent_context_id": context,
                      "intervention_id": context + str(i), "measured_delta": y, "score": score}
                     for i, (y, score) in enumerate(zip(effects, scores))]
        frame = pd.DataFrame(rows)
        decisions = decision_table(frame, frame.score.to_numpy())
        self.assertEqual(regret_from_decisions(decisions), .5)
        shuffled = frame.sample(frac=1, random_state=7).reset_index(drop=True)
        changed = decision_table(shuffled, shuffled.score.to_numpy())
        decisions_equal(decisions, changed)
        self.assertEqual(choice_digest(decisions), choice_digest(changed))
        changed.loc[0, "biological_component"] = "wrong"
        with self.assertRaises(AssertionError): decisions_equal(decisions, changed)

    def test_error_categories_and_recorded_choice_corruption(self):
        cases = [([-2., -1., -3.], [1., 0., -1.], 1., 0., 0.),
                 ([-2., 0., -3.], [1., 0., -1.], 0., 1., 0.),
                 ([-2., 1., -3.], [1., 0., -1.], 0., 0., 1.)]
        for effects, scores, unavoidable, neutral, avoidable in cases:
            frame = toy_frame(); frame["measured_delta"] = effects
            d = decision_table(frame, np.asarray(scores))
            up = d[d.direction.eq(1)].iloc[0]
            self.assertEqual(up.unavoidable_wrong, unavoidable)
            self.assertEqual(up.neutral_only_alternative_wrong, neutral)
            self.assertEqual(up.avoidable_wrong, avoidable)
            self.assertEqual(up.wrong_direction, unavoidable + neutral + avoidable)
        d = decision_table(toy_frame(), np.zeros(3))
        changed = d.copy(); changed.loc[0, "selected_id"] = "b"
        with self.assertRaises(AssertionError): decisions_equal(d, changed)

    def test_original_component_allele_purge_and_fixed_penalty_tie_order(self):
        frame = pd.DataFrame({"biological_component": ["shared", "shared", "other"],
            "parent_sequence": ["AAAA", "AAAA", "GGGG"], "mutant_sequence": ["CAAA", "GAAA", "TGGG"]})
        np.testing.assert_array_equal(reconstructed_purge(frame, [False, True, True], [True, False, False]), [False, False, True])
        frame.loc[1, "biological_component"] = "bad"
        with self.assertRaises(AssertionError): reconstructed_purge(frame, [False, True, True], [True, False, False])
        self.assertEqual(selected_index([.4, .4 - 5e-13, .5]), 0)
        self.assertEqual(selected_index([.4, .4 - 2e-12, .5]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
