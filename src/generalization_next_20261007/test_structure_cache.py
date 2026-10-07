"""Synthetic cache persistence and content-integrity checks only."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import route_structure as route
from . import structure_cache as cache


class StructureCacheTests(unittest.TestCase):
    def test_completed_cache_replay_and_preservation(self):
        route.ART.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="structure_cache_qa_", dir=route.ART) as directory:
            path = Path(directory) / "synthetic.npz"
            result = {"sequence": "CCTCCC", "summary": route.ensemble("CCTCCC")}
            with patch.object(cache, "cache_path", return_value=path):
                cache.persist_fold(result)
                checksum = cache.file_hash(path)
                replay = cache.validate_cached("CCTCCC")
                for expected, actual in zip(result["summary"], replay):
                    route.np.testing.assert_array_equal(expected, actual)
                cache.persist_fold(result)
                self.assertEqual(cache.file_hash(path), checksum)
                changed = list(result["summary"])
                changed[0] = changed[0] / 2
                with self.assertRaises(AssertionError):
                    cache.persist_fold({**result, "summary": tuple(changed)})
                self.assertEqual(cache.file_hash(path), checksum)

    def test_cache_rejects_wrong_allele_and_invalid_probability(self):
        route.ART.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="structure_cache_qa_", dir=route.ART) as directory:
            path = Path(directory) / "synthetic.npz"
            result = {"sequence": "CCTCCC", "summary": route.ensemble("CCTCCC")}
            with patch.object(cache, "cache_path", return_value=path):
                cache.persist_fold(result)
                with self.assertRaises(AssertionError):
                    cache.validate_cached("CCACCC")
                with route.np.load(path, allow_pickle=False) as data:
                    payload = {key: data[key].copy() for key in data.files}
                payload["unpaired"][0] = 1.1
                route.np.savez_compressed(path, **payload)
                with self.assertRaises(AssertionError):
                    cache.validate_cached("CCTCCC")


if __name__ == "__main__":
    unittest.main()
