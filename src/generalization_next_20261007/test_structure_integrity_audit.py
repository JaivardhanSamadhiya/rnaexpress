"""Synthetic-only checks of the additive structure audit; no project inputs."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import structure_integrity_audit as audit
from .route_structure import np, jsave


class StructureIntegrityAuditTests(unittest.TestCase):
    def test_selection_is_fixed_by_hash_and_length(self):
        sequences = ["A" * (length - 2) + a + b for length in audit.LENGTHS
                     for a in "ACGT" for b in "ACGT"]
        actual = audit.select_refolds(list(reversed(sequences)) + sequences[:2])
        expected = [sequence for length in audit.LENGTHS
                    for sequence in sorted((s for s in sequences if len(s) == length),
                                           key=audit.sequence_hash)[:8]]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 32)

    def test_identity_probabilities_and_numeric_schema(self):
        with tempfile.TemporaryDirectory(prefix="structure_postaudit_synthetic_") as directory:
            path = Path(directory) / "synthetic.npz"
            sequence, config = "ACGT", "synthetic_config_sha"
            value = {"sequence": sequence, "sequence_sha256": audit.sequence_hash(sequence),
                     "config_sha256": config, "unpaired": np.array([1., .8, .7, 1.]),
                     "entropy": np.array([0., .2, .3, 0.]), "distance": np.array([0., .1, .1, 0.]),
                     "energy": -1.25}
            np.savez_compressed(path, **value)
            actual = audit.validate_npz(path, sequence, config)
            audit.exact_comparison(actual, actual)
            for wrong_sequence, wrong_config in (("AGGT", config), (sequence, "wrong")):
                with self.assertRaises(AssertionError):
                    audit.validate_npz(path, wrong_sequence, wrong_config)
            for field, bad_value in (("unpaired", np.array([1., 1.1, .7, 1.])),
                                     ("entropy", np.array([0., -.2, .3, 0.])),
                                     ("distance", np.array([0., .1, 1.1, 0.])),
                                     ("energy", float("nan"))):
                np.savez_compressed(path, **{**value, field: bad_value})
                with self.assertRaises(AssertionError):
                    audit.validate_npz(path, sequence, config)

    def test_exact_refold_checks_do_not_accept_small_differences(self):
        baseline = (np.ones(4), np.zeros(4), np.zeros(4), -1.)
        for position in range(4):
            changed = [value.copy() if isinstance(value, np.ndarray) else value for value in baseline]
            if position < 3:
                changed[position][0] += 1e-12
            else:
                changed[position] += 1e-12
            with self.assertRaises(AssertionError):
                audit.exact_comparison(baseline, changed)

    def test_new_index_rejects_later_byte_change(self):
        with tempfile.TemporaryDirectory(prefix="structure_postaudit_hash_") as directory:
            root = Path(directory); art = root / "artifacts/generalization_next_20261007"
            path = art / "structure_ensemble_cache/synthetic.npz"
            path.parent.mkdir(parents=True); path.write_bytes(b"synthetic_saved_bytes")
            entry = {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                     "sha256": audit.file_hash(path)}
            with patch.object(audit, "ROOT", root), patch.object(audit, "ART", art):
                audit.validate_entry(entry, path)
                path.write_bytes(b"altered___saved_bytes")
                with self.assertRaises(AssertionError):
                    audit.validate_entry(entry, path)


def run():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(StructureIntegrityAuditTests))
    assert result.wasSuccessful()
    jsave(audit.TEST_RECEIPT, {"status": "PASS", "tests": result.testsRun,
          "audit_source_sha256": audit.file_hash(audit.__file__),
          "tests_source_sha256": audit.file_hash(__file__),
          "project_inventory_read": False, "project_cache_read": False,
          "fresh_project_folds": 0, "outcomes_used": False, "models_fit": 0})


if __name__ == "__main__":
    run()
