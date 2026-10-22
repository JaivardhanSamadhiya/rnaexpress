"""Invented stdlib objective/mask checks; no optimizer, numerical package or data."""
import ast
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest
from .spec import NS, CONFIGS, COUNTS, CELLS, FOLDS
from .kernels import shared_value_gradient, independent_value_gradient, pair_rms, dot
from .contracts import union_masks, exact_pairs, preference_weights, choose_config, paired_macro_regret

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'src' / NS
OUT = ROOT / 'results' / NS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invented_rows():
    rows = []
    for fold in FOLDS:
        for cell in CELLS:
            for candidate in (0, 1):
                rows.append({'intervention_id': f'{fold}:{cell}:{candidate}',
                             'cell_type': cell, 'biological_component': f'g{fold}',
                             'gene_transcript': f'gene{fold}', 'held_parent_fold': fold,
                             'parent_context_id': f'g{fold}:{cell}',
                             'parent_sequence': f'invented_parent_{fold}',
                             'mutant_sequence': f'invented_mutant_{fold}_{candidate}'})
    return rows


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.x = [[1., -.4], [-.5, .2], [.8, .3], [-.1, 1.2]]
        self.y = [1, -1, -1, 1]
        self.w = [.1, .4, .2, .3]
        self.c = [1, 1, -1, -1]
        self.b, self.d = [.2, -.3], [.6, .7]

    def test_multiplier1_independent_objective_and_gradient(self):
        u = [b + d for b, d in zip(self.b, self.d)]
        v = [b - d for b, d in zip(self.b, self.d)]
        for config in CONFIGS:
            lam = config['penalty']
            lhs, gb, gd = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, self.d, lam, 1.)
            rhs, gu, gv = independent_value_gradient(self.x, self.y, self.w, self.c, u, v, lam)
            self.assertAlmostEqual(lhs, rhs, places=13)
            for j in range(2):
                self.assertAlmostEqual(gb[j], gu[j] + gv[j], places=13)
                self.assertAlmostEqual(gd[j], gu[j] - gv[j], places=13)

    def test_separate_cell_loss_has_matching_lambda(self):
        u, v, lam = [.3, .1], [-.7, .5], .05
        joint, _, _ = independent_value_gradient(self.x, self.y, self.w, self.c, u, v, lam)
        expected = 0.
        for cell, coef in ((1, u), (-1, v)):
            loss = math.fsum(2 * w * math.log1p(math.exp(-y * dot(x, coef)))
                            for x, y, w, c in zip(self.x, self.y, self.w, self.c) if c == cell)
            expected += .5 * (loss + lam / 2 * dot(coef, coef))
        self.assertAlmostEqual(joint, expected, places=13)

    def test_multiplier10_is_only_fixed_extra_deviation_penalty(self):
        a, ga, da = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, self.d, .05, 1.)
        b, gb, db = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, self.d, .05, 10.)
        self.assertAlmostEqual(b - a, .05 / 2 * 9 * dot(self.d, self.d), places=13)
        self.assertEqual(ga, gb)
        for j in range(2): self.assertAlmostEqual(db[j] - da[j], .05 * 9 * self.d[j], places=13)

    def test_finite_difference_joint_gradient(self):
        lam, h = .05, 1e-6
        _, gb, gd = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, self.d, lam, 10.)
        original = self.b + self.d
        for j, analytic in enumerate(gb + gd):
            left, right = original.copy(), original.copy()
            left[j] -= h; right[j] += h
            f = lambda q: shared_value_gradient(self.x, self.y, self.w, self.c, q[:2], q[2:], lam, 10.)[0]
            self.assertLess(abs((f(right) - f(left)) / (2 * h) - analytic), 2e-9)

    def test_zero_deviation_equals_pooled_and_equal_independent_heads(self):
        a = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, [0., 0.], .05, 10.)[0]
        b = independent_value_gradient(self.x, self.y, self.w, self.c, self.b, self.b, .05)[0]
        self.assertAlmostEqual(a, b, places=13)

    def test_sign_and_pair_reversal(self):
        a = shared_value_gradient(self.x, self.y, self.w, self.c, self.b, self.d, .05)
        b = shared_value_gradient([[-v for v in row] for row in self.x], [-v for v in self.y],
                                  self.w, self.c, self.b, self.d, .05)
        for x, y in zip([a[0]] + a[1] + a[2], [b[0]] + b[1] + b[2]):
            self.assertAlmostEqual(x, y, places=13)

    def test_extreme_margins_finite(self):
        result = shared_value_gradient([[1000.], [-1000.]], [1, 1], [.5, .5], [1, -1], [1.], [0.], .05)
        self.assertTrue(all(math.isfinite(x) for x in [result[0]] + result[1] + result[2]))

    def test_weight_or_cell_mass_mismatch_fails(self):
        for weights in ([.1, .3, .2, .3], [.1, -.1, .5, .5], [.1, .3, .2, .4]):
            with self.assertRaises(AssertionError):
                shared_value_gradient(self.x, self.y, weights, self.c, self.b, self.d, .05)

    def test_common_pair_rms_and_unsupported_parent_constant(self):
        x = [[2., 0.], [-1., 0.], [3., 0.], [.5, 0.]]
        scales = pair_rms(x, self.w)
        self.assertEqual(scales[1], 0.)
        self.assertAlmostEqual(math.fsum(w * (row[0] / scales[0]) ** 2 for row, w in zip(x, self.w)), 1.)
        _, gb, gd = shared_value_gradient(x, self.y, self.w, self.c, [.2, 0.], [.3, 0.], .05)
        self.assertEqual((gb[1], gd[1]), (0., 0.))


