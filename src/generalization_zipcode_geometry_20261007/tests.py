"""Invented sequence controls; no project inventory, labels or estimator imports."""
from __future__ import annotations

import json
import unittest

from . import audit as module


class GeometryTests(unittest.TestCase):
    def test_primary_design_exact(self):
        self.assertEqual(module.assert_design()["spacer_convention"],
                         "strictly intervening nucleotides, excluding both recognition pieces")

    def test_both_orders_exact_boundary(self):
        for gap, count in ((9, 0), (10, 1), (25, 1), (26, 0)):
            for sequence in ("CGGAC" + "T" * gap + "ACAC", "ACAC" + "T" * gap + "CGGAC"):
                self.assertEqual(len(module.pairs(sequence)), count)

    def test_all_second_piece_bases_and_rna(self):
        for base in ("CCAC", "CCAT", "ACAC", "ACAT", "CCAU", "ACAU"):
            self.assertEqual(len(module.pairs("CGGAC" + "G" * 10 + base)), 1)
        self.assertFalse(module.pairs("CGGAC" + "G" * 10 + "TCAC"))

    def test_overlapping_occurrences(self):
        parent = "CGGAC" + "T" * 10 + "ACACAC"
        self.assertEqual(module.pieces(parent)[1], (15, 17))
        self.assertEqual(len(module.pairs(parent)), 2)

    def test_singles_alone_do_not_pair(self):
        self.assertFalse(module.pairs("CGGAC" + "T" * 20))
        self.assertFalse(module.pairs("ACAC" + "T" * 20))

    def test_no_change_and_reversal(self):
        parent = "CGGAC" + "T" * 10 + "ACAC"
        mutant = "CGGAT" + "T" * 10 + "ACAC"
        no_change = module.contrast(parent, parent)
        self.assertEqual(no_change["geometry_changed"], 0)
        forward, reverse = module.contrast(parent, mutant), module.contrast(mutant, parent)
        self.assertEqual(forward["lost_pair_count"], 1)
        self.assertEqual(forward["lost_pair_count"], reverse["gained_pair_count"])
        self.assertEqual(forward["pair_count_delta"], -reverse["pair_count_delta"])

    def test_spacer_only_substitution_invariant(self):
        parent = "CGGAC" + "T" * 10 + "ACAC"
        mutant = "CGGAC" + "T" * 4 + "A" + "T" * 5 + "ACAC"
        value = module.contrast(parent, mutant)
        self.assertEqual(value["edit_count"], 1)
        self.assertEqual(value["geometry_changed"], 0)

    def test_turnover_with_zero_net_count(self):
        parent = "CGGAC" + "T" * 10 + "ACACAAAA"
        mutant = "CGGAC" + "T" * 10 + "AAAAACAC"
        self.assertEqual(len(parent), len(mutant))
        value = module.contrast(parent, mutant)
        self.assertEqual(value["pair_count_delta"], 0)
        self.assertEqual(value["zero_net_turnover"], 1)

    def test_input_and_metadata_rejection(self):
        for invalid in ("N", "", "A-C", None):
            with self.assertRaises(ValueError):
                module.normalize(invalid)
        with self.assertRaises(ValueError):
            module.contrast("AAAA", "AAA")
        for columns in (module.FIELDS + ["measured_delta"], module.FIELDS[::-1]):
            with self.assertRaises(ValueError):
                module.validate_schema(columns)
        original = [{"intervention_id": "x", "dataset": "mikl_gse173098",
                     "biological_component": "g", "parent_context_id": "c",
                     "parent_sequence": "AAAA", "mutant_sequence": "AAAT"}]
        changed = [{**original[0], "biological_component": "other"}]
        with self.assertRaises(AssertionError):
            module.identity_check(original, changed)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeometryTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    module.jsave(module.OUT / "synthetic_tests_receipt_v2.json", {
        "status": "PASS", "tests": result.testsRun,
        "only_invented_sequences": True, "inventory_or_outcome_reads": False,
        "estimator_fits": 0, "sources": {
            path.relative_to(module.ROOT).as_posix(): module.sha256(path)
            for path in module.SRC.glob("*.py")}})


if __name__ == "__main__":
    main()
