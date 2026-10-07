"""Scoped synthetic-only tests; no project data or fitting."""

import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path
from . import feasibility as f
from . import scoring as s
from .common import np, pd, RBP_ART, RBP_OUT, CONTROLS, ART, sha256
from .assemble import validate_control_reference
from .engine import select_config, checkpoint_identity
from .routes import module
from .verify import independent_decisions, bounded_canonical_scores, independent_scores, decisions_roster_check
from .common import STUDIES
from .gate import incremental_checks, strict_checks
from src.generalization_rbp_20261007.production import requests, pooled_blocks as marginal_pool
from src.generalization_rbp_20261007.scoring import smooth_log_odds
from src.generalization_rbp_20261007.projection import generate
from . import production


class JointFeasibilityTests(unittest.TestCase):
    def test_all_a(self):
        matrix = f.joint_probabilities('A' * 32)
        for width in range(1, 26):
            self.assertTrue(f.np.allclose(matrix[:33 - width, width], 1., atol=1e-12))
            self.assertTrue(f.np.isnan(matrix[33 - width:, width]).all())

    def test_fixed_global_equivalence(self):
        records, maximum, _ = f.check_fixed_intervals()
        self.assertGreater(len(records), 250)
        self.assertTrue(all(row['pass'] for row in records), str(sorted(records, key=lambda row: row['abs_error'])[-3:]))

    def test_joint_not_marginal(self):
        matrix = f.joint_probabilities('GGGAAACCC')
        self.assertLess(matrix[0, 4], matrix[:4, 1].mean() - 1e-3)
        self.assertLessEqual(matrix[0, 4], matrix[:4, 1].min() + 1e-10)

    def test_monotonic_opening(self):
        matrix = f.joint_probabilities('GCGCAUGCGCAUGGGAAACCCACGUGCAUGCAGC')
        for width in range(2, 26):
            self.assertTrue((matrix[:len(matrix) - width + 1, width] <= matrix[:len(matrix) - width + 1, width - 1] + 1e-10).all())

    def test_invalid(self):
        for sequence in ('', 'NNNN'):
            with self.assertRaises(ValueError):
                f.joint_probabilities(sequence)
        with self.assertRaises(ValueError):
            f.joint_probabilities('A' * 32, 26)
        with self.assertRaises(ValueError):
            f.constrained_probability('AAAA', 3, 2)

    def test_dna_rna_equal(self):
        left = f.joint_probabilities('GCGTGCATGCAA')
        right = f.joint_probabilities('GCGUGCAUGCAA')
        self.assertTrue(f.np.array_equal(left, right, equal_nan=True))


def groups():
    matrices = [np.ones((4, 4)), np.array([[9., 1., 1., 1.], [1., 9., 1., 1.], [1., 1., 9., 1.], [1., 1., 1., 9.]])]
    return [(4, np.array([0, 1]), np.stack([smooth_log_odds(value) for value in matrices]))]


def neutral_probability(length):
    result = np.full((length, 26), np.nan)
    for width in range(1, min(length, 25) + 1):
        result[:length - width + 1, width] = 1.
    return result


