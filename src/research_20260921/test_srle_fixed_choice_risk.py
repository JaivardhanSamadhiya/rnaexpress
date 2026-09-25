"""Synthetic risk and paired-identity tests, with no biological inputs."""
from .srle_fixed_choice_risk import MODELS, indicators, paired_indicators, validate_frame, summarize
import unittest
import numpy as np
import pandas as pd


class FixedChoiceRiskTests(unittest.TestCase):
    def frame(self):
        rows = []
        # One class has one parent, another has three; both must receive equal weight.
        for parent, comp, value in [('p0', 'A', .3), ('p1', 'B', -.1), ('p2', 'B', -.1), ('p3', 'B', -.1)]:
            for model in MODELS:
                for direction in (-1, 1):
                    for rep in (1, 2):
                        rows.append(dict(parent=parent, composition=comp, model=model,
                                         direction=direction, replicate=rep, selected='fixed_'+str(direction),
                                         oriented_nrs_change=value))
        return pd.DataFrame(rows)

    def test_sign_ties_scale_and_mean_loss(self):
        a = indicators([.2, -.1, 0, 1e-13, -1e-13])
        np.testing.assert_array_equal(a['fraction_positive'], [1, 0, 0, 0, 0])
        np.testing.assert_array_equal(a['fraction_negative'], [0, 1, 0, 0, 0])
        np.testing.assert_array_equal(a['fraction_numerical_tie'], [0, 0, 1, 1, 1])
        np.testing.assert_array_equal(a['fraction_harm_at_least_0_1'], [0, 1, 0, 0, 0])
        np.testing.assert_allclose(a['mean_loss_including_zero'], [0, .1, 0, 0, 0])

    def test_disagreement_is_not_called_repeatable_benefit(self):
        a = paired_indicators([.3, -.2, .2, 0], [.1, -.1, -.2, .1])
        np.testing.assert_array_equal(a['fraction_positive_both'], [1, 0, 0, 0])
        np.testing.assert_array_equal(a['fraction_negative_both'], [0, 1, 0, 0])
        np.testing.assert_array_equal(a['fraction_opposite_signs'], [0, 0, 1, 0])
        np.testing.assert_array_equal(a['fraction_involving_tie'], [0, 0, 0, 1])

    def test_selection_changes_and_missing_replicates_fail(self):
        frame = self.frame(); validate_frame(frame)
        frame.loc[0, 'selected'] = 'different'
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            validate_frame(frame)
        with self.assertRaisesRegex(ValueError, 'all comparison decisions'):
            validate_frame(self.frame().iloc[1:])

    def test_classes_not_number_of_parents_determine_weight(self):
        result, _, _ = summarize(self.frame())
        value = result['kmer123']['1']['replicates']['1']
        self.assertAlmostEqual(value['mean_directed_change']['estimate'], .1)
        self.assertAlmostEqual(value['fraction_negative']['estimate'], .5)
        self.assertAlmostEqual(result['kmer123']['1']['paired_replicates']['fraction_positive_both']['estimate'], .5)


if __name__ == '__main__':
    unittest.main()
