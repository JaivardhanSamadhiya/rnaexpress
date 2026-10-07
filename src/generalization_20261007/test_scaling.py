"""Analytic and synthetic checks; no biological outcome file is read."""
import unittest

from src.cross_assay_20260927.common import np, pd
from src.generalization_20261007.route_scaling import (
    CONFIGS, fit_model, pair_rms, predict_model,
)


def toy_frame():
    return pd.DataFrame({
        "intervention_id": ["scaling-toy-" + str(i) for i in range(6)],
        "dataset": ["toy"] * 6,
        "biological_component": ["g1"] * 3 + ["g2"] * 3,
        "parent_context_id": ["p1"] * 3 + ["p2"] * 3,
        "measured_delta": [-1., 0., 1., -2., 0., 2.],
    })


class ScalingTests(unittest.TestCase):
    def test_pair_rms_matches_known_weighted_differences(self):
        x = np.array([[0., 5.], [2., 5.], [5., 8.], [8., 8.]])
        actual = pair_rms(x, np.array([0, 2]), np.array([1, 3]), np.array([.25, .75]))
        np.testing.assert_allclose(actual, [np.sqrt(.25 * 4 + .75 * 9), 0.], rtol=0, atol=1e-14)

    def test_parent_offsets_do_not_change_pair_fit_or_ordering(self):
        frame = toy_frame()
        x = np.column_stack([[-1., 0., 1., -2., 0., 2.], [0., 0., 0., 1., 1., 1.]])
        offset = np.array([100., 100., 100., -70., -70., -70.])
        changed = x.copy()
        changed[:, 0] += offset
        config = next(c for c in CONFIGS if c["id"] == "pair_05")
        first, second = fit_model(frame, x, config), fit_model(frame, changed, config)
        np.testing.assert_allclose(first["beta"], second["beta"], rtol=0, atol=1e-12)
        self.assertEqual(first["beta"][1], 0.)
        self.assertEqual(second["beta"][1], 0.)
        a, b = predict_model(first, x), predict_model(second, changed)
        for positions in [slice(0, 3), slice(3, 6)]:
            np.testing.assert_allclose(np.diff(a[positions]), np.diff(b[positions]), rtol=0, atol=1e-12)

    def test_synthetic_fit_recovers_direction_and_replays_saved_parameters(self):
        frame = toy_frame()
        x = np.column_stack([frame.measured_delta.to_numpy(), np.ones(6)])
        for config in CONFIGS:
            with self.subTest(config=config["id"]):
                model = fit_model(frame, x, config)
                score = predict_model(model, x)
                self.assertGreater(model["beta"][0], 0.)
                self.assertEqual(model["beta"][1], 0.)
                self.assertTrue((np.diff(score[:3]) > 0).all())
                self.assertTrue((np.diff(score[3:]) > 0).all())
                replay = ((x - model["mean"]) / model["scale"]) @ model["beta"]
                np.testing.assert_array_equal(score, replay)


if __name__ == "__main__":
    unittest.main()
