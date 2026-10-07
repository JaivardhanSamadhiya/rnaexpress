"""Projection/paired-control/roster checks using synthetic inputs only."""
import unittest

from .common import np, pd
from .projection import generate, project_pool_summaries
from .production import pooled_blocks, requests, positions_key, creation_receipt, validate_creation_bytes
from .scoring import scan, smooth_log_odds, summaries


class ExperimentTests(unittest.TestCase):
    def test_cache_creation_replay_rejects_corruption_and_request_change(self):
        import io
        buffer = io.BytesIO()
        np.savez_compressed(buffer, global_projected=np.arange(128, dtype=np.float64), sequence="AAAA")
        payload = buffer.getvalue()
        receipt = creation_receipt(payload, "AAAA", [(0,), (3,)], "raw", "synthetic_manifest")
        for _ in range(2):
            validate_creation_bytes(payload, receipt, "AAAA", [(0,), (3,)], "raw", "synthetic_manifest")
        corrupt = bytearray(payload); corrupt[len(corrupt) // 2] ^= 1
        with self.assertRaises(AssertionError):
            validate_creation_bytes(bytes(corrupt), receipt, "AAAA", [(0,), (3,)], "raw", "synthetic_manifest")
        with self.assertRaises(AssertionError):
            validate_creation_bytes(payload, receipt, "AAAA", [(3,), (0,)], "raw", "synthetic_manifest")
        with self.assertRaises(AssertionError):
            validate_creation_bytes(payload, receipt, "AAAA", [(0,), (3,)], "access", "synthetic_manifest")

    def test_projection_draw_order_and_single_motif_linear_solution(self):
        matrices = generate()
        reference = np.random.default_rng(20261007)
        for matrix in matrices:
            expected = (reference.standard_normal((421, 64)) / 8).astype(np.float32)
            np.testing.assert_array_equal(matrix, expected)
        self.assertFalse(np.array_equal(matrices[0], matrices[1]))
        pools = np.zeros((421, 4)); pools[0] = [1., 2., 3., 4.]
        expected = np.r_[matrices[0][0].astype(float), 2 * matrices[1][0].astype(float),
                         3 * matrices[2][0].astype(float), 4 * matrices[3][0].astype(float)]
        np.testing.assert_array_equal(project_pool_summaries(pools, matrices), expected)
        np.testing.assert_array_equal(project_pool_summaries(-pools, matrices), -expected)

    def test_off_control_pooling_and_final_delta_precision(self):
        pfm = np.array([[1., 0., 0., 0.], [0., 0., 1., 0.]])
        group = [(2, np.array([0]), smooth_log_odds(pfm)[None])]
        sequence = "AGCA"
        pooled = pooled_blocks(scan(sequence, group), 4, [1], np.ones(4))
        np.testing.assert_array_equal(pooled[0], summaries(sequence, [1], groups=group))
        np.testing.assert_allclose(pooled_blocks(scan(sequence, group), 4, [1], np.full(4, .5)), pooled * .5)
        matrices = generate()
        parent = project_pool_summaries(pooled, matrices)
        mutant_pools = pooled_blocks(scan("AACA", group), 4, [1], np.ones(4))
        mutant = project_pool_summaries(mutant_pools, matrices)
        delta = (mutant - parent).astype(np.float32)
        np.testing.assert_array_equal((parent - mutant).astype(np.float32), -delta)
        np.testing.assert_array_equal((parent - parent).astype(np.float32), np.zeros(256))

    def test_request_union_preserves_exact_coordinates_and_shared_parent(self):
        frame = pd.DataFrame({"parent_sequence": ["AAAA", "AAAA", "AAAT"],
                              "mutant_sequence": ["CAAA", "AAAT", "CAAT"]})
        roster, row_positions = requests(frame)
        self.assertEqual(row_positions, [(0,), (3,), (0,)])
        self.assertEqual(roster["AAAA"], [(0,), (3,)])
        self.assertEqual(roster["AAAT"], [(0,), (3,)])
        self.assertEqual(positions_key((0, 3)), "0,3")
        self.assertNotEqual(positions_key((1, 23)), positions_key((12, 3)))
        with self.assertRaises(AssertionError):
            requests(pd.DataFrame({"parent_sequence": ["AAAA"], "mutant_sequence": ["AAAA"]}))


if __name__ == "__main__":
    unittest.main()
