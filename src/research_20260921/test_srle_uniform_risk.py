"""Synthetic checks of exact random-choice risk expectations; no source data."""
from .srle_uniform_risk import uniform_metrics, existing_candidates, class_aggregate, validate_archived_numeric
import unittest
import pandas as pd


class UniformRiskTests(unittest.TestCase):
    def test_nonfinite_archived_values_cannot_silently_pass(self):
        for value in [float('nan'), float('inf'), float('-inf')]:
            for column in ['oriented_nrs_change', 'regret_gain']:
                row = {'oriented_nrs_change': 0., 'regret_gain': 0.}
                row[column] = value
                with self.assertRaisesRegex(ValueError, 'Nonfinite archived'):
                    validate_archived_numeric(pd.DataFrame([row]))

    def test_nonlinear_metrics_are_computed_before_expectations(self):
        result = uniform_metrics([[2., -1.], [-1., 2.]])
        self.assertEqual(result['replicates']['1']['mean_directed_change'], .5)
        self.assertEqual(result['replicates']['1']['fraction_negative'], .5)
        self.assertEqual(result['paired_replicates']['fraction_positive_both'], 0.)
        self.assertEqual(result['paired_replicates']['fraction_opposite_signs'], 1.)
        self.assertEqual(result['paired_replicates']['mean_smaller_directed_change'], -1.)

    def test_candidate_identity_is_shared_across_replicates(self):
        result = uniform_metrics([[1., 1.], [-1., -1.]])
        self.assertEqual(result['paired_replicates']['fraction_positive_both'], .5)
        self.assertEqual(result['paired_replicates']['fraction_negative_both'], .5)
        self.assertEqual(result['paired_replicates']['fraction_opposite_signs'], 0.)

    def test_filters_existing_identifiers_without_adding_candidates(self):
        candidates = {'AACCGT', 'ACACGT', 'CCGTAA', 'AACCAT'}
        self.assertEqual(existing_candidates('AACCGT', candidates), ['ACACGT'])
        self.assertLessEqual(set(existing_candidates('AACCGT', candidates)), candidates)

    def test_parents_get_equal_weight_after_candidate_expectations(self):
        first = uniform_metrics([[1., 1.], [-1., -1.]])
        second = uniform_metrics([[1., 1.]] * 8)
        rows = [{'composition': 'synthetic', 'direction': 1, 'replicate': 1,
                 'fraction_positive': item['replicates']['1']['fraction_positive']}
                for item in (first, second)]
        result = class_aggregate(pd.DataFrame(rows))
        self.assertAlmostEqual(result.fraction_positive.iloc[0], .75)
        self.assertEqual(result.parent_count.iloc[0], 2)


if __name__ == '__main__':
    unittest.main()
