"""Invented saved-decision fixtures; no actual report or project data opened."""
from copy import deepcopy
import unittest
from .analyze import analyze,ARMS


def fixture():
    rows=[]
    # Per cell: two contexts in g1 and one in g2. Their masses per cell are
    # 1/4,1/4,1/2, rather than one third each.
    for cell in ('c1','c2'):
        for gene,context,n,regret in (('g1','a',2,1.),('g1','b',3,0.),('g2','c',4,.5)):
            for direction in (-1,1):
                rows.append({'cell_type':cell,'biological_component':gene,
                             'parent_context_id':cell+context,'direction':direction,
                             'candidates':n,'regret':regret,'selected_id':str(direction),
                             'selected_score':float(direction)})
    return {'status':'NO-GO','primary_decisions':{arm:deepcopy(rows) for arm in ARMS}}


class FeasibilityTests(unittest.TestCase):
    def test_weights_conditional_regrets_and_restricted_bound(self):
        result=analyze(fixture())
        self.assertEqual(result['menus_per_arm'],6)
        self.assertEqual(result['menu_size_bins']['2']['primary_weight'],.25)
        self.assertEqual(result['menu_size_bins']['3']['primary_weight'],.25)
        self.assertEqual(result['menu_size_bins']['4']['primary_weight'],.5)
        for value in result['arms'].values():
            self.assertEqual(value['macro_regret_recomputed'],.5)
            self.assertEqual(value['binary_implied_tie_aware_pair_accuracy'],0.)
            self.assertEqual(value['multicandidate_current_regret_contribution'],.25)
            self.assertEqual(value['restricted_best_possible_regret_if_only_multicandidate_choices_change'],.25)

    def test_exact_constant_score_detection(self):
        f=fixture()
        for rows in f['primary_decisions'].values():
            for row in rows:
                if row['parent_context_id']=='c1c':row.update(selected_score=0.,selected_id='tie')
        result=analyze(f)
        for value in result['arms'].values():
            self.assertEqual(value['exact_constant_score_menus'],1)
            self.assertEqual(value['exact_constant_score_primary_weight'],.25)

    def test_missing_or_duplicate_direction_and_unequal_arm_roster_fail(self):
        f=fixture();f['primary_decisions']['pooled'].pop()
        with self.assertRaises(ValueError):analyze(f)
        f=fixture();f['primary_decisions']['pooled'].append(dict(f['primary_decisions']['pooled'][0]))
        with self.assertRaises(ValueError):analyze(f)
        f=fixture();f['primary_decisions']['pooled']=f['primary_decisions']['pooled'][2:]
        with self.assertRaises(ValueError):analyze(f)

    def test_bad_constant_regret_and_reversed_extrema_fail(self):
        f=fixture()
        for row in f['primary_decisions']['pooled'][:2]:row.update(selected_score=0.,selected_id='same')
        with self.assertRaises(ValueError):analyze(f)
        f=fixture();f['primary_decisions']['pooled'][0]['selected_score']=100.
        with self.assertRaises(ValueError):analyze(f)


if __name__=='__main__':unittest.main()
