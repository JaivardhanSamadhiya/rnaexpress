"""Synthetic loader and manifest-chain checks only; no project outcomes."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from .source_only_canonical_replay import (
    pd, np, read_admitted_frame, certified_core, IDENTITY,
    CORE_NAME, FOUNDATION_NAME, AUTHOR_ADMISSION_NAME,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SourceOnlyTests(unittest.TestCase):
    def test_explicit_columns_same_parser_and_original_row_order(self):
        with tempfile.TemporaryDirectory() as directory:
            core, rows = Path(directory) / "core.csv", Path(directory) / "rows.csv"
            frame = pd.DataFrame({"intervention_id": ["a", "b"], "dataset": ["s", "s"],
                "biological_component": ["g", "g"], "parent_context_id": ["p", "p"],
                "parent_sequence": ["AAAA", "AAAA"], "mutant_sequence": ["CAAA", "GAAA"],
                "endpoint_class": ["projection", "projection"], "measured_delta": [.12345678901234568, -.9876543210987654],
                "primary_eligible": [True, True], "invented_unused_column": ["ignored", "ignored"]})
            frame.to_csv(core, index=False); frame[IDENTITY].to_csv(rows, index=False)
            real_read = pd.read_csv; calls = []
            def explicit(*args, **kwargs):
                calls.append(kwargs["usecols"])
                return real_read(*args, **kwargs)
            with patch.object(pd, "read_csv", side_effect=explicit):
                result = read_admitted_frame(core, rows, IDENTITY, 2, ["s"])
            self.assertNotIn("invented_unused_column", result)
            self.assertEqual(calls[1], IDENTITY)
            self.assertEqual(set(calls[0]), set(IDENTITY + ["endpoint_class", "measured_delta", "primary_eligible"]))
            np.testing.assert_array_equal(result.measured_delta, real_read(core, low_memory=False).measured_delta)
            frame.iloc[::-1][IDENTITY].to_csv(rows, index=False)
            with self.assertRaises(AssertionError): read_admitted_frame(core, rows, IDENTITY, 2, ["s"])

    def test_ineligible_or_nonfinite_mean_effect_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            core, rows = Path(directory) / "core.csv", Path(directory) / "rows.csv"
            frame = pd.DataFrame({"intervention_id": ["a", "b"], "dataset": ["s"] * 2,
                "biological_component": ["g"] * 2, "parent_context_id": ["p"] * 2,
                "parent_sequence": ["AAAA"] * 2, "mutant_sequence": ["CAAA", "GAAA"],
                "endpoint_class": ["projection"] * 2, "measured_delta": [1., 2.], "primary_eligible": [False, True]})
            frame[IDENTITY].to_csv(rows, index=False); frame.to_csv(core, index=False)
            with self.assertRaises(AssertionError): read_admitted_frame(core, rows, IDENTITY, 2, ["s"])
            frame["primary_eligible"] = True; frame.loc[0, "measured_delta"] = np.nan; frame.to_csv(core, index=False)
            with self.assertRaises(AssertionError): read_admitted_frame(core, rows, IDENTITY, 2, ["s"])

    def test_hash_chain_rejects_changed_core_or_intermediate_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core, admission, foundation = [root / name for name in (CORE_NAME, AUTHOR_ADMISSION_NAME, FOUNDATION_NAME)]
            for p in (core, admission, foundation): p.parent.mkdir(parents=True, exist_ok=True)
            core.write_bytes(b"invented admitted core")
            admission.write_text(json.dumps({"files": {CORE_NAME: sha(core)}}))
            foundation.write_text(json.dumps({"files": {AUTHOR_ADMISSION_NAME: sha(admission)}}))
            manifest = {"files": {FOUNDATION_NAME: sha(foundation)}}
            common = SimpleNamespace(ROOT=root, sha256=sha, readj=lambda p: json.loads(Path(p).read_text()))
            self.assertEqual(certified_core(common, manifest)[0], core)
            core.write_bytes(b"changed")
            with self.assertRaises(AssertionError): certified_core(common, manifest)
            core.write_bytes(b"invented admitted core"); admission.write_text("{}")
            with self.assertRaises(AssertionError): certified_core(common, manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
