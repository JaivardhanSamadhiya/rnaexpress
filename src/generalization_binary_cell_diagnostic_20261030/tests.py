import unittest
from .analyze import analyze,CELLS


def fixture(conflict=False):
    rows = []
    for cell in CELLS:
        for direction,sequence in ((-1,'A'),(1,'C')):
            effect = float(direction)*(-1 if conflict and cell == CELLS[1] else 1)
            rows.append(dict(cell_type=cell,biological_component='gene',
                parent_context_id='assay|'+cell+'|context',direction=direction,candidates=2,
                selected_score=float(direction),selected_effect=effect,
                selected_mutant_sequence=sequence,regret=float(effect != direction)))
    return rows


class DiagnosticTests(unittest.TestCase):
    def test_concordant_truth_has_zero_shared_order_floor(self):
        got = analyze(fixture())
        self.assertEqual(got['cell_invariant_oracle_binary_conditional_regret_floor'],0.)
        self.assertEqual(got['saved_predictor_binary_regret_contribution'],0.)

    def test_conflict_has_half_regret_even_for_outcome_oracle(self):
        got = analyze(fixture(True))
        self.assertEqual(got['cell_invariant_oracle_binary_conditional_regret_floor'],.5)
        self.assertEqual(got['saved_predictor_binary_regret_contribution'],.5)
        self.assertEqual(got['weighted_discordant_binary_fraction'],1.)

    def test_order_and_effect_magnitude_do_not_change_normalized_binary_bound(self):
        rows = fixture(True)
        for r in rows:r['selected_effect'] *= 100.
        self.assertEqual(analyze(rows),analyze(list(reversed(rows))))
        self.assertEqual(analyze(rows),analyze(fixture(True)))

    def test_incomplete_candidate_roster_or_constant_score_rejects(self):
        rows = fixture();rows[0]['selected_mutant_sequence']='G'
        with self.assertRaisesRegex(ValueError,'alleles differ'):analyze(rows)
        rows = fixture();rows[0]['selected_score']=1.
        with self.assertRaisesRegex(ValueError,'unrecoverable'):analyze(rows)
        with self.assertRaisesRegex(ValueError,'both cells required'):analyze(fixture()[:2])

    def test_component_and_context_weighting_not_raw_context_counts(self):
        rows = fixture(True)
        for i in (1,2):
            extra = fixture()
            for r in extra:
                r['biological_component']='other'
                r['parent_context_id'] += str(i)
            rows += extra
        got = analyze(rows)
        self.assertEqual(got['weighted_discordant_binary_fraction'],.5)
        self.assertEqual(got['unweighted_discordant_binary_fraction'],1/3)


if __name__ == '__main__':unittest.main()