class ContractTests(unittest.TestCase):
    def test_both_cells_held_fold_and_complete_source_menus(self):
        rows = invented_rows()
        for fold in FOLDS:
            tr, te = union_masks(rows, fold)
            self.assertEqual(sum(tr), 8); self.assertEqual(sum(te), 4)
            self.assertEqual({r['cell_type'] for r, use in zip(rows, te) if use}, set(CELLS))
            self.assertTrue(all(not (a and b) for a, b in zip(tr, te)))

    def test_inner_masks_hold_both_remaining_cells(self):
        rows = invented_rows(); tr, _ = union_masks(rows, 0)
        source = [r for r, use in zip(rows, tr) if use]
        for fold in (1, 2):
            training, validation = union_masks(source, fold)
            self.assertEqual((sum(training), sum(validation)), (4, 4))

    def test_gene_alias_contradiction_stops_without_repair(self):
        rows = invented_rows()
        for r in rows:
            if r['held_parent_fold'] == 1: r['gene_transcript'] = ' GENE0 '
        with self.assertRaises(AssertionError): union_masks(rows, 0)

    def test_original_allele_contradiction_stops_without_repair(self):
        rows = invented_rows(); rows[4]['mutant_sequence'] = rows[0]['parent_sequence']
        with self.assertRaises(AssertionError): union_masks(rows, 0)

    def test_partial_menu_stops(self):
        rows = invented_rows(); rows[4]['parent_context_id'] = rows[0]['parent_context_id']
        with self.assertRaises(AssertionError): union_masks(rows, 0)

    def test_exact_pairing_and_no_intersection_trimming(self):
        rows = invented_rows(); pairs, missing = exact_pairs(rows)
        self.assertEqual((len(pairs), len(missing)), (3, 0))
        rows[-1]['mutant_sequence'] = 'different_nonintersection_candidate'
        pairs, missing = exact_pairs(rows)
        self.assertEqual((len(pairs), len(missing)), (2, 2))

    def test_duplicate_candidate_fails_pairing(self):
        rows = invented_rows(); rows[1]['mutant_sequence'] = rows[0]['mutant_sequence']
        with self.assertRaises(AssertionError): exact_pairs(rows)

    def test_cell_gene_context_pair_weights_balance_unequal_menus(self):
        records = []
        for cell in CELLS:
            for gene in ('g0', 'g1'):
                for context in range(3 if cell == 'CAD' and gene == 'g0' else 1):
                    for pair in range(context + 1):
                        records.append({'cell_type': cell, 'biological_component': gene,
                                        'parent_context_id': f'{cell}:{gene}:{context}'})
        weights = preference_weights(records)
        totals = defaultdict(float)
        for row, weight in zip(records, weights): totals[row['cell_type'], row['biological_component']] += weight
        for total in totals.values(): self.assertAlmostEqual(total, .25)

    def test_oof_combination_is_not_mean_of_unequal_fold_means(self):
        records = []
        for cell in CELLS:
            for gene, value in (('g0', 0.), ('g1', 0.), ('g2', 1.)):
                for direction in (-1, 1):
                    records.append({'cell_type': cell, 'biological_component': gene,
                                    'parent_context_id': cell + gene, 'direction': direction, 'regret': value})
        self.assertAlmostEqual(paired_macro_regret(records), 1. / 3.)
        self.assertNotAlmostEqual(paired_macro_regret(records), .5)
        with self.assertRaises(AssertionError): paired_macro_regret(records + [records[0]])

    def test_fixed_source_selection_order_and_tolerance(self):
        self.assertEqual(choose_config([.3 + 5e-13, .3, .4])['id'], 'pair_005')
        self.assertEqual(choose_config([.4, .3, .2])['id'], 'pair_5')
        with self.assertRaises(AssertionError): choose_config([.2, float('nan'), .3])

    def test_fit_counts(self):
        self.assertEqual(3 * (2 * 3 + 1) * 3, COUNTS['arm_checkpoints'])
        self.assertEqual(3 * (2 * 3 + 1) * (1 + 2 + 1), COUNTS['optimizer_units'])
        self.assertEqual(COUNTS['paired_contexts'] * 2, COUNTS['paired_directional_decisions'])


def run():
    forbidden = ('numpy', 'pandas', 'scipy', 'torch', 'openvino', 'sklearn')
    assert not any(name in sys.modules for name in forbidden)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful()
    sources = sorted(SOURCE.glob('*.py'))
    for path in sources: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    payload = {'status': 'PASS_INVENTED_STDLIB_DESIGN_CHECKS', 'tests': result.testsRun,
               'prepared_date': '2026-10-21', 'project_dataset_reads': 0,
               'project_feature_reads': 0, 'project_outcome_reads': 0, 'models_fitted': 0,
               'scientific_runtimes_imported': False, 'actual_optimizer_calls': 0,
               'source_files': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}}
    target = OUT / 'synthetic_tests_receipt.json'
    with target.open('xb') as handle: handle.write((json.dumps(payload, sort_keys=True, indent=2) + '\n').encode())
    print('DESIGN_ONLY_TESTS_PASS', result.testsRun, flush=True)


if __name__ == '__main__': run()
