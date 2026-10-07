"""Standard-library-only backend guards/tokenization tests; no model work."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import backend_probe as probe
from .backend_preparation import safe_member
from .resources import OUT, digest, jsave


class BackendPreparationTests(unittest.TestCase):
    def test_token_alignment_specials_and_padding(self):
        value = probe.tokenize_lists(["ACGT", "TG"])
        self.assertEqual(value["input_ids"], [[2, 6, 7, 8, 9, 3], [2, 9, 8, 3, 0, 0]])
        self.assertEqual(value["attention_mask"], [[1] * 6, [1, 1, 1, 1, 0, 0]])
        self.assertEqual(value["token_type_ids"], [[0] * 6, [0] * 6])
        with self.assertRaises(AssertionError):
            probe.tokenize_lists(["AN"])

    def test_synthetic_pairs_and_certified_arm_preservation(self):
        left, right = "ACGT" * 5, "TGCA" * 5
        values = probe.synthetic_sequences(left, right)
        self.assertEqual(values, probe.synthetic_sequences(left, right))
        self.assertEqual([len(value) for value in values], [length for length in (46, 150, 190, 260) for _ in range(4)])
        for parent, mutant in zip(values[::2], values[1::2]):
            self.assertEqual(sum(a != b for a, b in zip(parent, mutant)), 1)
            if len(parent) == 46:
                self.assertTrue(parent.startswith(left) and parent.endswith(right))
                self.assertTrue(mutant.startswith(left) and mutant.endswith(right))

    def test_safe_wheel_paths(self):
        with tempfile.TemporaryDirectory(prefix="splicebert_path_qa_") as folder:
            root = Path(folder)
            self.assertEqual(safe_member("torch/module.py", root), root / "torch/module.py")
            for name in ("../outside.py", "/outside.py", "C:/outside.py", "torch\\outside.py", "startup.pth"):
                with self.assertRaises(AssertionError):
                    safe_member(name, root)

    def test_root_and_resource_guards_precede_package_imports(self):
        with self.assertRaises(AssertionError):
            probe.guard(False)
        with patch.object(probe, "resource_state", return_value={"resource_admission_now": False}):
            with self.assertRaises(AssertionError):
                probe.guard(True)


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BackendPreparationTests))
    assert result.wasSuccessful()
    jsave(probe.TEST_RECEIPT, {"status": "PASS", "tests": result.testsRun,
          "backend_probe_sha256": digest(probe.__file__), "test_source_sha256": digest(__file__),
          "Torch_imported": False, "OpenVINO_imported": False, "model_loaded": False,
          "synthetic_model_inference_run": False, "project_alleles_inferred": 0, "outcomes_used": False})


if __name__ == "__main__":
    run()
