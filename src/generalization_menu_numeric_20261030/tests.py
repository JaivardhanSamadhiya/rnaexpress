"""Stdlib-only boundary checks, distinct from deferred numerical certification."""
import ast
import math
from pathlib import Path
import sys
import unittest
from . import cases, engine, policy
from src.generalization_menu_bound_reference_20261026.reference import evaluate
from src.generalization_menu_comparison_core_20261026 import layout


class SourceTests(unittest.TestCase):
    def test_default_floor_and_all_reserves(self):
        good = dict(physical_available=3*2**30,commit_headroom=1920*2**20,disk_available=2**30)
        self.assertIsNone(policy.resource_failure(good,0))
        for field in good:
            bad = dict(good);bad[field] -= 1
            self.assertIsNotNone(policy.resource_failure(bad,0),field)
        self.assertIsNotNone(policy.resource_failure(good,policy.DEADLINE+.01))
        for elapsed in (-1.,math.nan,math.inf):self.assertIsNotNone(policy.resource_failure(good,elapsed))

    def test_adversarial_fixture_is_valid_and_has_multiple_menu_sizes(self):
        rows,x,y,sampled = cases.problem()
        menu = layout.menus(rows,range(len(rows)))
        self.assertEqual({len(m['indices']) for m in menu},{2,3})
        self.assertEqual({r['dataset'] for r in rows},set(layout.STUDIES))
        self.assertNotEqual(len({m['weight'] for m in menu}),1)
        self.assertTrue(any(len({y[i] for i in m['indices']}) < len(m['indices']) for m in menu))
        for arm in layout.ARMS:
            got = evaluate(beta=(.12,-.23,0.,0.),features=x,effects=y,source_metadata=rows,
                           sampled_pairs=sampled,arm=arm,penalty=.05)
            self.assertEqual(got['source_scaling']['active'],(True,True,False,False))

    def test_deferred_engine_imports_no_scientific_package_or_file_reader(self):
        tree = ast.parse(Path(engine.__file__).read_text())
        imported = []
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imported.extend(a.name for a in node.names)
            if isinstance(node,ast.ImportFrom):imported.append(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,('open','eval','exec','__import__'))
        self.assertEqual(imported,['math','src.generalization_menu_comparison_core_20261026'])
        self.assertFalse(any(k.split('.')[0] in ('numpy','pandas','scipy','torch') for k in sys.modules))

    def test_optimizer_options_preserved(self):
        self.assertEqual(engine.OPTIONS,dict(maxiter=500,ftol=1e-11,gtol=1e-7))
        self.assertEqual(engine.TEMPERATURE,.25)

    def test_large_fixture_crosses_block_and_pair_caps(self):
        rows,x,y,sampled = cases.large_problem()
        self.assertEqual(len(rows),208)
        self.assertEqual(len(sampled),8)
        self.assertTrue(all(len(pairs) == 256 for pairs in sampled.values()))
        got = evaluate(beta=(.12,-.23,0.,0.),features=x,effects=y,source_metadata=rows,
                       sampled_pairs=sampled,arm='menu_cost',penalty=.05)
        self.assertGreater(got['valid_source_pairs'],256)

    def test_checkpoint_support_rejects_strings_before_numeric_coercion(self):
        with self.assertRaisesRegex(ValueError,'actual booleans'):
            engine.scores(None,dict(active=[True,'False']),[])

    def test_reference_rejects_same_omission_as_deferred_checks(self):
        rows,x,y,sampled = cases.problem()
        del sampled[next(iter(sampled))]
        with self.assertRaisesRegex(ValueError,'pair/context roster'):
            evaluate(beta=(0.,0.,0.,0.),features=x,effects=y,source_metadata=rows,
                     sampled_pairs=sampled,arm='menu_cost',penalty=.05)

    def test_new_runtime_does_not_reuse_old_native_anchor_values(self):
        self.assertEqual(policy.NEW_SHA,'38494d53203c0649321c99092616b52e800ca1fda651a4354c99c4701521b5bc')
        self.assertNotEqual(policy.NEW_INVENTORY,policy.OLD_INVENTORY)
        self.assertEqual(policy.CACHE.name,'source_cache_must_remain_absent')


if __name__ == '__main__':unittest.main()
