"""Scoped outcome-free test suite and receipt; never unfiltered pytest."""
from .common import OUT, SRC, sha256, jsave
from .test_experiment import ExperimentTests
from .test_scoring import MotifTests
import unittest


def run(filename="tests_receipt_final.json"):
    suite = unittest.TestSuite()
    for case in (MotifTests, ExperimentTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    jsave(OUT / filename, {"status": "PASS", "tests": result.testsRun,
        "scope": "Synthetic projection, independent motif arithmetic, evidence, paired controls and request roster only",
        "project_data_loaded": False, "project_features_built": False, "biological_fits": 0,
        "source_hashes": {path.name: sha256(path) for path in sorted(SRC.glob("*.py"))}})


if __name__ == "__main__":
    run()
