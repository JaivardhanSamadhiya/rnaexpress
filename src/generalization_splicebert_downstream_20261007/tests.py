"""Synthetic-only arithmetic/cache/guard tests; zero actual fitting/imports."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from .common import SRC, OUT, np, pd, sha256, jsave, row_identity, metadata_identity
from .producer import (compact_values, assemble_pair, requirements, validate_shard,
    projection_arrays, lookup_delta, changed_positions, tokenize_lists,
    validate_backend_receipt, production_guard, CHECKPOINT_SHA, certified_batch)
from .routes import module
from .common import IDENTITY, inner_regret, decisions
from .engine import checkpoint, checkpoint_identity, select_config
from .verify import independent_decisions, independent_regret, assert_disjoint, independent_scores, score_error, ERROR_METRICS, bounded_canonical_scores
from .gate import strict_checks, incremental_checks, shared_bootstrap
from .assemble import validate_control_reference
from .common import ROOT, NEXT_ART, NEXT_OUT, CONTROL_TRACKS
from src.cross_assay_20260927.models import purge


class DownstreamTests(unittest.TestCase):
    def setUp(self):
        self.pg, self.pl = projection_arrays()
        self.parent, self.mutant = "ACGTACGT", "TCGTACGA"
        rng = np.random.default_rng(103)
        self.hp = rng.normal(size=(10, 512)).astype(np.float32)
        self.hm = rng.normal(size=(10, 512)).astype(np.float32)

    def compact(self, parent=None, mutant=None, hp=None, hm=None):
        parent, mutant = parent or self.parent, mutant or self.mutant
        hp, hm = self.hp if hp is None else hp, self.hm if hm is None else hm
        positions = changed_positions(parent, mutant).astype(np.int16)
        gp, tp = compact_values(hp, len(parent), positions, self.pg, self.pl)
        gm, tm = compact_values(hm, len(mutant), positions, self.pg, self.pl)
        return {parent: (gp, positions, tp), mutant: (gm, positions, tm)}

    def test_compact_pool_projection_commutes(self):
        positions = changed_positions(self.parent, self.mutant)
        actual = assemble_pair(self.parent, self.mutant, self.compact())
        expected = np.r_[(self.hm[1:-1].mean(0) - self.hp[1:-1].mean(0)) @ self.pg,
            (self.hm[positions + 1] - self.hp[positions + 1]).mean(0) @ self.pl]
        np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=6e-6)

    def test_reversal_and_no_edit(self):
        summaries = self.compact()
        a = assemble_pair(self.parent, self.mutant, summaries)
        b = assemble_pair(self.mutant, self.parent, summaries)
        np.testing.assert_array_equal(a, -b)
        np.testing.assert_array_equal(assemble_pair(self.parent, self.parent, summaries), np.zeros(256))
        np.testing.assert_array_equal(lookup_delta(self.parent, self.mutant, self.pg, self.pl),
            -lookup_delta(self.mutant, self.parent, self.pg, self.pl))

    def test_special_exclusion_and_single_base_lookup(self):
        hp = np.zeros((10, 512), dtype=np.float32); hm = hp.copy()
        ids = {base: index for index, base in enumerate("ACGT")}
        for index, (p, m) in enumerate(zip(self.parent, self.mutant)):
            hp[index + 1, ids[p]] = 1; hm[index + 1, ids[m]] = 1
        hp[0] = 400; hm[-1] = -900
        actual = assemble_pair(self.parent, self.mutant, self.compact(hp=hp, hm=hm))
        np.testing.assert_allclose(actual, lookup_delta(self.parent, self.mutant, self.pg, self.pl), rtol=1e-5, atol=3e-7)
        self.assertLessEqual(np.linalg.matrix_rank(self.pg[:4]), 4)
        np.testing.assert_array_equal(changed_positions(self.parent, self.mutant), [0, 7])

    def test_token_ids_and_padding(self):
        encoded = tokenize_lists(["ACGT", "AC"])
        self.assertEqual(encoded["input_ids"], [[2, 6, 7, 8, 9, 3], [2, 6, 7, 3, 0, 0]])
        self.assertEqual(encoded["attention_mask"], [[1] * 6, [1, 1, 1, 1, 0, 0]])
        self.assertEqual(encoded["token_type_ids"], [[0] * 6, [0] * 6])
        with self.assertRaises(AssertionError):
            tokenize_lists(["ACGN"])

    def test_certified_tail_batch_duplicate_only(self):
        self.assertEqual(certified_batch(["ACGT"]), ["ACGT", "ACGT"])
        self.assertEqual(certified_batch(["ACGT", "TCGT"]), ["ACGT", "TCGT"])
        with self.assertRaises(AssertionError):
            certified_batch(["AC", "ACGT"])

    def test_required_positions_and_identity(self):
        frame = pd.DataFrame({"intervention_id": ["x", "y"], "dataset": ["srle", "srle"],
            "biological_component": ["c", "c"], "parent_context_id": ["p", "p"],
            "parent_sequence": [self.parent, self.parent], "mutant_sequence": [self.mutant, "ACCTACGT"]})
        required, alleles = requirements(frame)
        self.assertEqual(required[self.parent], {0, 2, 7})
        self.assertEqual(len(alleles), 3)
        edited = frame.copy(); edited.loc[0, "mutant_sequence"] = "CCGTACGA"
        self.assertNotEqual(row_identity(frame), row_identity(edited))
        self.assertNotEqual(metadata_identity(frame), metadata_identity(frame.iloc[::-1]))

    def test_shard_content_receipt_and_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shard.npz"
            hashes = np.asarray(["a" * 64, "b" * 64]); offsets = np.asarray([0, 2, 3]); positions = np.asarray([0, 7, 2], dtype=np.int16)
            np.savez_compressed(path, allele_hashes=hashes, offsets=offsets, positions=positions,
                globals=np.zeros((2, 128), np.float32), tokens=np.zeros((3, 128), np.float32))
            sidecar = {"sha256": sha256(path), "spec_sha256": "s" * 64, "allele_hashes": hashes.tolist()}
            path.with_suffix(".json").write_text(json.dumps(sidecar))
            validate_shard(path, hashes, offsets, positions, "s" * 64)
            with self.assertRaises(AssertionError):
                validate_shard(path, hashes, offsets, positions, "t" * 64)
            with self.assertRaises(AssertionError):
                validate_shard(path, hashes[::-1], offsets, positions, "s" * 64)
            payload = bytearray(path.read_bytes()); payload[-1] ^= 1; path.write_bytes(payload)
            with self.assertRaises(AssertionError):
                validate_shard(path, hashes, offsets, positions, "s" * 64)

    def test_backend_admission_refuses_failed_or_incomplete_parity(self):
        backend = {"status": "PASS", "scope": "SYNTHETIC_CPU_BACKEND_ADMISSION_ONLY", "checkpoint_sha256": CHECKPOINT_SHA,
            "project_alleles_inferred": 0, "models_fit": 0, "outcomes_used": False, "synthetic_alleles": 16, "CPU_threads": 2,
            "comparisons": [{"length_nt": length, "checks": {"check": True}, "maximum_hidden_absolute_difference": .0001,
                "mean_hidden_absolute_difference": .00001, "minimum_token_cosine": 1.} for length in [46, 46, 150, 150, 190, 190, 260, 260]]}
        validate_backend_receipt(backend)
        bad = copy.deepcopy(backend); bad["comparisons"][0]["maximum_hidden_absolute_difference"] = .002
        with self.assertRaises(AssertionError):
            validate_backend_receipt(bad)
        bad = copy.deepcopy(backend); bad["comparisons"].pop()
        with self.assertRaises(AssertionError):
            validate_backend_receipt(bad)
        bad = copy.deepcopy(backend); bad["outcomes_used"] = True
        with self.assertRaises(AssertionError):
            validate_backend_receipt(bad)

    def test_fixed_grid_and_no_automatic_heavy_work(self):
        for track in ("base", "raw", "structure", "lookup", "splicebert", "combined"):
            configs = module(track).CONFIGS
            self.assertEqual([config["penalty"] for config in configs], [.005, .05, .5])
            self.assertTrue(all(config["scaling"] == "pair" for config in configs))
        with self.assertRaises(AssertionError):
            production_guard(root_start=False)
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("openvino", sys.modules)
        self.assertNotIn("transformers", sys.modules)

    def frame(self):
        rows = []
        for index, parent in enumerate(["AAAAAA", "CCCCCC", "GGGGGG", "TTTTTT"]):
            for candidate, effect in enumerate([-.5, .7]):
                base = "ACGT"[(index + candidate + 1) % 4]
                rows.append({"intervention_id": f"s{index}_{candidate}", "dataset": f"source{index}",
                    "biological_component": f"c{index}", "parent_context_id": f"p{index}",
                    "parent_sequence": parent, "mutant_sequence": base + parent[1:],
                    "endpoint_class": "projection", "measured_delta": effect, "primary_eligible": True})
        return pd.DataFrame(rows)

    def test_original_allele_component_purge_and_inner_exclusion(self):
        frame = self.frame(); test = frame.dataset.eq("source0").to_numpy()
        train = purge(frame, ~test, test)
        assert_disjoint(frame.loc[train], frame.loc[test])
        self.assertNotIn("source0", frame.loc[train, "dataset"].unique())
        shared = frame.copy(); shared.loc[2:3, "biological_component"] = "c0"
        train = purge(shared, ~test, test)
        self.assertFalse(train[2] or train[3])
        inconsistent = frame.copy(); inconsistent.loc[2, "mutant_sequence"] = frame.loc[0, "parent_sequence"]
        with self.assertRaises(AssertionError):
            purge(inconsistent, ~test, test)
        source = frame.loc[~test].reset_index(drop=True)
        held = source.dataset.eq("source1").to_numpy(); permitted = purge(source, ~held, held)
        assert_disjoint(source.loc[permitted], source.loc[held])
        self.assertNotIn("source1", source.loc[permitted, "dataset"].unique())

    def test_original_truth_independent_choices_regret_and_ties(self):
        frame = self.frame()
        score = np.asarray([0., 0., -1., 1., 1., -1., -.2, .5])
        actual = independent_decisions(frame, score, include_ranking=True).sort_values(["parent_context_id", "direction"]).reset_index(drop=True)
        shared = decisions(frame, score, "test").sort_values(["parent_context_id", "direction"]).reset_index(drop=True)
        self.assertEqual(actual.selected_id.tolist(), shared.selected_id.tolist())
        for metric in ERROR_METRICS + ("candidates", "selected_effect", "selected_score", "best_recovery", "top5_best_recovery", "pairwise_accuracy"):
            np.testing.assert_allclose(actual[metric], shared[metric], atol=1e-12, rtol=0)
        self.assertAlmostEqual(independent_regret(frame, score), inner_regret(frame, score), places=12)
        configs = module("splicebert").CONFIGS
        self.assertEqual(select_config(configs, [.2 + 5e-13, .2, .3]), configs[0])
        self.assertEqual(select_config(configs, [.2 + 2e-12, .2, .3]), configs[1])

    def test_independent_blocked_score_formula_and_bound(self):
        rng = np.random.default_rng(128)
        matrix = rng.normal(size=(2053, 17))
        model = {"beta": rng.normal(size=17).tolist(), "mean": rng.normal(size=17).tolist(),
            "scale": rng.uniform(.2, 2, size=17).tolist()}
        independent = independent_scores(model, matrix)
        actual = module("splicebert").predict_model(model, matrix)
        self.assertLess(score_error(independent, actual), 1e-12)
        with self.assertRaises(AssertionError):
            score_error(independent, actual + .001)
        bad = copy.deepcopy(model); bad["scale"][0] = 0
        with self.assertRaises(AssertionError):
            independent_scores(bad, matrix)

    def test_independent_error_categories_and_pair_recovery(self):
        cases = [([-1., -.2], [1., 0.]), ([-1., 0.], [1., 0.]), ([-1., .3], [1., 0.]),
            ([-2e-12, .5e-12], [1., 0.]), ([-1., 0., 0., 1., .5, -.5], [0., 1., 0., 1., 0., -1.])]
        increased = []
        for number, (labels, scores) in enumerate(cases):
            frame = pd.DataFrame({"intervention_id": [f"x{index}" for index in range(len(labels))],
                "dataset": "synthetic", "biological_component": "component", "parent_context_id": "context", "measured_delta": labels})
            actual = independent_decisions(frame, np.asarray(scores), include_ranking=True).sort_values("direction").reset_index(drop=True)
            shared = decisions(frame, np.asarray(scores), "test").sort_values("direction").reset_index(drop=True)
            self.assertEqual(actual.selected_id.tolist(), shared.selected_id.tolist())
            for metric in ERROR_METRICS + ("candidates", "selected_effect", "selected_score", "best_recovery", "top5_best_recovery", "pairwise_accuracy"):
                np.testing.assert_allclose(actual[metric], shared[metric], atol=1e-12, rtol=0)
            increased.append(actual[actual.direction.eq(1)].iloc[0])
        self.assertEqual(increased[0].unavoidable_wrong, 1.)
        self.assertEqual(increased[0].no_feasible_candidate, 1.)
        self.assertEqual(increased[1].neutral_only_alternative_wrong, 1.)
        self.assertEqual(increased[1].unavoidable_wrong, 0.)
        self.assertEqual(increased[2].avoidable_wrong, 1.)
        self.assertEqual(increased[2].no_feasible_candidate, 0.)
        self.assertEqual(increased[3].neutral_only_alternative_wrong, 1.)

    def test_canonical_ties_retained_after_independent_rounding_bound(self):
        matrix = np.asarray([[1e16, 1., -1e16], [1e16, 0., -1e16]])
        model = {"beta": [1e-12] * 3, "mean": [0.] * 3, "scale": [1.] * 3}
        canonical, independent, error = bounded_canonical_scores(model, matrix, module("splicebert").predict_model)
        self.assertLess(error, 1e-9)
        self.assertEqual(canonical[0], canonical[1])
        self.assertNotEqual(independent[0], independent[1])
        frame = pd.DataFrame({"intervention_id": ["a", "b"], "dataset": "synthetic", "biological_component": "component",
            "parent_context_id": "context", "measured_delta": [-1., .3]})
        choices = independent_decisions(frame, canonical).set_index("direction")
        alternate = independent_decisions(frame, independent).set_index("direction")
        self.assertEqual(choices.loc[-1, "selected_id"], "a")
        self.assertEqual(alternate.loc[-1, "selected_id"], "b")

    def test_mocked_checkpoint_creation_resume_and_reject_mutations(self):
        frame = self.frame(); matrix = np.arange(len(frame) * 3, dtype=float).reshape(len(frame), 3)
        config = module("splicebert").CONFIGS[0]
        captured = []
        def fake_fit(training, values, supplied):
            captured.append(training.measured_delta.to_numpy().copy())
            return {"config": supplied, "training_rows": len(training), "beta": [0.] * values.shape[1],
                "mean": [0.] * values.shape[1], "scale": [1.] * values.shape[1]}
        def temp_jsave(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            assert not path.exists(); path.write_text(json.dumps(value, sort_keys=True))
        def temp_save(path, value):
            assert not path.exists(); path.write_bytes(value)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("src.generalization_splicebert_downstream_20261007.engine.OUT", root), \
                 patch("src.generalization_splicebert_downstream_20261007.engine.jsave", temp_jsave), \
                 patch("src.generalization_splicebert_downstream_20261007.engine.save", temp_save), \
                 patch("src.generalization_splicebert_downstream_20261007.engine.module", return_value=SimpleNamespace(fit_model=fake_fit)):
                model = checkpoint("splicebert", "synthetic", frame, matrix, config, "feature", "freeze", "core")
                same = checkpoint("splicebert", "synthetic", frame, matrix, config, "feature", "freeze", "core")
                self.assertEqual(model, same); self.assertEqual(len(captured), 1)
                np.testing.assert_array_equal(captured[0], frame.measured_delta)
                changed = frame.copy(); changed.loc[0, "measured_delta"] += .1
                with self.assertRaises(AssertionError):
                    checkpoint("splicebert", "synthetic", changed, matrix, config, "feature", "freeze", "core")
                with self.assertRaises(AssertionError):
                    checkpoint("splicebert", "synthetic", frame, matrix + 1, config, "feature", "freeze", "core")
                with self.assertRaises(AssertionError):
                    checkpoint("splicebert", "synthetic", frame, matrix, config, "feature", "different", "core")
                changed_config = {**config, "penalty": .05}
                with self.assertRaises(AssertionError):
                    checkpoint("splicebert", "synthetic", frame, matrix, changed_config, "feature", "freeze", "core")
                path = root / "splicebert/fits" / ("synthetic_" + config["id"] + ".json")
                payload = json.loads(path.read_text()); payload["beta"][0] = 1.; path.write_text(json.dumps(payload))
                with self.assertRaises(AssertionError):
                    checkpoint("splicebert", "synthetic", frame, matrix, config, "feature", "freeze", "core")

    def test_strict_gate_information_controls_and_correlated_bootstrap(self):
        checks, share = strict_checks([.42] * 4, [.03] * 4, [.02] * 4, [0.] * 4, [0.] * 4, np.full(5000, .03))
        self.assertTrue(all(checks.values())); self.assertEqual(share, .25)
        checks, _ = strict_checks([.42] * 4, [.07, -.02, .07, .07], [.02] * 4, [0.] * 4, [0.] * 4, np.full(5000, .03))
        self.assertFalse(checks["Mikl_SRLE_harm_at_most_0_01_vs_both"])
        checks, _ = strict_checks([.42] * 4, [.03] * 4, [.02] * 4, [0.] * 4, [0.] * 4, np.full(5000, -.02))
        self.assertFalse(checks["descriptive_bootstrap_lower_at_least_minus_0_01"])
        self.assertTrue(all(incremental_checks([.012] * 4).values()))
        self.assertFalse(incremental_checks([.04, 0, 0, 0])["incremental_leave_best_assay_out_positive"])
        values = pd.Series([1., -1.], index=["sharedA", "sharedB"])
        one = shared_bootstrap({"a": values}, draws=5000, seed=20261007)
        both = shared_bootstrap({"a": values, "b": values}, draws=5000, seed=20261007)
        np.testing.assert_array_equal(one, both)

    def test_shared_control_hashes_bind_to_prior_prefit(self):
        actual = {(NEXT_OUT / "prepare_receipt.json").relative_to(ROOT).as_posix(): "receipt_sha"}
        actual.update({(NEXT_ART / (track + "_model_features.npz")).relative_to(ROOT).as_posix(): track + "_sha" for track in CONTROL_TRACKS})
        reference = {"status": "FROZEN_PREFIT", "files": dict(actual)}
        validate_control_reference(reference, actual)
        changed = copy.deepcopy(reference); changed["files"][next(iter(actual))] = "different"
        with self.assertRaises(AssertionError):
            validate_control_reference(changed, actual)
        changed = copy.deepcopy(reference); changed["status"] = "FROZEN_PRODUCTION"
        with self.assertRaises(AssertionError):
            validate_control_reference(changed, actual)


def run(receipt_filename="synthetic_tests_receipt_final_review.json"):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DownstreamTests))
    assert result.wasSuccessful()
    jsave(OUT / receipt_filename, {"status": "PASS", "tests": result.testsRun,
        "source_hashes": {path.name: sha256(path) for path in sorted(SRC.glob("*.py"))},
        "scope": "Synthetic arithmetic/token/cache/guard tests only", "actual_model_imports": 0, "project_allele_inference": 0,
        "outcomes_read": False, "models_fit": 0})


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
