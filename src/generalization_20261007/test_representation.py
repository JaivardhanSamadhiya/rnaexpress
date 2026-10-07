"""Scoped ordered-motif tests using synthetic sequences and labels only."""

from collections import Counter
import unittest

from .route_representation import (
    WORDS, WORD_INDEX, K_VALUES, np, sparse,
    delta_counts, build_ordered_deltas, combine_with_baseline,
    pair_objective, fit_pairwise, predict_pairwise,
)


def brute(parent, mutant):
    result = Counter()
    for length in K_VALUES:
        for start in range(len(parent) - length + 1):
            result[WORD_INDEX[mutant[start:start + length]]] += 1
            result[WORD_INDEX[parent[start:start + length]]] -= 1
    return {index: value for index, value in result.items() if value}


class RepresentationTests(unittest.TestCase):
    def test_exact_full_count_equivalence(self):
        rng = np.random.default_rng(20261007)
        for length in (1, 3, 4, 6, 11, 50):
            for _ in range(8):
                parent = ''.join(rng.choice(list('ACGT'), length))
                mutant = list(parent)
                for index in rng.choice(length, min(3, length), replace=False):
                    mutant[index] = str(rng.choice(list('ACGT')))
                mutant = ''.join(mutant)
                self.assertEqual(delta_counts(parent, mutant), brute(parent, mutant))

    def test_antisymmetry_and_zero(self):
        parent, mutant = 'ACGTTACGTACGT', 'ACGATACCTACGT'
        self.assertEqual(delta_counts(parent, mutant), {i: -v for i, v in delta_counts(mutant, parent).items()})
        self.assertEqual(delta_counts(parent, parent), {})

    def test_unchanged_distant_flank(self):
        parent, mutant = 'AAAAAACGTTAAAAAA', 'AAAAAACATTAAAAAA'
        self.assertEqual(delta_counts(parent, mutant), delta_counts('CGCG' + parent + 'TTCC', 'CGCG' + mutant + 'TTCC'))

    def test_schema_and_total_counts(self):
        result = build_ordered_deltas(['ACGTTACGT'], ['ACGATACGT'])
        self.assertEqual(result.shape, (1, 5376))
        self.assertEqual(result.nnz, len(delta_counts('ACGTTACGT', 'ACGATACGT')))
        for length in K_VALUES:
            indices = [i for i, word in enumerate(WORDS) if len(word) == length]
            self.assertEqual(float(result[:, indices].sum()), 0.)

    def test_input_rejection(self):
        for parent, mutant in [('AACN', 'AACT'), ('AAC', 'AACT'), ('', '')]:
            with self.assertRaises(ValueError):
                delta_counts(parent, mutant)
        with self.assertRaises(ValueError):
            build_ordered_deltas(['AAA'], [])

    def test_gradient_and_dense_sparse_parity(self):
        rng = np.random.default_rng(17)
        differences = sparse.csr_matrix(rng.normal(size=(11, 5)))
        labels = np.where(rng.normal(size=11) > 0, 1., -1.)
        weights = rng.uniform(.1, 1., 11); weights /= weights.sum()
        beta = rng.normal(size=5)
        _, gradient = pair_objective(beta, differences, labels, weights, .05)
        eps = 1e-6
        numerical = []
        for column in range(5):
            direction = np.eye(5)[column] * eps
            numerical.append((pair_objective(beta + direction, differences, labels, weights, .05)[0] - pair_objective(beta - direction, differences, labels, weights, .05)[0]) / (2 * eps))
        np.testing.assert_allclose(gradient, numerical, atol=1e-9, rtol=1e-6)
        features = np.column_stack([rng.normal(size=(12, 4)), np.ones(12)])
        left, right = np.arange(11), np.arange(1, 12)
        dense = fit_pairwise(features, left, right, labels, weights)
        sparse_model = fit_pairwise(sparse.csr_matrix(features), left, right, labels, weights)
        np.testing.assert_array_equal(dense['beta'], sparse_model['beta'])
        self.assertEqual(dense['beta'][-1], 0.)
        self.assertIn(4, dense['unsupported_columns'])
        np.testing.assert_array_equal(predict_pairwise(dense, features), predict_pairwise(sparse_model, features))

    def test_parent_constant_cancels_in_pair_scaling(self):
        features = np.array([[1., 0.], [2., 0.], [1., 1000.], [3., 1000.]])
        model = fit_pairwise(features, [0, 2], [1, 3], [-1, -1], [.5, .5])
        self.assertEqual(model['pair_scale'][1], 1.)
        self.assertEqual(model['beta'][1], 0.)

    def test_baseline_join_and_numeric_finiteness(self):
        ordered = build_ordered_deltas(['ACGTTACGT'], ['ACGATACGT'])
        joined = combine_with_baseline(np.ones((1, 246)), ordered)
        self.assertEqual(joined.shape, (1, 5622))
        with self.assertRaises(ValueError):
            combine_with_baseline(np.full((1, 246), np.nan), ordered)


if __name__ == '__main__':
    unittest.main()
