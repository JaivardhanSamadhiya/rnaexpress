"""A constructed objective mismatch; no RNA data and no optimization."""
import itertools
import math
from .loss import menu_loss


def surrogate_mismatch():
    # Twenty invented candidates yield 190 pairs, below the historical cap256.
    truth = tuple(i / 19. for i in range(20))
    a = (truth[-1], *truth[1:-1], truth[0])
    b = (truth[0], *reversed(truth[1:-1]), truth[-1])
    rows = {}
    for name, scores in (('correct_middle_wrong_extrema', a),
                         ('wrong_middle_correct_extrema', b)):
        margins = tuple(scores[j] - scores[i]
                        for i, j in itertools.combinations(range(20), 2))
        pair_loss = math.fsum(math.log1p(math.exp(-v)) for v in margins) / len(margins)
        regrets = tuple((max(d*y for y in truth) -
                         d*truth[max(range(20), key=lambda i: d*scores[i])])
                        for d in (1., -1.))  # The effect span is exactly1.
        rows[name] = {'pair_accuracy': sum(v > 0 for v in margins) / len(margins),
                      'pair_logistic_loss': pair_loss,
                      'two_direction_regret': math.fsum(regrets) / 2.,
                      'menu_surrogate': menu_loss(scores, truth)[0],
                      'score_squared_norm': math.fsum(v*v for v in scores)}
    return {'status': 'INVENTED_OBJECTIVE_MISMATCH_NOT_BIOLOGICAL_EVIDENCE',
            'candidates': 20, 'pairs': 190, 'fit_calls': 0, 'predictors': rows}
