"""Only invented probability matrices and standard-library arithmetic."""
import unittest
from . import proof as p


class Tests(unittest.TestCase):
    def test_probability_ensembles_legal(self):
        for matrix in p.matrices():
            self.assertEqual(len(matrix), 15)
            for i, row in enumerate(matrix):
                self.assertTrue(0 <= sum(row) <= 1)
                self.assertEqual(row[i], 0)
                for j, value in enumerate(row):
                    self.assertEqual(value, matrix[j][i])
                    if value:
                        self.assertGreaterEqual(abs(i - j), 4)
                        self.assertIn(p.SEQUENCE[i] + p.SEQUENCE[j], p.ALLOWED)

    def test_all_nucleotide_cache_summaries_exactly_identical(self):
        a, b = p.matrices()
        self.assertEqual(p.summaries(a), p.summaries(b))
        self.assertNotEqual(a, b)

    def test_partner_base_identity_information_lost(self):
        a, b = p.matrices()
        self.assertEqual(p.partner_mass(a, 0, 'C'), .25)
        self.assertEqual(p.partner_mass(b, 0, 'C'), 0)
        self.assertEqual(p.partner_mass(a, 0, 'U'), 0)
        self.assertEqual(p.partner_mass(b, 0, 'U'), .25)


if __name__ == '__main__':
    unittest.main(verbosity=2)
