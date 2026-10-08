"""Invented coordinate/transport fixtures only; no remote or biological reads."""
from __future__ import annotations
import ast, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error
from . import common as c
from . import mapping as m, prepare as p, replay as r, transport as t


KEY = ("chr1", 100, 112)
DNA = "AACCGGTTACGT"
RECORD = {"name": "T1.2", "chrom": "chr1", "strand": "+", "txStart": 100, "txEnd": 112,
    "cdsStart": 100, "cdsEnd": 103, "exonStarts": "100,108,", "exonEnds": "106,112,", "exonCount": 2}
REF = {"transcript_id": "T1", "chromosome": "1", "gene_start1": 101, "gene_end1": 112}
PARENT = {"dataset": "invented", "parent_id": "p", "gene": "invented", "parent_sequence": "CGG", "reference_candidates": [REF]}


class Tests(unittest.TestCase):
    def test_spliced_both_strands_direct_replay_independent(self):
        sequence, positions = c.transcript_utr(RECORD, DNA, 100)
        self.assertEqual((sequence, positions), ("CGGACGT", [103, 104, 105, 108, 109, 110, 111]))
        minus = RECORD | {"strand": "-", "cdsStart": 110, "cdsEnd": 112}
        sequence, positions = c.transcript_utr(minus, DNA, 100)
        self.assertEqual((sequence, positions), ("GTCCGGTT", [109, 108, 105, 104, 103, 102, 101, 100]))
        with patch.object(c, "transcript_utr", side_effect=AssertionError("Shared reconstructor forbidden")):
            self.assertEqual(r.ordered_positions(minus), positions)
            self.assertEqual(r.direct_bases(DNA, 100, positions, "-"), sequence)

    def test_overlapping_occurrences_and_isoform_vector_collapse(self):
        self.assertEqual(c.occurrences("AAAAA", "AAA"), [0, 1, 2])
        refs = [REF, REF | {"transcript_id": "T2"}]
        result = m.resolve_parent(PARENT | {"reference_candidates": refs}, {KEY: {"failure": None, "data": ([RECORD, RECORD | {"name": "T2.1"}], DNA)}})
        self.assertEqual(result["mapping_status"], c.MAPPED)
        self.assertEqual(len(result["matches"]), 2)
        self.assertTrue(result["candidate_resolution_complete"])

    def test_observed_match_plus_missing_candidate_remains_empty(self):
        parent = PARENT | {"reference_candidates": [REF, REF | {"transcript_id": "absent"}]}
        result = m.resolve_parent(parent, {KEY: {"failure": None, "data": ([RECORD], DNA)}})
        self.assertEqual(result["mapping_status"], "unresolved_reference_candidates")
        self.assertEqual(len(result["matches"]), 1)
        self.assertFalse(result["candidate_resolution_complete"])
        changed, coords = c.edited_coordinates({"parent_sequence": "CGG", "mutant_sequence": "CGA"}, result)
        self.assertEqual(changed, [2])
        self.assertEqual(coords, [])

    def test_observed_match_plus_capped_or_failed_region_stays_empty(self):
        other = ("chr2", 200, 212)
        parent = PARENT | {"reference_candidates": [REF, REF | {"chromosome": "2", "gene_start1": 201, "gene_end1": 212}]}
        for reason in ("fixed_region_cap_or_invalid_interval", "reference_response_missing", "annotation_source_version_or_schema_mismatch"):
            result = m.resolve_parent(parent, {KEY: {"failure": None, "data": ([RECORD], DNA)}, other: {"failure": reason, "data": None}})
            self.assertEqual(result["mapping_status"], "unresolved_reference_candidates")
            self.assertEqual(len(result["matches"]), 1)
            self.assertEqual(c.edited_coordinates({"parent_sequence": "CGG", "mutant_sequence": "CGA"}, result)[1], [])

    def test_source_sequence_or_noncoding_not_silently_resolved(self):
        for record in (RECORD | {"cdsStart": 100, "cdsEnd": 100}, RECORD | {"cdsEnd": 109}):
            result = m.resolve_parent(PARENT, {KEY: {"failure": None, "data": ([record], DNA)}})
            self.assertEqual(result["mapping_status"], "unresolved_reference_candidates")
        with self.assertRaises(AssertionError):
            c.transcript_utr(RECORD | {"exonStarts": "100,102,"}, DNA, 100)
        with self.assertRaises(AssertionError):
            c.transcript_utr(RECORD | {"txEnd": 111}, DNA, 100)

    def test_distinct_vectors_and_strands_stay_ambiguous(self):
        one = {"chrom": "chr1", "strand": "+", "positions0": [1, 2, 4]}
        for other in (one | {"positions0": [1, 2, 5]}, one | {"strand": "-"}):
            self.assertEqual(c.mapping_status(PARENT, [one, other], []), "ambiguous_reference_site_vectors")

    def test_synthetic_and_unanchored_rows_keep_full_menu(self):
        parent = PARENT | {"dataset": "srle", "reference_candidates": []}
        result = m.resolve_parent(parent, {})
        self.assertEqual(result["mapping_status"], "synthetic_no_native_coordinates")
        self.assertEqual(c.edited_coordinates({"parent_sequence": "CGG", "mutant_sequence": "CGA"}, result)[1], [])
        self.assertEqual(m.resolve_parent(parent | {"dataset": "moffatt_gse334718"}, {})["mapping_status"], "no_exact_source_utr")
        rows = [{"dataset": "srle", "parent_context_id": "p", "intervention_id": str(i)} for i in range(3)]
        self.assertEqual(c.menu_counts(rows), c.menu_counts([row | {"mapping_status": "missing"} for row in rows]))

    def test_exact_forward_genome_edit_orientation(self):
        parent = {"mapping_status": c.MAPPED, "candidate_resolution_complete": True, "unresolved_candidates": [],
                  "matches": [{"chrom": "chr1", "strand": "-", "positions0": [11, 10, 5]}]}
        changes, coords = c.edited_coordinates({"parent_sequence": "ACG", "mutant_sequence": "ATG"}, parent)
        self.assertEqual(changes, [1])
        self.assertEqual((coords[0]["genomic_position0"], coords[0]["genomic_reference"], coords[0]["genomic_alternate"]), (10, "G", "A"))

    def test_exact_annotation_release_and_region_binding(self):
        ann = {"genome": "mm10", "track": "knownGene", "dataTime": c.ANNOTATION_TIME, "chrom": "chr1", "start": 100, "end": 112, "knownGene": [RECORD]}
        genome = {"genome": "mm10", "chrom": "chr1", "start": 100, "end": 112, "dna": DNA}
        self.assertIsNone(m.validate_region(ann, genome, KEY)[1])
        for corrupted in (ann | {"dataTime": "different"}, ann | {"start": 99}, ann | {"maxItemsLimit": True}):
            self.assertIsNone(m.validate_region(corrupted, genome, KEY)[0])

    def test_malformed_or_limit_annotation_is_missing_not_partial_certification(self):
        ann = {"genome": "mm10", "track": "knownGene", "dataTime": c.ANNOTATION_TIME, "chrom": "chr1", "start": 100, "end": 112, "knownGene": [RECORD]}
        genome = {"genome": "mm10", "chrom": "chr1", "start": 100, "end": 112, "dna": DNA}
        for corrupted in (ann | {"knownGene": [RECORD | {"txStart": "100"}]}, ann | {"itemsReturned": 2}, ann | {"knownGene": [RECORD] * 10000}):
            self.assertIsNone(m.validate_region(corrupted, genome, KEY)[0])

    def test_valid_JSON_malformed_top_level_or_DNA_stays_unresolved(self):
        ann = {"genome": "mm10", "track": "knownGene", "dataTime": c.ANNOTATION_TIME, "chrom": "chr1", "start": 100, "end": 112, "knownGene": [RECORD]}
        genome = {"genome": "mm10", "chrom": "chr1", "start": 100, "end": 112, "dna": DNA}
        self.assertIsNotNone(r.admit_reference(ann, genome, KEY))
        for bad_ann, bad_genome in (([], genome), (1, genome), (ann, []), (ann, 1),
                                    (ann, genome | {"dna": None}), (ann, genome | {"dna": ["A"]})):
            self.assertIsNone(m.validate_region(bad_ann, bad_genome, KEY)[0])
            self.assertIsNone(r.admit_reference(bad_ann, bad_genome, KEY))

    def test_fixed_caps_and_stable_region_order(self):
        parents = [PARENT, PARENT | {"reference_candidates": [REF | {"chromosome": "2", "gene_start1": 201, "gene_end1": 212}]}]
        with patch.object(c, "MAX_TOTAL", 15):
            plan = p.make_region_plan(parents)
            self.assertEqual([x["planned_status"] for x in plan], ["eligible", "fixed_total_region_cap"])
        huge = PARENT | {"reference_candidates": [REF | {"gene_end1": 500_102}]}
        self.assertEqual(p.make_region_plan([huge])[0]["planned_status"], "fixed_region_cap_or_invalid_interval")
        unsupported = PARENT | {"reference_candidates": [REF | {"chromosome": "unknown"}]}
        self.assertEqual(p.make_region_plan([unsupported])[0]["planned_status"], "unsupported_fixed_author_chromosome")

    def test_failed_transport_cache_without_payload_does_not_hash_or_retry(self):
        url = c.urls(KEY)["sequence"]
        with tempfile.TemporaryDirectory(dir=c.ART) as directory:
            path = Path(directory) / "failed.json"
            receipt = path.with_name(path.name + ".receipt.json")
            c.jsave(receipt, {"url": url, "http_status": 0, "bytes": 0, "sha256": None, "failure": "invented timeout"})
            data, item = t.cached(path, url, hasher=lambda _: self.fail("Missing path must not be hashed"))
            self.assertIsNone(data)
            self.assertEqual(item["http_status"], 0)
            opener = type("Forbidden", (), {"open": lambda *_args, **_kwargs: self.fail("No automatic retry")})()
            client = t.Client([url], opener=opener, sleep=lambda _: self.fail("No new request wait"))
            self.assertIsNone(client.get(url, path)[0])
            self.assertEqual(client.new_requests, 0)

    def test_first_transport_error_preserved_no_retry(self):
        url = c.urls(KEY)["sequence"]
        events = []
        class Fail:
            def open(self, *_args, **_kwargs):
                events.append("request")
                raise urllib.error.URLError("invented transport failure")
        with tempfile.TemporaryDirectory(dir=c.ART) as directory:
            path = Path(directory) / "error.json"
            client = t.Client([url], opener=Fail(), sleep=lambda seconds: events.append(seconds))
            self.assertIsNone(client.get(url, path)[0])
            receipt = path.with_name(path.name + ".receipt.json")
            before = receipt.read_bytes()
            self.assertIsNone(client.get(url, path)[0])
            self.assertEqual(before, receipt.read_bytes())
            self.assertEqual(events, [1.05, "request"])
            self.assertFalse(path.exists())

    def test_orphan_and_changed_success_cache_rejected(self):
        url = c.urls(KEY)["sequence"]
        with tempfile.TemporaryDirectory(dir=c.ART) as directory:
            path = Path(directory) / "body.json"
            c.save(path, b"{}")
            with self.assertRaises(AssertionError):
                t.cached(path, url)
            c.jsave(path.with_name(path.name + ".receipt.json"), {"url": url, "http_status": 200, "bytes": 2, "sha256": "changed"})
            with self.assertRaises(AssertionError):
                t.cached(path, url)

    def test_success_and_oversize_mock_responses_are_immutable(self):
        url = c.urls(KEY)["sequence"]
        class Response(io.BytesIO):
            status = 200
            headers = {}
            def geturl(self):
                return url
        class Opener:
            def __init__(self, payload):
                self.payload, self.calls = payload, 0
            def open(self, *_args, **_kwargs):
                self.calls += 1
                return Response(self.payload)
        with tempfile.TemporaryDirectory(dir=c.ART) as directory:
            path = Path(directory) / "success.json"
            opener = Opener(b'{"genome":"mm10"}')
            client = t.Client([url], opener=opener, sleep=lambda _: None)
            self.assertEqual(client.get(url, path)[0], {"genome": "mm10"})
            before = path.read_bytes()
            self.assertEqual(client.get(url, path)[0], {"genome": "mm10"})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(opener.calls, 1)
            oversize = Path(directory) / "oversize.json"
            opener = Opener(b"1234")
            with patch.object(c, "MAX_RESPONSE", 3):
                client = t.Client([url], opener=opener, sleep=lambda _: None)
                self.assertIsNone(client.get(url, oversize)[0])
                self.assertIsNone(client.get(url, oversize)[0])
                self.assertEqual(opener.calls, 1)
                self.assertFalse(oversize.exists())
                self.assertEqual(oversize.with_name(oversize.name + ".oversize_prefix.bin").read_bytes(), b"123")
    def test_nonofficial_url_and_redirect_not_allowed(self):
        self.assertFalse(t.official("https://example.com/getData/sequence"))
        self.assertFalse(t.official("https://api.genome.ucsc.edu/getData/sequenceevil"))
        with self.assertRaises(AssertionError):
            t.Client(["https://api.genome.ucsc.edu/getData/phyloP"])
        with self.assertRaises(urllib.error.URLError):
            t.OfficialRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.com/x")

    def test_independent_anchor_enumeration_not_shared_resolver(self):
        with patch.object(m, "resolve_parent", side_effect=AssertionError("Shared resolver forbidden")), \
             patch.object(c, "transcript_utr", side_effect=AssertionError("Shared exon reconstruction forbidden")):
            matches, unresolved, count = r.independent_parent(PARENT, {KEY: ({"knownGene": [RECORD]}, DNA)})
            self.assertEqual(count, 1)
            self.assertFalse(unresolved)
            self.assertEqual(len(matches), 1)
            self.assertEqual(next(iter(matches))[-1], (103, 104, 105))

    def test_mapping_time_response_hashes_and_complete_roster_bound(self):
        with tempfile.TemporaryDirectory(dir=c.ART) as directory:
            root = Path(directory)
            with patch.object(c, "ROOT", root), patch.object(c, "ART", root / "artifacts"):
                plan = [{"key": list(KEY), "planned_status": "eligible", "reuse": {}, "urls": c.urls(KEY)}]
                entries, snapshots = [], []
                for kind in ("knownGene", "sequence"):
                    path = c.ART / "public_metadata" / (c.tag(KEY) + "_" + kind + ".json")
                    receipt = path.with_name(path.name + ".receipt.json")
                    c.save(path, b"{}")
                    c.jsave(receipt, {"url": c.urls(KEY)[kind], "http_status": 200, "bytes": 2, "sha256": c.sha(path)})
                    entries.append({"region": list(KEY), "kind": kind, "response": path.relative_to(root).as_posix(), "receipt": receipt.relative_to(root).as_posix(),
                        "receipt_sha256": c.sha(receipt), "response_sha256": c.sha(path), "http_status": 200})
                    snapshots.append((path, receipt, path.read_bytes(), receipt.read_bytes()))
                completed = {"public_response_receipts": entries}
                r.bind_public_responses(completed, plan)
                path, receipt, body_before, receipt_before = snapshots[0]
                path.write_bytes(b'{"invented_changed":true}')
                internal = c.read(receipt)
                internal.update(sha256=c.sha(path), bytes=path.stat().st_size)
                receipt.write_text(json.dumps(internal), encoding="utf-8")
                with self.assertRaises(AssertionError):
                    r.bind_public_responses(completed, plan)
                path.write_bytes(body_before)
                receipt.write_bytes(receipt_before)
                for roster in (entries[:1], entries + [entries[0]], [entries[0], entries[1] | {"kind": "unexpected"}]):
                    with self.assertRaises(AssertionError):
                        r.bind_public_responses({"public_response_receipts": roster}, plan)


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful()
    assert not any(name == package or name.startswith(package + ".") for name in sys.modules for package in ("numpy", "pandas", "torch", "openvino"))
    sources = {path.relative_to(c.ROOT).as_posix(): c.sha(path) for path in sorted(c.SRC.glob("*.py"))}
    for path in c.SRC.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    c.jsave(c.OUT / "synthetic_tests_receipt_v4.json", {"status": "PASS", "test_count": result.testsRun, "source_hashes": sources,
        "scope": "Invented coordinate/exon/strand/cap/transport fixtures only", "project_metadata_read": False,
        "actual_remote_requests": 0, "numerical_packages_imported": False, "outcomes_read": False, "conservation_values_read": False, "models_fit": 0})
    print("Full coordinate mapping synthetic tests PASS", result.testsRun, "requests0; outcomes0", flush=True)


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
