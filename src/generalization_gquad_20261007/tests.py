"""Scoped stdlib synthetic/mock tests; zero native/numerical/model imports."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from . import spec, guards, production

def pure_backend():
    tree = ast.parse((guards.ROOT / 'src/generalization_gquad_feasibility_20261007/backend.py').read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('normalize', 'gq_patterns')]
    scope = {}; exec(compile(ast.Module(body=functions, type_ignores=[]), '<reviewed-pure-pattern-functions>', 'exec'), scope)
    return types.SimpleNamespace(**scope)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = pure_backend()

    def test_shapes_and_fixed_grid(self):
        self.assertEqual(spec.SHAPES, dict(zip(spec.TRACKS, [246, 258, 274, 260, 276])))
        self.assertEqual(spec.SPEC['penalties'], [.005, .05, .5]); self.assertEqual(spec.ELIGIBLE, ['physical', 'combined'])
        self.assertEqual(len(spec.RAW_NAMES), 12); self.assertEqual(len(spec.PHYSICS_NAMES), 2)

    def test_complete_one_two_layer_box(self):
        self.assertEqual(list(self.backend.gq_patterns('GGAGGAGGAGG')), [(0, 11, 2, (1, 1, 1))])

    def test_three_layers_and_DNA_RNA_parity(self):
        a = list(self.backend.gq_patterns('GGGAGGGAGGGAGGG'))
        self.assertIn((0, 15, 3, (1, 1, 1)), a)
        self.assertEqual(list(self.backend.gq_patterns('GGUGGUGGUGG')), list(self.backend.gq_patterns('GGTGGTGGTGG')))

    def test_layers_bounds(self):
        for n in (2, 7):
            s = ('G' * n + 'A') * 3 + 'G' * n
            self.assertIn((0, len(s), n, (1, 1, 1)), list(self.backend.gq_patterns(s)))
        self.assertTrue(all(2 <= p[2] <= 7 for p in self.backend.gq_patterns('G' * 8 + 'A' + 'G' * 8 + 'A' + 'G' * 8 + 'A' + 'G' * 8)))

    def test_linker_bound_and_disruption(self):
        s = 'GG' + ('A' * 15 + 'GG') * 3
        self.assertEqual(list(self.backend.gq_patterns(s)), [(0, 53, 2, (15, 15, 15))])
        self.assertEqual(list(self.backend.gq_patterns('GG' + ('A' * 16 + 'GG') * 3)), [])
        self.assertEqual(list(self.backend.gq_patterns('GAAGGAGGAGG')), [])

    def test_negative_all_production_lengths(self):
        for n in (46, 150, 190, 260):
            self.assertEqual(list(self.backend.gq_patterns('A' * n)), [])
            self.assertEqual(spec.count_pools([], n, [(0,), (n - 1,)])[0], [0] * 6)

    def test_half_open_boundaries(self):
        patterns = [(1, 12, 2, (1, 1, 1))]
        global_c, local = spec.count_pools(patterns, 13, [(0,), (1,), (11,), (12,)])
        self.assertEqual(global_c, [1, 0, 0, 0, 0, 0]); self.assertEqual([c[0] for c in local], [0, 1, 1, 0])

    def test_linker_and_multiple_changes_count_once(self):
        g, local = spec.count_pools([(0, 11, 2, (1, 1, 1))], 11, [(2,), (0, 2, 10)])
        self.assertEqual(g[0], 1); self.assertEqual([v[0] for v in local], [1, 1])

    def test_overlapping_boxes_are_separate(self):
        p = [(0, 11, 2, (1, 1, 1)), (1, 12, 2, (1, 1, 1))]
        self.assertEqual(spec.count_pools(p, 12, [(5,)])[0][0], 2)
        self.assertEqual(spec.count_pools(p, 12, [(5,)])[1][0][0], 2)

    def test_log_before_delta_and_reversal(self):
        a, b = spec.transformed_counts([1, 0, 0, 0, 0, 0]), spec.transformed_counts([3, 0, 0, 0, 0, 0])
        r, v = spec.delta_blocks(a, a, [-1., .3], b, b, [-2., .7])
        reverse_r, reverse_v = spec.delta_blocks(b, b, [-2., .7], a, a, [-1., .3])
        self.assertEqual(r[0], math.log(4) - math.log(2)); self.assertNotEqual(r[0], math.log1p(2))
        self.assertEqual(r, [-x for x in reverse_r]); self.assertEqual(v, [-x for x in reverse_v])

    def test_no_edit_delta_zero(self):
        a = spec.transformed_counts([3, 1, 0, 0, 0, 0])
        self.assertEqual(spec.delta_blocks(a, a, [-1., .8], a, a, [-1., .8]), ([0.] * 12, [0.] * 2))

    def test_requests_coordinates_union_exact(self):
        rows = [{'parent_sequence': 'ACGT', 'mutant_sequence': 'TCGT'}, {'parent_sequence': 'ACGT', 'mutant_sequence': 'ACGA'}]
        r, p = spec.request_plan(rows)
        self.assertEqual(p, [(0,), (3,)]); self.assertEqual(r['ACGT'], [(0,), (3,)])
        with self.assertRaises(AssertionError): spec.request_plan([{'parent_sequence': 'ACGT', 'mutant_sequence': 'ACGT'}])

    def test_position_validation(self):
        for requested in ([()], [(-1,)], [(11,)], [(2, 2)], [(3, 2)]):
            with self.assertRaises(AssertionError): spec.count_pools([], 11, requested)

    def test_endpoint_policy_is_exact(self):
        self.assertEqual(spec.ENDPOINT_SIGNS, {'projection': 1., 'nuclear_cytoplasmic': -1.})
        source = (guards.SRC / 'routes.py').read_text()
        self.assertIn('original * signs', source); self.assertIn('pair_predict(model, matrix) * endpoint_sign(frame)', source)
        self.assertIn('sign_is_learned_feature', source); self.assertNotIn('frame.dataset', source)

    def test_selection_order_fixed_tolerance(self):
        self.assertEqual(spec.select_index([.2, .2 - 5e-13, .4]), 0)
        self.assertEqual(spec.select_index([.2, .2 - 2e-12, .4]), 1)

    def test_incremental_gate_concentration_and_exact(self):
        self.assertTrue(all(spec.incremental_checks([.01, .01, .01, .01]).values()))
        self.assertFalse(spec.incremental_checks([.08, 0., 0., 0.])['incremental_leave_best_assay_out_positive'])
        self.assertEqual(spec.INCREMENTAL, {'physical': ['raw'], 'combined': ['ordinary_raw', 'physical']})

    def test_strict_gate_matches_original_function(self):
        def function(path, name):
            return next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
        old = function(guards.ROOT / 'src/generalization_splicebert_downstream_20261007/gate.py', 'strict_checks')
        new = function(guards.SRC / 'gate.py', 'strict_checks')
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))

    def test_path_normalization_collision_rejected(self):
        self.assertEqual(guards.canonical_map({'a\\b': 'x'}), {'a/b': 'x'})
        for mapping in ({'a\\b': 'x', 'a/b': 'x'}, {'A/b': 'x', 'a/b': 'x'}, {'../x': 'x'}, {'D:/x': 'x'}):
            with self.assertRaises(AssertionError): guards.canonical_map(mapping)

    def test_immutable_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / 'result.json'
            with patch.object(guards, 'OUT', root):
                guards.save(path, b'one'); guards.save(path, b'one')
                with self.assertRaises(AssertionError): guards.save(path, b'two')

    def test_first_creation_digest_tamper_or_orphan(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.json'; sequence = 'GGAGGAGGAGG'; requested = [(0,)]
            ident = {'synthetic': 'identity'}
            value = {'identity': ident, 'sequence': sequence, 'length': 11, 'keys': ['0'],
                'global_counts': [1, 0, 0, 0, 0, 0], 'local_counts': [[1, 0, 0, 0, 0, 0]],
                'global_raw': spec.transformed_counts([1, 0, 0, 0, 0, 0]),
                'local_raw': [spec.transformed_counts([1, 0, 0, 0, 0, 0])], 'physics': [-.1, .1],
                'native_measure': {'G_on_minus_off': -.1, 'modeled_at_least_one_GQ_probability': .1}}
            path.write_text(json.dumps(value)); birth_path = path.with_suffix('.birth.json')
            with patch.object(production, 'identity', lambda s, r: ident):
                with self.assertRaises(FileNotFoundError): production.validate(sequence, requested, path)
                birth_path.write_text(json.dumps({'identity': ident, 'cache_sha256': guards.sha256(path), 'role': 'IMMUTABLE_DIGEST_AT_FIRST_CREATION_NOT_RETROACTIVE'}))
                self.assertEqual(production.validate(sequence, requested, path)['physics'], [-.1, .1])
                path.write_text(json.dumps({**value, 'physics': [-.2, .2]}))
                with self.assertRaises(AssertionError): production.validate(sequence, requested, path)

    def test_full_namespace_AST(self):
        for path in guards.SRC.glob('*.py'): ast.parse(path.read_text())
        text = (guards.SRC / 'verify.py').read_text()
        self.assertIn('inner_count == 180 and outer_count == 20', text)
        self.assertIn('set(saved_d.model) == {track}', text)
        self.assertIn('independent_scores(model, matrix) * endpoint_sign(frame)', text)

    def test_fresh_resource_floors_mocked(self):
        def available(gib):
            def check(pointer):
                pointer._obj.avail_phys = int(gib * 2**30)
                return 1
            return types.SimpleNamespace(kernel32=types.SimpleNamespace(GlobalMemoryStatusEx=check))
        with patch.object(guards.ctypes, 'windll', available(1.1)), patch.object(guards.shutil, 'disk_usage', lambda p: types.SimpleNamespace(free=2**31)):
            self.assertEqual(guards.resource_check('production')['required_RAM_GiB'], 1.)
            with self.assertRaises(AssertionError): guards.resource_check('fit')
        with patch.object(guards.ctypes, 'windll', available(3.1)), patch.object(guards.shutil, 'disk_usage', lambda p: types.SimpleNamespace(free=2**31)):
            self.assertEqual(guards.resource_check('fit')['required_RAM_GiB'], 3.)
        with patch.object(guards.ctypes, 'windll', available(3.1)), patch.object(guards.shutil, 'disk_usage', lambda p: types.SimpleNamespace(free=2**29)):
            with self.assertRaises(AssertionError): guards.resource_check('production')

if __name__ == '__main__':
    unittest.main()
