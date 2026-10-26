"""Mathematical checks on invented menus only; no project inputs or fits."""
import itertools
import math
import random
import unittest
from .loss import menu_loss


def hard_regret(scores, effects):
    span = max(effects) - min(effects)
    return math.fsum((max(d*y for y in effects) -
                      d*effects[max(range(len(scores)), key=lambda i: d*scores[i])]) / span
                     for d in (1., -1.)) / 2.


class MenuLossTests(unittest.TestCase):
    def test_gradient_including_tied_best(self):
        for effects in ((-2., .1, 1.4, 3.), (1., 1., 0., 0.)):
            scores = [.3, -.7, .4, .9]
            _, gradient = menu_loss(scores, effects)
            for i, want in enumerate(gradient):
                plus, minus = list(scores), list(scores)
                plus[i] += 1e-6; minus[i] -= 1e-6
                got = (menu_loss(plus, effects)[0] - menu_loss(minus, effects)[0]) / 2e-6
                self.assertAlmostEqual(got, want, delta=2e-9)
            self.assertAlmostEqual(math.fsum(gradient), 0., delta=1e-14)

    def test_upper_bound_every_small_permutation(self):
        for scores in itertools.product((-2., 0., 2.), repeat=4):
            for effects in ((0., .1, .8, 1.), (0., 1., 1., 0.)):
                loss, _ = menu_loss(scores, effects)
                self.assertGreaterEqual(loss + 1e-14, hard_regret(scores, effects))

    def test_convexity_on_invented_segments(self):
        rng = random.Random(20261026)
        for _ in range(200):
            a, b = ([rng.uniform(-4, 4) for _ in range(5)] for _ in range(2))
            t = rng.random(); effects = [0., 1., .6, .2, 1.]
            value = menu_loss([t*x+(1-t)*y for x,y in zip(a,b)], effects)[0]
            bound = t*menu_loss(a,effects)[0] + (1-t)*menu_loss(b,effects)[0]
            self.assertLessEqual(value, bound + 1e-13)

    def test_permutation_invariance_and_ties(self):
        scores, effects = [.2, -.8, .7, .3], [1., 0., 1., 0.]
        loss, gradient = menu_loss(scores, effects)
        for order in itertools.permutations(range(4)):
            value, got = menu_loss([scores[i] for i in order], [effects[i] for i in order])
            self.assertAlmostEqual(value, loss, delta=1e-14)
            for j, i in enumerate(order):self.assertAlmostEqual(got[j],gradient[i],delta=1e-14)

    def test_offsets_positive_affine_effects_and_sign(self):
        scores, effects = [.25, -.75, 1.5], [-2., .5, 3.]
        loss, gradient = menu_loss(scores,effects)
        for s,y in (([v+1024 for v in scores],effects),
                    (scores,[4*v+8 for v in effects]),
                    (scores,[-v for v in effects])):
            value, got = menu_loss(s,y)
            if y == [-v for v in effects]:
                # Negating effects requires negating scores for identical behavior.
                value, got = menu_loss([-v for v in scores],y)
                got = tuple(-v for v in got)
            self.assertAlmostEqual(value,loss,delta=1e-13)
            for a,b in zip(got,gradient):self.assertAlmostEqual(a,b,delta=1e-13)

    def test_linear_chain_rule_and_regularization(self):
        x = ((1.,2.),(-1.,.5),(.25,-2.)); y = (-1.,.2,2.); beta = [.3,-.4]; penalty=.05
        def objective(b):
            loss,g = menu_loss([math.fsum(a*v for a,v in zip(row,b)) for row in x],y)
            return loss + penalty/2*math.fsum(v*v for v in b), tuple(
                math.fsum(g[i]*row[j] for i,row in enumerate(x))+penalty*b[j] for j in range(2))
        _, gradient = objective(beta)
        for j,want in enumerate(gradient):
            a,b=list(beta),list(beta);a[j]+=1e-6;b[j]-=1e-6
            self.assertAlmostEqual((objective(a)[0]-objective(b)[0])/2e-6,want,delta=2e-9)

    def test_stable_large_scores(self):
        loss,gradient=menu_loss((1e6,-1e6,0.),(0.,1.,.5))
        self.assertTrue(math.isfinite(loss) and all(math.isfinite(v) for v in gradient))
        self.assertGreaterEqual(loss,hard_regret((1e6,-1e6,0.),(0.,1.,.5)))

    def test_reject_invalid_inputs(self):
        for scores,effects,kwargs in (((1.,),(0.,),{}),((1.,2.),(0.,),{}),
                ((1.,2.),(0.,0.),{}),((math.nan,2.),(0.,1.),{}),
                ((1.,2.),(0.,math.inf),{}),((1.,2.),(0.,1.),{'temperature':0}),
                ((1.,2.),(0.,1.),{'temperature':math.nan}),
                ((1e308,-1e308),(0.,1.),{}),((1.,2.),(-1e308,1e308),{})):
            with self.assertRaises(ValueError):menu_loss(scores,effects,**kwargs)

    def test_score_scale_is_not_an_invariance(self):
        # Fixed temperature and score regularization matter; do not claim the
        # surrogate is invariant to multiplying a predictor's scores.
        self.assertNotAlmostEqual(menu_loss((0.,1.,2.),(0.,.2,1.))[0],
                                  menu_loss((0.,2.,4.),(0.,.2,1.))[0])

    def test_invented_surrogate_mismatch(self):
        from .example import surrogate_mismatch
        result = surrogate_mismatch()
        a = result['predictors']['correct_middle_wrong_extrema']
        b = result['predictors']['wrong_middle_correct_extrema']
        self.assertEqual(result['pairs'], 190)
        self.assertEqual(a['score_squared_norm'], b['score_squared_norm'])
        self.assertGreater(a['pair_accuracy'], b['pair_accuracy'])
        self.assertLess(a['pair_logistic_loss'], b['pair_logistic_loss'])
        self.assertEqual(a['two_direction_regret'], 1.)
        self.assertEqual(b['two_direction_regret'], 0.)
        self.assertGreater(a['menu_surrogate'], b['menu_surrogate'])


if __name__ == '__main__':unittest.main()
