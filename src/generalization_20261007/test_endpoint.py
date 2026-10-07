"""Synthetic tests for auxiliary purging and outcome-free endpoint dispatch."""

import unittest
from .route_endpoint import np, pd, select_auxiliary, build_features, predict_model


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.core = pd.DataFrame([
            {"intervention_id": "tr", "biological_component": "train", "parent_sequence": "AAAA", "mutant_sequence": "AAAC"},
            {"intervention_id": "outer", "biological_component": "held", "parent_sequence": "GGGG", "mutant_sequence": "GGGC"},
            {"intervention_id": "inner", "biological_component": "inner", "parent_sequence": "TTTT", "mutant_sequence": "TTTA"},
        ])
        self.aux = pd.DataFrame([
            {"intervention_id": "a", "biological_component": "a-unit", "parent_sequence": "GGGG", "mutant_sequence": "GGGA"},
            {"intervention_id": "a-sibling", "biological_component": "a-unit", "parent_sequence": "CCCC", "mutant_sequence": "CCCA"},
            {"intervention_id": "b", "biological_component": "held", "parent_sequence": "ACAC", "mutant_sequence": "ACAT"},
            {"intervention_id": "c", "biological_component": "c-unit", "parent_sequence": "TATA", "mutant_sequence": "TATT"},
            {"intervention_id": "d", "biological_component": "d-unit", "parent_sequence": "TTTA", "mutant_sequence": "TTTC"},
        ])

    def test_outer_and_inner_exact_any_allele_and_component_exclusion(self):
        outer, receipt = select_auxiliary(self.aux, self.core, {"tr", "inner"})
        np.testing.assert_array_equal(outer, [False, False, False, True, True])
        inner, receipt = select_auxiliary(self.aux, self.core, {"tr"})
        np.testing.assert_array_equal(inner, [False, False, False, True, False])
        self.assertEqual(receipt["retained_auxiliary_ids"], ["c"])
        self.assertEqual(receipt["excluded_core_rows"], 2)

    def test_exclusion_does_not_depend_on_auxiliary_labels(self):
        keep, receipt = select_auxiliary(self.aux, self.core, {"tr"})
        modified = self.aux.assign(measured_delta=[10., -10., 99., -99., 0.])
        alternate, alternate_receipt = select_auxiliary(modified, self.core, {"tr"})
        np.testing.assert_array_equal(keep, alternate)
        self.assertEqual(receipt, alternate_receipt)

    def test_unknown_core_ids_rejected(self):
        with self.assertRaises(ValueError):
            select_auxiliary(self.aux, self.core, {"not-in-frozen-core"})

    def test_endpoint_is_known_metadata_not_source_or_outcome(self):
        frame = pd.DataFrame({"endpoint_class": ["projection", "nuclear_cytoplasmic"]})
        feature = build_features(frame, np.zeros((2, 246)))
        np.testing.assert_array_equal(feature[:, -1], [0., 1.])
        self.assertEqual(feature.shape, (2, 247))
        with self.assertRaises(ValueError):
            build_features(pd.DataFrame({"endpoint_class": ["unknown"]}), np.zeros((1, 246)))

    def test_dispatch_and_explicit_unsupported_head(self):
        x = np.zeros((3, 247)); x[:, 0] = [1., 2., 3.]; x[:, -1] = [0., 1., 0.]
        head = {"mean": [0.] * 246, "scale": [1.] * 246, "beta": [2.] + [0.] * 245}
        model = {"heads": {"0": head, "1": {"unsupported": True}}}
        np.testing.assert_array_equal(predict_model(model, x), [2., 0., 6.])
        x[1, -1] = 2.
        with self.assertRaises(ValueError):
            predict_model(model, x)


if __name__ == "__main__":
    unittest.main()