class JointPoolAndControlTests(unittest.TestCase):
    def test_all_unpaired_is_exact_raw_control(self):
        sequence = 'ACGUACGUACGU'; blocks = s.scan(sequence, groups())
        actual = s.pooled_blocks(blocks, len(sequence), (1, 9), neutral_probability(len(sequence)))
        expected = marginal_pool(blocks, len(sequence), (1, 9), np.ones(len(sequence)))
        np.testing.assert_array_equal(actual, expected)

    def test_direct_window_joint_pool(self):
        sequence = 'ACGUACGU'; blocks = s.scan(sequence, groups()); table = neutral_probability(8)
        table[:5, 4] = np.array([.1, .2, .3, .4, .5])
        actual = s.pooled_blocks(blocks, 8, (4,), table)
        values = blocks[0][2] * table[:5, 4][None, :]
        np.testing.assert_array_equal(actual[:2, 0], values.mean(1)); np.testing.assert_array_equal(actual[:2, 1], values.max(1))
        np.testing.assert_array_equal(actual[:2, 2], values[:, 1:].mean(1)); np.testing.assert_array_equal(actual[:2, 3], values[:, 1:].max(1))

    def test_empty_affected_pool(self):
        sequence = 'ACGUACGU'; actual = s.pooled_blocks(s.scan(sequence, groups()), 8, (), neutral_probability(8))
        np.testing.assert_array_equal(actual[:, 2:], 0.)

    def test_no_edit_and_reversal(self):
        parent, mutant = 'ACGUACGUACGU', 'ACGAACGUACGU'; a, b = f.joint_probabilities(parent), f.joint_probabilities(mutant)
        self.assertTrue(np.array_equal(s.allele_delta(parent, parent, a, a, groups()), np.zeros(256, np.float32)))
        np.testing.assert_array_equal(s.allele_delta(parent, mutant, a, b, groups()), -s.allele_delta(mutant, parent, b, a, groups()))

    def test_delta_projection_commutes_after_pooling(self):
        matrices = generate(); a = np.arange(421 * 4, dtype=float).reshape(421, 4) / 421; b = a ** .5
        np.testing.assert_allclose(s.project(b - a, matrices), s.project(b, matrices) - s.project(a, matrices), atol=1e-11, rtol=1e-12)
        self.assertTrue(all(matrix.dtype == np.float32 for matrix in matrices)); self.assertTrue(all(np.array_equal(a, b) for a, b in zip(generate(), matrices)))

    def test_do_not_project_before_max(self):
        windows = np.array([[1., 0.], [0., 1.]]); projection = np.array([[1.], [-1.]])
        self.assertNotEqual(float(windows.max(1) @ projection[:, 0]), float((windows.T @ projection).max()))

    def test_duplicate_control_exact_copy(self):
        access = np.arange(4 * 758, dtype=np.float64).reshape(4, 758); duplicate = np.column_stack((access, access[:, 502:758]))
        self.assertEqual(duplicate.shape, (4, 1014)); np.testing.assert_array_equal(duplicate[:, :758], access)
        np.testing.assert_array_equal(duplicate[:, 758:], access[:, 502:758])

    def test_source_control_binding(self):
        names = [(RBP_OUT / 'prepare_receipt.json').relative_to(f.ROOT).as_posix()] + [(RBP_ART / (track + '_model_features.npz')).relative_to(f.ROOT).as_posix() for track in CONTROLS]
        actual = {name: 'fixed_' + name for name in names}; reference = {'status': 'FROZEN_PREFIT', 'files': dict(actual)}
        validate_control_reference(reference, actual)
        reference['files'][names[1]] = 'changed'
        with self.assertRaises(AssertionError):
            validate_control_reference(reference, actual)

    def test_requests_union_is_outcome_free(self):
        frame = pd.DataFrame({'parent_sequence': ['ACGT', 'ACGT'], 'mutant_sequence': ['ATGT', 'ACGA']})
        roster, changed = requests(frame)
        self.assertEqual(changed, [(1,), (3,)]); self.assertEqual(roster['ACGT'], [(1,), (3,)])

    def test_source_only_fixed_configuration_order(self):
        configs = module('joint').CONFIGS
        self.assertEqual([value['penalty'] for value in configs], [.005, .05, .5]); self.assertEqual(select_config(configs, [.2 + 5e-13, .2, .3]), configs[0])
        self.assertEqual(select_config(configs, [.3, .2, .4]), configs[1])

    def test_creation_hash_and_request_identity(self):
        ART.mkdir(parents=True, exist_ok=True)
        identity = {'sequence_sha256': 's', 'requests_sha256': 'r', 'spec_sha256': 'x'}
        with tempfile.TemporaryDirectory(dir=ART) as folder:
            path = Path(folder) / 'synthetic.npz'
            np.savez_compressed(path, **{'sequence': 'ACGT', **identity, 'keys': np.array(['1']), 'global': np.ones(128), 'local': np.ones((1, 128))})
            birth = {**identity, 'cache_sha256': sha256(path)}
            with patch.object(production, 'creation_identity', return_value=identity):
                self.assertEqual(production.validate(path, 'ACGT', [(1,)], birth)[0].shape, (128,))
                changed = dict(birth); changed['requests_sha256'] = 'changed'
                with self.assertRaises(AssertionError):
                    production.validate(path, 'ACGT', [(1,)], changed)
                path.write_bytes(path.read_bytes() + b'tamper')
                with self.assertRaises(AssertionError):
                    production.validate(path, 'ACGT', [(1,)], birth)

    def test_checkpoint_label_feature_metadata_identity(self):
        frame = pd.DataFrame({'intervention_id': ['a', 'b'], 'dataset': ['s', 's'], 'biological_component': ['g', 'g'],
            'parent_context_id': ['p', 'p'], 'parent_sequence': ['AAAA', 'AAAA'], 'mutant_sequence': ['AAAC', 'AAAG'], 'measured_delta': [1., -1.]})
        matrix = np.zeros((2, 1014)); config = module('joint').CONFIGS[0]
        first = checkpoint_identity('joint', frame, matrix, config, 'feature', 'prefit', 'core')
        altered = frame.copy(); altered.loc[0, 'measured_delta'] += .1
        second = checkpoint_identity('joint', altered, matrix, config, 'feature', 'prefit', 'core')
        self.assertNotEqual(first['training_labels_sha256'], second['training_labels_sha256'])
        matrix[0, 0] = 1.
        third = checkpoint_identity('joint', frame, matrix, config, 'feature', 'prefit', 'core')
        self.assertNotEqual(first['training_feature_values_sha256'], third['training_feature_values_sha256'])

    def test_canonical_tie_retained_with_bounded_arithmetic(self):
        model = {'beta': [1., 1.], 'mean': [0., 0.], 'scale': [1., 1.]}; x = np.array([[1., 0.], [1., 1e-12]])
        score, independent, error = bounded_canonical_scores(model, x, lambda model, values: np.ones(len(values)))
        self.assertLess(error, 1e-9); self.assertNotEqual(independent[0], independent[1])
        frame = pd.DataFrame({'parent_context_id': ['p', 'p'], 'intervention_id': ['a', 'b'], 'dataset': ['s', 's'],
            'biological_component': ['g', 'g'], 'measured_delta': [1., -1.]})
        self.assertEqual(set(independent_decisions(frame, score).selected_id), {'a'})

    def test_independent_error_categories(self):
        for truth, expected in [([-2., -1.], (0., 1., 0.)), ([-1., 0.], (0., 0., 1.)), ([-1., 1.], (1., 0., 0.))]:
            frame = pd.DataFrame({'parent_context_id': ['p', 'p'], 'intervention_id': ['a', 'b'], 'dataset': ['s', 's'],
                'biological_component': ['g', 'g'], 'measured_delta': truth})
            row = independent_decisions(frame, np.array([1., 0.])).query('direction == 1').iloc[0]
            self.assertEqual((row.avoidable_wrong, row.unavoidable_wrong, row.neutral_only_alternative_wrong), expected)

    def test_strict_and_two_incremental_controls(self):
        self.assertTrue(all(incremental_checks([.02, .02, .02, .02]).values()))
        self.assertFalse(all(incremental_checks([.06, -.001, -.001, -.001]).values()))
        checks, _ = strict_checks([.42] * 4, [.03] * 4, [.02] * 4, [0.] * 4, [0.] * 4, np.ones(5000) * .03)
        self.assertTrue(all(checks.values()))
        bad = list([.42] * 4); bad[0] = .8
        checks, _ = strict_checks(bad, [.03] * 4, [.02] * 4, [0.] * 4, [0.] * 4, np.ones(5000) * .03)
        self.assertFalse(checks['macro_regret_at_most_0_468'])

    def test_decision_roster_model_dataset_identity(self):
        frame = pd.DataFrame({'dataset': STUDIES, 'parent_context_id': ['p' + str(i) for i in range(4)]})
        rows = pd.DataFrame([{'model': 'joint', 'dataset': study, 'parent_context_id': 'p' + str(i), 'direction': direction}
            for i, study in enumerate(STUDIES) for direction in (-1, 1)])
        decisions_roster_check(rows, frame, 'joint')
        for changed in (rows.assign(model='false'), pd.concat((rows, rows.iloc[:1])), rows.iloc[:-1], rows.assign(dataset='unknown')):
            with self.assertRaises(AssertionError):
                decisions_roster_check(changed, frame, 'joint')


if __name__ == '__main__':
    unittest.main()
